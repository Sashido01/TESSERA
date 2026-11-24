#!/usr/bin/env python3
"""T12.02.02.04: exact installed Python dependency inventory, OSV and license metadata."""
from __future__ import annotations

import argparse
import base64
import hashlib
import collections
import importlib.metadata
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request

from check_nvidia_tier1 import require
from check_official_local_install import InstallCheckError

OSV = "https://api.osv.dev/v1/querybatch"
MAX_RESPONSE = 8 * 1024 * 1024
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.!+-]{0,79}\Z")
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
SHA = re.compile(r"[a-f0-9]{40}\Z")
LICENSE_EXPRESSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9 .+()_-]{0,199}\Z")
LOCK = re.compile(r"([A-Za-z0-9_.-]+)==([A-Za-z0-9_.!+-]+)"
                  r"(?:; sys_platform == '(win32)')? --hash=sha256:[a-f0-9]{64}\Z")


def canonical(name):
    require(isinstance(name, str), "DEP_NAME_INVALID")
    value = re.sub(r"[-_.]+", "-", name).lower()
    require(NAME.fullmatch(value), "DEP_NAME_INVALID")
    return value


def pinned_lock(text, platform):
    names = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = LOCK.fullmatch(line)
        require(match is not None, "DEP_LOCK_UNSUPPORTED")
        raw, version, marker = match.groups()
        if marker and platform != marker:
            continue
        name = canonical(raw)
        require(name not in names and VERSION.fullmatch(version), "DEP_LOCK_INVALID")
        names[name] = version
    require(names, "DEP_LOCK_EMPTY")
    return names


def license_info(meta, files):
    expression = meta.get("License-Expression")
    if isinstance(expression, str) and LICENSE_EXPRESSION.fullmatch(expression):
        status = "DECLARED_SPDX_EXPRESSION"
        value = expression
    elif expression:
        status, value = "UNRECOGNIZED_EXPRESSION", None
    else:
        legacy = meta.get("License", "")
        known = {"MIT": "MIT", "MIT License": "MIT", "Apache-2.0": "Apache-2.0",
                 "Apache License 2.0": "Apache-2.0", "BSD-3-Clause": "BSD-3-Clause",
                 "BSD-2-Clause": "BSD-2-Clause", "ISC": "ISC", "MPL-2.0": "MPL-2.0",
                 "PSF-2.0": "PSF-2.0", "Unlicense": "Unlicense"}
        if isinstance(legacy, str) and legacy.strip() in known:
            status, value = "LEGACY_DECLARATION", known[legacy.strip()]
        else:
            classifiers = meta.get_all("Classifier") or []
            labels = {"License :: OSI Approved :: MIT License": "MIT",
                      "License :: OSI Approved :: Apache Software License": "Apache-family",
                      "License :: OSI Approved :: BSD License": "BSD-family",
                      "License :: OSI Approved :: Python Software Foundation License": "PSF-family",
                      "License :: OSI Approved :: ISC License (ISCL)": "ISC",
                      "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)": "MPL-2.0"}
            found = sorted({labels[item] for item in classifiers if item in labels})
            status, value = ("CLASSIFIER_ONLY", " / ".join(found)) if found else ("UNKNOWN", None)
    # Count archive metadata entries only. Do not follow arbitrary paths.
    records = sum(1 for file in files or []
                  if any(part.endswith(".dist-info") for part in file.parts)
                  and any(part.upper().startswith(("LICENSE", "COPYING", "NOTICE"))
                          for part in file.parts))
    return {"status": status, "declared": value, "license_records": records}


# Reviewed exact upstream license texts; never replace package metadata with these.
LICENSE_PINS = {
    # Exact upstream commit 86ec4072580809cc3978f5d6bb40261eb60c3045.
    ("face", "26.0.1"): ("LICENSE", "c642862bf261c6d05d89766e68801bd8225d508205776a04fb1ace9866b5b66f"),
    # Exact upstream commit 45c166bce4630a55729f513a4b11fb95af23df5b.
    ("peewee", "3.19.0"): ("LICENSE", "3740096125b08735a247b8dd08cd82e0ba984d3bebd9221d378576637e5240da"),
    # Exact upstream commit 6e1998413a5bca7c058b85999667893f167434bc.
    ("protobuf", "6.33.6"): ("LICENSE", "6e5e117324afd944dcf67f36cf329843bc1a92229a8cd9bb573d7a83130fea7d"),
    ("tiktoken", "0.13.0"): ("LICENSE", "418cb499b436128d653d79941333a5437b7be2ea9213dcc2f04d15d5d2c51d86"),
    ("tqdm", "4.68.3"): ("LICENCE", "fcff87c3a47ce8028a8512aa182d4fcf0ad1c90544ee75cf9b343684cac194de"),
}
MAX_LICENSE_BYTES = 256 * 1024


