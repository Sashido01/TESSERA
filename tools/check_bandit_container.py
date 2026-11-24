#!/usr/bin/env python3
"""Standalone Bandit isolated parity for the pinned Python source inventory."""
from __future__ import annotations
import argparse
import importlib.metadata
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

from check_bandit_review import VERSION, MAX_REPORT, inventory, snapshot_digest, summarize
from check_docker_preflight import DOCKER, IMAGE
from check_integrated_gitleaks import invoke, read_file, snapshot
from check_official_local_install import fixture_env
from check_nvidia_tier1 import require

VERSIONS = {"bandit":"1.9.4","markdown-it-py":"4.2.0","mdurl":"0.1.2","pygments":"2.20.0","pyyaml":"6.0.3","rich":"15.0.0","stevedore":"5.9.0"}
MODULES = ("check_bandit_container.py", "check_bandit_review.py", "check_docker_preflight.py",
           "check_integrated_gitleaks.py", "check_gitleaks_container.py", "check_gitleaks_review.py",
           "gitleaks_frame.py",
           "check_official_local_install.py", "check_nvidia_tier1.py")
# Match the console-script argv[0]; upstream argparse uses %(prog)s in --version.
ENTRY = "import sys;sys.path.insert(0,'/packages');sys.argv[0]='bandit';from bandit.cli.main import main;main()"


def packages(root):
    require(root.resolve(strict=True) == root and root.is_dir(), "BANDIT_PACKAGE_ROOT")
    seen = {}
    for dist in importlib.metadata.distributions(path=[str(root)]):
        name = re.sub(r"[-_.]+", "-", dist.metadata["Name"]).lower()
        require(name not in seen, "BANDIT_DUPLICATE_DIST")
        seen[name] = dist.version
    require(seen == VERSIONS, "BANDIT_PACKAGE_INVENTORY")
    # Bound and fingerprint the exact wheel-install directory. No links or unusual files.
    data = {}
    total = 0
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in dirs:
            path = pathlib.Path(base) / name
            require(path.resolve(strict=True) == path and not path.is_symlink(), "BANDIT_PACKAGE_LINK")
        for name in files:
            path = pathlib.Path(base) / name
            raw = read_file(path, 16 * 1024 * 1024)
            total += len(raw)
            require(len(data) < 4096 and total <= 128 * 1024 * 1024, "BANDIT_PACKAGE_LIMIT")
            data[path.relative_to(root).as_posix()] = raw
    require(data, "BANDIT_PACKAGE_EMPTY")
    return snapshot_digest(data)


def validate_lock(subset, full):
    lines = [line.strip() for line in subset.splitlines() if line.strip() and not line.startswith("#")]
    names = {}
    for line in lines:
        match = re.fullmatch(r"([a-z0-9-]+)==([0-9.]+) --hash=sha256:[a-f0-9]{64}", line)
        require(match is not None and line in full.splitlines(), "BANDIT_LOCK_MISMATCH")
        name, version = match.groups()
        require(name not in names, "BANDIT_LOCK_DUPLICATE")
        names[name] = version
    require(names == VERSIONS, "BANDIT_LOCK_COVERAGE")


def worker():
    source = pathlib.Path("/stage/input")
    original, dirs = snapshot(source)
    require(all(name.endswith(".py") for name in original), "BANDIT_SOURCE_TYPE")
    package_digest = packages(pathlib.Path("/packages"))
    with tempfile.TemporaryDirectory(dir="/tmp") as folder:
        temp = pathlib.Path(folder)
        env = fixture_env(temp)
        env.update({"PATH": "/usr/local/bin:/usr/bin:/bin", "CI": "true", "PYTHONNOUSERSITE": "1"})
        def run(args, cwd):
            return subprocess.run([sys.executable, "-I", "-B", "-c", ENTRY, *args],
                                  cwd=cwd, env=env, stdin=subprocess.DEVNULL, capture_output=True,
                                  encoding="utf-8", timeout=90, check=False)
        ver = run(["--version"], temp)
        require(ver.returncode == 0, "BANDIT_CONTAINER_VERSION_EXEC")
        require(re.search(r"(?m)^bandit 1\.9\.4(?:\s|$)", ver.stdout + "\n" + ver.stderr),
                "BANDIT_CONTAINER_VERSION")
        def scan(label, root, data):
            report = temp / (label + ".json")
            result = run(["-q", "--ignore-nosec", "-f", "json", "-o", str(report),
                          "--", *sorted(data)], root)
            require(report.is_file() and not report.is_symlink()
                    and report.stat().st_size <= MAX_REPORT, "BANDIT_CONTAINER_REPORT")
            summary = summarize(json.loads(report.read_text(encoding="utf-8")), result.returncode, set(data))
            require(snapshot(root)[0] == data, "BANDIT_CONTAINER_SOURCE_MUTATED")
            return summary
        actual = scan("catalog", source, original)
        for label, content in (("clean", b"answer = 42\n"), ("negative", b"eval('1 + 1')  # nosec\n")):
            root = temp / label
            root.mkdir()
            data = {"fixture.py": content}
            (root / "fixture.py").write_bytes(content)
            result = scan(label, root, data)
            require(result["verdict"] == "NO_FINDINGS" if label == "clean"
                    else any(row["rule"] == "B307" for row in result["by_rule"]), "BANDIT_CONTAINER_FIXTURE")
        require(snapshot(source) == (original, dirs), "BANDIT_CONTAINER_SOURCE_MUTATED")
    require(packages(pathlib.Path("/packages")) == package_digest, "BANDIT_PACKAGE_MUTATED")
    return {"version": VERSION, "snapshot_sha256": snapshot_digest(original), "package_sha256": package_digest,
            "catalog": actual, "clean_fixture": "PASS", "negative_nosec_fixture": "PASS"}


