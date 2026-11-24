#!/usr/bin/env python3
"""Читает доказательства Git-релиза, не изменяя репозиторий или теги.

Внимание: PASS подтверждает только версию и аннотированный тег.
Сборка, тесты, публикация и готовность релиза здесь НЕ проверяются.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
from typing import Any

VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z")
PREFIX = re.compile(r"(?:[a-z0-9]+(?:-[a-z0-9]+)*/)*\Z")
COMMIT_SHA = re.compile(r"[a-fA-F0-9]{40}(?:[a-fA-F0-9]{24})?\Z")


class InspectionError(ValueError):
    """Не удалось безопасно изучить запрошенные доказательства."""


# Local inspection does not need identity, signing or authentication context.
GIT_CONTEXT = frozenset({
    "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE", "GIT_GRAFT_FILE", "GIT_SHALLOW_FILE",
    "GIT_REPLACE_REF_BASE", "GIT_IMPLICIT_WORK_TREE", "GIT_PREFIX",
    "GIT_INTERNAL_SUPER_PREFIX", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_COUNT", "GIT_CONFIG_SYSTEM", "GIT_CONFIG_GLOBAL",
    "GIT_CONFIG_NOSYSTEM", "GIT_EXEC_PATH",
})
LOCAL_ENV_KEYS = (
    "PATH", "HOME", "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "SystemRoot",
    "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP", "TMPDIR",
    "APPDATA", "LOCALAPPDATA", "LANG", "LC_ALL", "LC_CTYPE", "LC_MESSAGES", "TZ",
)
GIT_TIMEOUT = 30


def local_git_environment() -> dict[str, str]:
    if any(os.getenv(key) is not None for key in GIT_CONTEXT):
        raise InspectionError("GIT_CONTEXT_UNSAFE")
    result = {}
    for key in LOCAL_ENV_KEYS:
        value = os.getenv(key)
        if value is not None:
            result[key] = value
    result.update({"GIT_NO_LAZY_FETCH": "1", "GIT_TERMINAL_PROMPT": "0"})
    return result


def git(repo: pathlib.Path, *args: str, allow_failure: bool = False) -> subprocess.CompletedProcess[str]:
    env = local_git_environment()
    try:
        result = subprocess.run(
            ["git", "--no-replace-objects", "--no-optional-locks",
             "-c", "core.fsmonitor=false", "-C", str(repo), *args],
            text=True, encoding="utf-8", capture_output=True, check=False,
            stdin=subprocess.DEVNULL, env=env, timeout=GIT_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        raise InspectionError("GIT_INSPECTION_TIMEOUT") from exc
    except (OSError, UnicodeError) as exc:
        raise InspectionError("GIT_INSPECTION_FAILED") from exc
    if result.returncode and not allow_failure:
        raise InspectionError("GIT_INSPECTION_FAILED")
    return result


def canonical_repo(repo: pathlib.Path) -> pathlib.Path:
    try:
        root = repo.expanduser().resolve(strict=True)
    except OSError as exc:
        raise InspectionError("Каталог репозитория недоступен") from exc
    if not root.is_dir():
        raise InspectionError("Ожидается каталог Git-репозитория")
    actual = pathlib.Path(git(root, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
    if actual != root:
        raise InspectionError("Укажите корень репозитория, а не вложенный каталог")
    return root


def resolve_commit(root: pathlib.Path, commit: str | None) -> str:
    if commit is not None and not COMMIT_SHA.fullmatch(commit):
        raise InspectionError("--commit должен содержать полный SHA Git-коммита")
    target = commit or "HEAD"
    result = git(root, "rev-parse", "--verify", f"{target}^{{commit}}")
    sha = result.stdout.strip()
    if not COMMIT_SHA.fullmatch(sha):
        raise InspectionError("Git вернул некорректный commit SHA")
    if commit is not None and sha.lower() != commit.lower():
        raise InspectionError("COMMIT_SHA_NOT_DIRECT")
    return sha.lower()


def tag_name(version: str, prefix: str = "") -> str:
    if VERSION.fullmatch(version) is None:
        raise InspectionError("Номер версии должен иметь вид MAJOR.MINOR.PATCH")
    if PREFIX.fullmatch(prefix) is None:
        raise InspectionError("Недопустимый префикс тега; пример: microversion-release/")
    return f"{prefix}v{version}"


def inspect(repo: pathlib.Path, version: str, prefix: str = "", commit: str | None = None) -> dict[str, Any]:
    root = canonical_repo(repo)
    wanted = resolve_commit(root, commit)
    ref = f"refs/tags/{tag_name(version, prefix)}"
    problems: list[str] = []

    version_file = git(root, "show", f"{wanted}:VERSION", allow_failure=True)
    recorded_version = version_file.stdout.strip() if version_file.returncode == 0 else None
    if recorded_version is None:
        problems.append("VERSION_MISSING_IN_COMMIT")
    elif recorded_version != version:
        problems.append("VERSION_MISMATCH")

    status = git(root, "status", "--porcelain=v1", "--untracked-files=all").stdout
    tag_obj = git(root, "rev-parse", "--verify", ref, allow_failure=True)
    annotated = False
    tag_object_sha = None
    tag_commit_sha = None
    annotation_present = False

    if tag_obj.returncode != 0:
        problems.append("RELEASE_NOT_TAGGED")
    else:
        tag_object_sha = tag_obj.stdout.strip()
        if not COMMIT_SHA.fullmatch(tag_object_sha):
            raise InspectionError("TAG_OBJECT_SHA_INVALID")
        kind = git(root, "cat-file", "-t", tag_object_sha).stdout.strip()
        annotated = kind == "tag"
        if not annotated:
            problems.append("TAG_NOT_ANNOTATED")
            if kind == "commit":
                tag_commit_sha = tag_object_sha.lower()
            else:
                problems.append("TAG_TARGET_NOT_COMMIT")
        else:
            data = git(root, "cat-file", "-p", tag_object_sha).stdout
            header, separator, message = data.partition("\n\n")
            annotation_present = bool(separator and message.strip())
            if not annotation_present:
                problems.append("TAG_ANNOTATION_MISSING")
            fields = header.splitlines()
            if len(fields) < 3 or fields[2] != f"tag {ref.removeprefix('refs/tags/')}":
                problems.append("TAG_NAME_MISMATCH")
            target = fields[0].removeprefix("object ") if fields else ""
            if (len(fields) < 2 or not fields[0].startswith("object ")
                    or not COMMIT_SHA.fullmatch(target) or fields[1] != "type commit"):
                problems.append("TAG_TARGET_NOT_COMMIT")
            elif git(root, "cat-file", "-t", target, allow_failure=True).stdout.strip() != "commit":
                problems.append("TAG_TARGET_NOT_COMMIT")
            else:
                tag_commit_sha = target.lower()
        if tag_commit_sha is not None and tag_commit_sha != wanted:
            problems.append("TAG_WRONG_COMMIT")

    final_ref = git(root, "rev-parse", "--verify", ref, allow_failure=True)
    if ((final_ref.returncode == 0) != (tag_obj.returncode == 0)
            or (final_ref.returncode == 0 and final_ref.stdout.strip() != tag_object_sha)):
        problems.append("TAG_REF_CHANGED")
    if commit is None and resolve_commit(root, None) != wanted:
        problems.append("HEAD_CHANGED")

    return {
        "schema_version": 1,
        "requested_version": version,
        "requested_tag": ref.removeprefix("refs/tags/"),
        "expected_commit_sha": wanted,
        "version_in_commit": recorded_version,
        "tag_object_sha": tag_object_sha,
        "tag_target_commit_sha": tag_commit_sha,
        "tag_annotated": annotated,
        "tag_has_annotation": annotation_present,
        "worktree_clean": not bool(status.strip()),
        "inspection_status": "PASS" if not problems else "BLOCKED",
        "release_readiness": "NOT_VERIFIED",
        "remote_publication": "NOT_CHECKED",
        "checks_not_performed": ["build", "tests", "remote_tag", "github_release"],
        "problems": problems,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=pathlib.Path, help="Корень Git-репозитория")
    parser.add_argument("--version", required=True, help="Версия релиза, например 0.1.0")
    parser.add_argument("--prefix", default="", help="Префикс тега для монорепозитория")
    parser.add_argument("--commit", help="Полный SHA исторического коммита; по умолчанию HEAD")
    args = parser.parse_args()
    try:
        result = inspect(args.repo, args.version, args.prefix, args.commit)
    except InspectionError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["inspection_status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
