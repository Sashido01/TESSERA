#!/usr/bin/env python3
"""T11.02: run official, pinned GitHub CLI skill publish --dry-run in isolation.

No GitHub remote, no inherited GitHub auth, no release/topic creation.
Only local format validation is in scope, never remote publication readiness.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Callable

CLI_VERSION = "2.105.0"
EXPECTED_SHA256 = "79e7ab5db738c48777b696e374f8b428f0647debfb424f44d2f426370407fe2f"
MAX_SKILLS = 100
TIMEOUT = 60
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
HEADER_NAME = re.compile(r"(?m)^name:\s*[^\r\n]+$")


class DryRunError(RuntimeError):
    """No paths, secrets, tokens or arbitrary subprocess stderr in error codes."""


def safe_skills(src: pathlib.Path) -> list[pathlib.Path]:
    if src.is_symlink() or not src.is_dir():
        raise DryRunError("DRY_RUN_SKILLS_UNAVAILABLE")
    skills = sorted(src.iterdir(), key=lambda p: p.name)
    if not skills or len(skills) > MAX_SKILLS:
        raise DryRunError("DRY_RUN_SKILL_COUNT_INVALID")
    for skill in skills:
        if (not NAME.fullmatch(skill.name) or skill.is_symlink() or not skill.is_dir()
                or not (skill / "SKILL.md").is_file() or (skill / "SKILL.md").is_symlink()):
            raise DryRunError("DRY_RUN_SKILL_INVALID")
        for path in skill.rglob("*"):
            if path.is_symlink():
                raise DryRunError("DRY_RUN_SYMLINK_FORBIDDEN")
    return skills


def digest(file: pathlib.Path) -> str:
    h = hashlib.sha256()
    with file.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def tree_digest(directory: pathlib.Path) -> str:
    """Fingerprint file names and bytes without following symlinks."""
    h = hashlib.sha256()
    paths = sorted(directory.rglob("*"), key=lambda p: str(p.relative_to(directory)))
    if len(paths) > 2048:
        raise DryRunError("DRY_RUN_SKILL_TREE_TOO_LARGE")
    total = 0
    for path in paths:
        if path.is_symlink():
            raise DryRunError("DRY_RUN_SYMLINK_FORBIDDEN")
        if path.is_file():
            relative = path.relative_to(directory).as_posix()
            h.update(relative.encode("utf-8") + b"\0")
            size = path.stat().st_size
            total += size
            if total > 64 * 1024 * 1024:
                raise DryRunError("DRY_RUN_SKILL_TREE_TOO_LARGE")
            h.update(bytes.fromhex(digest(path)))
    return h.hexdigest()


def checked_cli_version(cli: pathlib.Path,
                        runner: Callable[..., subprocess.CompletedProcess[str]],
                        env: dict[str, str]) -> None:
    try:
        result = runner([str(cli), "version"], text=True, capture_output=True,
                        encoding="utf-8", timeout=10, check=False,
                        stdin=subprocess.DEVNULL, env=env)
    except (OSError, subprocess.TimeoutExpired, UnicodeError) as exc:
        raise DryRunError("DRY_RUN_CLI_UNAVAILABLE") from exc
    if result.returncode != 0 or not result.stdout.startswith("gh version " + CLI_VERSION + " "):
        raise DryRunError("DRY_RUN_CLI_VERSION_MISMATCH")


def checked_call(argv: list[str], cwd: pathlib.Path, env: dict[str, str],
                 runner: Callable[..., subprocess.CompletedProcess[str]], *, timeout: int = TIMEOUT
                 ) -> subprocess.CompletedProcess[str]:
    try:
        return runner(argv, cwd=str(cwd), env=env, text=True, encoding="utf-8",
                      capture_output=True, stdin=subprocess.DEVNULL,
                      check=False, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired, UnicodeError) as exc:
        raise DryRunError("DRY_RUN_EXECUTION_UNAVAILABLE") from exc


def run(root: pathlib.Path, cli: pathlib.Path, *,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run) -> dict[str, str]:
    try:
        root = root.resolve(strict=True)
        cli = cli.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise DryRunError("DRY_RUN_INPUT_UNAVAILABLE") from exc
    if not cli.is_file() or not os.access(cli, os.X_OK):
        raise DryRunError("DRY_RUN_CLI_UNAVAILABLE")
    safe_skills(root / "skills")
    source_digest = tree_digest(root / "skills")
    with tempfile.TemporaryDirectory(prefix="tessera-publish-") as temp:
        base = pathlib.Path(temp)
        isolated = base / "source"
        isolated.mkdir()
        shutil.copytree(root / "skills", isolated / "skills", symlinks=True)
        if tree_digest(isolated / "skills") != source_digest:
            raise DryRunError("DRY_RUN_SNAPSHOT_MISMATCH")
        # No global git config, credentials, current-user home or remote.
        (base / "home").mkdir()
        (base / "config").mkdir()
        env = os.environ.copy()
        for secret in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN",
                       "GH_HOST", "GIT_ASKPASS", "SSH_ASKPASS"):
            env.pop(secret, None)
        env.update({
            "GH_PROMPT_DISABLED": "1",
            "GH_NO_UPDATE_NOTIFIER": "1",
            "GH_CONFIG_DIR": str(base / "config"),
            "HOME": str(base / "home"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
            "NO_COLOR": "1",
        })
        checked_cli_version(cli, runner, env)
        init = checked_call(["git", "init", "-q"], isolated, env, runner)
        if init.returncode:
            raise DryRunError("DRY_RUN_GIT_INIT_FAILED")
        # No commits or remotes required: gh only reads current working files.
        remotes = checked_call(["git", "remote"], isolated, env, runner)
        if remotes.returncode != 0 or remotes.stdout.strip():
            raise DryRunError("DRY_RUN_REMOTE_PRESENT")
        good = checked_call([str(cli), "skill", "publish", "--dry-run", str(isolated)],
                            isolated, env, runner)
        if good.returncode != 0 or "Dry run complete." not in good.stderr:
            raise DryRunError("DRY_RUN_POSITIVE_FAILED")
        if tree_digest(isolated / "skills") != source_digest:
            raise DryRunError("DRY_RUN_POSITIVE_MODIFIED_FILES")
        # Inject one harmless malformed field in a temporary copy only.
        first = isolated / "skills" / sorted(p.name for p in (isolated / "skills").iterdir())[0] / "SKILL.md"
        original = first.read_text(encoding="utf-8")
        changed, count = HEADER_NAME.subn("name: invalid-other-skill", original, count=1)
        if count != 1 or changed == original:
            raise DryRunError("DRY_RUN_NEGATIVE_FIXTURE_INVALID")
        first.write_text(changed, encoding="utf-8")
        negative_hash = digest(first)
        bad = checked_call([str(cli), "skill", "publish", "--dry-run", str(isolated)],
                           isolated, env, runner)
        if bad.returncode == 0 or digest(first) != negative_hash:
            raise DryRunError("DRY_RUN_NEGATIVE_NOT_REJECTED")
        if tree_digest(root / "skills") != source_digest:
            raise DryRunError("DRY_RUN_ORIGINAL_CHANGED")
        remotes_again = checked_call(["git", "remote"], isolated, env, runner)
        if remotes_again.returncode or remotes_again.stdout.strip():
            raise DryRunError("DRY_RUN_REMOTE_ADDED")
        return {
            "status": "PASS",
            "cli_version": CLI_VERSION,
            "mode": "OFFLINE_ISOLATED_NO_REMOTE",
            "positive": "PASS",
            "negative": "REJECTED",
            "source_tree": "UNCHANGED",
            "github_release_publication": "NOT_CHECKED",
            "remote_security_diagnostics": "NOT_CHECKED",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=pathlib.Path, required=True)
    parser.add_argument("--cli", type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.repo, args.cli)
    except DryRunError as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 1
    print("GH_SKILL_DRY_RUN_PASS: " + result["cli_version"] +
          " (isolated/offline; remote publication NOT_VERIFIED)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