# Only fixed codes can cross the diagnostic boundary; never echo scanner text.
ERROR_CODES = frozenset({
    "BANDIT_PACKAGE_ROOT", "BANDIT_DUPLICATE_DIST", "BANDIT_PACKAGE_INVENTORY",
    "BANDIT_PACKAGE_LINK", "BANDIT_PACKAGE_LIMIT", "BANDIT_PACKAGE_EMPTY",
    "BANDIT_LOCK_MISMATCH", "BANDIT_LOCK_DUPLICATE", "BANDIT_LOCK_COVERAGE",
    "BANDIT_SOURCE_TYPE", "BANDIT_CONTAINER_VERSION", "BANDIT_CONTAINER_VERSION_EXEC", "BANDIT_CONTAINER_REPORT",
    "BANDIT_CONTAINER_SOURCE_MUTATED", "BANDIT_CONTAINER_FIXTURE", "BANDIT_PACKAGE_MUTATED",
    "BANDIT_CONTAINER_PARITY", "BANDIT_CONTAINER_RUNNER", "BANDIT_CONTAINER_HOST_REPORT",
    "BANDIT_CONTAINER_STAGE", "BANDIT_CONTAINER_CREATE", "BANDIT_CONTAINER_WORKER",
    "BANDIT_CONTAINER_CLEANUP", "BANDIT_CONTAINER_STAGE_MUTATED",
    "BANDIT_SCAN_INCOMPLETE", "BANDIT_REPORT_INVALID", "BANDIT_COVERAGE_MISMATCH",
    "BANDIT_METRICS_INVALID", "BANDIT_EXIT_MISMATCH", "BANDIT_FINDING_INVALID",
    "INTEGRATED_PATH_REDIRECTED", "INTEGRATED_FILE_LIMIT", "INTEGRATED_FILE_CHANGED",
    "INTEGRATED_SOURCE", "INTEGRATED_DIR", "INTEGRATED_FILE", "INTEGRATED_TOTAL",
    "INTEGRATED_EMPTY", "INTEGRATED_OUTPUT_LIMIT",
    "BANDIT_CONTAINER_IMPORT", "BANDIT_CONTAINER_FAILED",
})


def error_code(exc):
    return str(exc) if isinstance(exc, RuntimeError) and str(exc) in ERROR_CODES else "BANDIT_CONTAINER_FAILED"


def worker_error(raw):
    if len(raw) > 512:
        return "BANDIT_CONTAINER_WORKER"
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict) and set(obj) == {"error"} and isinstance(obj["error"], str) and obj["error"] in ERROR_CODES:
            return obj["error"]
    except (ValueError, TypeError):
        pass
    return "BANDIT_CONTAINER_WORKER"


def worker_main():
    try:
        print(json.dumps(worker(), sort_keys=True))
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        print(json.dumps({"error": error_code(exc)}))
        sys.exit(1)


