#!/usr/bin/env python3
"""Проверяет версию самого репозитория TESSERA и переход относительно предыдущего коммита."""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATTERN = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z")
CYRILLIC = re.compile(r"[А-Яа-яЁё]")


def parse(value: str) -> tuple[int, int, int]:
    match = PATTERN.fullmatch(value.strip())
    if match is None:
        raise ValueError("Нужна версия MAJOR.MINOR.PATCH без буквы v и начальных нулей")
    result = tuple(int(part) for part in match.groups())
    if result[1] > 99:
        raise ValueError("MINOR должен быть от 0 до 99")
    return result


def allowed_next(previous: str) -> set[str]:
    major, minor, patch = parse(previous)
    choices = {f"{major}.{minor}.{patch + 1}"}
    if patch >= 99:
        if minor == 99:
            choices.add(f"{major + 1}.0.0")
        else:
            choices.add(f"{major}.{minor + 1}.0")
    return choices


def check_transition(previous: str | None, current: str) -> list[str]:
    try:
        parse(current)
    except ValueError as exc:
        return [str(exc)]
    if previous is None:
        if current != "0.0.1":
            return ["Первое подключение VERSION к существующему репозиторию должно быть 0.0.1"]
        return []
    try:
        allowed = allowed_next(previous)
    except ValueError as exc:
        return [f"Некорректная предыдущая версия: {exc}"]
    if current not in allowed:
        return [
            f"Недопустимый переход {previous} → {current}. "
            f"Допустимо: {', '.join(sorted(allowed))}"
        ]
    return []


def check_changelogs(root: pathlib.Path, current: str) -> list[str]:
    errors: list[str] = []
    for name in ("CHANGELOG.md", "CHANGELOG.en.md"):
        path = root / name
        if not path.is_file():
            errors.append(f"Нет файла {name}")
            continue
        body = path.read_text(encoding="utf-8")
        if not re.search(r"(?m)^## " + re.escape(current) + r"(?:\s|$)", body):
            errors.append(f"Нет записи о версии {current} в {name}")
    return errors


def check_commit_title(title: str) -> list[str]:
    title = title.strip()
    errors: list[str] = []
    if len(title) < 14 or not CYRILLIC.search(title):
        errors.append("Заголовок коммита должен конкретно описывать изменение по-русски")
    if re.search(r"(?i)^(chore|fix|feat|bump|update)\s*[:(]", title):
        errors.append("Замените технический шаблон на понятный русский заголовок")
    return errors


def git(root: pathlib.Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=check
    )


SKILL_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
SKILL_METADATA = {"VERSION", "CHANGELOG.md", "CHANGELOG.en.md"}


def check_skill_versions(root: pathlib.Path, parent: str) -> list[str]:
    """Check independent versions against the first parent of the audited commit."""
    errors: list[str] = []
    skills = root / "skills"
    if skills.is_symlink() or not skills.is_dir():
        return ["SKILL_VERSION_ROOT_INVALID"]
    changed = set(git(root, "diff", "--name-only", "--no-renames", "-z",
                      parent, "HEAD", "--", "skills/").stdout.split("\0")) - {""}
    previous_paths = set(git(root, "ls-tree", "-r", "--name-only", "-z",
                             parent, "--", "skills/").stdout.split("\0")) - {""}
    current_versions: set[str] = set()
    for skill in sorted(skills.iterdir()):
        name = skill.name
        if skill.is_symlink() or not skill.is_dir() or not SKILL_NAME.fullmatch(name):
            errors.append("SKILL_VERSION_DIRECTORY_INVALID")
            continue
        prefix = f"skills/{name}/"
        version_path = prefix + "VERSION"
        current_versions.add(version_path)
        if any((skill / x).is_symlink() or not (skill / x).is_file() for x in SKILL_METADATA):
            errors.append(f"{name}: SKILL_VERSION_METADATA_MISSING")
            continue
        try:
            current = (skill / "VERSION").read_text(encoding="utf-8").strip()
            parse(current)
            errors.extend(f"{name}: {e}" for e in check_changelogs(skill, current))
            if version_path not in previous_paths:
                errors.extend(f"{name}: {e}" for e in check_transition(None, current))
                continue
            previous = git(root, "show", f"{parent}:{version_path}").stdout.strip()
            parse(previous)
        except (ValueError, OSError, UnicodeError):
            errors.append(f"{name}: SKILL_VERSION_METADATA_INVALID")
            continue
        delta = {p[len(prefix):] for p in changed if p.startswith(prefix)}
        if not delta:
            if current != previous:
                errors.append(f"{name}: SKILL_VERSION_UNCOMMITTED")
            continue
        if not delta - SKILL_METADATA:
            errors.append(f"{name}: SKILL_VERSION_METADATA_ONLY")
            continue
        errors.extend(f"{name}: {e}" for e in check_transition(previous, current))
        if not SKILL_METADATA.issubset(delta):
            errors.append(f"{name}: SKILL_VERSION_CHANGELOG_NOT_UPDATED")
    for path in sorted(previous_paths - current_versions):
        if re.fullmatch(r"skills/[a-z0-9]+(?:-[a-z0-9]+)*/VERSION", path):
            errors.append(f"{path}: SKILL_VERSION_REMOVAL_REQUIRES_POLICY")
    return errors


def check_repository(root: pathlib.Path) -> list[str]:
    errors: list[str] = []
    version_file = root / "VERSION"
    if not version_file.is_file():
        return ["Не найден основной файл VERSION"]
    current = version_file.read_text(encoding="utf-8").strip()
    try:
        parse(current)
    except ValueError as exc:
        return [f"VERSION: {exc}"]
    errors.extend(check_changelogs(root, current))
    try:
        # Для PR merge ref первый родитель — текущее состояние целевой ветки.
        parent = git(root, "rev-parse", "HEAD^", check=False)
        if parent.returncode != 0:
            errors.append("Не удаётся прочесть родительский коммит: необходима полная Git-история")
            return errors
        old = git(root, "show", f"{parent.stdout.strip()}:VERSION", check=False)
        if old.returncode != 0:
            previous = None
        else:
            previous = old.stdout.strip()
        errors.extend(check_transition(previous, current))
        errors.extend(check_skill_versions(root, parent.stdout.strip()))
        subject_ref = "HEAD^2" if os.environ.get("GITHUB_EVENT_NAME") == "pull_request" else "HEAD"
        subject = git(root, "log", "-1", "--format=%s", subject_ref).stdout.strip()
        errors.extend(check_commit_title(subject))
    except (OSError, subprocess.CalledProcessError) as exc:
        errors.append(f"Не удалось проверить историю Git: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=pathlib.Path, default=ROOT,
        help="Корень репозитория (по умолчанию каталог скрипта/../)"
    )
    args = parser.parse_args()
    errors = check_repository(args.root.resolve())
    if errors:
        for error in errors:
            print("ОШИБКА:", error, file=sys.stderr)
        return 1
    print("Микроверсионность TESSERA: PASS")
    print("Проверен VERSION, CHANGELOG, переход относительно предыдущего коммита и заголовок.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
