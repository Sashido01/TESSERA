#!/usr/bin/env python3
"""T08.01: prevent reverting approved pinned Node.js 24 GitHub Actions.

The exact upstream action.yml manifests were independently checked before
pinning. This static check does not fetch code or execute a signing workflow.
"""
from __future__ import annotations

from collections import Counter
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PINS = {
    "actions/checkout": "3d3c42e5aac5ba805825da76410c181273ba90b1",  # v7.0.1 node24
    "actions/setup-python": "6d4fd22b20465ccc0f7354476588e8df7c9ca0e0",  # v7.1.0 node24
    "actions/attest": "1e69f48acb82d1966a394da916b4c1698aa569d6",  # v4.2.2 node24
    "actions/upload-artifact": "cf430e030ddbb5b0abf93d22962f4752f3646cd9",  # v7.0.2 node24
}
EXPECTED = {
    "validate.yml": {"actions/checkout": 3, "actions/setup-python": 2},
    "build-attested-catalog.yml": {
        "actions/checkout": 1,
        "actions/setup-python": 1,
        "actions/attest": 1,
        "actions/upload-artifact": 1,
    },
}
USE = re.compile(r"(?m)^\s*uses:\s*(\S+)\s*(?:#.*)?$")
REF = re.compile(r"([a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+)@([a-f0-9]{40})\Z")


def check_workflow(content: str, file_name: str) -> list[str]:
    expected = EXPECTED.get(file_name)
    if expected is None:
        return ["NODE24_UNKNOWN_WORKFLOW"]
    found: Counter[str] = Counter()
    errors: set[str] = set()
    for raw in USE.findall(content):
        match = REF.fullmatch(raw)
        if not match:
            errors.add("NODE24_ACTION_NOT_SHA_PINNED")
            continue
        action, sha = match.groups()
        found[action] += 1
        if action not in expected:
            errors.add("NODE24_UNEXPECTED_ACTION")
        if PINS.get(action) != sha:
            errors.add("NODE24_ACTION_PIN_MISMATCH")
    if dict(found) != expected:
        errors.add("NODE24_ACTION_SET_CHANGED")
    return sorted(errors)


def validate(root: pathlib.Path) -> list[str]:
    problems: list[str] = []
    for filename in EXPECTED:
        path = root / ".github" / "workflows" / filename
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            problems.append("NODE24_WORKFLOW_UNAVAILABLE:" + filename)
            continue
        problems.extend(check_workflow(content, filename))
    return sorted(set(problems))


def main() -> int:
    problems = validate(ROOT)
    for code in problems:
        print("BLOCKED: " + code, file=sys.stderr)
    if problems:
        return 1
    print("Node.js 24 Actions: PASS (pinned SHA inventory; runtime is CI-verified)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
