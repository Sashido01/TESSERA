#!/usr/bin/env python3
"""Вычисляет следующую рабочую микроверсию или релизный номер без побочных действий."""
from __future__ import annotations

import argparse
import re

PATTERN = re.compile(r"^(?:v)?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


def next_version(version: str, mode: str = "work") -> str:
    """Release mode assumes confirmed readiness; this function does not verify it."""
    match = PATTERN.fullmatch(version)
    if not match:
        raise ValueError("Ожидается версия MAJOR.MINOR.PATCH, например 0.0.99")
    major, minor, patch = (int(part) for part in match.groups())
    if minor > 99:
        raise ValueError("MINOR превышает 99: проверьте политику проекта")
    if mode == "work":
        return f"{major}.{minor}.{patch + 1}"
    if mode == "release":
        if patch < 99:
            raise ValueError("PATCH должен быть не меньше 99 для релизного рубежа")
        if minor < 99:
            return f"{major}.{minor + 1}.0"
        return f"{major + 1}.0.0"
    raise ValueError("Режим должен быть work или release")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("current", help="Текущая версия, например v0.0.99")
    parser.add_argument(
        "--mode", choices=("work", "release"), default="work",
        help="work: рабочий коммит; release: следующий рубеж после завершения задачи",
    )
    args = parser.parse_args()
    try:
        print(next_version(args.current, mode=args.mode))
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