def args_for(name, stage, package_root):
    return ["create", "--name", name, "--pull=never", "--platform=linux/amd64",
            "--log-driver=none", "--network=none", "--read-only", "--cap-drop=ALL",
            "--security-opt=no-new-privileges=true", "--user=65534:65534", "--ipc=private",
            "--memory=512m", "--memory-swap=512m", "--cpus=2", "--pids-limit=64", "--ulimit=core=0:0",
            "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=32m,mode=1777",
            "--mount", f"type=bind,source={stage},target=/stage,readonly",
            "--mount", f"type=bind,source={package_root},target=/packages,readonly",
            "--entrypoint=/usr/local/bin/python3", IMAGE, "-I", "-B", "-c",
            "import sys;sys.path.insert(0,'/stage/tools');import check_bandit_container as m;m.worker_main()"]


def parity(report, host, digest, package_digest):
    keys = ("version", "snapshot_sha256", "catalog", "clean_fixture", "negative_nosec_fixture")
    require(isinstance(report, dict) and set(report) == set(keys) | {"package_sha256"}
            and report["snapshot_sha256"] == digest and report["package_sha256"] == package_digest
            and host.get("execution") == "PASS" and host.get("scanner") == "bandit"
            and report["version"] == VERSION and report["clean_fixture"] == "PASS"
            and report["negative_nosec_fixture"] == "PASS"
            and all(json.dumps(report[k], sort_keys=True) == json.dumps(host[k], sort_keys=True)
                    for k in keys), "BANDIT_CONTAINER_PARITY")


def accept(repo, package_root, host_path):
    require(sys.platform == "linux" and os.getuid() != 0, "BANDIT_CONTAINER_RUNNER")
    repo, package_root = repo.resolve(strict=True), package_root.resolve(strict=True)
    validate_lock((repo / "tools/bandit-requirements.txt").read_text(encoding="utf-8"),
                  (repo / "tools/nvidia-tier1-requirements.txt").read_text(encoding="utf-8"))
    digest = packages(package_root)
    data = inventory(repo)
    source_digest = snapshot_digest(data)
    with host_path.open("rb") as stream:
        raw = stream.read(MAX_REPORT + 1)
    prefix = b"BANDIT_REVIEW_EXECUTION_PASS: "
    require(len(raw) <= MAX_REPORT and raw.startswith(prefix) and raw.count(b"\n") == 1,
            "BANDIT_CONTAINER_HOST_REPORT")
    host = json.loads(raw[len(prefix):])
    with tempfile.TemporaryDirectory(prefix="tessera-bandit-isolated-") as folder:
        home = pathlib.Path(folder)
        stage = home / "stage"
        tools = stage / "tools"
        tools.mkdir(parents=True)
        source = pathlib.Path(__file__).resolve().parent
        for module in MODULES:
            dest = tools / module
            shutil.copyfile(source / module, dest)
            dest.chmod(0o444)
        input_root = stage / "input"
        input_root.mkdir()
        for name, content in data.items():
            path = input_root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            path.chmod(0o444)
        require(snapshot(input_root)[0] == data, "BANDIT_CONTAINER_STAGE")
        name = "tessera-bandit-" + uuid.uuid4().hex
        created = False
        try:
            rc, _ = invoke(args_for(name, stage, package_root), home, 15)
            require(rc == 0, "BANDIT_CONTAINER_CREATE")
            created = True
            rc, raw = invoke(["start", "--attach", name], home, 180)
            require(rc == 0, worker_error(raw))
            report = json.loads(raw)
            parity(report, host, source_digest, digest)
        finally:
            rc, _ = invoke(["rm", "--force", name], home, 10)
            if rc != 0:
                absent_rc, listing = invoke(["ps", "-a", "--filter", "name=^/" + name + "$",
                                             "--format", "{{.Names}}"], home, 5)
                require(not created and absent_rc == 0 and not listing.strip(), "BANDIT_CONTAINER_CLEANUP")
        require(snapshot(input_root)[0] == data, "BANDIT_CONTAINER_STAGE_MUTATED")
    require(snapshot_digest(inventory(repo)) == source_digest and packages(package_root) == digest,
            "BANDIT_CONTAINER_SOURCE_MUTATED")
    return {"execution": "PASS", "scope": "TRACKED_PYTHON_DOCKER", "version": VERSION,
            "packages": len(VERSIONS), "catalog": report["catalog"], "host_parity": "PASS",
            "clean_fixture": "PASS", "negative_nosec_fixture": "PASS", "source_preserved": "PASS",
            "integrated_bandit": "NOT_RUN"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("repo", "packages", "host-report"):
        parser.add_argument("--" + arg, type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        result = accept(args.repo, args.packages, args.host_report)
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + error_code(exc), file=sys.stderr)
        return 1
    print("BANDIT_CONTAINER_PASS: " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
