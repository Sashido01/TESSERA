#!/usr/bin/env python3
"""T12.02.02.01: direct, pinned Bandit acceptance; findings remain advisory."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time

from check_official_local_install import fixture_env, InstallCheckError
from check_nvidia_tier1 import require

VERSION = "1.9.4"
LEVELS = {"LOW", "MEDIUM", "HIGH"}
MAX_REPORT = 16 * 1024 * 1024


def scope(name):
    parts = pathlib.PurePosixPath(name).parts
    return "tests" if "tests" in parts else "runtime"


def inventory(repo):
    result = subprocess.run(["git", "ls-files", "-z", "--", "*.py"], cwd=repo,
                            capture_output=True, check=True, timeout=30)
    names = result.stdout.decode("utf-8").split("\0")[:-1]
    require(0 < len(names) <= 2048 and len(set(names)) == len(names),
            "BANDIT_INVENTORY_INVALID")
    data = {}
    total = 0
    for name in names:
        relative = pathlib.PurePosixPath(name)
        require(not relative.is_absolute() and ".." not in relative.parts
                and relative.as_posix() == name
                and not name.startswith("-") and "\\" not in name,
                "BANDIT_PATH_INVALID")
        path = repo / name
        require(path.is_file() and path.resolve() == path and not path.is_symlink(),
                "BANDIT_SOURCE_INVALID")
        total += path.stat().st_size
        require(total <= 64 * 1024 * 1024, "BANDIT_SOURCE_LIMIT")
        data[name] = path.read_bytes()
    return data


def fingerprint(data):
    return {name: hashlib.sha256(content).hexdigest() for name, content in data.items()}


def summarize(report, rc, expected):
    require(isinstance(report, dict) and rc in (0, 1)
            and report.get("errors") == [], "BANDIT_SCAN_INCOMPLETE")
    metrics, rows = report.get("metrics"), report.get("results")
    require(isinstance(metrics, dict) and isinstance(rows, list)
            and len(rows) <= 10000, "BANDIT_REPORT_INVALID")
    require(set(metrics) == set(expected) | {"_totals"},
            "BANDIT_COVERAGE_MISMATCH")
    require(all(isinstance(m, dict) and type(m.get("loc")) is int and m["loc"] >= 0
                for m in metrics.values()), "BANDIT_METRICS_INVALID")
    require((rc == 0) == (not rows), "BANDIT_EXIT_MISMATCH")
    counter = collections.Counter()
    for row in rows:
        require(isinstance(row, dict), "BANDIT_FINDING_INVALID")
        name, rule = row.get("filename"), row.get("test_id")
        severity, confidence = row.get("issue_severity"), row.get("issue_confidence")
        require(isinstance(name, str) and name in expected
                and isinstance(rule, str) and re.fullmatch(r"B[0-9]{3}", rule)
                and isinstance(severity, str) and severity in LEVELS
                and isinstance(confidence, str) and confidence in LEVELS,
                "BANDIT_FINDING_INVALID")
        counter[(scope(name), rule, severity, confidence)] += 1
    return {"files": len(expected), "findings": len(rows),
            "verdict": "FINDINGS" if rows else "NO_FINDINGS",
            "by_rule": [{"scope": s, "rule": r, "severity": sev, "confidence": conf,
                         "count": count}
                        for (s, r, sev, conf), count in sorted(counter.items())]}


def accept(repo, cli):
    repo, cli = repo.resolve(strict=True), cli.resolve(strict=True)
    require(cli.is_file() and os.access(cli, os.X_OK), "BANDIT_CLI_MISSING")
    original = inventory(repo)
    before = fingerprint(original)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="tessera-bandit-") as folder:
        temp = pathlib.Path(folder)
        env = fixture_env(temp)
        env.update({"PATH": str(cli.parent) + os.pathsep + env["PATH"],
                    "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONSAFEPATH": "1", "CI": "true"})
        def run(args, cwd):
            return subprocess.run([str(cli), *args], cwd=cwd, env=env,
                                  stdin=subprocess.DEVNULL, capture_output=True,
                                  encoding="utf-8", timeout=120, check=False)
        ver = run(["--version"], temp)
        require(ver.returncode == 0 and bool(re.search(
            r"(?m)^bandit 1\.9\.4(?:\s|$)", ver.stdout + "\n" + ver.stderr)),
            "BANDIT_VERSION_MISMATCH")

        def scan(label, data):
            root = temp / label
            root.mkdir()
            for name, content in data.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            report = temp / (label + ".json")
            names = sorted(data)
            result = run(["-q", "--ignore-nosec", "-f", "json", "-o", str(report),
                          "--", *names], root)
            require(report.is_file() and not report.is_symlink()
                    and report.stat().st_size <= MAX_REPORT, "BANDIT_REPORT_MISSING")
            summary = summarize(json.loads(report.read_text(encoding="utf-8")),
                                result.returncode, set(names))
            require(all((root / name).read_bytes() == content
                        for name, content in data.items()), "BANDIT_SNAPSHOT_MUTATED")
            return summary

        actual = scan("catalog", original)
        clean = scan("clean", {"fixture.py": b"answer = 42\n"})
        require(clean["verdict"] == "NO_FINDINGS", "BANDIT_CLEAN_FIXTURE_FAILED")
        # Inert synthetic source; the scanner reads its AST, never executes it.
        bad = scan("negative", {"fixture.py": b"eval('1 + 1')  # nosec\n"})
        require(any(item["rule"] == "B307" for item in bad["by_rule"]),
                "BANDIT_NEGATIVE_NOT_DETECTED")
        require(fingerprint(inventory(repo)) == before, "BANDIT_SOURCE_MUTATED")
    return {"execution": "PASS", "scanner": "bandit", "version": VERSION,
            "policy": "ADVISORY_FINDINGS", "catalog": actual,
            "clean_fixture": "PASS", "negative_nosec_fixture": "PASS",
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "nvidia_code_integrity": "NOT_VERIFIED",
            "gitleaks": "NOT_RUN", "skillspector": "NOT_RUN", "cve": "NOT_RUN"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=pathlib.Path, required=True)
    parser.add_argument("--cli", type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        result = accept(args.repo, args.cli)
    except (InstallCheckError, OSError, UnicodeError, ValueError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + (str(exc) if isinstance(exc, InstallCheckError)
                              else "BANDIT_RUNTIME_FAILED"), file=sys.stderr)
        return 1
    print("BANDIT_REVIEW_EXECUTION_PASS: " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
