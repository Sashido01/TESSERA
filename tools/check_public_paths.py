#!/usr/bin/env python3
"""Не допускает публикацию абсолютных локальных путей в документах библиотеки."""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEXT_EXTENSIONS = {".md", ".yml", ".yaml", ".json", ".toml", ".txt"}
WINDOWS_ABSOLUTE = re.compile(r"(?<![\w])[A-Za-z]:[\\/]")
HOME_ABSOLUTE = re.compile(r"(?<![\w])/(?:home|Users)/[A-Za-z0-9_.-]+/")
IGNORE_DIRS = {".git", ".venv", "venv", "__pycache__", ".mypy_cache", ".external"}


def scan(root: pathlib.Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(root.rglob("*")):
        if any(part in IGNORE_DIRS for part in path.relative_to(root).parts):
            continue
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if WINDOWS_ABSOLUTE.search(line) or HOME_ABSOLUTE.search(line):
                errors.append(f"{path.relative_to(root)}:{number}: обнаружен абсолютный локальный путь")
    return errors


def main() -> int:
    errors = scan(ROOT)
    for message in errors:
        print(f"ОШИБКА: {message}", file=sys.stderr)
    if errors:
        return 1
    print("Проверка приватных локальных путей: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
