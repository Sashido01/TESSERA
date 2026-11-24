#!/usr/bin/env python3
"""T12.02.02.02: pinned Gitleaks, tracked UTF-8 snapshot, per-file stdin."""
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
import time

from check_bandit_review import fingerprint
from check_nvidia_tier1 import require
from check_official_local_install import InstallCheckError, fixture_env

VERSION = "8.30.1"
FINDINGS_EXIT = 10
MAX_FILE = 2 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
MAX_REPORT = 4 * 1024 * 1024


def inventory(repo):
    result = subprocess.run(["git", "ls-files", "-z"], cwd=repo,
                            capture_output=True, check=True, timeout=30)
    require(result.stdout.endswith(b"\0"), "GITLEAKS_INVENTORY_INVALID")
    names = result.stdout.decode("utf-8").split("\0")[:-1]
    require(0 < len(names) <= 2048 and len(set(names)) == len(names),
            "GITLEAKS_INVENTORY_INVALID")
    data = {}
    total = 0
    for name in names:
        relative = pathlib.PurePosixPath(name)
        require(not relative.is_absolute() and ".." not in relative.parts
                and relative.as_posix() == name and "\\" not in name,
                "GITLEAKS_PATH_INVALID")
        path = repo / name
        require(path.is_file() and not path.is_symlink() and path.resolve() == path,
                "GITLEAKS_SOURCE_INVALID")
        with path.open("rb") as stream:
            content = stream.read(MAX_FILE + 1)
        total += len(content)
        require(len(content) <= MAX_FILE and total <= MAX_TOTAL, "GITLEAKS_SOURCE_LIMIT")
        # Unsupported binary/non-UTF-8 files must not become silent clean results.
        require(b"\0" not in content, "GITLEAKS_UNSUPPORTED_BINARY")
        try:
            content.decode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise InstallCheckError("GITLEAKS_UNSUPPORTED_ENCODING") from exc
        data[name] = content
    return data


def parse_scan(stdout, stderr, rc, size):
    require(rc in (0, FINDINGS_EXIT) and len(stdout) <= MAX_REPORT
            and len(stderr) <= MAX_REPORT, "GITLEAKS_EXECUTION_INVALID")
    log = stderr.decode("utf-8", errors="strict")
    counts = re.findall(r"\bscanned ~([0-9]+) bytes\b", log)
    require(counts == [str(size)], "GITLEAKS_COVERAGE_MISMATCH")
    require(not re.search(r"(?i)\bpartial scan\b|\b(?:ERR|FTL)\b|issue reading file", log),
            "GITLEAKS_SCAN_INCOMPLETE")
    rows = json.loads(stdout)
    # Go's JSON encoder can represent an empty findings slice as null.
    if rows is None:
        rows = []
    require(isinstance(rows, list) and len(rows) <= 10000,
            "GITLEAKS_REPORT_INVALID")
    require((rc == FINDINGS_EXIT) == bool(rows), "GITLEAKS_EXIT_MISMATCH")
    rules = collections.Counter()
    for row in rows:
        require(isinstance(row, dict), "GITLEAKS_FINDING_INVALID")
        rule = row.get("RuleID")
        require(isinstance(rule, str) and re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,99}", rule)
                and row.get("Secret") == "REDACTED",
                "GITLEAKS_FINDING_INVALID")
        rules[rule] += 1
    return rules


def scan(cli, cwd, env, content):
    result = subprocess.run(
        [str(cli), "stdin", "--no-banner", "--no-color", "--log-level", "info",
         "--redact=100", "--ignore-gitleaks-allow", "--exit-code", str(FINDINGS_EXIT),
         "--report-format", "json", "--report-path", "-", "--timeout", "15"],
        cwd=cwd, env=env, input=content, capture_output=True, timeout=20, check=False)
    rules = parse_scan(result.stdout, result.stderr, result.returncode, len(content))
    return rules, result.stdout, result.stderr


