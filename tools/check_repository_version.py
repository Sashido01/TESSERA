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
