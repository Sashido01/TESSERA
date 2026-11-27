#!/usr/bin/env python3
"""Проверяет наличие русских оригиналов и парных английских переводов."""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROOT_DOCS = (
    "README.md", "AGENTS.md", "CHANGELOG.md", "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md", "SECURITY.md", "UPDATE.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
)
EXCLUDED = {".git", ".venv", "venv", "__pycache__"}


def pairs(root: pathlib.Path) -> dict[pathlib.Path, pathlib.Path]:
    result: dict[pathlib.Path, pathlib.Path] = {}
    for name in ROOT_DOCS:
        original = root / name
        result[original] = original.with_name(original.stem + ".en.md")
    for original in (root / "docs").rglob("*.md") if (root / "docs").is_dir() else ():
        if original.name.endswith(".en.md"):
            continue
        result[original] = original.with_name(original.stem + ".en.md")
    skills = root / "skills"
    if skills.is_dir():
        for skill in skills.iterdir():
            if not skill.is_dir():
                continue
            result[skill / "README.md"] = skill / "README.en.md"
            result[skill / "CHANGELOG.md"] = skill / "CHANGELOG.en.md"
            result[skill / "SKILL.md"] = skill / "references" / "SKILL.en.md"
            refs = skill / "references"
            if refs.is_dir():
                for original in refs.rglob("*.md"):
                    if original.name.endswith(".en.md"):
                        continue
                    result[original] = original.with_name(original.stem + ".en.md")
    return result


def validate(root: pathlib.Path) -> list[str]:
    root = root.resolve()
    expected = pairs(root)
    errors: list[str] = []
    for original, translated in sorted(expected.items()):
        src = original.relative_to(root)
        dst = translated.relative_to(root)
        if not original.is_file():
            errors.append(f"Нет русского оригинала: {src}")
            continue
        if not translated.is_file():
            errors.append(f"Нет английского перевода: {dst}")
            continue
        try:
            ru = original.read_text(encoding="utf-8")
            en = translated.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"Не удалось прочитать {src} или {dst}: {exc}")
            continue
        # Проверяем навигацию, но не делаем вид, что это проверка смысла перевода.
        relative_translation = translated.relative_to(original.parent).as_posix() if translated.is_relative_to(original.parent) else "references/SKILL.en.md"
        relative_original = "../SKILL.md" if original.name == "SKILL.md" else original.name
        if "English" not in ru[:1500] or relative_translation not in ru[:1500]:
            errors.append(f"Нет ссылки на английский перевод: {src}")
        if "Русский" not in en[:1500] or relative_original not in en[:1500]:
            errors.append(f"Нет обратной ссылки на русский оригинал: {dst}")
        if not ru.strip() or not en.strip():
            errors.append(f"Пустой языковой документ: {src} / {dst}")
        if original.name == "SKILL.md" and en.startswith("---\n"):
            errors.append(f"Перевод SKILL.md не должен иметь frontmatter: {dst}")
    # Каждый перевод должен иметь известный русский оригинал.
    expected_en = {p.resolve() for p in expected.values()}
    scopes = [root, root / "docs", root / ".github", root / "skills"]
    for scope in scopes:
        if not scope.is_dir():
            continue
        candidates = scope.glob("*.en.md") if scope == root else scope.rglob("*.en.md")
        for translation in candidates:
            if any(part in EXCLUDED for part in translation.relative_to(root).parts):
                continue
            if translation.resolve() not in expected_en:
                errors.append(f"Английский документ без русского оригинала: {translation.relative_to(root)}")
    return errors


def main() -> int:
    errors = validate(ROOT)
    if errors:
        for error in errors:
            print(f"ОШИБКА: {error}", file=sys.stderr)
        return 1
    print(f"Языковые пары проверены: {len(pairs(ROOT))} шт. (русский оригинал + английский перевод)")
    print("Проверка полноты и точности перевода по смыслу остаётся задачей ревью.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
