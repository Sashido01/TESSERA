#!/usr/bin/env python3
"""T12.02.02.02: scan distinct UTF-8 blobs reachable from local refs and HEAD."""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time

from check_gitleaks_review import VERSION, MAX_FILE, synthetic_marker, scan
from check_nvidia_tier1 import require
from check_official_local_install import InstallCheckError, fixture_env

MAX_OBJECTS = 20000
MAX_BLOBS = 2560
MAX_TOTAL = 128 * 1024 * 1024
HOST_BATCH_COUNT = 32
HOST_BATCH_BYTES = 4 * 1024 * 1024
MAX_SECONDS = 480  # 8 min host budget; container deadline remains 540 s, job limit 20 min.
OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


def git(repo, env, *args, data=None):
    return subprocess.run(
        ["git", "--no-replace-objects", "-c", "core.hooksPath=" + os.devnull, *args],
        cwd=repo, env=env, input=data, capture_output=True,
        timeout=60, check=True).stdout


def blob_metadata(raw, expected):
    lines = raw.decode("ascii").splitlines()
    require(len(lines) == len(expected), "HISTORY_OBJECT_COUNT_MISMATCH")
    result = {}
    seen = set()
    total = 0
    for line in lines:
        fields = line.split()
        require(len(fields) == 3, "HISTORY_OBJECT_MISSING")
        oid, kind, length = fields
        require(oid in expected and oid not in seen and OID.fullmatch(oid)
                and kind in {"blob", "tree", "commit", "tag"} and length.isdecimal(),
                "HISTORY_OBJECT_INVALID")
        seen.add(oid)
        if kind == "blob":
            size = int(length)
            total += size
            require(size <= MAX_FILE and total <= MAX_TOTAL and len(result) < MAX_BLOBS,
                    "HISTORY_LIMIT_EXCEEDED")
            result[oid] = size
    require(seen == expected and result, "HISTORY_OBJECT_COVERAGE_MISMATCH")
    return result


def inventory(repo, env):
    require(git(repo, env, "rev-parse", "--is-shallow-repository").strip() == b"false",
            "HISTORY_SHALLOW_REPOSITORY")
    output = git(repo, env, "rev-list", "--objects", "--all", "--no-object-names", "HEAD")
    ids = output.decode("ascii").splitlines()
    require(0 < len(ids) <= MAX_OBJECTS and len(set(ids)) == len(ids)
            and all(OID.fullmatch(x) for x in ids), "HISTORY_OBJECT_INVENTORY_INVALID")
    raw = git(repo, env, "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)",
              data=("\n".join(ids) + "\n").encode("ascii"))
    return blob_metadata(raw, set(ids))


def blob_oid(content, length):
    require(length in (40, 64), "HISTORY_OBJECT_INVALID")
    digest = hashlib.new("sha1" if length == 40 else "sha256")
    digest.update(f"blob {len(content)}\0".encode("ascii"))
    digest.update(content)
    return digest.hexdigest()


