"""Actual child termination and fresh-process inspection in temporary fixtures.

No arbitrary production paths, no power-loss claim, no automatic recovery.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import pathlib
import tempfile

from catalog_index import REPO, require
from profile_transaction_fixture import fingerprint
from profile_journal import append, encode, scan
from profile_move import move_verified
from profile_recovery import inspect

POINTS = ("prepared", "old_move", "old_record", "new_move", "new_record")
TIMEOUT = 15


def _child(root, record, point, ready, hold):
    root = pathlib.Path(root)
    profile, stage, backup, log = [root / n for n in ("profile", "stage", "backup", "journal")]
    name = record["id"]

    def pause(at):
        if point == at:
            ready.set()
            hold.wait(TIMEOUT * 2)
            raise RuntimeError("fixture child was not terminated")

    append(log, record)
    pause("prepared")
    if record["operation"] == "update":
        move_verified(profile, backup, name, (record["old_version"], record["old_sha256"]))
        pause("old_move")
        append(log, {**record, "phase": "OLD_MOVED"})
        pause("old_record")
    move_verified(stage, profile, name, (record["new_version"], record["new_sha256"]))
    pause("new_move")
    append(log, {**record, "phase": "NEW_MOVED"})
    pause("new_record")


def _observer(root, sender):
    try:
        root = pathlib.Path(root)
        history = scan(root / "journal")
        result = inspect(root / "profile", root / "stage", root / "backup", encode(history[-1]))
        sender.send(json.dumps({"state": result["state"], "layout": result["layout"],
                                "phases": [r["phase"] for r in history]}))
    finally:
        sender.close()


def run_crash_fixture(operation="update", point="old_move"):
    require(operation in ("install", "update") and point in POINTS, "CRASH_FIXTURE_ARGUMENT")
    require(operation == "update" or point not in ("old_move", "old_record"),
            "CRASH_FIXTURE_ARGUMENT")
    ctx = mp.get_context("spawn")
    with tempfile.TemporaryDirectory(prefix="tessera-crash-") as folder:
        root = pathlib.Path(folder).resolve()
        profile, stage, backup, log = [root / n for n in ("profile", "stage", "backup", "journal")]
        for path in (profile, stage, backup, log):
            path.mkdir()
        name = "fixture-alpha"
        pairs = [(stage / name, "0.0.2")]
        if operation == "update":
            pairs.append((profile / name, "0.0.1"))
        for path, version in pairs:
            path.mkdir()
            (path / "VERSION").write_bytes((version + "\n").encode())
            (path / "SKILL.md").write_bytes(b"synthetic fixture only\n")
        other = profile / "fixture-other"
        other.mkdir()
        marker = other / "marker"
        marker.write_bytes(b"unselected fixture")
        old_version, old_sha = fingerprint(profile / name) if operation == "update" else (None, None)
        new_version, new_sha = fingerprint(stage / name)
        record = {"schema_version": 1, "repository": REPO, "id": name, "operation": operation,
                  "phase": "PREPARED", "old_version": old_version, "old_sha256": old_sha,
                  "new_version": new_version, "new_sha256": new_sha}
        ready, hold = ctx.Event(), ctx.Event()
        child = ctx.Process(target=_child, args=(str(root), record, point, ready, hold))
        child.start()
        try:
            require(ready.wait(TIMEOUT) and child.is_alive(), "CRASH_FIXTURE_BOUNDARY")
            child.kill()
            child.join(TIMEOUT)
            require(not child.is_alive() and child.exitcode not in (None, 0), "CRASH_FIXTURE_EXIT")
            exit_code = child.exitcode
        finally:
            if child.is_alive():
                child.kill()
                child.join()
            child.close()
        receiver, sender = ctx.Pipe(duplex=False)
        observer = ctx.Process(target=_observer, args=(str(root), sender))
        observer.start()
        sender.close()
        try:
            require(receiver.poll(TIMEOUT), "CRASH_FIXTURE_OBSERVER")
            result = json.loads(receiver.recv())
            observer.join(TIMEOUT)
            require(observer.exitcode == 0, "CRASH_FIXTURE_OBSERVER")
        finally:
            receiver.close()
            if observer.is_alive():
                observer.kill()
                observer.join()
            observer.close()
        require(marker.read_bytes() == b"unselected fixture", "CRASH_FIXTURE_UNSELECTED")
        return {**result, "child_exitcode": exit_code, "interruption": "PROCESS_KILLED",
                "fresh_process_observation": True, "unselected_preserved": True,
                "power_loss": "NOT_VERIFIED", "apply_authorized": False}