def synthetic_marker():
    # Upstream AWS rule accepts only A-Z and 2-7 after the prefix.
    return b"AK" + b"IA" + b"Q7M4T6X2P3R5V7Z5"


def accept(repo, cli):
    repo, cli = repo.resolve(strict=True), cli.resolve(strict=True)
    require(cli.is_file() and os.access(cli, os.X_OK), "GITLEAKS_CLI_MISSING")
    original = inventory(repo)
    before = fingerprint(original)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="tessera-gitleaks-") as folder:
        temp = pathlib.Path(folder)
        env = fixture_env(temp)
        env["PATH"] = str(cli.parent) + os.pathsep + env["PATH"]
        env["CI"] = "true"
        # Run outside the source tree: no repository .gitleaksignore/config,
        # inherited GITLEAKS_* settings, or credentials.
        version = subprocess.run([str(cli), "version"], cwd=temp, env=env,
                                 stdin=subprocess.DEVNULL, capture_output=True,
                                 timeout=10, check=False)
        require(version.returncode == 0 and version.stdout.strip() == VERSION.encode(),
                "GITLEAKS_VERSION_MISMATCH")
        clean, _, _ = scan(cli, temp, env, b"plain text fixture\n")
        require(not clean, "GITLEAKS_CLEAN_FIXTURE_FAILED")
        # Fabricated, nonfunctional key-shaped marker, built in memory only.
        marker = synthetic_marker()
        negative, stdout, stderr = scan(
            cli, temp, env, b"fixture " + marker + b" # gitleaks:allow\n")
        require(negative.get("aws-access-token", 0) > 0, "GITLEAKS_NEGATIVE_NOT_DETECTED")
        require(marker not in stdout and marker not in stderr, "GITLEAKS_REDACTION_FAILED")
        counts = collections.Counter()
        scanned = 0
        empty = 0
        bytes_scanned = 0
        for name, content in original.items():
            if not content:
                empty += 1
                continue
            require(time.monotonic() - started < 180, "GITLEAKS_TOTAL_TIMEOUT")
            rules, _, _ = scan(cli, temp, env, content)
            scanned += 1
            bytes_scanned += len(content)
            group = "tests" if "tests" in pathlib.PurePosixPath(name).parts else "other"
            for rule, count in rules.items():
                counts[group, rule] += count
        require(scanned > 0 and scanned + empty == len(original)
                and bytes_scanned == sum(map(len, original.values())),
                "GITLEAKS_TOTAL_COVERAGE_MISMATCH")
        require(fingerprint(inventory(repo)) == before, "GITLEAKS_SOURCE_MUTATED")
    return {"execution": "PASS", "scanner": "gitleaks", "version": VERSION,
            "scope": "TRACKED_UTF8_CONTENT_STDIN", "policy": "ADVISORY_FINDINGS",
            "files": len(original), "scanned_nonempty": scanned, "empty": empty,
            "bytes_scanned": bytes_scanned, "findings": sum(counts.values()),
            "verdict": "FINDINGS" if counts else "NO_FINDINGS",
            "by_rule": [{"scope": s, "rule": r, "count": count}
                        for (s, r), count in sorted(counts.items())],
            "clean_fixture": "PASS", "negative_allow_fixture": "PASS",
            "fixture_redaction": "PASS", "history": "NOT_RUN",
            "path_specific_rules": "NOT_VERIFIED", "binary_archives": "NOT_SUPPORTED",
            "elapsed_seconds": round(time.monotonic() - started, 2)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=pathlib.Path, required=True)
    parser.add_argument("--cli", type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        report = accept(args.repo, args.cli)
    except (InstallCheckError, OSError, UnicodeError, ValueError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + (str(exc) if isinstance(exc, InstallCheckError)
                              else "GITLEAKS_RUNTIME_FAILED"), file=sys.stderr)
        return 1
    print("GITLEAKS_REVIEW_EXECUTION_PASS: " + json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