def installed_license_evidence(dist, name, version, files):
    pin = LICENSE_PINS.get((name, version))
    if pin is None:
        return None
    filename, upstream_digest = pin
    info_dir = name.replace("-", "_") + "-" + version + ".dist-info"
    allowed = {(info_dir, filename), (info_dir, "licenses", filename)}
    matches = [entry for entry in files or [] if tuple(entry.parts) in allowed]
    result = {"status": "NOT_VERIFIED", "upstream_sha256": upstream_digest}
    if len(matches) != 1:
        return {**result, "status": "RECORD_MISSING_OR_AMBIGUOUS"}
    entry = matches[0]
    try:
        root = pathlib.Path(dist.locate_file("")).resolve(strict=True)
        path = root.joinpath(*entry.parts)
        # Use only the exact fixed record inside the resolved installation root.
        # No symlinks, redirected directories, arbitrary metadata paths or raw text.
        parent = root
        for part in entry.parts:
            parent = parent / part
            if parent.is_symlink() or parent.resolve(strict=True) != parent:
                return {**result, "status": "REDIRECTED_PATH"}
        if not path.is_file() or path.stat().st_size > MAX_LICENSE_BYTES:
            return {**result, "status": "INVALID_FILE"}
        with path.open("rb") as stream:
            raw = stream.read(MAX_LICENSE_BYTES + 1)
        if not raw or len(raw) > MAX_LICENSE_BYTES:
            return {**result, "status": "INVALID_FILE"}
        digest = hashlib.sha256(raw)
        actual = digest.hexdigest()
        record = getattr(entry, "hash", None)
        size = getattr(entry, "size", None)
        encoded = base64.urlsafe_b64encode(digest.digest()).decode("ascii").rstrip("=")
        if (getattr(record, "mode", None) != "sha256"
                or getattr(record, "value", None) != encoded or size != len(raw)):
            return {**result, "status": "RECORD_MISMATCH_OR_UNVERIFIED", "installed_sha256": actual}
        return {**result, "status": ("UPSTREAM_TEXT_MATCH" if actual == upstream_digest
                                     else "UPSTREAM_TEXT_DIFFERS"),
                "installed_sha256": actual, "record_integrity": "MATCH"}
    except (OSError, ValueError, RuntimeError):
        return result


def inventory(locked=None):
    result = {}
    if locked is not None:
        distributions = [importlib.metadata.distribution(name) for name in locked]
    else:
        distributions = list(importlib.metadata.distributions())
    require(0 < len(distributions) <= 500, "DEP_INVENTORY_INVALID")
    for dist in distributions:
        meta = dist.metadata
        name, version = canonical(meta.get("Name")), dist.version
        require(isinstance(version, str) and VERSION.fullmatch(version)
                and name not in result, "DEP_INVENTORY_INVALID")
        if locked is not None:
            require(locked.get(name) == version, "DEP_VERSION_MISMATCH")
        files = dist.files
        result[name] = {"version": version, "license": license_info(meta, files)}
        evidence = installed_license_evidence(dist, name, version, files)
        if evidence is not None:
            result[name]["license_text_evidence"] = evidence
    if locked is not None:
        require(set(result) == set(locked), "DEP_COVERAGE_MISMATCH")
    return result


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise InstallCheckError("DEP_OSV_REDIRECT_FORBIDDEN")


def request_batch(queries):
    body = json.dumps({"queries": queries}, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(OSV, data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 "User-Agent": "TESSERA-dependency-review"}, method="POST")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=30) as response:
            require(response.geturl() == OSV, "DEP_OSV_REDIRECT_FORBIDDEN")
            content = response.read(MAX_RESPONSE + 1)
    except (OSError, urllib.error.URLError, TimeoutError) as exc:
        raise InstallCheckError("DEP_OSV_UNAVAILABLE") from exc
    require(len(content) <= MAX_RESPONSE, "DEP_OSV_RESPONSE_LIMIT")
    return json.loads(content)


