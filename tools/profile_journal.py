"""Append-only phase journal for a single skill transaction.

Library only. Requires caller-controlled exclusive private journal directory.
No profile changes, no automatic recovery, no authorization from journal data.
"""
from __future__ import annotations

import json
import os
import pathlib
import stat

from catalog_index import CatalogError, require
from profile_plan import identity, metadata, ordinary_root, read_file
from profile_recovery import journal, MAX_JOURNAL

FILES = ("00-prepared.json", "01-old-moved.json", "02-new-moved.json", "03-verified.json")
PHASES = ("PREPARED", "OLD_MOVED", "NEW_MOVED", "VERIFIED")


def encode(record):
    raw = (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    journal(raw)
    require(len(raw) <= MAX_JOURNAL, "JOURNAL_SIZE")
    return raw


def sequence(operation):
    return (0, 2, 3) if operation == "install" else (0, 1, 2, 3)


def scan(root):
    root = ordinary_root(root)
    before = identity(metadata(root))
    with os.scandir(root) as items:
        names = set()
        for item in items:
            require(item.name in FILES, "JOURNAL_UNKNOWN_ENTRY")
            names.add(item.name)
    if not names:
        require(identity(metadata(root)) == before, "JOURNAL_CHANGED")
        return []
    require(FILES[0] in names, "JOURNAL_MISSING_PREPARED")
    records, observed = [], []
    for index, name in enumerate(FILES):
        if name not in names:
            continue
        path = root / name
        info = metadata(path)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                and 0 < info.st_size <= MAX_JOURNAL, "JOURNAL_ENTRY")
        raw = read_file(path, info)
        record = journal(raw)
        require(raw == encode(record) and record["phase"] == PHASES[index],
                "JOURNAL_NONCANONICAL")
        records.append((index, record))
        observed.append((path, info))
    first = records[0][1]
    expected = sequence(first["operation"])
    require(tuple(i for i, _ in records) == expected[:len(records)], "JOURNAL_PHASE_GAP")
    for _, record in records:
        require({**record, "phase": first["phase"]} == first, "JOURNAL_RECORD_CHANGED")
    ordinary_root(root)
    require(identity(metadata(root)) == before, "JOURNAL_CHANGED")
    for path, info in observed:
        require(identity(metadata(path)) == identity(info), "JOURNAL_CHANGED")
    return [record for _, record in records]


def append(root: pathlib.Path, record: dict):
    """Exclusive file creation; incomplete write remains as blocking evidence.

    Flush file bytes before return. Parent directory durability and exclusive
    ownership of the directory are not established by this function.
    """
    raw = encode(record)
    record = journal(raw)
    root = ordinary_root(root)
    history = scan(root)
    steps = sequence(record["operation"])
    require(len(history) < len(steps), "JOURNAL_COMPLETE")
    index = steps[len(history)]
    require(record["phase"] == PHASES[index], "JOURNAL_PHASE_ORDER")
    if history:
        require({**record, "phase": "PREPARED"} == history[0], "JOURNAL_RECORD_CHANGED")
    path = root / FILES[index]
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "wb", closefd=False) as stream:
            require(stream.write(raw) == len(raw), "JOURNAL_SHORT_WRITE")
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(fd)
    require(scan(root) == history + [record], "JOURNAL_POSTCHECK")
    return {"phase": record["phase"], "file_fsync": "COMPLETED",
            "directory_durability": "NOT_VERIFIED", "exclusive_access": "NOT_VERIFIED",
            "apply_authorized": False}
