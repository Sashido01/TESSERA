"""Resume a verified install/update in exclusively controlled roots.

Library only: no CLI, automatic authorization, deletion or fallback.
The caller supplies independently verified expected versions/digests and
exclusive access; this module does not establish either prerequisite.
"""
from __future__ import annotations

from catalog_index import require
from profile_plan import disjoint, metadata, ordinary_root
from profile_journal import append, encode, scan
from profile_move import move_verified
from profile_recovery import inspect, journal


def advance(profile, stage, backup, forward_log, rollback_log, cancel_log, prepared):
    """Explicitly complete or resume one forward operation.

    Refuse to resume once either reverse journal exists. On error preserve
    every copy and journal; a later explicit invocation rechecks the layout.
    """
    record = journal(encode(prepared))
    require(record["operation"] in ("install", "update")
            and record["phase"] == "PREPARED", "ADVANCE_RECORD")
    roots = [ordinary_root(p) for p in (profile, stage, backup, forward_log,
                                        rollback_log, cancel_log)]
    disjoint(roots)
    ids = [(metadata(p).st_dev, metadata(p).st_ino) for p in roots]
    require(len({x[0] for x in ids}) == 1, "ADVANCE_CROSS_DEVICE")
    install = record["operation"] == "install"
    name = record["id"]
    final = "NEW_PRESENT" if install else "NEW_PRESENT_OLD_RETAINED"

    def stable():
        require([(metadata(ordinary_root(p)).st_dev, metadata(p).st_ino)
                 for p in roots] == ids, "ADVANCE_ROOT_CHANGED")
        require(not scan(rollback_log) and not scan(cancel_log), "ADVANCE_REVERSE_STARTED")

    def observe():
        stable()
        history = scan(forward_log)
        require(bool(history) and history[0] == record, "ADVANCE_JOURNAL_MISMATCH")
        state = inspect(profile, stage, backup, encode(history[-1]))
        require(state["status"] == "OBSERVATION_ONLY", "ADVANCE_LAYOUT")
        return history[-1]["phase"], state["state"]

    def log(phase):
        stable()
        append(forward_log, {**record, "phase": phase})

    stable()
    if not scan(forward_log):
        require(inspect(profile, stage, backup, encode(record))["state"] == "NOT_STARTED",
                "ADVANCE_INITIAL_LAYOUT")
        log("PREPARED")
    phase, state = observe()
    if state == "NOT_STARTED":
        if install:
            move_verified(stage, profile, name, (record["new_version"], record["new_sha256"]))
        else:
            move_verified(profile, backup, name, (record["old_version"], record["old_sha256"]))
        phase, state = observe()
    if not install and state == "OLD_IN_BACKUP":
        if phase == "PREPARED":
            log("OLD_MOVED")
            phase, state = observe()
        require(phase == "OLD_MOVED" and state == "OLD_IN_BACKUP", "ADVANCE_LAYOUT")
        move_verified(stage, profile, name, (record["new_version"], record["new_sha256"]))
        phase, state = observe()
    require(state == final, "ADVANCE_LAYOUT")
    if phase == ("PREPARED" if install else "OLD_MOVED"):
        log("NEW_MOVED")
        phase, state = observe()
    if phase == "NEW_MOVED":
        log("VERIFIED")
        phase, state = observe()
    require(phase == "VERIFIED" and state == final, "ADVANCE_POSTCHECK")
    return {"status": "INSTALLED_OBSERVED" if install else "UPDATED_OBSERVED",
            "id": name, "version": record["new_version"],
            "backup_retained": not install, "apply_authorized": False,
            "source_authenticity": "NOT_VERIFIED", "exclusive_access": "NOT_VERIFIED",
            "durability": "NOT_VERIFIED"}
