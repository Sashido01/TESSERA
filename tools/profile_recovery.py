#!/usr/bin/env python3
"""Read-only recovery classification for a single skill transaction.

A supplied journal is evidence, not authority. Never moves or deletes files.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import stat
import sys

from catalog_index import CatalogError, NAME, REPO, decode, require, version
from profile_plan import (Budget, aliases, disjoint, identity, inventory, metadata,
                          ordinary_root, read_file, recheck_tree, snapshot)

DIGEST = re.compile(r"[0-9a-f]{64}\Z")
PHASES = {"PREPARED", "OLD_MOVED", "NEW_MOVED", "VERIFIED"}
MAX_JOURNAL = 16 * 1024


def digest(value):
    require(isinstance(value, str) and DIGEST.fullmatch(value), "RECOVERY_DIGEST")
    return value


def journal(raw):
    obj = decode(raw, MAX_JOURNAL)
    require(isinstance(obj, dict) and set(obj) == {
        "schema_version", "repository", "id", "operation", "phase",
        "old_version", "new_version", "old_sha256", "new_sha256"
    } and type(obj["schema_version"]) is int and obj["schema_version"] == 1
        and obj["repository"] == REPO, "RECOVERY_JOURNAL")
    name = obj["id"]
    require(isinstance(name, str) and len(name) <= 64 and NAME.fullmatch(name)
            and obj["operation"] in ("install", "update", "rollback", "cancel-install", "cancel-update")
            and obj["phase"] in PHASES, "RECOVERY_JOURNAL")
    version(obj["new_version"])
    digest(obj["new_sha256"])
    if obj["operation"].startswith("cancel-"):
        require(obj["phase"] in ("PREPARED", "VERIFIED"), "RECOVERY_JOURNAL")
    if obj["operation"] in ("install", "cancel-install"):
        require(obj["old_version"] is None and obj["old_sha256"] is None
                and obj["phase"] != "OLD_MOVED", "RECOVERY_JOURNAL")
    else:
        old, new = version(obj["old_version"]), version(obj["new_version"])
        require((old > new if obj["operation"] == "rollback" else old < new)
                and digest(obj["old_sha256"]) != obj["new_sha256"], "RECOVERY_JOURNAL")
    return obj


def classify_layout(operation, phase, layout):
    # Journal may lag a completed rename by one step, never by two.
    if operation == "cancel-install":
        rules = {
            ("NEW", "ABSENT", "ABSENT"): ({"PREPARED"}, "CANCEL_READY"),
            ("ABSENT", "NEW", "ABSENT"): ({"PREPARED", "VERIFIED"}, "CANCELLED"),
        }
    elif operation == "cancel-update":
        rules = {
            ("ABSENT", "NEW", "OLD"): ({"PREPARED"}, "CANCEL_READY"),
            ("OLD", "NEW", "ABSENT"): ({"PREPARED", "VERIFIED"}, "CANCELLED"),
        }
    elif operation == "install":
        rules = {
            ("ABSENT", "NEW", "ABSENT"): ({"PREPARED"}, "NOT_STARTED"),
            ("NEW", "ABSENT", "ABSENT"): ({"PREPARED", "NEW_MOVED", "VERIFIED"}, "NEW_PRESENT"),
        }
    else:
        rules = {
            ("OLD", "NEW", "ABSENT"): ({"PREPARED"}, "NOT_STARTED"),
            ("ABSENT", "NEW", "OLD"): ({"PREPARED", "OLD_MOVED"}, "OLD_IN_BACKUP"),
            ("NEW", "ABSENT", "OLD"): ({"OLD_MOVED", "NEW_MOVED", "VERIFIED"}, "NEW_PRESENT_OLD_RETAINED"),
        }
    allowed, state = rules.get(tuple(layout), (set(), "AMBIGUOUS"))
    return state if phase in allowed else "AMBIGUOUS"


def inspect(profile, stage, backup, raw):
    record = journal(raw)
    roots = [ordinary_root(p) for p in (profile, stage, backup)]
    disjoint(roots)
    budget = Budget()
    identities = [identity(metadata(p)) for p in roots]
    require(len({metadata(p).st_dev for p in roots}) == 1, "RECOVERY_CROSS_DEVICE")
    name = record["id"]
    require(not any(aliases(p, {name}, budget) for p in roots), "RECOVERY_ALIAS")
    observed, absent, layout = [], [], []
    for root in roots:
        path = root / name
        try:
            metadata(path)
        except FileNotFoundError:
            absent.append(path)
            layout.append("ABSENT")
            continue
        rows = inventory(path, budget)
        observed.append((path, rows))
        current = snapshot(path, rows, budget)
        if current == (record["new_version"], record["new_sha256"]):
            layout.append("NEW")
        elif current == (record["old_version"], record["old_sha256"]):
            layout.append("OLD")
        else:
            layout.append("OTHER")
    for root in roots:
        ordinary_root(root)
    require([identity(metadata(p)) for p in roots] == identities
            and not any(aliases(p, {name}, budget) for p in roots), "RECOVERY_ROOT_CHANGED")
    for path, rows in observed:
        recheck_tree(path, rows, budget)
    for path in absent:
        budget.check()
        try:
            metadata(path)
        except FileNotFoundError:
            continue
        raise CatalogError("RECOVERY_TARGET_APPEARED")
    state = classify_layout(record["operation"], record["phase"], layout)
    return {"status": "OBSERVATION_ONLY" if state != "AMBIGUOUS" else "BLOCKED",
            "id": name, "phase": record["phase"], "layout": dict(zip(
                ("profile", "stage", "backup"), layout)), "state": state,
            "bytes_read": budget.read, "apply_authorized": False,
            "journal_authenticity": "NOT_VERIFIED", "exclusive_access": "NOT_VERIFIED",
            "snapshot_atomic": False, "durability": "NOT_VERIFIED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("profile", "stage", "backup", "journal"):
        parser.add_argument("--" + name, required=True, type=pathlib.Path)
    args = parser.parse_args()
    try:
        path = args.journal
        ordinary_root(path.parent)
        info = metadata(path)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                and 0 < info.st_size <= MAX_JOURNAL, "RECOVERY_JOURNAL")
        disjoint([ordinary_root(p) for p in (args.profile, args.stage, args.backup, path.parent)])
        result = inspect(args.profile, args.stage, args.backup, read_file(path, info))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print("BLOCKED: " + (str(exc) if isinstance(exc, CatalogError) else "RECOVERY_RUNTIME"),
              file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 1 if result["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    sys.exit(main())
