#!/usr/bin/env python3
"""Безопасно создаёт или проверяет обязательный аннотированный тег релиза."""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import subprocess
import sys

VERSION = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.0$")
PREFIX = re.compile(r"^(?:[a-z0-9]+(?:-[a-z0-9]+)*/)*$")
GIT_TIMEOUT = 60
MAX_GIT_OUTPUT = 1024 * 1024


class TagError(ValueError):
    """Невозможность создать или подтвердить корректный релизный тег."""


# An explicit repository argument must not be redirected by inherited Git context.
GIT_CONTEXT = frozenset({
    "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE", "GIT_GRAFT_FILE", "GIT_SHALLOW_FILE",
    "GIT_REPLACE_REF_BASE", "GIT_IMPLICIT_WORK_TREE", "GIT_PREFIX",
    "GIT_INTERNAL_SUPER_PREFIX", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_COUNT", "GIT_CONFIG_SYSTEM", "GIT_CONFIG_GLOBAL",
    "GIT_CONFIG_NOSYSTEM", "GIT_EXEC_PATH",
})


# Forward only explicit process, identity and local signing context.
# Git config override keys require GIT_CONFIG_COUNT; neither is forwarded.
CHILD_ENV_KEYS = (
    "PATH", "HOME", "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "SystemRoot",
    "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP", "TMPDIR", "APPDATA", "LOCALAPPDATA",
    "LANG", "LC_ALL", "LC_CTYPE", "LC_MESSAGES", "TZ", "TERM",
    "GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_AUTHOR_DATE",
    "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL", "GIT_COMMITTER_DATE",
    "GNUPGHOME", "GPG_TTY", "SSH_AUTH_SOCK",
)


def child_environment() -> dict[str, str]:
    if any(os.getenv(key) is not None for key in GIT_CONTEXT):
        raise TagError("RELEASE_NOT_TAGGED: внешнее окружение Git может изменить выбранный репозиторий или конфигурацию")
    result = {}
    for key in CHILD_ENV_KEYS:
        value = os.getenv(key)
        if value is not None:
            result[key] = value
    return result


def git_executable(env: dict[str, str]) -> pathlib.Path:
    # Only explicit absolute PATH entries; never search cwd or relative entries.
    # The installation and absolute PATH directories still must be trusted.
    name = "git.exe" if os.name == "nt" else "git"
    for entry in env.get("PATH", "").split(os.pathsep):
        directory = pathlib.Path(entry)
        if not directory.is_absolute():
            continue
        candidate = directory / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve(strict=True)
    raise TagError("GIT_EXECUTABLE_NOT_FOUND")


