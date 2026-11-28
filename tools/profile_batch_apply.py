"""Sequential application of an independently trusted batch preflight.

Exclusive caller-controlled roots only; no CLI, automatic rollback, deletion,
or authorization. Partial completion is possible and retained for explicit retry.
"""
from __future__ import annotations

import json
import os
import stat

from catalog_index import MAX_SKILLS, NAME, REPO, oid, require, version
from profile_plan import (Budget, aliases, disjoint, inventory, metadata,
                          ordinary_root, read_file, snapshot)
from profile_journal import encode, scan
from profile_recovery import digest, inspect, journal
from profile_move import absent
from profile_advance import advance

RECEIPT = "batch.json"
MAX_RECEIPT = 256 * 1024
LOGS = ("forward", "rollback", "cancel")


def manifest(preflight):
    require(preflight["status"] == "BATCH_PREFLIGHT_OBSERVED"
            and preflight["apply_authorized"] is False
            and preflight["operation"] in ("install", "update")
            and preflight["selection"] in ("EXPLICIT", "ALL"), "BATCH_INPUT")
    records, skipped, pins = (preflight[k] for k in ("records", "skipped", "pins"))
    require(all(isinstance(x, list) and len(x) <= MAX_SKILLS for x in (records, skipped, pins)),
            "BATCH_INPUT")
    records = [journal(encode(r)) for r in records]
    require(all(r["phase"] == "PREPARED" and r["operation"] in ("install", "update")
                and (preflight["operation"] == "update" or r["operation"] == "install")
                for r in records), "BATCH_RECORD")
    expected = {}
    for row in records + skipped:
        name = row["id"]
        require(isinstance(name, str) and len(name) <= 64 and NAME.fullmatch(name)
                and name not in expected, "BATCH_NAME")
        v, h = ((row["new_version"], row["new_sha256"]) if row in records
                else (row["version"], row["sha256"]))
        version(v)
        digest(h)
        expected[name] = (v, h)
    require(type(preflight["selected_count"]) is int
            and 0 < len(expected) == preflight["selected_count"] == len(pins) <= MAX_SKILLS,
            "BATCH_COUNT")
    observed = set()
    for row in pins:
        name = row["id"]
        require(name in expected and name not in observed
                and (row["version"], row["stage_sha256"]) == expected[name]
                and row["ref"] == "refs/tags/" + name + "/v" + row["version"],
                "BATCH_PIN")
        for field in ("tree", "commit", "tag_object"):
            oid(row[field])
        digest(row["raw_sha256"])
        observed.add(name)
    require(observed == set(expected), "BATCH_PIN_SET")
    result = {"schema_version": 1, "repository": REPO, "operation": preflight["operation"],
              "selection": preflight["selection"], "records": records,
              "skipped": skipped, "pins": pins}
    raw = (json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    require(len(raw) <= MAX_RECEIPT, "BATCH_RECEIPT_SIZE")
    # Detach all nested objects from caller mutation.
    return json.loads(raw), raw


def receipt_bytes(path):
    try:
        info = metadata(path)
    except FileNotFoundError:
        return None
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
            and 0 < info.st_size <= MAX_RECEIPT, "BATCH_RECEIPT_FILE")
    return read_file(path, info)


def write_receipt(path, raw):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "wb", closefd=False) as stream:
            require(stream.write(raw) == len(raw), "BATCH_RECEIPT_WRITE")
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(fd)
    require(receipt_bytes(path) == raw, "BATCH_RECEIPT_CHANGED")


def exact_entries(path, names):
    with os.scandir(path) as items:
        found = set()
        for item in items:
            require(item.name in names, "BATCH_LOG_ENTRY")
            found.add(item.name)
    require(found == names, "BATCH_LOG_ENTRY")


def execute(profile, stage, backup, log_root, preflight):
    """Apply ordered records, stopping at first failure.

    The caller creates an empty log_root containing exactly one directory per
    actionable skill, each with empty forward/rollback/cancel directories.
    On resume the original independently verified preflight is required.
    """
    contract, raw = manifest(preflight)
    records, skipped = contract["records"], contract["skipped"]
    roots = [ordinary_root(p) for p in (profile, stage, backup, log_root)]
    disjoint(roots)
    path = log_root / RECEIPT
    existing = receipt_bytes(path)
    require(existing is None or existing == raw, "BATCH_RECEIPT_MISMATCH")
    names = {r["id"] for r in records}
    exact_entries(log_root, names | ({RECEIPT} if existing is not None else set()))
    logs = {}
    for record in records:
        name = record["id"]
        parent = ordinary_root(log_root / name)
        exact_entries(parent, set(LOGS))
        logs[name] = [ordinary_root(parent / k) for k in LOGS]
    leaves = [p for paths in logs.values() for p in paths]
    disjoint(roots[:3] + leaves)
    checked = roots + leaves
    ids = [(metadata(p).st_dev, metadata(p).st_ino) for p in checked]
    require(len({x[0] for x in ids}) == 1, "BATCH_CROSS_DEVICE")

    def stable():
        require([(metadata(ordinary_root(p)).st_dev, metadata(p).st_ino)
                 for p in checked] == ids, "BATCH_ROOT_CHANGED")

    def observe():
        stable()
        budget = Budget()
        selected = names | {r["id"] for r in skipped}
        require(not any(aliases(p, selected, budget) for p in roots[:3]), "BATCH_ALIAS")
        statuses = []
        pending = False
        for record in records:
            forward, rollback, cancel = logs[record["id"]]
            require(not scan(rollback) and not scan(cancel), "BATCH_REVERSE_STARTED")
            history = scan(forward)
            require(not history or history[0] == record, "BATCH_JOURNAL_MISMATCH")
            require(existing is not None or not history, "BATCH_MISSING_RECEIPT")
            require(not pending or not history, "BATCH_ORDER")
            result = inspect(profile, stage, backup, encode(history[-1] if history else record),
                             budget=budget)
            require(result["status"] == "OBSERVATION_ONLY"
                    and (bool(history) or result["state"] == "NOT_STARTED"), "BATCH_LAYOUT")
            done = bool(history) and history[-1]["phase"] == "VERIFIED"
            pending = pending or not done
            statuses.append(done)
        for row in skipped:
            for root in (profile, stage):
                target = root / row["id"]
                require(snapshot(target, inventory(target, budget), budget) ==
                        (row["version"], row["sha256"]), "BATCH_SKIPPED_CHANGED")
            absent(backup / row["id"])
        stable()
        require(receipt_bytes(path) == existing, "BATCH_RECEIPT_CHANGED")
        return statuses

    completed = observe()  # No writes if any selected item fails preliminary checks.
    if existing is None:
        write_receipt(path, raw)
        existing = raw
    for done, record in zip(completed, records):
        stable()
        require(receipt_bytes(path) == raw, "BATCH_RECEIPT_CHANGED")
        if not done:
            advance(profile, stage, backup, *logs[record["id"]], record)
    require(all(observe()), "BATCH_POSTCHECK")
    return {"status": "BATCH_COMPLETED_OBSERVED",
            "completed": [r["id"] for r in records],
            "skipped": [r["id"] for r in skipped],
            "apply_authorized": False, "atomic_batch": False,
            "source_authenticity": "NOT_VERIFIED", "exclusive_access": "NOT_VERIFIED",
            "durability": "NOT_VERIFIED", "lockfile": "NOT_VERIFIED"}
