#!/usr/bin/env python3
"""Compare isolated history-blob scanning with the existing trusted host scan."""
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

from check_gitleaks_container import binary_ok, run_records, LIMIT
from check_gitleaks_history import (inventory, checked_blob_batch, history_batches,
                                    history_snapshot, MAX_BLOBS, MAX_TOTAL, MAX_FILE)
from check_gitleaks_review import VERSION, synthetic_marker
from check_nvidia_tier1 import require
from check_official_local_install import fixture_env

BATCH_COUNT = 256
BATCH_BYTES = 16 * 1024 * 1024
DEADLINE = 540
CONTROLS = ("clean_fixture", "negative_allow_fixture", "fixture_redaction",
            "fixture_top_level_entries_unchanged")
RULE = re.compile(r"[a-z0-9][a-z0-9_-]{0,99}\Z")


def batches(blobs):
    require(0 < len(blobs) <= MAX_BLOBS and sum(blobs.values()) <= MAX_TOTAL,
            "HISTORY_CONTAINER_INVENTORY_LIMIT")
    batch = []
    total = 0
    for oid, size in sorted(blobs.items()):
        require(type(size) is int and 0 <= size <= min(MAX_FILE, BATCH_BYTES),
                "HISTORY_CONTAINER_BLOB_SIZE")
        if batch and (len(batch) == BATCH_COUNT or total + size > BATCH_BYTES):
            yield batch
            batch, total = [], 0
        batch.append((oid, size))
        total += size
    if batch:
        yield batch


def records_for_batch(repo, env, batch, deadline):
    """Read each inventoried object once; preserve order and content boundaries."""
    require(0 < len(batch) <= BATCH_COUNT
            and all(type(size) is int and 0 <= size <= MAX_FILE for _, size in batch)
            and sum(size for _, size in batch) <= BATCH_BYTES,
            "HISTORY_CONTAINER_READ_LIMIT")
    mapping = dict(batch)
    require(len(mapping) == len(batch) and batch == sorted(mapping.items()),
            "HISTORY_CONTAINER_READ_INPUT")
    # Validate all smaller chunks before the first Git subprocess. The shared
    # reader checks exact framing, type, size, object digest and UTF-8 per blob.
    chunks = list(history_batches(mapping))
    records = []
    observed = []
    for chunk in chunks:
        require(time.monotonic() < deadline, "HISTORY_CONTAINER_DEADLINE")
        rows = checked_blob_batch(repo, env, chunk)
        require([(oid, size) for oid, size, _ in rows] == chunk,
                "HISTORY_CONTAINER_READ_COVERAGE")
        for oid, size, content in rows:
            require(type(content) is bytes and len(content) == size,
                    "HISTORY_CONTAINER_READ_COVERAGE")
            observed.append((oid, size))
            records.append((0, content))
        require(time.monotonic() < deadline, "HISTORY_CONTAINER_DEADLINE")
    require(observed == batch, "HISTORY_CONTAINER_READ_COVERAGE")
    return records


def validate_batch(report, records, digest):
    keys = {"digest", "version", "files", "scanned_nonempty", "empty", "bytes_scanned",
            "by_rule", "findings", *CONTROLS}
    nonempty = sum(bool(data) for _, data in records)
    expected = {"files": len(records), "scanned_nonempty": nonempty,
                "empty": len(records) - nonempty, "bytes_scanned": sum(len(d) for _, d in records)}
    require(isinstance(report, dict) and set(report) == keys and report["digest"] == digest
            and report["version"] == VERSION and all(report[k] == "PASS" for k in CONTROLS)
            and all(type(report[k]) is int and report[k] == v for k, v in expected.items()),
            "HISTORY_CONTAINER_BATCH_COVERAGE")
    rows = report["by_rule"]
    require(isinstance(rows, list) and len(rows) <= 10000, "HISTORY_CONTAINER_RULES")
    counts = collections.Counter()
    for row in rows:
        require(isinstance(row, dict) and set(row) == {"scope", "rule", "count"}
                and row["scope"] == "other" and isinstance(row["rule"], str)
                and RULE.fullmatch(row["rule"]) and type(row["count"]) is int
                and 0 < row["count"] <= 10000 * len(records) and row["rule"] not in counts,
                "HISTORY_CONTAINER_RULE_INVALID")
        counts[row["rule"]] = row["count"]
    require(type(report["findings"]) is int and report["findings"] == sum(counts.values()),
            "HISTORY_CONTAINER_FINDINGS")
    return counts


