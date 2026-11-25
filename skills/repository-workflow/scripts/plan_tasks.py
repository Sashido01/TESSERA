#!/usr/bin/env python3
"""Read-only selection of independent work from an explicit local task snapshot."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
STATES = frozenset({"BACKLOG", "READY", "IN_PROGRESS", "WAIT_DEPENDENCY", "WAIT_CI",
                    "CI_FAILED", "READY_TO_INTEGRATE", "WAIT_RELEASE", "WAIT_OWNER",
                    "BLOCKED", "COMPLETE"})
HELD = frozenset({"IN_PROGRESS", "WAIT_CI", "CI_FAILED", "READY_TO_INTEGRATE",
                  "WAIT_RELEASE", "WAIT_OWNER", "BLOCKED"})
PRIORITIES = ("P0", "P1", "P2")
MAX_BYTES = 2 * 1024 * 1024


class PlanError(ValueError):
    """Invalid or incomplete planning input."""


def require(condition, code):
    if not condition:
        raise PlanError(code)


def identifiers(values):
    require(isinstance(values, list) and len(values) <= 1000 and
            all(isinstance(x, str) and ID.fullmatch(x) for x in values), "PLAN_IDS")
    require(len(set(values)) == len(values), "PLAN_DUPLICATE_ID")
    return values


def path_scope(value):
    require(isinstance(value, str) and 0 < len(value) <= 512, "PLAN_SCOPE")
    if value == ".":
        return value
    parts = value.split("/")
    require(all(p not in ("", ".", "..") and not p.endswith((".", " ")) and
                not any(ord(c) < 32 or c in '\\:*?"<>|' for c in p) for p in parts), "PLAN_SCOPE")
    return "/".join(p.casefold() for p in parts)


def overlaps(a, b):
    return a == "." or b == "." or a == b or a.startswith(b + "/") or b.startswith(a + "/")


def conflicts(a, b):
    return (bool(a["resources"] & b["resources"]) or
            any(overlaps(x, y) for x in a["scope"] for y in b["scope"]))


def plan(data):
    require(isinstance(data, dict) and set(data) == {"streams", "tasks"}, "PLAN_FORMAT")
    streams = identifiers(data["streams"])
    rows = data["tasks"]
    require(streams and isinstance(rows, list) and len(rows) <= 1000, "PLAN_SIZE")
    tasks = {}
    fields = {"id", "stream", "priority", "status", "depends_on", "write_scope", "resources", "read_only", "evidence"}
    for row in rows:
        require(isinstance(row, dict) and set(row) == fields, "PLAN_TASK_FORMAT")
        name = identifiers([row["id"]])[0]
        require(name not in tasks and row["stream"] in streams and row["priority"] in PRIORITIES and
                isinstance(row["status"], str) and row["status"] in STATES, "PLAN_TASK_STATE")
        deps = identifiers(row["depends_on"])
        resources = {x.casefold() for x in identifiers(row["resources"])}
        scope = row["write_scope"]
        require(isinstance(scope, list) and len(scope) <= 100 and type(row["read_only"]) is bool, "PLAN_SCOPE")
        scope = {path_scope(x) for x in scope}
        require(bool(scope) != row["read_only"], "PLAN_SCOPE_UNKNOWN")
        evidence = row["evidence"]
        require(isinstance(evidence, list) and len(evidence) <= 100 and
                all(isinstance(x, str) and 0 < len(x.strip()) <= 512 for x in evidence), "PLAN_EVIDENCE")
        require(row["status"] != "COMPLETE" or evidence, "PLAN_COMPLETE_WITHOUT_EVIDENCE")
        tasks[name] = {"id": name, "stream": row["stream"], "priority": row["priority"],
                       "status": row["status"], "deps": deps, "scope": scope, "resources": resources}
    for task in tasks.values():
        require(set(task["deps"]) <= tasks.keys(), "PLAN_UNKNOWN_DEPENDENCY")
    # Bounded iterative DAG validation; no recursion on user-provided graphs.
    pending = set(tasks)
    while pending:
        layer = {i for i in pending if not (set(tasks[i]["deps"]) & pending)}
        require(layer, "PLAN_DEPENDENCY_CYCLE")
        pending -= layer
    for task in tasks.values():
        require(task["status"] != "COMPLETE" or all(tasks[d]["status"] == "COMPLETE" for d in task["deps"]),
                "PLAN_COMPLETE_DEPENDENCY_OPEN")
    held = [t for t in tasks.values() if t["status"] in HELD]
    selected = []
    deferred = {}
    for stream in streams:
        choices = sorted((t for t in tasks.values() if t["stream"] == stream and t["status"] in {"READY", "CI_FAILED"}),
                         key=lambda t: (PRIORITIES.index(t["priority"]), t["status"] != "CI_FAILED", t["id"]))
        for task in choices:
            name = task["id"]
            unmet = [d for d in task["deps"] if tasks[d]["status"] != "COMPLETE"]
            blockers = sorted({t["id"] for t in held + selected if t["id"] != name and conflicts(task, t)})
            if unmet or blockers:
                deferred[name] = {"dependencies": unmet, "conflicts": blockers}
                continue
            selected.append(task)
            break
    return {"selection": [{"id": t["id"], "stream": t["stream"],
                           "action": "FIX_CI" if t["status"] == "CI_FAILED" else "START"} for t in selected],
            "deferred": deferred,
            "waiting": sorted(t["id"] for t in tasks.values() if t["status"] in HELD),
            "status": "READY_WORK" if selected else "NO_READY_WORK",
            "scope": "ADVISORY_SNAPSHOT_NOT_A_LOCK"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, required=True)
    args = parser.parse_args()
    try:
        with args.tasks.open("rb") as source:
            raw = source.read(MAX_BYTES + 1)
        require(len(raw) <= MAX_BYTES, "PLAN_SIZE")
        result = plan(json.loads(raw))
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        print(str(exc) if isinstance(exc, PlanError) else "PLAN_INPUT_INVALID", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
