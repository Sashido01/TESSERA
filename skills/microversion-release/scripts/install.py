#!/usr/bin/env python3
"""Безопасная установка Agent Skill в проект; по умолчанию — только предварительный просмотр."""
from __future__ import annotations

import argparse
import pathlib
import shutil
import sys

PROJECT_ROOTS = {
    "codex": ".agents/skills",
    "harness": ".dsh/skills",
    "claude": ".claude/skills",
    "hermes": ".hermes/skills",
    "shared": ".agents/skills",  # Codex + Hermes, при поддержке активной конфигурации
}
SKILL_NAME = "microversion-release"


class InstallError(ValueError):
    pass


def require_direct_path(path: pathlib.Path) -> None:
    # Reject links (including dangling links) and redirected directories such as junctions.
    if path.is_symlink() or path.resolve() != path:
        raise InstallError("Перенаправление пути установки запрещено")


def require_plain_tree(root: pathlib.Path) -> None:
    pending = [root]
    while pending:
        folder = pending.pop()
        for entry in folder.iterdir():
            require_direct_path(entry)
            if entry.is_dir():
                pending.append(entry)
            elif not entry.is_file():
                raise InstallError("Недопустимый тип файла в исходном навыке")


def destination(platform: str, project_root: pathlib.Path | None, target_root: pathlib.Path | None) -> pathlib.Path:
    if (project_root is None) == (target_root is None):
        raise InstallError("Укажите либо --project-root, либо --target-root")
    if target_root is not None:
        return target_root.expanduser().resolve() / SKILL_NAME
    if platform not in PROJECT_ROOTS:
        raise InstallError("Для generic и пользовательского профиля используйте --target-root")
    root = project_root.expanduser().resolve()
    if not root.is_dir():
        raise InstallError("Корневой каталог проекта не существует")
    parent = root
    for component in pathlib.Path(PROJECT_ROOTS[platform]).parts:
        parent = parent / component
        require_direct_path(parent)
        if parent.exists() and not parent.is_dir():
            raise InstallError("Компонент пути установки не является каталогом")
    return parent / SKILL_NAME


def display(message: str, *, stream=None) -> None:
    # Redirected Windows streams may use a legacy code page.
    # Escape only characters the actual stream cannot represent.
    stream = sys.stdout if stream is None else stream
    encoding = getattr(stream, "encoding", None)
    if encoding:
        message = message.encode(encoding, errors="backslashreplace").decode(encoding)
    print(message, file=stream)


def run(platform: str, project_root: pathlib.Path | None, target_root: pathlib.Path | None, apply: bool) -> pathlib.Path:
    src = pathlib.Path(__file__).resolve().parents[1]
    if not (src / "SKILL.md").is_file():
        raise InstallError("Не найден исходный SKILL.md")
    require_plain_tree(src)
    dst = destination(platform, project_root, target_root)
    require_direct_path(dst)
    if dst.exists() or dst.is_symlink():
        raise InstallError(f"Каталог уже существует; перезапись запрещена: {dst}")
    if dst == src or src in dst.parents:
        raise InstallError("Нельзя устанавливать навык внутрь исходного каталога")
    if not apply:
        display(f"DRY-RUN: {src} -> {dst} (без изменений)")
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    if destination(platform, project_root, target_root) != dst:
        raise InstallError("Путь установки изменился")
    require_direct_path(dst)
    shutil.copytree(
        src, dst, symlinks=False,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
    )
    display(f"Установлен каталог навыка: {dst}")
    display("Обнаружение и автоматическая активация должны быть проверены в самой агентной среде.")
    return dst


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--platform", choices=(*PROJECT_ROOTS, "generic"), required=True)
    p.add_argument("--project-root", type=pathlib.Path, help="Существующий каталог проекта")
    p.add_argument("--target-root", type=pathlib.Path, help="Явно заданный каталог skills/ профиля")
    p.add_argument("--apply", action="store_true", help="Реально скопировать файлы; иначе DRY-RUN")
    args = p.parse_args()
    try:
        run(args.platform, args.project_root, args.target_root, args.apply)
    except (OSError, InstallError) as exc:
        display(f"ОШИБКА: {exc}", stream=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
