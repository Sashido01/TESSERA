#!/usr/bin/env python3
"""T11.01: run pinned upstream skills-ref validation, without installation or publishing.

The caller must supply an independently checked-out upstream source revision
and its separately installed, hash-locked Python runtime dependencies.
This wrapper makes no network connections and never executes skill scripts.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import subprocess
import sys
from typing import Callable

NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
MAX_SKILLS = 100
TIMEOUT = 30


def inspect(root: pathlib.Path, source: pathlib.Path, *,
            runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run) -> list[str]:
    """Return stable, path-free problem codes; an empty list means validated."""
    try:
        root = pathlib.Path(root).resolve(strict=True)
        source = pathlib.Path(source).resolve(strict=True)
    except (OSError, RuntimeError):
        return ["REFERENCE_ROOT_OR_SOURCE_MISSING"]
    if not root.is_dir() or not source.is_dir():
        return ["REFERENCE_ROOT_OR_SOURCE_INVALID"]
    if not all((source / "skills_ref" / name).is_file()
               for name in ("__init__.py", "cli.py", "validator.py", "parser.py")):
        return ["REFERENCE_UPSTREAM_SOURCE_INVALID"]
    skills = root / "skills"
    if skills.is_symlink() or not skills.is_dir():
        return ["REFERENCE_SKILLS_DIRECTORY_INVALID"]
    try:
        children = sorted(skills.iterdir(), key=lambda path: path.name)
    except OSError:
        return ["REFERENCE_SKILLS_UNREADABLE"]
    if not children or len(children) > MAX_SKILLS:
        return ["REFERENCE_SKILL_COUNT_INVALID"]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(source)
    env["PYTHONSAFEPATH"] = "1"
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    errors: list[str] = []
    for child in children:
        if child.is_symlink() or not child.is_dir() or not NAME.fullmatch(child.name):
            errors.append("REFERENCE_SKILL_DIRECTORY_INVALID")
            continue
        if (child / "SKILL.md").is_symlink() or not (child / "SKILL.md").is_file():
            errors.append("REFERENCE_SKILL_FILE_INVALID:" + child.name)
            continue
        args = [sys.executable, "-P", "-m", "skills_ref.cli", "validate", str(child)]
        try:
            result = runner(
                args, cwd=str(root), env=env, text=True, encoding="utf-8",
                capture_output=True, stdin=subprocess.DEVNULL, check=False, timeout=TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            errors.append("REFERENCE_TIMEOUT:" + child.name)
            continue
        except (OSError, UnicodeError):
            errors.append("REFERENCE_EXECUTION_UNAVAILABLE:" + child.name)
            continue
        if result.returncode != 0:
            errors.append("REFERENCE_VALIDATION_FAILED:" + child.name)
        elif not isinstance(result.stdout, str) or not result.stdout.startswith("Valid skill:"):
            errors.append("REFERENCE_OUTPUT_UNEXPECTED:" + child.name)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=pathlib.Path,
                        default=pathlib.Path(__file__).resolve().parents[1])
    parser.add_argument("--reference-src", type=pathlib.Path, required=True)
    args = parser.parse_args()
    problems = inspect(args.repo, args.reference_src)
    if problems:
        for code in problems:
            print("BLOCKED: " + code, file=sys.stderr)
        return 1
    print("REFERENCE_VALIDATION_PASS (format only; client activation NOT_VERIFIED)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
