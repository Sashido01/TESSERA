#!/usr/bin/env python3
"""T10.02: live remote pin acceptance, confined to fresh temporary directories.

Only the published, independently identified TESSERA baseline is permitted.
Requires a short-lived read-only CI token; never prints raw CLI output or
executes downloaded skills. The ordinary local test suite stays offline.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

from check_official_local_install import (
    VERSION, SKILL, fixture_env, run_command, safe_destination,
    tree_fingerprint, InstallCheckError,
)

REPO = "Sashido01/TESSERA"
URL = "https://github.com/" + REPO
REF = "refs/tags/v0.0.22"
COMMIT = "34923e27e669da0092440a0bbfb00b2dfdd98a37"
TAG_OBJECT = "b9967ac3aa1abac7fdb8e7abceb8c6a3f79da66c"
SKILL_PATH = "skills/" + SKILL
MAX_FILES = 128
MAX_BYTES = 4 * 1024 * 1024


def require(ok: bool, code: str) -> None:
    if not ok:
        raise InstallCheckError(code)


def git_bytes(repo: pathlib.Path, env: dict[str, str], *args: str) -> bytes:
    # Do not pass the GitHub token to git or inherit repository override env.
    clean = {k: v for k, v in env.items() if k != "GH_TOKEN"}
    result = subprocess.run(
        ["git", "-C", str(repo), *args], env=clean, stdin=subprocess.DEVNULL,
        capture_output=True, timeout=20, check=False,
    )
    require(result.returncode == 0, "REMOTE_BASELINE_GIT_FAILED")
    return result.stdout


def expected_files(repo: pathlib.Path, env: dict[str, str]) -> tuple[str, dict[str, bytes]]:
    require(git_bytes(repo, env, "rev-parse", REF).decode().strip() == TAG_OBJECT,
            "REMOTE_TAG_OBJECT_MISMATCH")
    require(git_bytes(repo, env, "cat-file", "-t", REF).strip() == b"tag",
            "REMOTE_ANNOTATED_TAG_REQUIRED")
    require(git_bytes(repo, env, "rev-parse", REF + "^{commit}").decode().strip() == COMMIT,
            "REMOTE_TAG_COMMIT_MISMATCH")
    tree = git_bytes(repo, env, "rev-parse", COMMIT + ":" + SKILL_PATH).decode().strip()
    require(bool(re.fullmatch(r"[0-9a-f]{40}", tree)), "REMOTE_TREE_INVALID")
    records = git_bytes(repo, env, "ls-tree", "-r", "-z", tree).split(b"\0")
    files: dict[str, bytes] = {}
    total = 0
    for record in filter(None, records):
        meta, name_bytes = record.split(b"\t", 1)
        mode, kind, sha = meta.decode("ascii").split()
        name = name_bytes.decode("utf-8")
        path = pathlib.PurePosixPath(name)
        require(mode in ("100644", "100755") and kind == "blob",
                "REMOTE_SOURCE_NONREGULAR")
        require(not path.is_absolute() and path.as_posix() == name
                and ".." not in path.parts and "\\" not in name
                and name not in files, "REMOTE_SOURCE_PATH_INVALID")
        require(len(files) < MAX_FILES, "REMOTE_SOURCE_LIMIT")
        data = git_bytes(repo, env, "cat-file", "blob", sha)
        total += len(data)
        require(total <= MAX_BYTES, "REMOTE_SOURCE_LIMIT")
        files[name] = data
    require("SKILL.md" in files, "REMOTE_SOURCE_SKILL_MISSING")
    return tree, files


def split_skill(data: bytes) -> tuple[str, bytes]:
    header, sep, body = data.removeprefix(b"---\n").partition(b"\n---\n")
    require(data.startswith(b"---\n") and bool(sep), "REMOTE_FRONTMATTER_INVALID")
    return header.decode("utf-8"), body.lstrip(b"\r\n")


def check_metadata(header: str, tree: str, pin: str) -> None:
    expected = {
        "github-repo": URL,
        "github-path": SKILL_PATH,
        "github-ref": pin,
        "github-pinned": pin,
        "github-tree-sha": tree,
    }
    for key, value in expected.items():
        matches = re.findall(r"(?m)^[ \t]+" + re.escape(key) + r":[ \t]*(.*?)\s*$", header)
        require(len(matches) == 1, "REMOTE_METADATA_MISSING_OR_DUPLICATE")
        actual = matches[0]
        if len(actual) >= 2 and actual[0] == actual[-1] and actual[0] in "\"'":
            actual = actual[1:-1]
        require(actual == value, "REMOTE_METADATA_MISMATCH")


def verify_install(target: pathlib.Path, files: dict[str, bytes], tree: str, pin: str) -> None:
    require(target.is_dir() and not target.is_symlink(), "REMOTE_TARGET_INVALID")
    installed: dict[str, pathlib.Path] = {}
    for p in target.rglob("*"):
        require(not p.is_symlink(), "REMOTE_TARGET_SYMLINK")
        if p.is_dir():
            continue
        require(p.is_file(), "REMOTE_TARGET_NONREGULAR")
        installed[p.relative_to(target).as_posix()] = p
    require(set(installed) == set(files), "REMOTE_FILE_INVENTORY_MISMATCH")
    for name, raw in files.items():
        p = installed[name]
        require(p.stat().st_size <= MAX_BYTES, "REMOTE_TARGET_LIMIT")
        got = p.read_bytes()
        if name == "SKILL.md":
            _, original_body = split_skill(raw)
            header, body = split_skill(got)
            require(body == original_body, "REMOTE_SKILL_BODY_MISMATCH")
            check_metadata(header, tree, pin)
        else:
            require(got == raw, "REMOTE_FILE_BYTES_MISMATCH")


def check_listing(stdout: str, pin: str, target: pathlib.Path) -> None:
    rows = json.loads(stdout)
    require(isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict),
            "REMOTE_LIST_INVALID")
    row = rows[0]
    require(row.get("skillName") == SKILL and row.get("pinned") is True
            and row.get("sourceURL") == URL
            and row.get("version") == pin.removeprefix("refs/tags/")
            and row.get("path") == str(target), "REMOTE_LIST_METADATA_MISMATCH")


def accept(repo: pathlib.Path, cli: pathlib.Path, token: str, *,
           runner=subprocess.run, baseline=expected_files) -> dict[str, str]:
    require(bool(token.strip()), "REMOTE_READ_TOKEN_REQUIRED")
    repo = repo.resolve(strict=True)
    cli = cli.resolve(strict=True)
    require(cli.is_file() and os.access(cli, os.X_OK), "REMOTE_CLI_UNAVAILABLE")
    source_before = tree_fingerprint(repo / "skills")
    with tempfile.TemporaryDirectory(prefix="tessera-gh-remote-") as folder:
        temp = pathlib.Path(folder)
        env = fixture_env(temp)
        env["GH_TOKEN"] = token
        env["GH_TELEMETRY"] = "off"
        env["GH_NO_EXTENSION_UPDATE_NOTIFIER"] = "1"
        # CWD and home are outside both the repository and real agent profiles.
        tree, files = baseline(repo, env)

        def gh(*args: str):
            return run_command(runner, [str(cli), *args], cwd=temp, env=env)

        version = gh("version")
        require(version.returncode == 0 and bool(re.match(
            r"^gh version " + re.escape(VERSION) + r" \(", version.stdout)),
            "REMOTE_CLI_VERSION_MISMATCH")
        for kind, pin in (("tag", REF), ("sha", COMMIT)):
            dest = temp / kind
            target = safe_destination(dest, SKILL)
            args = ("skill", "install", REPO, SKILL, "--pin", pin, "--dir", str(dest))
            result = gh(*args)
            require(result.returncode == 0, "REMOTE_INSTALL_" + kind.upper() + "_FAILED")
            verify_install(target, files, tree, pin)
            listing = gh("skill", "list", "--dir", str(dest),
                         "--json", "skillName,sourceURL,version,pinned,path")
            require(listing.returncode == 0, "REMOTE_LIST_FAILED")
            check_listing(listing.stdout, pin, target)

            fingerprint = tree_fingerprint(dest)
            update = gh("skill", "update", SKILL, "--dir", str(dest), "--dry-run")
            require(update.returncode == 0
                    and "is pinned to " + pin + " (skipped)" in update.stderr,
                    "REMOTE_PIN_UPDATE_SKIP_MISSING")
            require(tree_fingerprint(dest) == fingerprint, "REMOTE_DRY_RUN_MUTATED_FILES")

            # Actual negative test, ONLY on the disposable installed skill.
            # Never use --force, --unpin, real user directory or global scope.
            duplicate = gh(*args)
            require(duplicate.returncode != 0
                    and "already installed" in duplicate.stderr.lower(),
                    "REMOTE_DUPLICATE_NOT_REFUSED")
            require(tree_fingerprint(dest) == fingerprint, "REMOTE_DUPLICATE_MUTATED_FILES")

        require(tree_fingerprint(repo / "skills") == source_before,
                "REMOTE_ORIGINAL_SOURCE_MODIFIED")
    return {"status": "PASS", "gh_version": VERSION, "tag": REF,
            "commit": COMMIT, "tree": tree, "tag_install": "PASS",
            "sha_install": "PASS", "pinned_update_dry_run": "PASS",
            "duplicate_install_refusal": "PASS", "client_activation": "NOT_VERIFIED",
            "unpin_apply": "NOT_VERIFIED", "multi_skill_namespace": "NOT_VERIFIED"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=pathlib.Path, required=True)
    parser.add_argument("--cli", type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        result = accept(args.repo, args.cli, os.environ.get("GH_TOKEN", ""))
    except (InstallCheckError, OSError, UnicodeError, ValueError,
            subprocess.SubprocessError) as exc:
        code = str(exc) if isinstance(exc, InstallCheckError) else "REMOTE_RUNTIME_FAILED"
        print("BLOCKED: " + code, file=sys.stderr)
        return 1
    print("GH_SKILL_REMOTE_PIN_PASS: " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
