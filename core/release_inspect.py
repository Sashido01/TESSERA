#!/usr/bin/env python3
"""Читает доказательства Git-релиза, не изменяя репозиторий или теги.

Внимание: PASS подтверждает только версию и аннотированный тег.
Сборка, тесты, публикация и готовность релиза здесь НЕ проверяются.
"""
from __future__ import annotations

import argparse
import json
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


def git(repo: pathlib.Path, *args: str, allow_failure: bool = False) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            text=True, encoding="utf-8", capture_output=True, check=False,
        )
    except (OSError, UnicodeError) as exc:
        raise InspectionError(f"Не удалось выполнить Git: {exc}") from exc
    if result.returncode and not allow_failure:
        raise InspectionError(f"Git завершился с ошибкой: {result.stderr.strip() or result.stdout.strip()}")
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
        kind = git(root, "cat-file", "-t", ref).stdout.strip()
        annotated = kind == "tag"
        if not annotated:
            problems.append("TAG_NOT_ANNOTATED")
        else:
            data = git(root, "cat-file", "-p", ref).stdout
            annotation_present = bool(data.partition("\n\n")[2].strip())
            if not annotation_present:
                problems.append("TAG_ANNOTATION_MISSING")
        tagged = git(root, "rev-parse", "--verify", f"{ref}^{{commit}}", allow_failure=True)
        if tagged.returncode != 0:
            problems.append("TAG_TARGET_NOT_COMMIT")
        else:
            tag_commit_sha = tagged.stdout.strip().lower()
            if tag_commit_sha != wanted:
                problems.append("TAG_WRONG_COMMIT")

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
