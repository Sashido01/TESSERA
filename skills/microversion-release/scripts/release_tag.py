#!/usr/bin/env python3
"""Безопасно создаёт или проверяет обязательный аннотированный тег релиза."""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

VERSION = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.0$")
PREFIX = re.compile(r"^(?:[a-z0-9]+(?:-[a-z0-9]+)*/)*$")


class TagError(ValueError):
    """Невозможность создать или подтвердить корректный релизный тег."""


def git(repo: pathlib.Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True, encoding="utf-8", capture_output=True, check=False,
    )
    if check and proc.returncode:
        raise TagError(f"Git: {proc.stderr.strip() or proc.stdout.strip()}")
    return proc


def name_for(version: str, prefix: str = "") -> str:
    match = VERSION.fullmatch(version)
    if match is None or (int(match.group(1)) == 0 and int(match.group(2)) == 0):
        raise TagError("Тег релиза требует версию вида 0.1.0 или 1.0.0 (PATCH равен нулю)")
    if not PREFIX.fullmatch(prefix):
        raise TagError("Недопустимый префикс; пример: microversion-release/")
    return f"{prefix}v{version}"


def verify(repo: pathlib.Path, version: str, prefix: str = "") -> str:
    tag = name_for(version, prefix)
    repo = repo.resolve(strict=True)
    top = pathlib.Path(git(repo, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
    if top != repo:
        raise TagError("Укажите корень Git-репозитория, а не вложенный каталог")
    obj = git(repo, "rev-parse", "--verify", f"refs/tags/{tag}", check=False)
    if obj.returncode != 0:
        raise TagError(f"RELEASE_NOT_TAGGED: отсутствует тег {tag}")
    kind = git(repo, "cat-file", "-t", f"refs/tags/{tag}").stdout.strip()
    if kind != "tag":
        raise TagError(f"RELEASE_NOT_TAGGED: тег {tag} не аннотирован")
    annotated = git(repo, "cat-file", "-p", f"refs/tags/{tag}").stdout
    if not annotated.partition("\n\n")[2].strip():
        raise TagError(f"RELEASE_NOT_TAGGED: у тега {tag} пустая аннотация")
    commit = git(repo, "rev-parse", "HEAD^{commit}").stdout.strip()
    actual = git(repo, "rev-parse", f"refs/tags/{tag}^{{commit}}").stdout.strip()
    if actual != commit:
        raise TagError(f"RELEASE_NOT_TAGGED: {tag} указывает не на HEAD")
    return obj.stdout.strip()


def create(repo: pathlib.Path, version: str, message: str, prefix: str = "") -> str:
    tag = name_for(version, prefix)
    if not message.strip() or len(message.strip()) < 12:
        raise TagError("Для аннотированного тега нужно осмысленное описание релиза")
    repo = repo.resolve(strict=True)
    top = pathlib.Path(git(repo, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
    if top != repo:
        raise TagError("Укажите корень Git-репозитория")
    exists = git(repo, "rev-parse", "--verify", f"refs/tags/{tag}", check=False)
    if exists.returncode == 0:
        # Повторный запуск допускается только для правильного тега того же коммита.
        return verify(repo, version, prefix)
    git(repo, "tag", "-a", tag, "-m", message.strip())
    return verify(repo, version, prefix)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for action in ("verify", "create"):
        p = sub.add_parser(action)
        p.add_argument("version", help="Релизная версия, например 0.1.0")
        p.add_argument("--repo", type=pathlib.Path, required=True, help="Корень проекта")
        p.add_argument("--prefix", default="", help="Префикс для монорепозитория, например skill-name/")
        if action == "create":
            p.add_argument("--message", required=True, help="Русская аннотация реального релиза")
    args = parser.parse_args()
    try:
        sha = (create(args.repo, args.version, args.message, args.prefix)
               if args.command == "create" else verify(args.repo, args.version, args.prefix))
    except (OSError, TagError) as exc:
        print(f"BLOCKED / RELEASE_NOT_TAGGED: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: аннотированный тег {name_for(args.version, args.prefix)} подтверждён; SHA объекта: {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
