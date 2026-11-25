#!/usr/bin/env python3
"""Run the tests of every skill in the trusted TESSERA checkout independently."""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
import unittest


class ExecutionResult(unittest.TextTestResult):
    """Require at least one ordinary successful test, not skip/expected failure."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.passed = 0

    def addSuccess(self, test):
        super().addSuccess(test)
        self.passed += 1


DEFAULT_TIMEOUT = 120
MAX_TIMEOUT = 900


def run(root: pathlib.Path, *, quiet: bool = False, selected: str | None = None,
        timeout: int = DEFAULT_TIMEOUT, worker: bool = False) -> int:
    if not 1 <= timeout <= MAX_TIMEOUT or (worker and selected is None):
        print("SKILL_TEST_ARGUMENT_INVALID", file=sys.stderr)
        return 1
    skills = root / "skills"
    if skills.is_symlink() or not skills.is_dir():
        print("SKILL_TEST_ROOT_INVALID", file=sys.stderr)
        return 1
    folders = sorted(skills.iterdir())
    if not folders:
        print("SKILL_TEST_ROOT_EMPTY", file=sys.stderr)
        return 1
    if selected is not None:
        folders = [p for p in folders if p.name == selected]
        if not folders:
            print("SKILL_TEST_SELECTION_INVALID", file=sys.stderr)
            return 1
    failed = False
    tested = 0
    for skill in folders:
        if skill.is_symlink() or not skill.is_dir():
            print("SKILL_TEST_DIRECTORY_INVALID", file=sys.stderr)
            return 1
        directory = skill / "tests"
        if directory.is_symlink():
            print("SKILL_TEST_PATH_INVALID", file=sys.stderr)
            return 1
        if not directory.exists():
            print(f"{skill.name}: NO_AUTOMATED_TESTS", flush=True)
            continue
        if not directory.is_dir() or any(p.is_symlink() for p in directory.rglob("*")):
            print("SKILL_TEST_PATH_INVALID", file=sys.stderr)
            return 1
        if not any(p.is_file() for p in directory.rglob("test*.py")):
            print(f"{skill.name}: EMPTY_TEST_DIRECTORY", file=sys.stderr)
            return 1
        if not worker:
            print(f"{skill.name}: RUN", flush=True)
        tested += 1
        if worker:
            suite = unittest.TestLoader().discover(str(directory))
            if not suite.countTestCases():
                print("SKILL_TEST_NONE_DISCOVERED", file=sys.stderr)
                return 1
            outcome = unittest.TextTestRunner(verbosity=0 if quiet else 2, resultclass=ExecutionResult).run(suite)
            if not outcome.passed:
                print("SKILL_TEST_NO_ORDINARY_EXECUTION", file=sys.stderr)
                return 1
            return int(not outcome.wasSuccessful())
        try:
            result = subprocess.run(
                [sys.executable, "-B", str(pathlib.Path(__file__).resolve()), "--repo", str(root),
                 "--skill", skill.name, "--worker", *(["-q"] if quiet else [])],
                cwd=root, check=False, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            print(f"{skill.name}: SKILL_TEST_TIMEOUT", file=sys.stderr, flush=True)
            failed = True
            continue
        except OSError:
            print(f"{skill.name}: SKILL_TEST_EXECUTION_FAILED", file=sys.stderr, flush=True)
            failed = True
            continue
        failed |= result.returncode != 0
    if not tested:
        print("SKILL_TEST_NONE_EXECUTED", file=sys.stderr)
        return 1
    return int(failed)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1])
    parser.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument("--skill", help="Run a single skill in a separate process")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help="Maximum seconds per skill (1–900; default 120)")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    return run(args.repo.resolve(), quiet=args.quiet, selected=args.skill,
               timeout=args.timeout, worker=args.worker)


if __name__ == "__main__":
    sys.exit(main())
