"""Explicit rollback of an installed update, retaining both versions.

Library for trusted, exclusive same-volume roots. The caller must independently
authorize rollback and verify source provenance. No CLI, deletion, or automatic
rollback on error. Separate append-only journal; forward history stays intact.
"""
from __future__ import annotations

from catalog_index import require
from profile_plan import disjoint, metadata, ordinary_root
from profile_journal import append, encode, scan
from profile_move import move_verified
from profile_recovery import inspect

FINAL = "NEW_PRESENT_OLD_RETAINED"


def restore(profile, stage, backup, forward_log, rollback_log):
    """Restore the previous version, or resume a proven rollback boundary.

    The rollback uses the original backup as its incoming stage and the
    original stage as its destination for the displaced newer version.
    A failure is propagated; a later explicit invocation rechecks the layout.
    No trust or authorization is derived from supplied journal contents.
    """
    roots = [ordinary_root(p) for p in (profile, stage, backup, forward_log, rollback_log)]
    disjoint(roots)
    ids = [(metadata(p).st_dev, metadata(p).st_ino) for p in roots]
    require(len({x[0] for x in ids}) == 1, "ROLLBACK_CROSS_DEVICE")
    history = scan(forward_log)
    require(bool(history) and history[-1]["operation"] == "update"
            and history[-1]["phase"] in ("OLD_MOVED", "NEW_MOVED", "VERIFIED"),
            "ROLLBACK_FORWARD_HISTORY")
    forward = history[-1]
    record = {**forward, "operation": "rollback", "phase": "PREPARED",
              "old_version": forward["new_version"], "new_version": forward["old_version"],
              "old_sha256": forward["new_sha256"], "new_sha256": forward["old_sha256"]}
    name = record["id"]

    def stable():
        require([(metadata(ordinary_root(p)).st_dev, metadata(p).st_ino)
                 for p in roots] == ids, "ROLLBACK_ROOT_CHANGED")
        require(scan(forward_log) == history, "ROLLBACK_FORWARD_CHANGED")

    def observe():
        stable()
        progress = scan(rollback_log)
        require(bool(progress) and progress[0] == record, "ROLLBACK_JOURNAL_MISMATCH")
        state = inspect(profile, backup, stage, encode(progress[-1]))
        require(state["status"] == "OBSERVATION_ONLY", "ROLLBACK_LAYOUT")
        return progress[-1]["phase"], state["state"]

    def log(phase):
        stable()
        append(rollback_log, {**record, "phase": phase})

    existing = scan(rollback_log)
    if not existing:
        stable()
        require(inspect(profile, stage, backup, encode(forward))["state"] == FINAL,
                "ROLLBACK_FORWARD_LAYOUT")
        log("PREPARED")

    phase, state = observe()
    if state == "NOT_STARTED":
        move_verified(profile, stage, name, (record["old_version"], record["old_sha256"]))
        phase, state = observe()
    if state == "OLD_IN_BACKUP":
        if phase == "PREPARED":
            log("OLD_MOVED")
            phase, state = observe()
        require(phase == "OLD_MOVED" and state == "OLD_IN_BACKUP", "ROLLBACK_LAYOUT")
        move_verified(backup, profile, name, (record["new_version"], record["new_sha256"]))
        phase, state = observe()
    require(state == FINAL, "ROLLBACK_LAYOUT")
    if phase == "OLD_MOVED":
        log("NEW_MOVED")
        phase, state = observe()
    if phase == "NEW_MOVED":
        log("VERIFIED")
        phase, state = observe()
    require(phase == "VERIFIED" and state == FINAL, "ROLLBACK_POSTCHECK")
    return {"status": "RESTORED_OBSERVED", "id": name,
            "restored_version": record["new_version"],
            "retained_version": record["old_version"],
            "forward_history_preserved": True,
            "apply_authorized": False, "exclusive_access": "NOT_VERIFIED",
            "source_authenticity": "NOT_VERIFIED", "durability": "NOT_VERIFIED"}
