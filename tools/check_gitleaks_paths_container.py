#!/usr/bin/env python3
"""Bounded TSP1 path-rule scan with exact independent host parity."""
from __future__ import annotations
import argparse
import collections
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

from check_gitleaks_container import binary_ok, run_records, LIMIT
from check_gitleaks_history import inventory as history_inventory, checked_blob
from check_gitleaks_paths import RULES, matching, historical_pairs, scan_rule, fixtures, path_snapshot
from check_gitleaks_review import VERSION, inventory
from check_nvidia_tier1 import require
from check_official_local_install import fixture_env
from gitleaks_frame import decode, MAX_FILE

CATEGORIES = tuple((scope, rule) for scope in ("current", "history") for rule, _, _ in RULES)
MAX_TARGETS = 4096
MAX_BYTES = 192 * 1024 * 1024
BATCH_COUNT = 256
BATCH_BYTES = 16 * 1024 * 1024
DEADLINE = 180


def batches(records):
    batch = []
    size = total = count = 0
    for category, data in records:
        count += 1
        total += len(data)
        require(type(category) is int and 0 <= category < len(CATEGORIES)
                and len(data) <= MAX_FILE and count <= MAX_TARGETS and total <= MAX_BYTES,
                "PATH_CONTAINER_LIMIT")
        if batch and (len(batch) == BATCH_COUNT or size + len(data) > BATCH_BYTES):
            yield batch
            batch, size = [], 0
        batch.append((category, data))
        size += len(data)
    if batch or count == 0:
        yield batch


def rows(coverage, counts):
    return [{"scope": scope, "rule": rule, "targets": coverage[i], "findings": counts[i]}
            for i, (scope, rule) in enumerate(CATEGORIES)]


def worker():
    cli = pathlib.Path("/stage/gitleaks")
    binary_ok(cli)
    records, digest = decode(sys.stdin.buffer, mode="paths")
    coverage = collections.Counter()
    counts = collections.Counter()
    with tempfile.TemporaryDirectory(dir="/tmp") as folder:
        temp = pathlib.Path(folder)
        env = fixture_env(temp)
        env.update({"PATH": "/usr/local/bin:/usr/bin:/bin", "CI": "true", "GOMAXPROCS": "2"})
        version = subprocess.run([str(cli), "version"], cwd=temp, env=env,
                                 stdin=subprocess.DEVNULL, capture_output=True, timeout=10)
        require(version.returncode == 0 and version.stdout.strip() == VERSION.encode(), "PATH_CONTAINER_VERSION")
        entries = set(temp.iterdir())
        fixtures(cli, temp, env)
        for category, data in records:
            coverage[category] += 1
            counts[category] += scan_rule(cli, temp, env, CATEGORIES[category][1], data)
        require(set(temp.iterdir()) == entries, "PATH_CONTAINER_FIXTURE_MUTATED")
    return {"digest": digest, "version": VERSION, "negative_fixtures": len(RULES),
            "fixture_top_level_entries_unchanged": "PASS", "results": rows(coverage, counts)}


def validate(report, records, digest):
    require(isinstance(report, dict) and set(report) == {"digest", "version", "negative_fixtures",
            "fixture_top_level_entries_unchanged", "results"} and report["digest"] == digest
            and report["version"] == VERSION and report["negative_fixtures"] == len(RULES)
            and report["fixture_top_level_entries_unchanged"] == "PASS", "PATH_CONTAINER_REPORT")
    coverage = collections.Counter(category for category, _ in records)
    results = report["results"]
    require(isinstance(results, list) and len(results) == len(CATEGORIES), "PATH_CONTAINER_ROWS")
    counts = collections.Counter()
    for i, (row, (scope, rule)) in enumerate(zip(results, CATEGORIES)):
        require(isinstance(row, dict) and set(row) == {"scope", "rule", "targets", "findings"}
                and row["scope"] == scope and row["rule"] == rule
                and type(row["targets"]) is int and row["targets"] == coverage[i]
                and type(row["findings"]) is int and 0 <= row["findings"] <= 10000 * coverage[i],
                "PATH_CONTAINER_ROW")
        counts[i] = row["findings"]
    return coverage, counts


def targets(repo, env, current, blobs, pairs):
    for name, data in sorted(current.items()):
        for rule in matching(name):
            yield CATEGORIES.index(("current", rule)), data
    for rule, oid in sorted(pairs):
        yield CATEGORIES.index(("history", rule)), checked_blob(repo, env, oid, blobs[oid])


def accept(repo, cli, host_path):
    require(sys.platform == "linux" and os.getuid() != 0, "PATH_CONTAINER_RUNNER_SCOPE")
    repo, cli = repo.resolve(strict=True), cli.resolve(strict=True)
    binary_ok(cli)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="tessera-path-host-") as folder:
        env = fixture_env(pathlib.Path(folder))
        env.update({"GIT_NO_LAZY_FETCH": "1", "CI": "true"})
        current = inventory(repo)
        blobs = history_inventory(repo, env)
        pairs, commits = historical_pairs(repo, env, blobs)
        snapshot = path_snapshot(current, blobs, pairs, commits)
        with host_path.open("rb") as stream:
            raw = stream.read(LIMIT + 1)
        prefix = b"GITLEAKS_PATH_EXECUTION_PASS: "
        require(len(raw) <= LIMIT and raw.startswith(prefix) and raw.count(b"\n") == 1,
                "PATH_CONTAINER_HOST_REPORT")
        host = json.loads(raw[len(prefix):])
        require(host.get("execution") == "PASS" and host.get("version") == VERSION
                and host.get("scope") == "FIVE_PINNED_PATH_CONSTRAINED_RULES"
                and host.get("snapshot_sha256") == snapshot and host.get("history_commits") == commits
                and host.get("negative_fixtures") == len(RULES)
                and host.get("fixture_top_level_entries_unchanged") == "PASS", "PATH_CONTAINER_HOST_SNAPSHOT")
        coverage, counts = collections.Counter(), collections.Counter()
        batch_count = 0
        for batch in batches(targets(repo, env, current, blobs, pairs)):
            remaining = DEADLINE - (time.monotonic() - started)
            require(remaining > 0, "PATH_CONTAINER_DEADLINE")
            report, digest = run_records(cli, batch, timeout=remaining, mode="paths")
            seen, found = validate(report, batch, digest)
            coverage.update(seen)
            counts.update(found)
            batch_count += 1
        actual = rows(coverage, counts)
        require(time.monotonic() - started < DEADLINE and actual == host.get("results")
                and inventory(repo) == current and history_inventory(repo, env) == blobs
                and historical_pairs(repo, env, blobs) == (pairs, commits), "PATH_CONTAINER_HOST_PARITY")
    return {"execution": "PASS", "scope": "FIVE_PINNED_PATH_CONSTRAINED_RULES_DOCKER",
            "version": VERSION, "history_commits": commits, "negative_fixtures": len(RULES),
            "results": actual, "batches": batch_count, "host_parity": "PASS", "frame_digest": "PASS",
            "source_preserved": "PASS", "elapsed_seconds": round(time.monotonic() - started, 2)}


def worker_main():
    try:
        print(json.dumps(worker(), sort_keys=True))
    except Exception:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("repo", "cli", "host-report"):
        parser.add_argument("--" + arg, type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        report = accept(args.repo, args.cli, args.host_report)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError):
        print("BLOCKED: GITLEAKS_PATH_CONTAINER_FAILED", file=sys.stderr)
        return 1
    print("GITLEAKS_PATH_CONTAINER_PASS: " + json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