def query(queries, request=request_batch):
    require(0 < len(queries) <= 500, "DEP_QUERY_COUNT_INVALID")
    found = [set() for _ in queries]
    pending = [(i, q, None) for i, q in enumerate(queries)]
    seen = set()
    rounds = 0
    while pending:
        rounds += 1
        require(rounds <= 20, "DEP_OSV_PAGINATION_LIMIT")
        batch, pending = pending[:50], pending[50:]
        sent = [dict(q, page_token=token) if token else q for _, q, token in batch]
        reply = request(sent)
        require(isinstance(reply, dict) and isinstance(reply.get("results"), list)
                and len(reply["results"]) == len(batch), "DEP_OSV_COVERAGE_MISMATCH")
        for (i, q, token), row in zip(batch, reply["results"]):
            require(isinstance(row, dict), "DEP_OSV_RESULT_INVALID")
            vulns = row.get("vulns", [])
            require(isinstance(vulns, list) and len(vulns) <= 1000, "DEP_OSV_RESULT_INVALID")
            for vuln in vulns:
                require(isinstance(vuln, dict) and isinstance(vuln.get("id"), str)
                        and ID.fullmatch(vuln["id"]), "DEP_OSV_ID_INVALID")
                found[i].add(vuln["id"])
            more = row.get("next_page_token")
            if more:
                require(isinstance(more, str) and len(more) <= 4096
                        and (i, more) not in seen, "DEP_OSV_PAGINATION_INVALID")
                seen.add((i, more))
                pending.append((i, q, more))
    return [sorted(ids) for ids in found]


def accept(locked, root, source_commit):
    packages = inventory(locked)
    if root:
        name, separator, version = root.partition("==")
        require(separator and packages.get(canonical(name), {}).get("version") == version,
                "DEP_ROOT_VERSION_MISMATCH")
    names = sorted(packages)
    queries = [{"package": {"ecosystem": "PyPI", "name": name},
                "version": packages[name]["version"]} for name in names]
    if source_commit:
        require(SHA.fullmatch(source_commit), "DEP_SOURCE_COMMIT_INVALID")
        queries.append({"commit": source_commit})
    result = query(queries)
    # Real known-vulnerability control, never install the vulnerable package.
    control = query([{"package": {"ecosystem": "PyPI", "name": "requests"},
                      "version": "2.19.1"}])
    require(bool(control[0]), "DEP_OSV_NEGATIVE_NOT_DETECTED")
    licenses = collections.Counter()
    findings = []
    for name, ids in zip(names, result):
        row = packages[name]
        licenses[row["license"]["status"]] += 1
        if ids:
            findings.append({"package": name, "version": row["version"], "ids": ids})
    return {"execution": "PASS", "scope": "INSTALLED_PYTHON_DISTRIBUTIONS",
            "policy": "ADVISORY_FINDINGS", "packages": len(names),
            "queried": len(result), "vulnerable_packages": len(findings),
            "findings": findings, "source_commit_ids": result[-1] if source_commit else None,
            "license_status_counts": dict(sorted(licenses.items())),
            "inventory": [{"name": name, **packages[name]} for name in names],
            "osv_negative_control": "PASS", "license_compliance": "NOT_VERIFIED",
            "native_binaries": "NOT_SCANNED", "unknown_vulnerabilities": "NOT_VERIFIED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--locked", type=pathlib.Path)
    parser.add_argument("--root")
    parser.add_argument("--source-commit")
    args = parser.parse_args()
    try:
        locked = pinned_lock(args.locked.read_text(encoding="utf-8"), sys.platform) if args.locked else None
        report = accept(locked, args.root, args.source_commit)
    except (InstallCheckError, OSError, ValueError, UnicodeError, importlib.metadata.PackageNotFoundError) as exc:
        print("BLOCKED: " + (str(exc) if isinstance(exc, InstallCheckError)
                              else "DEP_RUNTIME_FAILED"), file=sys.stderr)
        return 1
    print("DEPENDENCY_REVIEW_EXECUTION_PASS: " + json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
