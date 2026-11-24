#!/usr/bin/env python3
"""Run the tracked UTF-8 Gitleaks scope inside one restricted Docker container."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

from check_docker_preflight import DOCKER, IMAGE, required
from check_gitleaks_review import VERSION, inventory, scan, synthetic_marker
from check_bandit_review import fingerprint
from check_official_local_install import fixture_env, InstallCheckError
from check_nvidia_tier1 import require
from gitleaks_frame import encode, decode

BINARY_SHA = "88f91962aa2f93ac6ab281d553b9e125f5197bbbce38f9f2437f7299c32e5509"
MODULES = ("check_gitleaks_container.py", "gitleaks_frame.py", "check_docker_preflight.py",
           "check_gitleaks_review.py", "check_bandit_review.py",
           "check_nvidia_tier1.py", "check_official_local_install.py")
LIMIT = 1024 * 1024


def binary_ok(cli):
    require(cli.is_file() and cli.stat().st_size <= 128 * 1024 * 1024
            and hashlib.sha256(cli.read_bytes()).hexdigest() == BINARY_SHA,
            "CONTAINER_BINARY_DIGEST")


def records_for(data):
    return [(int("tests" in pathlib.PurePosixPath(name).parts), content)
            for name, content in sorted(data.items())]


def worker():
    cli = pathlib.Path("/stage/gitleaks")
    binary_ok(cli)
    records, digest = decode(sys.stdin.buffer)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(dir="/tmp") as folder:
        temp = pathlib.Path(folder)
        env = fixture_env(temp)
        env.update({"PATH": "/usr/local/bin:/usr/bin:/bin", "CI": "true", "GOMAXPROCS": "2"})
        version = subprocess.run([str(cli), "version"], cwd=temp, env=env,
                                 stdin=subprocess.DEVNULL, capture_output=True, timeout=10)
        require(version.returncode == 0 and version.stdout.strip() == VERSION.encode(), "CONTAINER_VERSION")
        entries = set(temp.iterdir())
        clean, _, _ = scan(cli, temp, env, b"plain text fixture\n")
        require(not clean, "CONTAINER_CLEAN_FIXTURE")
        marker = synthetic_marker()
        negative, stdout, stderr = scan(cli, temp, env, b"fixture " + marker + b" # gitleaks:allow\n")
        require(negative.get("aws-access-token", 0) > 0 and marker not in stdout and marker not in stderr,
                "CONTAINER_DETECTION_REDACTION")
        counts = collections.Counter()
        for category, data in records:
            if data:
                require(time.monotonic() - started < 240, "CONTAINER_SCAN_TIMEOUT")
                rules, _, _ = scan(cli, temp, env, data)
                for rule, count in rules.items():
                    counts["tests" if category else "other", rule] += count
        require(set(temp.iterdir()) == entries, "CONTAINER_FIXTURE_MUTATED")
    return {"digest": digest, "version": VERSION, "files": len(records),
            "scanned_nonempty": sum(bool(data) for _, data in records),
            "empty": sum(not data for _, data in records), "bytes_scanned": sum(len(data) for _, data in records),
            "by_rule": [{"scope": scope, "rule": rule, "count": count}
                        for (scope, rule), count in sorted(counts.items())],
            "findings": sum(counts.values()), "clean_fixture": "PASS",
            "negative_allow_fixture": "PASS", "fixture_redaction": "PASS",
            "fixture_top_level_entries_unchanged": "PASS"}


def args_for(name, stage, *, mode="content"):
    require(mode in ("content", "paths"), "CONTAINER_MODE_INVALID")
    entry = ("import sys;sys.path.insert(0,'/stage');import check_gitleaks_container as m;m.worker_main()"
             if mode == "content" else
             "import sys;sys.path.insert(0,'/stage');import check_gitleaks_paths_container as m;m.worker_main()")
    return ["create", "--name", name, "--pull=never", "--platform=linux/amd64",
            "--interactive", "--log-driver=none", "--network=none", "--read-only",
            "--cap-drop=ALL", "--security-opt=no-new-privileges=true", "--user=65534:65534",
            "--ipc=private", "--memory=512m", "--memory-swap=512m", "--cpus=2",
            "--pids-limit=64", "--ulimit=core=0:0",
            "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=32m,mode=1777",
            "--mount", f"type=bind,source={stage},target=/stage,readonly",
            "--entrypoint=/usr/local/bin/python3", IMAGE, "-I", "-B", "-c",
            entry]


def verify(report, host, digest):
    keys = ("version", "files", "scanned_nonempty", "empty", "bytes_scanned", "by_rule",
            "findings", "clean_fixture", "negative_allow_fixture", "fixture_redaction",
            "fixture_top_level_entries_unchanged")
    require(isinstance(report, dict) and set(report) == set(keys) | {"digest"}
            and report["digest"] == digest and all(report[k] == host[k] for k in keys),
            "CONTAINER_HOST_PARITY_FAILED")


def accept(repo, cli, host_file):
    require(sys.platform == "linux" and os.getuid() != 0, "CONTAINER_RUNNER_SCOPE")
    repo, cli = repo.resolve(strict=True), cli.resolve(strict=True)
    binary_ok(cli)
    data = inventory(repo)
    before = fingerprint(data)
    with host_file.open("rb") as stream:
        raw = stream.read(LIMIT + 1)
    prefix = b"GITLEAKS_REVIEW_EXECUTION_PASS: "
    require(len(raw) <= LIMIT and raw.startswith(prefix) and raw.count(b"\n") == 1,
            "CONTAINER_HOST_REPORT_INVALID")
    host = json.loads(raw[len(prefix):])
    require(host.get("execution") == "PASS" and host.get("snapshot_sha256") == snapshot_digest(before),
            "CONTAINER_HOST_SNAPSHOT_MISMATCH")
    report, digest = run_records(cli, records_for(data))
    verify(report, host, digest)
    require(fingerprint(inventory(repo)) == before, "CONTAINER_SOURCE_MUTATED")
    # Report only already validated counts; never emit frame digest or raw worker output.
    return {"execution": "PASS", "scope": "TRACKED_UTF8_CONTENT_STDIN_DOCKER",
            "version": VERSION, "files": report["files"], "bytes_scanned": report["bytes_scanned"],
            "findings": report["findings"], "host_parity": "PASS", "frame_digest": "PASS",
            "fixture_redaction": "PASS", "source_preserved": "PASS",
            "history": "NOT_RUN", "path_specific_rules": "NOT_RUN"}


def run_records(cli, records, timeout=300, *, mode="content"):
    require(mode in ("content", "paths"), "CONTAINER_MODE_INVALID")
    modules = MODULES if mode == "content" else MODULES + (
        "check_gitleaks_paths_container.py", "check_gitleaks_paths.py", "check_gitleaks_history.py")
    with tempfile.TemporaryDirectory(prefix="tessera-isolated-") as folder:
        home = pathlib.Path(folder)
        stage = home / "stage"
        stage.mkdir(mode=0o755)
        source = pathlib.Path(__file__).resolve().parent
        for module in modules:
            dest = stage / module
            shutil.copyfile(source / module, dest)
            dest.chmod(0o444)
        shutil.copyfile(cli, stage / "gitleaks")
        (stage / "gitleaks").chmod(0o555)
        binary_ok(stage / "gitleaks")
        stage.chmod(0o555)
        name = "tessera-gitleaks-" + uuid.uuid4().hex
        with tempfile.TemporaryFile() as frame, tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            digest = encode(records, frame, mode=mode)
            frame.seek(0)
            required(args_for(name, stage, mode=mode), home, "CONTAINER_CREATE_FAILED")
            try:
                env = {"PATH": "/usr/bin:/bin", "HOME": str(home), "LANG": "C", "LC_ALL": "C",
                       "DOCKER_CONFIG": str(home / "docker-config")}
                result = subprocess.run([*DOCKER, "start", "--attach", "--interactive", name],
                                        cwd=home, env=env, stdin=frame, stdout=out, stderr=err,
                                        timeout=timeout, check=False)
                require(result.returncode == 0, "CONTAINER_WORKER_FAILED")
                out.seek(0)
                raw = out.read(LIMIT + 1)
                require(len(raw) <= LIMIT and err.tell() == 0, "CONTAINER_REPORT_LIMIT_OR_STDERR")
                report = json.loads(raw)
                require(isinstance(report, dict) and report.get("digest") == digest,
                        "CONTAINER_FRAME_DIGEST")
            finally:
                required(["rm", "--force", name], home, "CONTAINER_CLEANUP_FAILED")
                stage.chmod(0o755)
    return report, digest


def snapshot_digest(mapping):
    return hashlib.sha256(json.dumps(mapping, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def worker_main():
    try:
        print(json.dumps(worker(), sort_keys=True))
    except Exception:
        # Only trusted fixture code runs; never emit exception text from scanner or frame.
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("repo", "cli", "host-report"):
        parser.add_argument("--" + arg, type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        report = accept(args.repo, args.cli, args.host_report)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError):
        print("BLOCKED: GITLEAKS_CONTAINER_FAILED", file=sys.stderr)
        return 1
    print("GITLEAKS_CONTAINER_PASS: " + json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
