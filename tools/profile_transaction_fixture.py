"""Fixture-only transaction integration; no production profile entry point.

Creates its own disposable workspace. No arbitrary path argument, no automatic
rollback, no claim of crash durability or production update authorization.
"""
from __future__ import annotations

import pathlib
import tempfile

from catalog_index import REPO, require
from profile_plan import Budget, inventory, snapshot
from profile_journal import append, encode, scan
from profile_move import move_verified
from profile_recovery import inspect


def fingerprint(path):
    budget = Budget()
    return snapshot(path, inventory(path, budget), budget)


def run_fixture(operation="update", *, interrupt=None):
    """Simulate interruption at named boundaries; return observations only."""
    require(operation in ("install", "update"), "FIXTURE_OPERATION")
    require(interrupt in (None, "prepared", "old_move", "old_record",
                          "new_move", "new_record"), "FIXTURE_INTERRUPT")
    require(operation == "update" or interrupt not in ("old_move", "old_record"),
            "FIXTURE_INTERRUPT")
    with tempfile.TemporaryDirectory(prefix="tessera-transaction-") as folder:
        root = pathlib.Path(folder).resolve()
        profile, stage, backup, log = [root / n for n in ("profile", "stage", "backup", "journal")]
        for path in (profile, stage, backup, log):
            path.mkdir()
        name = "fixture-alpha"
        old, new = profile / name, stage / name
        pairs = [(new, "0.0.2")]
        if operation == "update":
            pairs.append((old, "0.0.1"))
        for path, version in pairs:
            path.mkdir()
            (path / "VERSION").write_bytes((version + "\n").encode())
            (path / "SKILL.md").write_bytes(b"synthetic fixture only\n")
        other = profile / "fixture-other"
        other.mkdir()
        marker = other / "marker"
        marker.write_bytes(b"unselected fixture")
        old_version, old_sha = fingerprint(old) if operation == "update" else (None, None)
        new_version, new_sha = fingerprint(new)
        record = {"schema_version": 1, "repository": REPO, "id": name,
                  "operation": operation, "phase": "PREPARED",
                  "old_version": old_version, "old_sha256": old_sha,
                  "new_version": new_version, "new_sha256": new_sha}

        def observe(expected):
            history = scan(log)
            result = inspect(profile, stage, backup, encode(history[-1]))
            require(result["state"] == expected, "FIXTURE_STATE")
            require(marker.read_bytes() == b"unselected fixture", "FIXTURE_UNSELECTED_CHANGED")
            return {"state": result["state"], "layout": result["layout"],
                    "phases": [item["phase"] for item in history],
                    "unselected_preserved": True, "apply_authorized": False,
                    "durability": "NOT_VERIFIED", "interruption": "SIMULATED"}

        append(log, record)
        if interrupt == "prepared":
            return observe("NOT_STARTED")
        if operation == "update":
            move_verified(profile, backup, name, (old_version, old_sha))
            if interrupt == "old_move":
                return observe("OLD_IN_BACKUP")
            append(log, {**record, "phase": "OLD_MOVED"})
            if interrupt == "old_record":
                return observe("OLD_IN_BACKUP")
        move_verified(stage, profile, name, (new_version, new_sha))
        final = "NEW_PRESENT_OLD_RETAINED" if operation == "update" else "NEW_PRESENT"
        if interrupt == "new_move":
            return observe(final)
        append(log, {**record, "phase": "NEW_MOVED"})
        if interrupt == "new_record":
            return observe(final)
        observe(final)
        append(log, {**record, "phase": "VERIFIED"})
        result = observe(final)
        result["interruption"] = "NONE"
        return result
