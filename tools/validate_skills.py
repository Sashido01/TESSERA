#!/usr/bin/env python3
"""Проверяет структуру каталога Agent Skills без сторонних зависимостей."""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
META_NAME = re.compile(r"^name:\s*(\S+)\s*$", re.MULTILINE)
META_DESCRIPTION = re.compile(r"^description:\s*(\S.*|[>|]-?)\s*$", re.MULTILINE)


def validate(root: pathlib.Path) -> list[str]:
    root = root.resolve()
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        return ["Отсутствует каталог skills/"]
    folders = sorted(skills_dir.iterdir())
    if not folders:
        return ["Каталог skills/ пуст"]
    errors: list[str] = []
    found = 0
    for folder in folders:
        if not folder.is_dir():
            errors.append(f"Неожиданный объект в skills/: {folder.name}")
            continue
        found += 1
        if folder.is_symlink():
            errors.append(f"Символическая ссылка вместо каталога навыка: {folder.name}")
            continue
        if not NAME.fullmatch(folder.name):
            errors.append(f"Недопустимое имя папки: {folder.name}")
        skill = folder / "SKILL.md"
        if not skill.is_file() or skill.is_symlink():
            errors.append(f"Отсутствует обычный файл: {folder.name}/SKILL.md")
            continue
        try:
            data = skill.read_text(encoding="utf-8")
        except (UnicodeError, OSError) as exc:
            errors.append(f"Не удалось прочесть {skill}: {exc}")
            continue
        if not data.startswith("---\n"):
            errors.append(f"{folder.name}: нет YAML frontmatter")
            continue
        end = data.find("\n---\n", 4)
        if end == -1:
            errors.append(f"{folder.name}: frontmatter не закрыт")
            continue
        header = data[4:end]
        name = META_NAME.search(header)
        description = META_DESCRIPTION.search(header)
        if not name or name.group(1) != folder.name:
            errors.append(f"{folder.name}: name должен совпадать с именем каталога")
        if not description:
            errors.append(f"{folder.name}: нет description в frontmatter")
        if not (folder / "README.md").is_file():
            errors.append(f"{folder.name}: отсутствует README.md")
    if not found:
        errors.append("В skills/ нет каталогов навыков")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root)
    if errors:
        for error in errors:
            print(f"ОШИБКА: {error}", file=sys.stderr)
        return 1
    print("Каталог навыков проверен: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
