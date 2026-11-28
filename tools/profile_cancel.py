"""Explicit cancellation of an unfinished update or a first installation.

Trusted, exclusive same-volume roots only. Caller authorization and provenance
are independent prerequisites. No CLI, deletion, or automatic fallback.
"""
from __future__ import annotations

from catalog_index import require
from profile_plan import disjoint, metadata, ordinary_root
from profile_journal import append, encode, scan
from profile_move import move_verified
from profile_recovery import inspect


def cancel(profile, stage, backup, forward_log, cancel_log):
    """Cancel without losing either skill copy; explicitly resume on retry.

    A completed update requires profile_rollback instead. Original journal
    stays intact; cancel journal is separate. Neither journal authorizes writes.
    """
    roots = [ordinary_root(p) for p in (profile, stage, backup, forward_log, cancel_log)]
    disjoint(roots)
    ids = [(metadata(p).st_dev, metadata(p).st_ino) for p in roots]
    require(len({x[0] for x in ids}) == 1, "CANCEL_CROSS_DEVICE")
    history = scan(forward_log)
    require(bool(history) and history[-1]["operation"] in ("install", "update"),
            "CANCEL_FORWARD_HISTORY")
    forward = history[-1]
    install = forward["operation"] == "install"
    require(install or forward["phase"] in ("PREPARED", "OLD_MOVED"),
            "CANCEL_FORWARD_PHASE")
    record = {**forward, "operation": "cancel-" + forward["operation"], "phase": "PREPARED"}

    def stable():
        require([(metadata(ordinary_root(p)).st_dev, metadata(p).st_ino)
                 for p in roots] == ids, "CANCEL_ROOT_CHANGED")
        require(scan(forward_log) == history, "CANCEL_FORWARD_CHANGED")

    def observe():
        stable()
        progress = scan(cancel_log)
        require(bool(progress) and progress[0] == record, "CANCEL_JOURNAL_MISMATCH")
        state = inspect(profile, stage, backup, encode(progress[-1]))
        require(state["status"] == "OBSERVATION_ONLY", "CANCEL_LAYOUT")
        return progress[-1]["phase"], state["state"]

    def log(phase):
        stable()
        append(cancel_log, {**record, "phase": phase})

    if not scan(cancel_log):
        stable()
        forward_state = inspect(profile, stage, backup, encode(forward))["state"]
        allowed = ("NOT_STARTED", "NEW_PRESENT") if install else ("NOT_STARTED", "OLD_IN_BACKUP")
        require(forward_state in allowed, "CANCEL_FORWARD_LAYOUT")
        log("PREPARED")

    phase, state = observe()
    if state == "CANCEL_READY":
        require(phase == "PREPARED", "CANCEL_LAYOUT")
        if install:
            move_verified(profile, stage, record["id"],
                          (record["new_version"], record["new_sha256"]))
        else:
            move_verified(backup, profile, record["id"],
                          (record["old_version"], record["old_sha256"]))
        phase, state = observe()
    require(state == "CANCELLED", "CANCEL_LAYOUT")
    if phase == "PREPARED":
        log("VERIFIED")
        phase, state = observe()
    require(phase == "VERIFIED" and state == "CANCELLED", "CANCEL_POSTCHECK")
    return {"status": "CANCELLED_OBSERVED", "id": record["id"],
            "restored_version": record["old_version"],
            "retained_version": record["new_version"],
            "forward_history_preserved": True,
            "apply_authorized": False, "exclusive_access": "NOT_VERIFIED",
            "source_authenticity": "NOT_VERIFIED", "durability": "NOT_VERIFIED"}
