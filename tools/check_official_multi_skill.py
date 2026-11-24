#!/usr/bin/env python3
"""T10.03.02: isolated multi-skill Git and official CLI acceptance.

All fixtures are generated in a new temporary directory. No network, tokens,
push, production skill changes, or execution of installed skill content.
Local snapshot installs do not establish remote pin metadata.
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
    VERSION, fixture_env, run_command, safe_destination,
    tree_fingerprint, InstallCheckError,
)
from check_official_remote_install import require, split_skill
from check_official_skill_update import snapshot, guarded_swap

ALPHA = "fixture-alpha"
BETA = "fixture-beta"
NAMES = (ALPHA, BETA)
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
SEMVER = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z")
FILES = ("SKILL.md", "VERSION", "references/marker.txt")


def skill_ref(name: str, version: str) -> str:
    require(bool(NAME.fullmatch(name)) and len(name) <= 64, "MULTI_NAME_INVALID")
    require(bool(SEMVER.fullmatch(version)), "MULTI_VERSION_INVALID")
    return "refs/tags/" + name + "/v" + version


def validate_names(names) -> None:
    seen = set()
    for name in names:
        require(bool(NAME.fullmatch(name)) and len(name) <= 64, "MULTI_NAME_INVALID")
        require(name not in seen, "MULTI_NAME_COLLISION")
        seen.add(name)


def git(repo, env, *args) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], env=env, stdin=subprocess.DEVNULL,
        capture_output=True, check=False, timeout=20,
    )
    require(result.returncode == 0, "MULTI_GIT_FAILED")
    return result.stdout


def write_skill(root: pathlib.Path, name: str, version: str, marker: str) -> None:
    skill = root / name
    (skill / "references").mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Synthetic acceptance fixture only\n---\n"
        f"\nSynthetic body {marker}\n", encoding="utf-8",
    )
    (skill / "VERSION").write_text(version + "\n", encoding="utf-8")
    (skill / "references" / "marker.txt").write_text(marker + "\n", encoding="utf-8")


def commit(repo, env, message):
    git(repo, env, "add", "--", "skills", "VERSION")
    git(repo, env, "commit", "-m", message)
    return git(repo, env, "rev-parse", "HEAD").decode().strip()


def tag(repo, env, ref, sha):
    git(repo, env, "tag", "-a", ref.removeprefix("refs/tags/"), sha,
        "-m", "Disposable annotated fixture")
    return git(repo, env, "rev-parse", ref).decode().strip()


def check_tag(repo, env, ref, sha, obj):
    require(git(repo, env, "cat-file", "-t", ref).strip() == b"tag",
            "MULTI_ANNOTATED_TAG_REQUIRED")
    require(git(repo, env, "rev-parse", ref).decode().strip() == obj
            and git(repo, env, "rev-parse", ref + "^{commit}").decode().strip() == sha,
            "MULTI_TAG_MISMATCH")


def skill_tree(repo, env, sha, name):
    return git(repo, env, "rev-parse", sha + ":skills/" + name).decode().strip()


def export(repo, env, sha, dest):
    dest.mkdir()
    for name in NAMES:
        prefix = "skills/" + name + "/"
        records = git(repo, env, "ls-tree", "-r", "-z", sha, "--", prefix).split(b"\0")
        found = set()
        for record in filter(None, records):
            meta, raw = record.split(b"\t", 1)
            mode, kind, blob = meta.decode("ascii").split()
            path = raw.decode("utf-8")
            require(path.startswith(prefix), "MULTI_EXPORT_PATH_INVALID")
            rel = path.removeprefix(prefix)
            require(rel in FILES and rel not in found and mode == "100644" and kind == "blob",
                    "MULTI_EXPORT_ENTRY_INVALID")
            found.add(rel)
            data = git(repo, env, "cat-file", "blob", blob)
            require(len(data) <= 65536, "MULTI_EXPORT_LIMIT")
            p = dest / prefix / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        require(found == set(FILES), "MULTI_EXPORT_INCOMPLETE")


def verify_local(target, source):
    require(target.is_dir() and not target.is_symlink(), "MULTI_INSTALL_TARGET_INVALID")
    got = snapshot(target)
    require(set(got) == set(FILES) | {"references"}, "MULTI_INVENTORY_MISMATCH")
    for name in FILES:
        original = (source / name).read_bytes()
        installed = (target / name).read_bytes()
        if name == "SKILL.md":
            header, body = split_skill(installed)
            _, expected_body = split_skill(original)
            require(body == expected_body and "local-path:" in header
                    and "github-pinned:" not in header, "MULTI_LOCAL_METADATA_MISMATCH")
        else:
            require(installed == original, "MULTI_FILE_MISMATCH")


def accept(repo: pathlib.Path, cli: pathlib.Path) -> dict:
    repo = repo.resolve(strict=True)
    cli = cli.resolve(strict=True)
    require(cli.is_file() and os.access(cli, os.X_OK), "MULTI_CLI_UNAVAILABLE")
    before = tree_fingerprint(repo / "skills")
    with tempfile.TemporaryDirectory(prefix="tessera-multi-skill-") as folder:
        temp = pathlib.Path(folder)
        env = fixture_env(temp)
        env["GH_TELEMETRY"] = "off"
        env["GH_NO_EXTENSION_UPDATE_NOTIFIER"] = "1"
        env["GIT_ALLOW_PROTOCOL"] = "file"
        fixture = temp / "fixture"
        fixture.mkdir()
        git(fixture, env, "init", "--initial-branch=main")
        git(fixture, env, "config", "user.name", "Fixture")
        git(fixture, env, "config", "user.email", "fixture@example.invalid")
        git(fixture, env, "config", "core.autocrlf", "false")
        git(fixture, env, "config", "commit.gpgsign", "false")
        git(fixture, env, "config", "tag.gpgSign", "false")
        validate_names(NAMES)
        write_skill(fixture / "skills", ALPHA, "0.0.1", "alpha-old")
        write_skill(fixture / "skills", BETA, "0.0.1", "beta-old")
        (fixture / "VERSION").write_text("0.0.1\n", encoding="utf-8")
        first = commit(fixture, env, "Initial two-skill fixture")
        alpha1, beta1 = skill_ref(ALPHA, "0.0.1"), skill_ref(BETA, "0.0.1")
        catalog = "refs/tags/v0.0.1"
        refs = [(r, first, tag(fixture, env, r, first)) for r in (alpha1, beta1, catalog)]

        write_skill(fixture / "skills", ALPHA, "0.0.2", "alpha-new")
        second = commit(fixture, env, "Alpha only")
        alpha2 = skill_ref(ALPHA, "0.0.2")
        refs.append((alpha2, second, tag(fixture, env, alpha2, second)))
        require(skill_tree(fixture, env, first, ALPHA) != skill_tree(fixture, env, second, ALPHA)
                and skill_tree(fixture, env, first, BETA) == skill_tree(fixture, env, second, BETA),
                "MULTI_ALPHA_INDEPENDENCE_FAILED")

        write_skill(fixture / "skills", BETA, "0.0.2", "beta-new")
        third = commit(fixture, env, "Beta only")
        beta2 = skill_ref(BETA, "0.0.2")
        refs.append((beta2, third, tag(fixture, env, beta2, third)))
        require(skill_tree(fixture, env, second, ALPHA) == skill_tree(fixture, env, third, ALPHA)
                and skill_tree(fixture, env, second, BETA) != skill_tree(fixture, env, third, BETA),
                "MULTI_BETA_INDEPENDENCE_FAILED")
        for ref, sha, obj in refs:
            check_tag(fixture, env, ref, sha, obj)
        require(len({obj for _, _, obj in refs}) == len(refs), "MULTI_TAG_OBJECT_COLLISION")
        require(not git(fixture, env, "remote").strip(), "MULTI_REMOTE_FORBIDDEN")

        sources = [temp / name for name in ("source-first", "source-second", "source-third")]
        for sha, dest in zip((first, second, third), sources):
            export(fixture, env, sha, dest)
        source_fingerprints = [tree_fingerprint(s / "skills") for s in sources]

        def gh(*args):
            return run_command(subprocess.run, [str(cli), *args], cwd=temp, env=env)

        ver = gh("version")
        require(ver.returncode == 0 and bool(re.match(
            r"^gh version " + re.escape(VERSION) + r" \(", ver.stdout)),
            "MULTI_CLI_VERSION_MISMATCH")

        def install(source, name, dest):
            target = safe_destination(dest, name)
            result = gh("skill", "install", str(source), name, "--from-local", "--dir", str(dest))
            require(result.returncode == 0, "MULTI_LOCAL_INSTALL_FAILED")
            verify_local(target, source / "skills" / name)
            return target

        dest = temp / "installed"
        alpha = install(sources[0], ALPHA, dest)
        beta = install(sources[2], BETA, dest)
        alpha_old, beta_before = snapshot(alpha), snapshot(beta)
        staged = install(sources[1], ALPHA, temp / "staging")
        alpha_new = snapshot(staged)
        backup = temp / "alpha-backup"
        guarded_swap(alpha, staged, backup, alpha_old, alpha_new)
        verify_local(alpha, sources[1] / "skills" / ALPHA)
        require(snapshot(beta) == beta_before, "MULTI_BETA_CHANGED_ON_ALPHA_UPDATE")
        guarded_swap(alpha, backup, temp / "new-alpha-backup", alpha_new, alpha_old)
        require(snapshot(alpha) == alpha_old and snapshot(beta) == beta_before,
                "MULTI_BETA_CHANGED_ON_ALPHA_RESTORE")

        listing = gh("skill", "list", "--dir", str(dest),
                     "--json", "skillName,pinned,version,sourceURL,path")
        require(listing.returncode == 0, "MULTI_LIST_FAILED")
        rows = json.loads(listing.stdout)
        require(isinstance(rows, list) and len(rows) == 2
                and {r.get("skillName") for r in rows} == set(NAMES),
                "MULTI_LIST_MISMATCH")
        for row in rows:
            name = row["skillName"]
            source = sources[0] if name == ALPHA else sources[2]
            require(row.get("pinned") is False and row.get("version") == ""
                    and row.get("path") == str(dest / name)
                    and row.get("sourceURL") == str(source / "skills" / name),
                    "MULTI_LIST_LOCAL_METADATA_MISMATCH")

        # Actual command-level duplicate refusal, distinct from InstallLocal's
        # low-level overwrite semantics. Check both installed skills unchanged.
        duplicate = gh("skill", "install", str(sources[1]), ALPHA,
                       "--from-local", "--dir", str(dest))
        require(duplicate.returncode != 0 and "already installed" in duplicate.stderr.lower(),
                "MULTI_LOCAL_DUPLICATE_NOT_REFUSED")
        require(snapshot(alpha) == alpha_old and snapshot(beta) == beta_before,
                "MULTI_LOCAL_DUPLICATE_MUTATED")

        collision = temp / "collision-source"
        write_skill(collision / "skills" / "team-a", "fixture-shared", "0.0.1", "team-a")
        write_skill(collision / "skills" / "team-b", "fixture-shared", "0.0.1", "team-b")
        rejected = temp / "collision-rejected"
        result = gh("skill", "install", str(collision), "--all", "--from-local", "--dir", str(rejected))
        require(result.returncode != 0 and "conflicting names" in result.stderr.lower()
                and not rejected.exists(), "MULTI_COLLISION_NOT_REFUSED")

        # Explicit namespace selects the source; both target paths remain flat.
        explicit = temp / "explicit"
        first_install = gh("skill", "install", str(collision), "team-a/fixture-shared",
                           "--from-local", "--dir", str(explicit))
        shared = explicit / "fixture-shared"
        require(first_install.returncode == 0, "MULTI_NAMESPACE_SELECT_FAILED")
        verify_local(shared, collision / "skills/team-a/fixture-shared")
        shared_before = snapshot(shared)
        other = gh("skill", "install", str(collision), "team-b/fixture-shared",
                   "--from-local", "--dir", str(explicit))
        require(other.returncode != 0 and "already installed" in other.stderr.lower()
                and snapshot(shared) == shared_before, "MULTI_NAMESPACE_FLAT_COLLISION")
        separate = temp / "explicit-other"
        second_install = gh("skill", "install", str(collision), "team-b/fixture-shared",
                            "--from-local", "--dir", str(separate))
        require(second_install.returncode == 0, "MULTI_NAMESPACE_SECOND_SELECT_FAILED")
        verify_local(separate / "fixture-shared", collision / "skills/team-b/fixture-shared")

        # The local selector accepts an ambiguous bare name; record this as a
        # risk, never use it for a production selection.
        ambiguous = temp / "ambiguous"
        bare = gh("skill", "install", str(collision), "fixture-shared",
                  "--from-local", "--dir", str(ambiguous))
        require(bare.returncode == 0, "MULTI_LOCAL_AMBIGUITY_BEHAVIOR_CHANGED")
        marker = (ambiguous / "fixture-shared/references/marker.txt").read_bytes()
        require(marker in (b"team-a\n", b"team-b\n"), "MULTI_AMBIGUOUS_SOURCE_UNKNOWN")

        require([tree_fingerprint(s / "skills") for s in sources] == source_fingerprints,
                "MULTI_SNAPSHOT_SOURCE_MUTATED")
        require(tree_fingerprint(repo / "skills") == before, "MULTI_REAL_CATALOG_MUTATED")
        require(not git(fixture, env, "remote").strip(), "MULTI_REMOTE_FORBIDDEN")

    return {"status": "PASS", "gh_version": VERSION, "fixture_mode": "LOCAL_ONLY",
            "annotated_independent_tags": "PASS", "independent_git_trees": "PASS",
            "two_local_installs": "PASS", "scoped_swap_and_restore": "PASS",
            "cli_duplicate_refusal": "PASS", "batch_collision_refusal": "PASS",
            "flat_namespace_collision": "CONFIRMED", "local_bare_name_ambiguity": "CONFIRMED",
            "remote_namespaced_pin": "NOT_VERIFIED", "production_skill_versions": "NOT_IMPLEMENTED",
            "client_activation": "NOT_VERIFIED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=pathlib.Path, required=True)
    parser.add_argument("--cli", type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        result = accept(args.repo, args.cli)
    except (InstallCheckError, OSError, ValueError, UnicodeError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + (str(exc) if isinstance(exc, InstallCheckError)
                             else "MULTI_RUNTIME_FAILED"), file=sys.stderr)
        return 1
    print("GH_SKILL_MULTI_FIXTURE_PASS: " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