def read_host(path, blobs):
    with path.open("rb") as stream:
        raw = stream.read(LIMIT + 1)
    prefix = b"GITLEAKS_HISTORY_EXECUTION_PASS: "
    require(len(raw) <= LIMIT and raw.startswith(prefix) and raw.count(b"\n") == 1,
            "HISTORY_CONTAINER_HOST_REPORT")
    outer = json.loads(raw[len(prefix):])
    require(outer.get("execution") == "PASS" and outer.get("version") == VERSION
            and outer.get("scope") == "DISTINCT_REACHABLE_UTF8_BLOBS_LOCAL_REFS_AND_HEAD"
            and outer.get("removed_marker_fixture") == "PASS", "HISTORY_CONTAINER_HOST_REPORT")
    report = outer["history"]
    require(report.get("snapshot_sha256") == history_snapshot(blobs), "HISTORY_CONTAINER_SNAPSHOT")
    return report


def accept(repo, cli, host_path):
    require(sys.platform == "linux" and os.getuid() != 0, "HISTORY_CONTAINER_RUNNER_SCOPE")
    repo, cli = repo.resolve(strict=True), cli.resolve(strict=True)
    binary_ok(cli)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="tessera-history-host-") as folder:
        env = fixture_env(pathlib.Path(folder))
        env.update({"GIT_NO_LAZY_FETCH": "1", "CI": "true"})
        blobs = inventory(repo, env)
        host = read_host(host_path, blobs)

        def execute(records):
            remaining = DEADLINE - (time.monotonic() - started)
            require(remaining > 0, "HISTORY_CONTAINER_DEADLINE")
            report, digest = run_records(cli, records, timeout=min(300, remaining))
            return validate_batch(report, records, digest)

        # Simulate the two contents enumerated by the independent host history fixture.
        marker = synthetic_marker()
        fixture = execute([(0, b"fixture " + marker + b"\n"), (0, b"clean fixture\n")])
        require(fixture.get("aws-access-token", 0) > 0, "HISTORY_CONTAINER_FIXTURE")

        seen = set()
        counts = collections.Counter()
        total = empty = batch_count = 0
        for batch in batches(blobs):
            records = records_for_batch(repo, env, batch, started + DEADLINE)
            counts.update(execute(records))
            for oid, size in batch:
                require(oid not in seen, "HISTORY_CONTAINER_DUPLICATE")
                seen.add(oid)
                total += size
                empty += int(size == 0)
            batch_count += 1
        require(time.monotonic() - started < DEADLINE and seen == set(blobs)
                and total == sum(blobs.values()) and inventory(repo, env) == blobs,
                "HISTORY_CONTAINER_COVERAGE")
        actual = {"distinct_blobs": len(seen), "empty": empty, "scanned_nonempty": len(seen) - empty,
                  "bytes_scanned": total, "findings": sum(counts.values()),
                  "by_rule": [{"rule": rule, "count": count} for rule, count in sorted(counts.items())],
                  "verdict": "FINDINGS" if counts else "NO_FINDINGS"}
        require(all(host.get(k) == v for k, v in actual.items()), "HISTORY_CONTAINER_HOST_PARITY")
    return {"execution": "PASS", "scope": "DISTINCT_REACHABLE_UTF8_BLOBS_DOCKER",
            "version": VERSION, **{k: v for k, v in actual.items() if k != "by_rule"},
            "batches": batch_count, "host_parity": "PASS", "frame_digest": "PASS",
            "blob_identity": "PASS", "synthetic_previous_content": "PASS",
            "removed_marker_host_fixture": "PASS", "path_specific_rules": "NOT_RUN",
            "unreachable_objects": "NOT_SCANNED", "remote_unfetched_refs": "NOT_SCANNED",
            "elapsed_seconds": round(time.monotonic() - started, 2)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("repo", "cli", "host-report"):
        parser.add_argument("--" + arg, type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        report = accept(args.repo, args.cli, args.host_report)
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, subprocess.SubprocessError):
        print("BLOCKED: GITLEAKS_HISTORY_CONTAINER_FAILED", file=sys.stderr)
        return 1
    print("GITLEAKS_HISTORY_CONTAINER_PASS: " + json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
