#!/usr/bin/env python3
"""Bounded Govulncheck binary-mode evidence; never executes the audited target."""
from __future__ import annotations

import argparse
import collections
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

from check_dependency_review import ID, query
from check_go_dependency_review import ARCHIVES, parse_build, sha256_stream, verify_binary
from check_nvidia_tier1 import require
from check_official_local_install import InstallCheckError, fixture_env

PIN = "ef4cb2f7cae47fe3e21fc596455f694951867b29"
DB = "https://vuln.go.dev"
MAX_OUTPUT = 32 * 1024 * 1024
MAX_MESSAGES = 100000
GO_VERSION = re.compile(r"go[0-9]+\.[0-9]+(?:\.[0-9]+)?\Z")


def messages(raw):
    require(isinstance(raw, bytes) and 0 < len(raw) <= MAX_OUTPUT, "GOVULN_OUTPUT_LIMIT")
    text = raw.decode("utf-8", errors="strict")
    decoder = json.JSONDecoder()
    pos = count = 0
    while pos < len(text):
        while pos < len(text) and text[pos] in " \t\r\n":
            pos += 1
        if pos == len(text):
            break
        value, pos = decoder.raw_decode(text, pos)
        count += 1
        require(count <= MAX_MESSAGES and isinstance(value, dict), "GOVULN_PROTOCOL_INVALID")
        yield value


def extract_evidence(raw):
    rows = list(messages(raw))
    require(len(rows) == 2 and rows[0] == {"name": "govulncheck-extract", "version": "0.1.0"},
            "GOVULN_EXTRACT_PROTOCOL")
    body = rows[1]
    version = body.get("goVersion")
    require(isinstance(version, str) and GO_VERSION.fullmatch(version), "GOVULN_GO_VERSION")
    require(body.get("goos") == "linux" and body.get("goarch") == "amd64",
            "GOVULN_PLATFORM_UNVERIFIED")
    modules = body.get("modules")
    require(isinstance(modules, list) and 0 < len(modules) <= 400, "GOVULN_MODULE_INVENTORY")
    symbols = body.get("pkgSymbols", [])
    require(isinstance(symbols, list) and len(symbols) <= 500000, "GOVULN_SYMBOL_INVENTORY")
    for row in symbols:
        require(isinstance(row, dict) and isinstance(row.get("pkg"), str)
                and 0 < len(row["pkg"]) <= 1024 and isinstance(row.get("name"), str)
                and 0 < len(row["name"]) <= 4096, "GOVULN_SYMBOL_INVALID")
    return {"go_version": version, "modules_extracted": len(modules),
            "symbols_extracted": len(symbols),
            "symbol_evidence": "EXTRACTED" if symbols else "MODULE_ONLY_FALLBACK"}


def scan_evidence(raw, extraction):
    config = sbom = None
    ids = set()
    levels = {}
    for index, row in enumerate(messages(raw)):
        require(len(row) == 1, "GOVULN_PROTOCOL_INVALID")
        key, value = next(iter(row.items()))
        require(isinstance(value, dict), "GOVULN_PROTOCOL_INVALID")
        if index == 0:
            require(key == "config", "GOVULN_CONFIG_MISSING")
        if key == "config":
            require(config is None and value.get("protocol_version") == "v1.0.0"
                    and value.get("scanner_name") == "govulncheck"
                    and isinstance(value.get("scanner_version"), str)
                    and value["scanner_version"].startswith("v0.0.0-" + PIN[:12])
                    and value.get("db") == DB and value.get("scan_mode") == "binary"
                    and value.get("scan_level") == "symbol", "GOVULN_CONFIG_INVALID")
            config = value
        elif key == "SBOM":
            require(sbom is None and value.get("go_version") == extraction["go_version"]
                    and isinstance(value.get("modules"), list) and bool(value["modules"]),
                    "GOVULN_SBOM_INVALID")
            sbom = value
        elif key == "osv":
            ident = value.get("id")
            require(isinstance(ident, str) and ID.fullmatch(ident), "GOVULN_ID_INVALID")
            ids.add(ident)
        elif key == "finding":
            ident, trace = value.get("osv"), value.get("trace")
            require(isinstance(ident, str) and ID.fullmatch(ident)
                    and isinstance(trace, list) and len(trace) == 1
                    and isinstance(trace[0], dict), "GOVULN_FINDING_INVALID")
            frame = trace[0]
            require(isinstance(frame.get("module"), str) and bool(frame["module"]),
                    "GOVULN_FRAME_INVALID")
            rank = 3 if frame.get("function") else 2 if frame.get("package") else 1
            levels[ident] = max(levels.get(ident, 0), rank)
        else:
            require(key == "progress", "GOVULN_UNKNOWN_MESSAGE")
    require(config is not None and sbom is not None and set(levels) <= ids,
            "GOVULN_COVERAGE_UNVERIFIED")
    # Stripped executables can produce synthetic package/symbol findings.
    # Do not treat those findings as physical presence or call reachability.
    labels = {1: "MODULE", 2: "PACKAGE_REPORTED", 3: "SYMBOL_REPORTED"}
    findings = [{"id": ident, "level": ("MODULE_ONLY_FALLBACK"
                  if extraction["symbols_extracted"] == 0 else labels[rank])}
                for ident, rank in sorted(levels.items())]
    return {**extraction, "database_timestamp": "REPORTED" if config.get("db_last_modified")
            else "NOT_RECORDED", "advisory_records": len(ids),
            "findings": findings, "by_level": dict(collections.Counter(x["level"] for x in findings)),
            "call_reachability": "NOT_VERIFIED"}


