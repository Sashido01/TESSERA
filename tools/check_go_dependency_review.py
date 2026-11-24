#!/usr/bin/env python3
"""T12.02.02.04: inspect Go build metadata without executing the audited binaries."""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import json
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


def parse_build(raw, root, release, commit):
    lines = raw.decode("utf-8", errors="strict").splitlines()
    require(1 < len(lines) <= 3000, "GO_BUILD_INFO_INVALID")
    header = lines[0].rsplit(": ", 1)
    require(len(header) == 2 and GO.fullmatch(header[1]), "GO_TOOLCHAIN_UNKNOWN")
    toolchain = GO.fullmatch(header[1]).group(1)
    modules = {}
    root_version = None
    source_revision = None
    previous = None
    for line in lines[1:]:
        fields = line.strip().split()
        if not fields:
            continue
        if fields[0] == "mod":
            require(root_version is None and len(fields) in (3, 4) and fields[1] == root
                    and fields[2] in (release, "(devel)"), "GO_ROOT_MISMATCH")
            root_version = fields[2]
            previous = None
        elif fields[0] == "dep":
            require(len(fields) in (3, 4), "GO_DEPENDENCY_FIELD_COUNT_" + str(len(fields)))
            require(MODULE.fullmatch(fields[1]), "GO_DEPENDENCY_PATH_INVALID")
            require(fields[1] not in modules, "GO_DEPENDENCY_DUPLICATE")
            require(VERSION.fullmatch(fields[2]), "GO_DEPENDENCY_VERSION_UNVERIFIED")
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
    require(root_version is not None and 0 < len(modules) <= 300, "GO_BUILD_INFO_INCOMPLETE")
    require(source_revision is None or source_revision == commit, "GO_SOURCE_REVISION_MISMATCH")
    result = set(modules.values()) | {(root, release)}
    return {"toolchain": toolchain, "root_build_version": root_version,
            "source_revision": "MATCH" if source_revision else "NOT_RECORDED",
            "modules": sorted(result)}


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


def accept(gh, gitleaks):
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
        for label, path in (("gh", gh), ("gitleaks", gitleaks)):
            path = path.resolve(strict=True)
            require(path.is_file(), "GO_BINARY_MISSING")
            root, release, commit = ROOTS[label]
            result = subprocess.run(["go", "version", "-m", str(path)], cwd=temp, env=env,
                                    capture_output=True, timeout=30, check=True)
            report = parse_build(result.stdout, root, release, commit)
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
            reports[label] = report
    require(0 < len(all_modules) <= 400, "GO_MODULE_COUNT_INVALID")
    # License data are public metadata, not a legal compatibility assessment.
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        license_rows = list(pool.map(license_lookup, sorted(all_modules)))
    counts = collections.Counter(row["status"] for row in license_rows)
    return {"execution": "PASS", "scope": "GO_MODULE_BUILD_METADATA_OSV_AND_LICENSE_METADATA",
            "policy": "ADVISORY_FINDINGS", "go_parser": match.group(1).decode("ascii"),
            "binaries": reports, "distinct_modules": len(all_modules),
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
    args = parser.parse_args()
    try:
        result = accept(args.gh, args.gitleaks)
    except (InstallCheckError, OSError, ValueError, UnicodeError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + (str(exc) if isinstance(exc, InstallCheckError)
                              else "GO_REVIEW_RUNTIME_FAILED"), file=sys.stderr)
        return 1
    print("GO_DEPENDENCY_REVIEW_EXECUTION_PASS: " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