def history_snapshot(blobs):
    return hashlib.sha256(json.dumps(blobs, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_blob(content, oid, size):
    require(OID.fullmatch(oid) is not None, "HISTORY_OBJECT_INVALID")
    require(len(content) == size, "HISTORY_BLOB_SIZE_MISMATCH")
    require(blob_oid(content, len(oid)) == oid, "HISTORY_BLOB_OID_MISMATCH")
    require(b"\0" not in content, "HISTORY_UNSUPPORTED_BINARY")
    try:
        content.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise InstallCheckError("HISTORY_UNSUPPORTED_ENCODING") from exc
    return content


def checked_blob(repo, env, oid, size):
    require(OID.fullmatch(oid) is not None, "HISTORY_OBJECT_INVALID")
    return validate_blob(git(repo, env, "cat-file", "blob", oid), oid, size)


def history_batches(blobs):
    batch = []
    total = 0
    for oid, size in sorted(blobs.items()):
        require(OID.fullmatch(oid) is not None and type(size) is int
                and 0 <= size <= min(MAX_FILE, HOST_BATCH_BYTES), "HISTORY_BATCH_INPUT")
        if batch and (len(batch) >= HOST_BATCH_COUNT or total + size > HOST_BATCH_BYTES):
            yield batch
            batch, total = [], 0
        batch.append((oid, size))
        total += size
    if batch:
        yield batch


def validate_batch_input(batch):
    require(0 < len(batch) <= HOST_BATCH_COUNT, "HISTORY_BATCH_INPUT")
    require(all(OID.fullmatch(oid) is not None and type(size) is int
                and 0 <= size <= MAX_FILE for oid, size in batch), "HISTORY_BATCH_INPUT")
    require(len({oid for oid, _ in batch}) == len(batch)
            and sum(size for _, size in batch) <= HOST_BATCH_BYTES, "HISTORY_BATCH_INPUT")


def parse_blob_batch(raw, batch):
    validate_batch_input(batch)
    require(len(raw) <= HOST_BATCH_BYTES + HOST_BATCH_COUNT * 96, "HISTORY_BATCH_OUTPUT_LIMIT")
    result = []
    pos = 0
    for oid, size in batch:
        header = f"{oid} blob {size}\n".encode("ascii")
        require(raw.startswith(header, pos), "HISTORY_BATCH_HEADER")
        start = pos + len(header)
        end = start + size
        require(raw[end:end + 1] == b"\n", "HISTORY_BATCH_FRAME")
        result.append((oid, size, validate_blob(raw[start:end], oid, size)))
        pos = end + 1
    require(pos == len(raw), "HISTORY_BATCH_TRAILING_DATA")
    return result


def checked_blob_batch(repo, env, batch):
    # The caller provides bounded, inventoried chunks; the parser rechecks framing.
    validate_batch_input(batch)
    raw = git(repo, env, "cat-file", "--batch",
              data=("\n".join(oid for oid, _ in batch) + "\n").encode("ascii"))
    return parse_blob_batch(raw, batch)


def review(repo, cli, temp, env):
    started = time.monotonic()
    deadline = started + MAX_SECONDS

    def check_deadline():
        require(time.monotonic() < deadline, "HISTORY_TIMEOUT")

    before = inventory(repo, env)
    check_deadline()

    def one(item):
        check_deadline()
        oid, size, content = item
        if size == 0:
            return oid, size, collections.Counter()
        rules, _, _ = scan(cli, temp, env, content)
        check_deadline()
        return oid, size, rules

    seen = set()
    counts = collections.Counter()
    bytes_scanned = 0
    empty = 0
    # Bounded worker pool. Each scanner receives exactly one object via stdin.
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for batch in history_batches(before):
            check_deadline()
            records = checked_blob_batch(repo, env, batch)
            check_deadline()
            for oid, size, rules in pool.map(one, records):
                check_deadline()
                require(oid not in seen and before.get(oid) == size, "HISTORY_DUPLICATE_BLOB")
                seen.add(oid)
                bytes_scanned += size
                empty += int(size == 0)
                counts.update(rules)
    require(seen == set(before) and bytes_scanned == sum(before.values()),
            "HISTORY_BLOB_COVERAGE_MISMATCH")
    check_deadline()
    require(inventory(repo, env) == before, "HISTORY_REFS_CHANGED")
    check_deadline()
    return {"snapshot_sha256": history_snapshot(before), "distinct_blobs": len(before), "empty": empty,
            "scanned_nonempty": len(before) - empty, "bytes_scanned": bytes_scanned,
            "findings": sum(counts.values()),
            "verdict": "FINDINGS" if counts else "NO_FINDINGS",
            "by_rule": [{"rule": rule, "count": n} for rule, n in sorted(counts.items())],
            "elapsed_seconds": round(time.monotonic() - started, 2)}


def fixture(cli, temp, env):
    root = temp / "fixture"
    root.mkdir()
    git(root, env, "init", "-q", "-b", "main")
    file = root / "fixture.txt"
    marker = synthetic_marker()
    file.write_bytes(b"fixture " + marker + b"\n")
    git(root, env, "add", "fixture.txt")
    git(root, env, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
        "commit", "-qm", "synthetic fixture")
    file.write_bytes(b"clean fixture\n")
    git(root, env, "add", "fixture.txt")
    git(root, env, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
        "commit", "-qm", "remove synthetic marker")
    clean, _, _ = scan(cli, temp, env, file.read_bytes())
    require(not clean, "HISTORY_CURRENT_FIXTURE_NOT_CLEAN")
    result = review(root, cli, temp, env)
    require(result["distinct_blobs"] == 2
            and any(row["rule"] == "aws-access-token" for row in result["by_rule"]),
            "HISTORY_REMOVED_MARKER_NOT_DETECTED")


def accept(repo, cli):
    repo, cli = repo.resolve(strict=True), cli.resolve(strict=True)
    require(cli.is_file() and os.access(cli, os.X_OK), "HISTORY_CLI_MISSING")
    with tempfile.TemporaryDirectory(prefix="tessera-gitleaks-history-") as folder:
        temp = pathlib.Path(folder)
        env = fixture_env(temp)
        env.update({"PATH": str(cli.parent) + os.pathsep + env["PATH"],
                    "GIT_NO_LAZY_FETCH": "1", "CI": "true", "GOMAXPROCS": "1"})
        version = subprocess.run([str(cli), "version"], cwd=temp, env=env,
                                 stdin=subprocess.DEVNULL, capture_output=True,
                                 timeout=10, check=False)
        require(version.returncode == 0 and version.stdout.strip() == VERSION.encode(),
                "HISTORY_VERSION_MISMATCH")
        fixture(cli, temp, env)
        result = review(repo, cli, temp, env)
    return {"execution": "PASS", "scanner": "gitleaks", "version": VERSION,
            "scope": "DISTINCT_REACHABLE_UTF8_BLOBS_LOCAL_REFS_AND_HEAD",
            "policy": "ADVISORY_FINDINGS", "history": result,
            "removed_marker_fixture": "PASS", "path_specific_rules": "NOT_VERIFIED",
            "unreachable_objects": "NOT_SCANNED", "remote_unfetched_refs": "NOT_SCANNED",
            "binary_archives": "NOT_SUPPORTED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=pathlib.Path, required=True)
    parser.add_argument("--cli", type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        result = accept(args.repo, args.cli)
    except (InstallCheckError, OSError, UnicodeError, ValueError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + (str(exc) if isinstance(exc, InstallCheckError)
                              else "HISTORY_RUNTIME_FAILED"), file=sys.stderr)
        return 1
    print("GITLEAKS_HISTORY_EXECUTION_PASS: " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