def git(repo: pathlib.Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = child_environment()
    try:
        executable = git_executable(env)
        proc = subprocess.run(
            [str(executable), "--no-replace-objects", "-C", str(repo), *args],
            text=True, encoding="utf-8", capture_output=True, check=False, env=env,
            shell=False, stdin=subprocess.DEVNULL, timeout=GIT_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        raise TagError("GIT_TIMEOUT: проверьте состояние тега перед повторной операцией") from exc
    except (OSError, UnicodeError) as exc:
        raise TagError("GIT_EXECUTION_FAILED") from exc
    # Post-capture limit, not a bound on process memory or pipe output.
    if len(proc.stdout) + len(proc.stderr) > MAX_GIT_OUTPUT:
        raise TagError("GIT_OUTPUT_LIMIT")
    if check and proc.returncode:
        # Do not publish untrusted Git diagnostics, paths or signing-helper output.
        raise TagError("GIT_EXECUTION_FAILED")
    return proc


def name_for(version: str, prefix: str = "") -> str:
    match = VERSION.fullmatch(version)
    if match is None or (int(match.group(1)) == 0 and int(match.group(2)) == 0):
        raise TagError("Тег релиза требует версию вида 0.1.0 или 1.0.0 (PATCH равен нулю)")
    if not PREFIX.fullmatch(prefix):
        raise TagError("Недопустимый префикс; пример: microversion-release/")
    return f"{prefix}v{version}"


OID = re.compile(r"(?:[a-f0-9]{40}|[a-f0-9]{64})\Z")


def head_commit(repo: pathlib.Path, expected_head: str | None = None) -> str:
    commit = git(repo, "rev-parse", "--verify", "HEAD^{commit}").stdout.strip()
    if not OID.fullmatch(commit):
        raise TagError("RELEASE_NOT_TAGGED: некорректный SHA HEAD")
    if expected_head is not None and (
            not OID.fullmatch(expected_head) or expected_head != commit):
        raise TagError("RELEASE_NOT_TAGGED: HEAD не совпадает с проверенным коммитом")
    return commit


def verify(repo: pathlib.Path, version: str, prefix: str = "",
           *, expected_head: str | None = None) -> str:
    tag = name_for(version, prefix)
    repo = repo.resolve(strict=True)
    top = pathlib.Path(git(repo, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
    if top != repo:
        raise TagError("Укажите корень репозитория Git, а не вложенный каталог")
    commit = head_commit(repo, expected_head)
    ref = f"refs/tags/{tag}"
    obj = git(repo, "rev-parse", "--verify", ref, check=False)
    if obj.returncode != 0:
        raise TagError(f"RELEASE_NOT_TAGGED: отсутствует тег {tag}")
    oid = obj.stdout.strip()
    if not OID.fullmatch(oid):
        raise TagError("RELEASE_NOT_TAGGED: некорректный SHA тега")
    # Inspect a fixed object, not a ref that could change between reads.
    kind = git(repo, "cat-file", "-t", oid).stdout.strip()
    if kind != "tag":
        raise TagError(f"RELEASE_NOT_TAGGED: тег {tag} не аннотирован")
    annotated = git(repo, "cat-file", "-p", oid).stdout
    header, separator, message = annotated.partition("\n\n")
    if not separator or not message.strip():
        raise TagError(f"RELEASE_NOT_TAGGED: у тега {tag} пустая аннотация")
    fields = header.splitlines()
    if fields[:3] != [f"object {commit}", "type commit", f"tag {tag}"]:
        raise TagError(f"RELEASE_NOT_TAGGED: {tag} указывает не на HEAD напрямую или имя объекта не совпадает")
    if head_commit(repo) != commit or git(repo, "rev-parse", "--verify", ref).stdout.strip() != oid:
        raise TagError("RELEASE_NOT_TAGGED: HEAD или ссылка тега изменились во время проверки")
    return oid


def create(repo: pathlib.Path, version: str, message: str, prefix: str = "",
           *, expected_head: str | None = None) -> str:
    tag = name_for(version, prefix)
    if not message.strip() or len(message.strip()) < 12:
        raise TagError("Для аннотированного тега нужно осмысленное описание релиза")
    repo = repo.resolve(strict=True)
    top = pathlib.Path(git(repo, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
    if top != repo:
        raise TagError("Укажите корень репозитория Git")
    commit = head_commit(repo, expected_head)
    exists = git(repo, "rev-parse", "--verify", f"refs/tags/{tag}", check=False)
    if exists.returncode == 0:
        return verify(repo, version, prefix, expected_head=commit)
    # Explicit target prevents tagging a different HEAD if another writer moves it.
    git(repo, "tag", "-a", tag, "-m", message.strip(), commit)
    return verify(repo, version, prefix, expected_head=commit)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for action in ("verify", "create"):
        p = sub.add_parser(action)
        p.add_argument("version", help="Релизная версия, например 0.1.0")
        p.add_argument("--repo", type=pathlib.Path, required=True, help="Корень проекта")
        p.add_argument("--prefix", default="", help="Префикс для монорепозитория, например skill-name/")
        p.add_argument("--expected-head", help="Полный SHA ранее проверенного релизного коммита")
        if action == "create":
            p.add_argument("--message", required=True, help="Русская аннотация реального релиза")
    args = parser.parse_args()
    try:
        sha = (create(args.repo, args.version, args.message, args.prefix, expected_head=args.expected_head)
               if args.command == "create" else verify(args.repo, args.version, args.prefix, expected_head=args.expected_head))
    except (OSError, TagError) as exc:
        print(f"BLOCKED / RELEASE_NOT_TAGGED: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: аннотированный тег {name_for(args.version, args.prefix)} подтверждён; SHA объекта: {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
