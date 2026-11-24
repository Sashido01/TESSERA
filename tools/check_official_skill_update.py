#!/usr/bin/env python3
"""T10.03.01: real remote update and guarded re-pin acceptance.

This is a CI acceptance harness, not a user-profile updater. Destructive
upstream behavior is tested only against synthetic edits in a temporary
installation. No downloaded skill code is executed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import stat
import subprocess
import sys
import tempfile

from check_official_local_install import (
    VERSION, SKILL, fixture_env, run_command, safe_destination,
    tree_fingerprint, InstallCheckError,
)
from check_official_remote_install import (
    REPO, REF, COMMIT, TAG_OBJECT, expected_files, files_at_commit,
    require, verify_install, check_listing, MAX_FILES, MAX_BYTES,
)

OLD_REF = "refs/tags/v0.0.5"
OLD_COMMIT = "b50d430b4d555380098dd7a88e7d849ff68583d1"
OLD_TAG = "652fdf798254335c753ad40df3b10561699d5147"
NEW_REF = "refs/tags/v0.0.23"
NEW_COMMIT = "90ba23df206934d90a2067019c0b38f0548ec5fc"
NEW_TAG = "e821244a623981e40e05b91894973b8e334c53a5"
MAIN_REF = "refs/heads/main"


def snapshot(root: pathlib.Path) -> dict[str, tuple]:
    """Include all entries, including extra files, hidden files and modes."""
    require(root.is_dir() and not root.is_symlink(), "UPDATE_DIRECTORY_INVALID")
    result = {}
    size = 0
    for p in sorted(root.rglob("*")):
        info = p.lstat()
        mode = stat.S_IMODE(info.st_mode)
        require(len(result) < MAX_FILES, "UPDATE_SNAPSHOT_LIMIT")
        if stat.S_ISDIR(info.st_mode):
            value = ("dir", mode)
        else:
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
                    "UPDATE_NONREGULAR_OR_LINK")
            size += info.st_size
            require(size <= MAX_BYTES, "UPDATE_SNAPSHOT_LIMIT")
            value = ("file", mode, info.st_size, hashlib.sha256(p.read_bytes()).hexdigest())
        result[p.relative_to(root).as_posix()] = value
    require("SKILL.md" in result, "UPDATE_SKILL_MISSING")
    return result


def guarded_swap(target: pathlib.Path, staged: pathlib.Path, backup: pathlib.Path,
                 original: dict, replacement: dict, *, inject_failure=False) -> None:
    """Bounded rename/rollback test for exclusive, disposable same-volume paths.

    Not crash-atomic or safe against concurrent writers. Never deletes backup
    on rollback failure. Caller has independently verified both snapshots.
    """
    roots = (target, staged, backup)
    require(len({p.resolve() for p in roots}) == 3, "UPDATE_PATH_ALIAS")
    require(all(not p.is_symlink() for p in roots), "UPDATE_PATH_SYMLINK")
    require(all(not a.resolve().is_relative_to(b.resolve())
                for a in roots for b in roots if a != b), "UPDATE_NESTED_PATH")
    require(not backup.exists(), "UPDATE_BACKUP_EXISTS")
    require(target.parent.stat().st_dev == staged.parent.stat().st_dev ==
            backup.parent.stat().st_dev, "UPDATE_CROSS_VOLUME")
    require(snapshot(target) == original, "UPDATE_LOCAL_CHANGES")
    require(snapshot(staged) == replacement, "UPDATE_STAGED_CHANGES")
    moved_old = False
    moved_new = False
    try:
        target.rename(backup)
        moved_old = True
        if inject_failure:
            raise InstallCheckError("UPDATE_INJECTED_FAILURE")
        staged.rename(target)
        moved_new = True
        require(snapshot(target) == replacement, "UPDATE_POST_SWAP_MISMATCH")
    except Exception:
        try:
            if moved_new:
                target.rename(staged)
            if moved_old:
                backup.rename(target)
            require(snapshot(target) == original, "UPDATE_ROLLBACK_MISMATCH")
        except Exception as exc:
            raise InstallCheckError("UPDATE_ROLLBACK_FAILED_KEEP_BACKUP") from exc
        raise


def accept(repo: pathlib.Path, cli: pathlib.Path, token: str) -> dict[str, str]:
    require(bool(token.strip()), "UPDATE_READ_TOKEN_REQUIRED")
    repo = repo.resolve(strict=True)
    cli = cli.resolve(strict=True)
    require(cli.is_file() and os.access(cli, os.X_OK), "UPDATE_CLI_UNAVAILABLE")
    before = tree_fingerprint(repo / "skills")
    with tempfile.TemporaryDirectory(prefix="tessera-gh-update-") as folder:
        temp = pathlib.Path(folder)
        env = fixture_env(temp)
        env.update(GH_TOKEN=token, GH_TELEMETRY="off", GH_NO_EXTENSION_UPDATE_NOTIFIER="1")

        def gh(*args):
            return run_command(subprocess.run, [str(cli), *args], cwd=temp, env=env)

        v = gh("version")
        require(v.returncode == 0 and bool(re.match(
            r"^gh version " + re.escape(VERSION) + r" \(", v.stdout)),
            "UPDATE_CLI_VERSION_MISMATCH")
        old_tree, old_files = expected_files(
            repo, env, ref=OLD_REF, commit=OLD_COMMIT, tag_object=OLD_TAG)
        new_tree, new_files = expected_files(
            repo, env, ref=NEW_REF, commit=NEW_COMMIT, tag_object=NEW_TAG)
        require(old_tree != new_tree, "UPDATE_BASELINES_IDENTICAL")

        def install(name, pin, tree, files):
            dest = temp / name
            target = safe_destination(dest, SKILL)
            got = gh("skill", "install", REPO, SKILL, "--pin", pin, "--dir", str(dest))
            require(got.returncode == 0, "UPDATE_BASELINE_INSTALL_FAILED")
            verify_install(target, files, tree, pin)
            listing = gh("skill", "list", "--dir", str(dest),
                         "--json", "skillName,sourceURL,version,pinned,path")
            require(listing.returncode == 0, "UPDATE_LIST_FAILED")
            check_listing(listing.stdout, pin, target)
            return target

        def main_commit():
            result = gh("api", "repos/" + REPO + "/git/ref/heads/main", "--jq", ".object.sha")
            sha = result.stdout.strip()
            require(result.returncode == 0 and bool(re.fullmatch(r"[0-9a-f]{40}", sha)),
                    "UPDATE_MAIN_REF_UNAVAILABLE")
            return sha

        main_sha = main_commit()
        main_tree, main_files = files_at_commit(repo, env, main_sha)
        require(main_tree != old_tree, "UPDATE_NO_ACTUAL_TREE_CHANGE")

        # Demonstrate actual native update behavior with fabricated local edits.
        native = install("native", OLD_REF, old_tree, old_files)
        marker = native / "owner-test-marker.txt"
        marker.write_bytes(b"synthetic owner edit; never real user data\n")
        (native / "README.md").write_bytes(b"synthetic locally modified README\n")
        native_modified = snapshot(native)
        base = ("skill", "update", SKILL, "--dir", str(native.parent))
        dry = gh(*base, "--unpin", "--dry-run")
        require(dry.returncode == 0 and "1 update(s) available" in dry.stderr
                and old_tree[:7] in dry.stdout and main_tree[:7] in dry.stdout,
                "UPDATE_NATIVE_DRY_RUN_NOT_CONFIRMED")
        require(snapshot(native) == native_modified, "UPDATE_DRY_RUN_MUTATED_FILES")
        apply = gh(*base, "--unpin", "--all")
        require(apply.returncode == 0 and "Updated " + SKILL in apply.stdout,
                "UPDATE_NATIVE_APPLY_FAILED")
        verify_install(native, main_files, main_tree, None, ref=MAIN_REF)
        require(not marker.exists() and (native / "README.md").read_bytes() ==
                main_files["README.md"], "UPDATE_NATIVE_LOCAL_EDIT_RISK_NOT_CONFIRMED")
        require(main_commit() == main_sha, "UPDATE_MAIN_MOVED")

        # Safe alternative: stage an exact new pin separately and compare
        # all local entries against a known clean installed snapshot.
        current = install("current", OLD_REF, old_tree, old_files)
        staged = install("staged", NEW_REF, new_tree, new_files)
        clean, fresh = snapshot(current), snapshot(staged)
        backup = temp / "backup"
        local = current / ".owner-test-marker"
        local.write_bytes(b"keep this synthetic local file\n")
        changed = snapshot(current)
        try:
            guarded_swap(current, staged, backup, clean, fresh)
        except InstallCheckError as exc:
            require(str(exc) == "UPDATE_LOCAL_CHANGES", "UPDATE_WRONG_LOCAL_EDIT_ERROR")
        else:
            raise InstallCheckError("UPDATE_LOCAL_EDIT_NOT_REFUSED")
        require(snapshot(current) == changed and snapshot(staged) == fresh
                and not backup.exists(), "UPDATE_LOCAL_EDIT_MUTATED")
        local.unlink()
        require(snapshot(current) == clean, "UPDATE_CLEAN_BASELINE_MISMATCH")

        try:
            guarded_swap(current, staged, backup, clean, fresh, inject_failure=True)
        except InstallCheckError as exc:
            require(str(exc) == "UPDATE_INJECTED_FAILURE", "UPDATE_WRONG_FAILURE")
        else:
            raise InstallCheckError("UPDATE_INJECTED_FAILURE_NOT_RAISED")
        require(snapshot(current) == clean and snapshot(staged) == fresh
                and not backup.exists(), "UPDATE_ROLLBACK_MISMATCH")

        guarded_swap(current, staged, backup, clean, fresh)
        verify_install(current, new_files, new_tree, NEW_REF)
        require(snapshot(backup) == clean, "UPDATE_BACKUP_MISMATCH")
        # Explicit restoration of the previous pin, keeping the newer copy.
        newer_backup = temp / "newer-backup"
        guarded_swap(current, backup, newer_backup, fresh, clean)
        verify_install(current, old_files, old_tree, OLD_REF)
        require(snapshot(newer_backup) == fresh, "UPDATE_RESTORE_MISMATCH")
        require(tree_fingerprint(repo / "skills") == before, "UPDATE_SOURCE_MUTATED")
    return {"status": "PASS", "gh_version": VERSION, "old_ref": OLD_REF,
            "new_ref": NEW_REF, "old_tree": old_tree, "new_tree": new_tree,
            "native_update_main_commit": main_sha, "native_update_tree": main_tree,
            "native_unpin_dry_run": "PASS", "native_unpin_apply": "PASS",
            "native_local_edits_removed": "CONFIRMED", "local_edit_refusal": "PASS",
            "staged_repin": "PASS", "injected_rename_rollback": "PASS",
            "explicit_restore": "PASS", "crash_recovery": "NOT_VERIFIED",
            "concurrent_writers": "NOT_VERIFIED", "multi_skill_namespace": "NOT_VERIFIED",
            "user_profile_activation": "NOT_VERIFIED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=pathlib.Path, required=True)
    parser.add_argument("--cli", type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        result = accept(args.repo, args.cli, os.environ.get("GH_TOKEN", ""))
    except (InstallCheckError, OSError, UnicodeError, ValueError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + (str(exc) if isinstance(exc, InstallCheckError)
                             else "UPDATE_RUNTIME_FAILED"), file=sys.stderr)
        return 1
    print("GH_SKILL_UPDATE_PASS: " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