def read_output(path):
    with path.open("rb") as stream:
        raw = stream.read(MAX_OUTPUT + 1)
    require(len(raw) <= MAX_OUTPUT, "GOVULN_OUTPUT_LIMIT")
    return raw


def scanner_inventory(raw, lookup=query):
    meta = raw.decode("utf-8", errors="strict")
    rows = meta.splitlines()
    require(sum(line.strip() == "path\tgolang.org/x/vuln/cmd/govulncheck" for line in rows) == 1
            and sum(line.strip() == "build\tvcs.revision=" + PIN for line in rows) == 1
            and sum(line.strip() == "build\tvcs.modified=false" for line in rows) == 1,
            "GOVULN_SCANNER_IDENTITY")
    build = parse_build(raw, "golang.org/x/vuln", "v1.10.0", PIN)
    require(build["source_revision"] == "MATCH" and not build["unversioned_modules"],
            "GOVULN_SCANNER_INVENTORY_UNVERIFIED")
    modules = build["modules"] + [(name, build["toolchain"]) for name in ("stdlib", "toolchain")]
    queries = [{"package": {"ecosystem": "Go", "name": name}, "version": version}
               for name, version in modules]
    queries.append({"commit": PIN})
    found = lookup(queries)
    require(len(found) == len(queries), "GOVULN_SCANNER_OSV_COVERAGE")
    return {"scope": "SCANNER_BUILD_METADATA_OSV", "toolchain": build["toolchain"],
            "modules": len(build["modules"]), "findings": [
                {"module": name, "version": version, "ids": ids}
                for (name, version), ids in zip(modules, found) if ids],
            "source_commit_ids": found[-1], "license_compliance": "NOT_VERIFIED",
            "call_reachability": "NOT_VERIFIED"}


def scanner_digest(cli):
    with cli.open("rb") as stream:
        return sha256_stream(stream, 128 * 1024 * 1024)[0]


def accept(cli, gh, gitleaks, gh_archive, gitleaks_archive):
    cli = cli.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="tessera-go-binary-") as folder:
        temp = pathlib.Path(folder)
        env = fixture_env(temp)
        env.update({"GOTOOLCHAIN": "local", "GOPROXY": "off", "GOSUMDB": "off",
                    "XDG_CONFIG_HOME": str(temp / "config"), "CGO_ENABLED": "0"})
        subprocess.run(["go", "telemetry", "off"], cwd=temp, env=env,
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=True, timeout=15)
        initial_digest = scanner_digest(cli)
        meta = subprocess.run(["go", "version", "-m", str(cli)], cwd=temp, env=env,
                              capture_output=True, check=True, timeout=15).stdout
        scanner = scanner_inventory(meta)
        reports = {}
        for label, binary, archive in (("gh", gh, gh_archive), ("gitleaks", gitleaks, gitleaks_archive)):
            digest = verify_binary(archive, binary, *ARCHIVES[label])
            binary = binary.resolve(strict=True)
            extract = temp / (label + ".extract")
            output = temp / (label + ".json")
            for args, path in ((["-mode=extract", "-db=" + DB, str(binary)], extract),
                               (["-mode=binary", "-scan=symbol", "-format=json", "-db=" + DB,
                                 str(extract)], output)):
                with path.open("wb") as out:
                    subprocess.run([str(cli), *args], cwd=temp, env=env,
                                   stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.DEVNULL,
                                   check=True, timeout=120)
                if path == extract:
                    extraction = extract_evidence(read_output(extract))
            require(verify_binary(archive, binary, *ARCHIVES[label]) == digest,
                    "GOVULN_TARGET_MUTATED")
            reports[label] = {**scan_evidence(read_output(output), extraction),
                              "binary_sha256": digest}
        require(scanner_digest(cli) == initial_digest, "GOVULN_SCANNER_MUTATED")
    return {"execution": "PASS", "policy": "ADVISORY_FINDINGS", "scanner_source": PIN,
            "scanner_sha256": initial_digest, "scanner_inventory": scanner,
            "scope": "GO_BINARY_EXTRACT_AND_BINARY_MODE", "telemetry": "OFF_REQUESTED",
            "network_sandbox": "NOT_IMPLEMENTED", "binaries": reports,
            "call_reachability": "NOT_VERIFIED", "live_positive_control": "NOT_IMPLEMENTED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("cli", "gh", "gitleaks", "gh-archive", "gitleaks-archive"):
        parser.add_argument("--" + flag, type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        result = accept(args.cli, args.gh, args.gitleaks, args.gh_archive, args.gitleaks_archive)
    except (InstallCheckError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + (str(exc) if isinstance(exc, InstallCheckError)
              else "GOVULN_RUNTIME_FAILED"), file=sys.stderr)
        return 1
    print("GO_BINARY_REVIEW_EXECUTION_PASS: " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
