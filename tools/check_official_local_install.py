#!/usr/bin/env python3
"""T10.01: actual gh skill install --from-local in temporary directories only.

This is an acceptance test, NOT a general-purpose installer. Never point the
official CLI at an existing user's skill directory: local mode copies files
with overwrite semantics, unlike the remote install flow.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Callable

VERSION = "2.105.0"
SKILL = "microversion-release"
TIMEOUT = 60
MAX_FILES = 2048
MAX_BYTES = 64 * 1024 * 1024
OMIT = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".DS_Store"}
VALID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


class InstallCheckError(RuntimeError):
    """Code-only failures; no raw executable output or local paths."""


def tree_fingerprint(root: pathlib.Path) -> str:
    if root.is_symlink() or not root.is_dir():
        raise InstallCheckError("INSTALL_SOURCE_INVALID")
    h = hashlib.sha256()
    files = 0
    total = 0
    for path in sorted(root.rglob("*"), key=lambda x: x.relative_to(root).as_posix()):
        rel = path.relative_to(root)
        if any(x in OMIT for x in rel.parts) or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise InstallCheckError("INSTALL_SYMLINK_FORBIDDEN")
        if path.is_dir():
            continue
        if not path.is_file():
            raise InstallCheckError("INSTALL_UNUSUAL_ENTRY")
        files += 1
        size = path.stat().st_size
        total += size
        if files > MAX_FILES or total > MAX_BYTES:
            raise InstallCheckError("INSTALL_SOURCE_LIMIT_EXCEEDED")
        h.update(rel.as_posix().encode("utf-8") + b"\0")
        with path.open("rb") as stream:
            for buf in iter(lambda: stream.read(1024 * 1024), b""):
                h.update(buf)
    if not files:
        raise InstallCheckError("INSTALL_SOURCE_EMPTY")
    return h.hexdigest()


def safe_destination(root: pathlib.Path, skill_name: str) -> pathlib.Path:
    """Refuse preexisting directories/files, including symlinks, before invoking gh."""
    if not VALID.fullmatch(skill_name):
        raise InstallCheckError("INSTALL_TARGET_NAME_INVALID")
    if root.is_symlink():
        raise InstallCheckError("INSTALL_TARGET_SYMLINK")
    target = root / skill_name
    if target.is_symlink() or target.exists():
        raise InstallCheckError("INSTALL_TARGET_ALREADY_EXISTS")
    return target


def run_command(runner: Callable[..., subprocess.CompletedProcess[str]], argv: list[str],
                *, cwd: pathlib.Path, env: dict[str, str], seconds: int = TIMEOUT
                ) -> subprocess.CompletedProcess[str]:
    try:
        return runner(argv, cwd=str(cwd), env=env, capture_output=True,
                      stdin=subprocess.DEVNULL, text=True, encoding="utf-8",
                      timeout=seconds, check=False)
    except (OSError, subprocess.TimeoutExpired, UnicodeError) as exc:
        raise InstallCheckError("INSTALL_PROCESS_UNAVAILABLE") from exc


def fixture_env(temp: pathlib.Path) -> dict[str, str]:
    home = temp / "home"
    config = temp / "gh-config"
    home.mkdir()
    config.mkdir()
    # Do not inherit GH/GITHUB tokens, alternate hosts or user Git config.
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "LANG": "C.UTF-8",
        "HOME": str(home),
        "GH_CONFIG_DIR": str(config),
        "GH_PROMPT_DISABLED": "1",
        "GH_NO_UPDATE_NOTIFIER": "1",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
        "NO_COLOR": "1",
    }


def inspect(repo: pathlib.Path, cli: pathlib.Path,
            *, runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run
            ) -> dict[str, str]:
    try:
        repo = repo.resolve(strict=True)
        cli = cli.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise InstallCheckError("INSTALL_INPUT_UNAVAILABLE") from exc
    if not cli.is_file() or not os.access(cli, os.X_OK):
        raise InstallCheckError("INSTALL_CLI_UNAVAILABLE")
    source_skills = repo / "skills"
    src_skill = source_skills / SKILL
    if not (src_skill / "SKILL.md").is_file() or src_skill.is_symlink():
        raise InstallCheckError("INSTALL_SKILL_UNAVAILABLE")
    before = tree_fingerprint(source_skills)
    with tempfile.TemporaryDirectory(prefix="tessera-gh-install-") as folder:
        temp = pathlib.Path(folder)
        env = fixture_env(temp)
        source = temp / "source"
        source.mkdir()
        shutil.copytree(source_skills, source / "skills",
                        symlinks=True,
                        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache",
                                                      ".mypy_cache", ".ruff_cache",
                                                      "*.pyc", ".DS_Store"))
        if tree_fingerprint(source / "skills") != before:
            raise InstallCheckError("INSTALL_SOURCE_SNAPSHOT_MISMATCH")
        v = run_command(runner, [str(cli), "version"], cwd=source, env=env, seconds=10)
        if v.returncode or not re.match(r"^gh version " + re.escape(VERSION) + r" \(", v.stdout):
            raise InstallCheckError("INSTALL_CLI_VERSION_MISMATCH")

        target_root = temp / "installed"
        target = safe_destination(target_root, SKILL)
        args = [str(cli), "skill", "install", str(source), SKILL,
                "--from-local", "--dir", str(target_root)]
        result = run_command(runner, args, cwd=source, env=env)
        if result.returncode or not (target / "SKILL.md").is_file():
            raise InstallCheckError("INSTALL_OFFICIAL_LOCAL_FAILED")
        if target.is_symlink():
            raise InstallCheckError("INSTALL_TARGET_SYMLINK")
        body = (src_skill / "SKILL.md").read_text(encoding="utf-8")
        installed = (target / "SKILL.md").read_text(encoding="utf-8")
        marker = "\n---\n"
        if marker not in body or marker not in installed:
            raise InstallCheckError("INSTALL_FRONTMATTER_INVALID")
        # The official CLI adds source-tracking metadata. The original body
        # and all supplementary files still have to be identical.
        if installed.split(marker, 1)[1] != body.split(marker, 1)[1]:
            raise InstallCheckError("INSTALL_CONTENT_MISMATCH")
        reference = pathlib.Path("references") / "INTEGRATION.md"
        if (target / reference).read_bytes() != (src_skill / reference).read_bytes():
            raise InstallCheckError("INSTALL_REFERENCE_MISMATCH")
        if "github" not in installed.split(marker, 1)[0]:
            raise InstallCheckError("INSTALL_SOURCE_METADATA_MISSING")

        # The CLI must enumerate the installed skill through its own API.
        listing = run_command(runner,
                              [str(cli), "skill", "list", "--dir", str(target_root),
                               "--json", "skillName"],
                              cwd=source, env=env)
        try:
            items = json.loads(listing.stdout) if listing.returncode == 0 else None
        except (ValueError, TypeError):
            items = None
        if not isinstance(items, list) or SKILL not in [
            row.get("skillName") for row in items if isinstance(row, dict)
        ]:
            raise InstallCheckError("INSTALL_CLI_DISCOVERY_FAILED")

        # --from-local and --pin are intentionally incompatible in CLI v2.105.0.
        pinned_dest = temp / "invalid-pin"
        invalid = run_command(runner,
                              [str(cli), "skill", "install", str(source), SKILL,
                               "--from-local", "--pin", "v0.0.19",
                               "--dir", str(pinned_dest)],
                              cwd=source, env=env)
        if invalid.returncode == 0 or pinned_dest.exists():
            raise InstallCheckError("INSTALL_LOCAL_PIN_NOT_REJECTED")

        # The safe caller must reject a pre-existing installation before any
        # subprocess can run. We never attempt destructive reinstallation.
        try:
            safe_destination(target_root, SKILL)
        except InstallCheckError as exc:
            if str(exc) != "INSTALL_TARGET_ALREADY_EXISTS":
                raise
        else:
            raise InstallCheckError("INSTALL_OVERWRITE_GUARD_MISSING")
        if tree_fingerprint(source_skills) != before:
            raise InstallCheckError("INSTALL_ORIGINAL_SOURCE_MODIFIED")
        if tree_fingerprint(source / "skills") != before:
            raise InstallCheckError("INSTALL_TEMP_SOURCE_MODIFIED")
    return {
        "status": "PASS", "gh_version": VERSION,
        "test_mode": "TEMPORARY_LOCAL_ONLY",
        "official_install": "PASS",
        "official_discovery": "PASS",
        "no_overwrite_guard": "PASS",
        "local_pin": "NOT_SUPPORTED",
        "remote_pinned_install": "NOT_VERIFIED",
        "agent_host_activation": "NOT_VERIFIED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=pathlib.Path)
    parser.add_argument("--cli", required=True, type=pathlib.Path)
    args = parser.parse_args()
    try:
        result = inspect(args.repo, args.cli)
    except (InstallCheckError, OSError, UnicodeError, ValueError) as exc:
        code = str(exc) if isinstance(exc, InstallCheckError) else "INSTALL_RUNTIME_UNAVAILABLE"
        print("BLOCKED: " + code, file=sys.stderr)
        return 1
    print("GH_SKILL_LOCAL_INSTALL_PASS: " + result["gh_version"] +
          " (temporary only; remote pin/client activation NOT_VERIFIED)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
