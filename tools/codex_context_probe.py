#!/usr/bin/env python3
"""Read-only TD17 diagnostic. No Git, no subprocess, no environment mutations.

Recognizes fixed configuration-key labels, not configuration values. Unknown
keys are never reproduced. Presence of a known label is NOT authorization.
"""
from __future__ import annotations

import json
import os
import re
import sys

MAX_PAIRS = 64
INDEX = re.compile(r"GIT_CONFIG_(KEY|VALUE)_([0-9]{1,6})\Z")
COUNT = re.compile(r"(?:0|[1-9][0-9]?)\Z")
LABELS = frozenset({
    "core.hookspath", "core.fsmonitor", "core.worktree", "core.sshcommand",
    "core.askpass", "core.autocrlf", "core.longpaths", "core.protectntfs",
    "core.protecthfs", "core.bare", "core.filemode", "core.repositoryformatversion",
    "credential.helper", "credential.interactive", "safe.directory",
    "protocol.allow", "protocol.file.allow", "protocol.ext.allow",
    "protocol.http.allow", "protocol.https.allow", "protocol.ssh.allow",
    "protocol.git.allow", "protocol.version", "http.sslverify",
    "commit.gpgsign", "tag.gpgsign", "gpg.program", "gpg.format",
    "include.path", "user.name", "user.email", "user.useconfigonly",
    "maintenance.auto", "gc.auto", "fetch.recurseSubmodules".lower(),
    "submodule.recurse", "core.pager", "pager.log", "diff.external",
    "core.attributesfile", "core.excludesfile", "core.safecrlf",
    "core.untrackedcache", "core.ignorecase", "core.precomposeunicode",
    "core.symlinks", "init.defaultbranch", "core.fsync",
})


def observe(env):
    names = set(env)
    indexed = {"KEY": set(), "VALUE": set()}
    malformed = False
    other_git = False
    for name in names:
        if not name.upper().startswith("GIT_"):
            continue
        if name in ("GIT_CONFIG_COUNT", "GIT_PAGER"):
            continue
        match = INDEX.fullmatch(name)
        if match:
            kind, index = match.groups()
            i = int(index)
            if str(i) != index or i >= MAX_PAIRS:
                malformed = True
            else:
                indexed[kind].add(i)
        elif name.upper().startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")):
            malformed = True
        else:
            other_git = True
    count_present = "GIT_CONFIG_COUNT" in names
    count = env["GIT_CONFIG_COUNT"] if count_present else None
    valid = (isinstance(count, str) and COUNT.fullmatch(count) is not None
             and int(count) <= MAX_PAIRS)
    expected = set(range(int(count))) if valid else set()
    shape_ok = (not malformed and (valid if count_present else not any(indexed.values()))
                and indexed["KEY"] == indexed["VALUE"] == expected)
    rows = []
    # Only the key-name field is inspected; VALUE_n is never retrieved.
    if shape_ok and count_present:
        for i in sorted(expected):
            label = env[f"GIT_CONFIG_KEY_{i}"]
            recognized = label.lower() if isinstance(label, str) and len(label) <= 128 else ""
            rows.append({"index": i, "label": recognized if recognized in LABELS else "OTHER"})
    return {"schema_version": 1,
            "context_shape": "WELL_FORMED" if shape_ok else "MALFORMED",
            "indexed_pair_count": len(expected) if shape_ok else None,
            "key_labels": rows,
            "other_git_names_present": other_git,
            "pager_present": "GIT_PAGER" in names,
            "git_execution": "NOT_EXECUTED", "configuration_values_read": False,
            "environment_changed": False, "release_authorized": False,
            "wrapper_provenance": "NOT_VERIFIED",
            "policy_compatibility": "NOT_VERIFIED"}


def main():
    report = observe(os.environ)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["context_shape"] == "WELL_FORMED" else 1


if __name__ == "__main__":
    sys.exit(main())
