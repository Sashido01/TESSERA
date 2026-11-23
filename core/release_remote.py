#!/usr/bin/env python3
"""T09.03: проверка удалённого аннотированного Git-тега без изменения refs."""
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys
from typing import Any

try:
    from .release_inspect import InspectionError, canonical_repo, inspect, tag_name
except ImportError:
    from release_inspect import InspectionError, canonical_repo, inspect, tag_name

REMOTE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
OBJECT_SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


def verify_remote_tag(
    repo: pathlib.Path,
    version: str,
    *,
    prefix: str = "",
    commit: str | None = None,
    remote: str = "origin",
    timeout_seconds: int = 15,
) -> dict[str, Any]:
    """Проверяет совпадение SHA самого аннотированного тега, не выполняя fetch/push."""
    if not isinstance(remote, str) or not REMOTE_NAME.fullmatch(remote):
        raise InspectionError("REMOTE_NAME_INVALID")
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 60:
        raise InspectionError("REMOTE_TIMEOUT_INVALID")
    root = canonical_repo(repo)
    local = inspect(root, version, prefix=prefix, commit=commit)
    tag = tag_name(version, prefix)
    result: dict[str, Any] = {
        "schema_version": 1,
        "remote": remote,
        "tag": tag,
        "expected_commit_sha": local["expected_commit_sha"],
        "local_tag_object_sha": local["tag_object_sha"],
        "remote_tag_object_sha": None,
        "local_tag_status": local["inspection_status"],
        "remote_tag_status": "BLOCKED",
        "remote_publication": "NOT_VERIFIED",
        "github_release": "NOT_CHECKED",
        "problems": [],
    }
    if local["inspection_status"] != "PASS":
        result["problems"] = ["LOCAL_TAG_INVALID", *local["problems"]]
        return result

    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GCM_INTERACTIVE"] = "never"
    ref = f"refs/tags/{tag}"
    try:
        response = subprocess.run(
            ["git", "-C", str(root), "-c", "protocol.ext.allow=never",
             "ls-remote", "--refs", "--tags", remote, ref],
            capture_output=True, text=True, encoding="utf-8",
            env=env, timeout=timeout_seconds, check=False,
        )
    except subprocess.TimeoutExpired:
        result["problems"] = ["REMOTE_QUERY_TIMEOUT"]
        return result
    except (OSError, UnicodeError):
        result["problems"] = ["REMOTE_QUERY_FAILED"]
        return result
    if response.returncode != 0:
        result["problems"] = ["REMOTE_QUERY_FAILED"]
        return result
    lines = [line for line in response.stdout.splitlines() if line.strip()]
    if not lines:
        result["problems"] = ["REMOTE_TAG_MISSING"]
        return result
    if len(lines) != 1:
        result["problems"] = ["REMOTE_RESPONSE_INVALID"]
        return result
    fields = lines[0].split("\t")
    if len(fields) != 2 or fields[1] != ref or not OBJECT_SHA.fullmatch(fields[0]):
        result["problems"] = ["REMOTE_RESPONSE_INVALID"]
        return result
    result["remote_tag_object_sha"] = fields[0]
    if fields[0] != local["tag_object_sha"]:
        result["problems"] = ["REMOTE_TAG_OBJECT_MISMATCH"]
        return result
    result["remote_tag_status"] = "PASS"
    result["remote_publication"] = "TAG_REF_VERIFIED"
    return result


if __name__ == "__main__":
    print("Используйте core/release_report.py --verify-remote для проверки и отчёта.", file=sys.stderr)
    sys.exit(2)
