#!/usr/bin/env python3
"""T09.03: проверка удалённого аннотированного Git-тега без изменения refs."""
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys
import urllib.parse
from typing import Any

try:
    from .release_inspect import InspectionError, canonical_repo, inspect, git, local_git_environment
except ImportError:
    from release_inspect import InspectionError, canonical_repo, inspect, git, local_git_environment

REMOTE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
OBJECT_SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


def remote_url(root: pathlib.Path, remote: str) -> str:
    """Resolve exactly one configured fetch URL; never infer a repository path."""
    if not isinstance(remote, str) or not REMOTE_NAME.fullmatch(remote):
        raise InspectionError("REMOTE_NAME_INVALID")
    resolved = git(root, "remote", "get-url", "--all", remote, allow_failure=True)
    lines = resolved.stdout.splitlines()
    if resolved.returncode != 0 or len(lines) != 1:
        raise InspectionError("REMOTE_URL_UNVERIFIED")
    address = lines[0]
    if (not address or len(address) > 4096 or address != address.strip()
            or any(ord(c) < 32 or ord(c) == 127 for c in address)):
        raise InspectionError("REMOTE_URL_INVALID")
    if pathlib.Path(address).is_absolute():
        return address
    if re.fullmatch(r"[A-Za-z0-9._-]+@[A-Za-z0-9][A-Za-z0-9.-]*:[^\s]+", address):
        return address
    try:
        parts = urllib.parse.urlsplit(address)
        if parts.scheme == "file":
            if (parts.netloc not in ("", "localhost") or not parts.path.startswith("/")
                    or parts.query or parts.fragment):
                raise ValueError("file URL")
        elif parts.scheme in ("https", "ssh"):
            if (not parts.hostname or not parts.path or parts.query or parts.fragment
                    or parts.password is not None or any(c.isspace() for c in address)
                    or (parts.scheme == "https" and parts.username is not None)
                    or (parts.port is not None and not 1 <= parts.port <= 65535)):
                raise ValueError("remote URL")
        else:
            raise ValueError("protocol")
    except ValueError as exc:
        raise InspectionError("REMOTE_URL_INVALID") from exc
    return address


def github_remote_matches(address: str, repository: str) -> bool:
    try:
        if address.startswith("git@github.com:"):
            path = address.removeprefix("git@github.com:")
        else:
            parts = urllib.parse.urlsplit(address)
            if (parts.scheme not in ("https", "ssh")
                    or parts.hostname != "github.com" or parts.port is not None
                    or parts.query or parts.fragment or parts.password is not None
                    or (parts.scheme == "ssh" and parts.username != "git")
                    or (parts.scheme == "https" and parts.username is not None)):
                return False
            path = parts.path.removeprefix("/")
        return path.removesuffix(".git").casefold() == repository.casefold()
    except ValueError:
        return False


def query_remote(root, remote, ref, timeout_seconds):
    env = local_git_environment()
    agent = os.getenv("SSH_AUTH_SOCK")
    if agent is not None:
        env["SSH_AUTH_SOCK"] = agent
    env.update({"GCM_INTERACTIVE": "never", "GIT_ALLOW_PROTOCOL": "file:https:ssh"})
    return subprocess.run(
        ["git", "--no-replace-objects", "--no-optional-locks", "-C", str(root),
         "-c", "protocol.ext.allow=never", "-c", "http.followRedirects=false",
         "ls-remote", "--upload-pack=git-upload-pack", "--refs", "--tags", remote, ref],
        capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL,
        env=env, timeout=timeout_seconds, check=False,
    )


def verify_remote_tag(
    repo: pathlib.Path,
    version: str,
    *,
    prefix: str = "",
    skill: str | None = None,
    commit: str | None = None,
    remote: str = "origin",
    timeout_seconds: int = 15,
    expected_repository: str | None = None,
) -> dict[str, Any]:
    """Проверяет совпадение SHA самого аннотированного тега, не выполняя fetch/push."""
    if not isinstance(remote, str) or not REMOTE_NAME.fullmatch(remote):
        raise InspectionError("REMOTE_NAME_INVALID")
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 60:
        raise InspectionError("REMOTE_TIMEOUT_INVALID")
    root = canonical_repo(repo)
    local = inspect(root, version, prefix=prefix, commit=commit, skill=skill)
    tag = local["requested_tag"]
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

    ref = f"refs/tags/{tag}"
    try:
        address = remote_url(root, remote)
        if expected_repository is not None and not github_remote_matches(address, expected_repository):
            result["problems"] = ["REMOTE_REPOSITORY_MISMATCH"]
            return result
        response = query_remote(root, remote, ref, timeout_seconds)
    except subprocess.TimeoutExpired:
        result["problems"] = ["REMOTE_QUERY_TIMEOUT"]
        return result
    except (OSError, UnicodeError, InspectionError):
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
    try:
        current = inspect(root, version, prefix=prefix, commit=commit, skill=skill)
        if (current["inspection_status"] != "PASS"
                or current["expected_commit_sha"] != local["expected_commit_sha"]
                or current["tag_object_sha"] != local["tag_object_sha"]
                or remote_url(root, remote) != address):
            result["problems"] = ["REMOTE_EVIDENCE_CHANGED"]
            return result
    except (InspectionError, OSError):
        result["problems"] = ["REMOTE_EVIDENCE_CHANGED"]
        return result
    result["remote_tag_status"] = "PASS"
    result["remote_publication"] = "TAG_REF_VERIFIED"
    return result


if __name__ == "__main__":
    print("Используйте core/release_report.py --verify-remote для проверки и отчёта.", file=sys.stderr)
    sys.exit(2)
