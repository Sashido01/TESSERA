#!/usr/bin/env python3
"""T12.02.02.04: inspect Go build metadata without executing the audited binaries."""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import json
import hashlib
import tarfile
import pathlib
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

from check_dependency_review import query, NoRedirect, LICENSE_EXPRESSION
from check_nvidia_tier1 import require
from check_official_local_install import InstallCheckError, fixture_env

MODULE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._~/-]{0,199}\Z")
VERSION = re.compile(r"v[0-9][A-Za-z0-9.+-]{0,99}\Z")
GO = re.compile(r"go([0-9]+\.[0-9]+(?:\.[0-9]+)?(?:rc[0-9]+|beta[0-9]+)?)\Z")
ROOTS = {
    "gh": ("github.com/cli/cli/v2", "v2.105.0", "e1219499a578b69e3437adaa31cd60614e23c802"),
    "gitleaks": ("github.com/zricethezav/gitleaks/v8", "v8.30.1", "83d9cd684c87d95d656c1458ef04895a7f1cbd8e"),
}
MAX_RESPONSE = 1024 * 1024
MAX_ARCHIVE = 64 * 1024 * 1024
MAX_BINARY = 128 * 1024 * 1024
ARCHIVES = {
    "gh": ("79e7ab5db738c48777b696e374f8b428f0647debfb424f44d2f426370407fe2f",
           "gh_2.105.0_linux_amd64/bin/gh"),
    "gitleaks": ("551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb",
                 "gitleaks"),
}


def sha256_stream(stream, limit):
    size = 0
    digest = hashlib.sha256()
    while chunk := stream.read(1024 * 1024):
        size += len(chunk)
        require(size <= limit, "GO_INPUT_SIZE_LIMIT")
        digest.update(chunk)
    require(size > 0, "GO_INPUT_EMPTY")
    return digest.hexdigest(), size


def verify_binary(archive, binary, digest, member):
    require(archive.is_file() and not archive.is_symlink()
            and binary.is_file() and not binary.is_symlink(), "GO_ARCHIVE_INPUT_INVALID")
    # Verify and inspect the same open archive. Never extract paths to disk.
    with archive.open("rb") as stream:
        observed, _ = sha256_stream(stream, MAX_ARCHIVE)
        require(observed == digest, "GO_ARCHIVE_DIGEST_MISMATCH")
        stream.seek(0)
        with tarfile.open(fileobj=stream, mode="r:gz") as tar:
            matches = [row for row in tar if row.name == member]
            require(len(matches) == 1 and matches[0].isreg()
                    and 0 < matches[0].size <= MAX_BINARY, "GO_ARCHIVE_MEMBER_INVALID")
            source = tar.extractfile(matches[0])
            require(source is not None, "GO_ARCHIVE_MEMBER_INVALID")
            with source:
                expected = sha256_stream(source, MAX_BINARY)
            require(expected[1] == matches[0].size, "GO_ARCHIVE_MEMBER_INVALID")
    with binary.open("rb") as stream:
        actual = sha256_stream(stream, MAX_BINARY)
    require(actual == expected, "GO_BINARY_DIGEST_MISMATCH")
    return actual[0]


