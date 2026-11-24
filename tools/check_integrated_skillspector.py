#!/usr/bin/env python3
"""Restricted local-only adapter for pinned NVIDIA SkillSpector invocation."""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

from check_integrated_gitleaks import exact, invoke, MAX_OUTPUT
from check_nvidia_tier1 import NAME, require
from check_skillspector_container import ENTRY, VERSIONS, inventory
from check_skillspector_review import VERSION, summary

DEADLINE = 140


def contract(args, root):
    exact(root)
    if args == ["--version"]:
        return None
    require(len(args) == 5 and args[0] == "scan"
            and args[2:] == ["--format", "json", "--no-llm"],
            "INTEGRATED_SP_ARGUMENTS")
    skill = exact(pathlib.Path(args[1]))
    require(skill.is_dir() and NAME.fullmatch(skill.name)
            and (skill / "SKILL.md").is_file()
            and (skill.parent == root / "skills"
                 or skill.parent == root / "sp-controls" and
                 skill.name in ("fixture-clean", "fixture-negative")),
            "INTEGRATED_SP_ROOT")
    return skill


def docker_args(name, stage, package_root, skill_name):
    from check_docker_preflight import IMAGE
    require(all(p.is_absolute() and "," not in str(p) and "\n" not in str(p)
                for p in (stage, package_root)) and stage != package_root
            and stage not in package_root.parents and package_root not in stage.parents,
            "INTEGRATED_SP_MOUNT")
    if skill_name is None:
        args = ["--version"]
    else:
        require(NAME.fullmatch(skill_name), "INTEGRATED_SP_ROOT")
        args = ["scan", "/stage/" + skill_name, "--format", "json", "--no-llm"]
    return ["create", "--name", name, "--pull=never", "--platform=linux/amd64",
            "--log-driver=none", "--network=none", "--read-only", "--cap-drop=ALL",
            "--security-opt=no-new-privileges=true", "--user=65534:65534", "--ipc=private",
            "--memory=1g", "--memory-swap=1g", "--cpus=2", "--pids-limit=64",
            "--ulimit=core=0:0", "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=64m,mode=1777",
            "--env=HOME=/tmp", "--env=XDG_CACHE_HOME=/tmp", "--env=AWS_EC2_METADATA_DISABLED=true",
            "--env=PIP_NO_INDEX=1", "--env=UV_OFFLINE=1", "--env=CI=true",
            "--env=OPENBLAS_NUM_THREADS=1", "--env=OMP_NUM_THREADS=1",
            "--mount", f"type=bind,source={stage},target=/stage,readonly",
            "--mount", f"type=bind,source={package_root},target=/packages,readonly",
            "--workdir", "/tmp", "--entrypoint=/usr/local/bin/python3", IMAGE,
            "-I", "-S", "-B", "-c", ENTRY, *args]


def run_container(stage, home, package_root, skill_name):
    name = "tessera-integrated-sp-" + uuid.uuid4().hex
    started = time.monotonic()
    created = False
    try:
        rc, _ = invoke(docker_args(name, stage, package_root, skill_name), home, 15)
        require(rc == 0, "INTEGRATED_SP_CREATE")
        created = True
        remaining = DEADLINE - (time.monotonic() - started)
        require(remaining > 0, "INTEGRATED_SP_TIMEOUT")
        return invoke(["start", "--attach", name], home, remaining)
    finally:
        rc, _ = invoke(["rm", "--force", name], home, 10)
        if rc != 0:
            check, listing = invoke(["ps", "-a", "--filter", "name=^/" + name + "$",
                                      "--format", "{{.Names}}"], home, 5)
            require(not created and check == 0 and not listing.strip(), "INTEGRATED_SP_CLEANUP")


def checked_report(rc, raw, expected):
    require(0 < len(raw) < MAX_OUTPUT, "INTEGRATED_SP_REPORT")
    data = json.loads(raw)
    report = summary(data, rc, expected)
    require(report["analysis_status"] == "complete" and report["missing_files"] == 0
            and report["coverage_percent"] == 100, "INTEGRATED_SP_COVERAGE")
    # Preserve upstream schema for NVIDIA's own validation. This raw payload is
    # private process-to-process data, not a log or published report.
    return report


def accept(args, root, package_root):
    require(sys.platform == "linux" and os.getuid() != 0, "INTEGRATED_SP_RUNNER")
    skill = contract(args, root)
    before = inventory(package_root, VERSIONS)
    source_before = inventory(skill) if skill else None
    expected = {p.relative_to(skill).as_posix(): p.stat().st_size
                for p in skill.rglob("*") if p.is_file()} if skill else {}
    with tempfile.TemporaryDirectory(prefix="tessera-sp-adapter-", dir=root) as folder:
        home = pathlib.Path(folder)
        stage = home / "stage"
        stage.mkdir()
        if skill:
            dest = stage / skill.name
            shutil.copytree(skill, dest, symlinks=True)
            require(inventory(dest) == source_before, "INTEGRATED_SP_MUTATED")
        rc, raw = run_container(stage, home, package_root, skill.name if skill else None)
        if skill:
            report = checked_report(rc, raw, expected)
            require(inventory(dest) == inventory(skill) == source_before, "INTEGRATED_SP_MUTATED")
        else:
            require(rc == 0 and raw.strip() == ("SkillSpector v" + VERSION).encode(),
                    "INTEGRATED_SP_VERSION")
    require(inventory(package_root, VERSIONS) == before, "INTEGRATED_SP_PACKAGES")
    if skill:
        receipt = root / "sp-receipts" / (skill.name + "-" + uuid.uuid4().hex)
        with receipt.open("x", encoding="ascii") as stream:
            json.dump(report, stream, sort_keys=True)
    return rc, raw


def main(args, root, package_root):
    try:
        rc, raw = accept(args, pathlib.Path(root), pathlib.Path(package_root))
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        print("BLOCKED: INTEGRATED_SP_FAILED", file=sys.stderr)
        return 2
    sys.stdout.buffer.write(raw)
    return rc