def parse_build(raw, root, release, commit, *, verified_file_build=False):
    lines = raw.decode("utf-8", errors="strict").splitlines()
    require(1 < len(lines) <= 3000, "GO_BUILD_INFO_INVALID")
    header = lines[0].rsplit(": ", 1)
    require(len(header) == 2 and GO.fullmatch(header[1]), "GO_TOOLCHAIN_UNKNOWN")
    toolchain = GO.fullmatch(header[1]).group(1)
    modules = {}
    root_version = None
    source_revision = None
    previous = None
    entrypoint = None
    for line in lines[1:]:
        fields = line.strip().split()
        if not fields:
            continue
        if fields[0] == "path":
            require(entrypoint is None and len(fields) == 2, "GO_ENTRYPOINT_INVALID")
            entrypoint = fields[1]
            previous = None
        elif fields[0] == "mod":
            require(root_version is None and len(fields) in (3, 4) and fields[1] == root
                    and fields[2] in (release, "(devel)"), "GO_ROOT_MISMATCH")
            root_version = fields[2]
            previous = None
        elif fields[0] == "dep":
            require(len(fields) in (3, 4), "GO_DEPENDENCY_FIELD_COUNT_" + str(len(fields)))
            require(MODULE.fullmatch(fields[1]), "GO_DEPENDENCY_PATH_INVALID")
            require(fields[1] not in modules, "GO_DEPENDENCY_DUPLICATE")
            # Go build info may contain an unversioned (devel) module. A
            # later versioned replacement resolves it; otherwise keep it as
            # an explicit coverage gap instead of querying a guessed version.
            require(VERSION.fullmatch(fields[2]) or fields[2] == "(devel)",
                    "GO_DEPENDENCY_VERSION_UNVERIFIED:" + fields[1])
            previous = fields[1]
            modules[previous] = (fields[1], fields[2])
        elif fields[0] == "=>":
            require(previous in modules and len(fields) in (3, 4)
                    and MODULE.fullmatch(fields[1]) and VERSION.fullmatch(fields[2]),
                    "GO_REPLACEMENT_UNVERSIONED")
            modules[previous] = (fields[1], fields[2])
            previous = None
        else:
            previous = None
            if fields[0] == "build" and len(fields) == 2 and fields[1].startswith("vcs.revision="):
                source_revision = fields[1].split("=", 1)[1]
    root_source = "BUILD_METADATA_AND_PINNED_RELEASE"
    if root_version is None:
        # v8.30.1 .goreleaser.yml builds main.go, not the package.
        # This exact representation was reproduced using go build main.go.
        require(verified_file_build and root == ROOTS["gitleaks"][0]
                and entrypoint == "command-line-arguments"
                and modules.get(root) == (root, "(devel)"),
                "GO_ROOT_MODULE_NOT_RECORDED:" + root)
        del modules[root]
        root_version = "NOT_RECORDED"
        root_source = "PINNED_ARCHIVE_RELEASE_METADATA_ONLY"
    else:
        require(root not in modules, "GO_DUPLICATE_ROOT")
    require(len(modules) > 0, "GO_NO_DEPENDENCIES:" + root)
    require(len(modules) <= 300, "GO_DEPENDENCY_LIMIT:" + root + ":" + str(len(modules)))
    require(source_revision is None or source_revision == commit, "GO_SOURCE_REVISION_MISMATCH")
    unresolved = sorted({name for name, version in modules.values() if version == "(devel)"})
    result = {(name, version) for name, version in modules.values() if version != "(devel)"}
    result.add((root, release))
    return {"toolchain": toolchain, "root_build_version": root_version,
            "root_version_source": root_source,
            "source_revision": "MATCH" if source_revision else "NOT_RECORDED",
            "modules": sorted(result), "unversioned_modules": unresolved,
            "dependency_coverage": "PARTIAL" if unresolved else "VERSIONED"}


def license_lookup(item):
    name, version = item
    url = ("https://api.deps.dev/v3/systems/GO/packages/"
           + urllib.parse.quote(name, safe="") + "/versions/" + urllib.parse.quote(version, safe=""))
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    request = urllib.request.Request(url, headers={"Accept": "application/json",
                                                    "User-Agent": "TESSERA-go-review"})
    try:
        with opener.open(request, timeout=10) as response:
            require(response.geturl() == url, "GO_LICENSE_REDIRECT_FORBIDDEN")
            raw = response.read(MAX_RESPONSE + 1)
        require(len(raw) <= MAX_RESPONSE, "GO_LICENSE_RESPONSE_LIMIT")
        data = json.loads(raw)
        key = data.get("versionKey", {})
        require(key.get("system") == "GO" and key.get("name") == name
                and key.get("version") in (version, version.removeprefix("v")),
                "GO_LICENSE_IDENTITY_MISMATCH")
        licenses = data.get("licenses", [])
        require(isinstance(licenses, list) and len(licenses) <= 100
                and all(isinstance(x, str) and LICENSE_EXPRESSION.fullmatch(x) for x in licenses),
                "GO_LICENSE_METADATA_INVALID")
        return {"status": "DEPS_DEV_REPORTED" if licenses else "UNKNOWN",
                "licenses": sorted(set(licenses))}
    except urllib.error.HTTPError as exc:
        return {"status": "NOT_INDEXED" if exc.code == 404 else "SERVICE_UNAVAILABLE", "licenses": []}
    except (OSError, ValueError, AttributeError, InstallCheckError):
        return {"status": "NOT_VERIFIED", "licenses": []}


def accept(gh, gitleaks, gh_archive, gitleaks_archive):
    started = time.monotonic()
    reports = {}
    all_modules = set()
    with tempfile.TemporaryDirectory(prefix="tessera-go-metadata-") as folder:
        temp = pathlib.Path(folder)
        env = fixture_env(temp)
        env.update({"GOTOOLCHAIN": "local", "GOPROXY": "off", "GOSUMDB": "off"})
        go = subprocess.run(["go", "version"], cwd=temp, env=env,
                            capture_output=True, timeout=10, check=True)
        match = re.fullmatch(rb"go version (go[0-9A-Za-z.]+) [a-z0-9_/]+\s*", go.stdout)
        require(match is not None, "GO_PARSER_VERSION_INVALID")
        for label, path, archive in (("gh", gh, gh_archive), ("gitleaks", gitleaks, gitleaks_archive)):
            digest = verify_binary(archive, path, *ARCHIVES[label])
            path = path.resolve(strict=True)
            root, release, commit = ROOTS[label]
            result = subprocess.run(["go", "version", "-m", str(path)], cwd=temp, env=env,
                                    capture_output=True, timeout=30, check=True)
            # Public, hash-verified binaries only: record shape, never local paths.
            rows = [line.strip().split() for line in result.stdout.decode("utf-8", errors="strict").splitlines()[1:]]
            print("GO_BUILD_INFO_SHAPE: " + json.dumps({"binary": label,
                "mod_rows": sum(bool(row) and row[0] == "mod" for row in rows),
                "dep_rows": sum(bool(row) and row[0] == "dep" for row in rows),
                "path_rows": sum(bool(row) and row[0] == "path" for row in rows),
                "unversioned_dep_rows": sum(len(row) >= 3 and row[0] == "dep" and row[2] == "(devel)" for row in rows)}, sort_keys=True))
            report = parse_build(result.stdout, root, release, commit,
                                 verified_file_build=(label == "gitleaks"))
            report["archive_verification"] = "PASS"
            report["binary_sha256"] = digest
            all_modules.update(report["modules"])
            queries = [{"package": {"ecosystem": "Go", "name": name}, "version": version}
                       for name, version in report["modules"]]
            queries += [{"package": {"ecosystem": "Go", "name": name},
                         "version": report["toolchain"]} for name in ("stdlib", "toolchain")]
            queries.append({"commit": commit})
            found = query(queries)
            labels = report["modules"] + [("stdlib", report["toolchain"]),
                                          ("toolchain", report["toolchain"])]
            report["findings"] = [{"module": name, "version": version, "ids": ids}
                                  for (name, version), ids in zip(labels, found) if ids]
            report["source_commit_ids"] = found[-1]
            report["module_count"] = len(report["modules"])
            report["unversioned_count"] = len(report["unversioned_modules"])
            reports[label] = report
    require(0 < len(all_modules) <= 400, "GO_MODULE_COUNT_INVALID")
    # License data are public metadata, not a legal compatibility assessment.
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        license_rows = list(pool.map(license_lookup, sorted(all_modules)))
    counts = collections.Counter(row["status"] for row in license_rows)
    return {"execution": "PASS", "scope": "GO_MODULE_BUILD_METADATA_OSV_AND_LICENSE_METADATA",
            "policy": "ADVISORY_FINDINGS", "go_parser": match.group(1).decode("ascii"),
            "binaries": reports, "distinct_modules": len(all_modules),
            "coverage": ("PARTIAL" if any(row["unversioned_count"] for row in reports.values())
                         else "VERSIONED_MODULES"),
            "license_status_counts": dict(sorted(counts.items())),
            "license_inventory": [{"module": name, "version": version, **row}
                                  for (name, version), row in zip(sorted(all_modules), license_rows)],
            "license_compliance": "NOT_VERIFIED", "call_reachability": "NOT_VERIFIED",
            "native_non_go_components": "NOT_VERIFIED",
            "elapsed_seconds": round(time.monotonic() - started, 2)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gh", type=pathlib.Path, required=True)
    parser.add_argument("--gitleaks", type=pathlib.Path, required=True)
    parser.add_argument("--gh-archive", type=pathlib.Path, required=True)
    parser.add_argument("--gitleaks-archive", type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        result = accept(args.gh, args.gitleaks, args.gh_archive, args.gitleaks_archive)
    except (InstallCheckError, OSError, ValueError, UnicodeError, subprocess.SubprocessError, tarfile.TarError) as exc:
        print("BLOCKED: " + (str(exc) if isinstance(exc, InstallCheckError)
                              else "GO_REVIEW_RUNTIME_FAILED"), file=sys.stderr)
        return 1
    print("GO_DEPENDENCY_REVIEW_EXECUTION_PASS: " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
