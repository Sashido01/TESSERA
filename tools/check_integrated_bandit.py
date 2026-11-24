#!/usr/bin/env python3
"""Restricted Linux adapter for NVIDIA's pinned Bandit argument contract."""
from __future__ import annotations
import fnmatch
import glob
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time
import uuid

from check_bandit_container import ENTRY, packages
from check_bandit_review import summarize, LEVELS
from check_integrated_gitleaks import exact, read_file, snapshot, invoke, MAX_OUTPUT
from check_docker_preflight import IMAGE
from check_nvidia_tier1 import NAME, require

INI_BLOB = "3d1f1b039c78013871f85efee6dd92d35c89aebd"
SKIP_DIRS = frozenset({"tests", "test", "evals", ".evals", "results", ".results",
                       "versions", ".versions", "__pycache__", ".git", ".venv", "node_modules"})
MAX_TARGETS = 2048
DEADLINE = 95
TARGET = "/stage/input"


def ini_ok(raw):
    require(hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest() ==
            INI_BLOB, "INTEGRATED_BANDIT_INI")


def exclusions(root):
    prefix = glob.escape(str(root)).replace(",", "?")
    rows = [f"{base}/{glob.escape(name)}/*" for name in sorted(SKIP_DIRS)
            for base in (prefix, prefix + "/*")]
    rows += [f"{prefix}/{name}" for name in ("*_test.py", "test_*.py", "*/test_*.py")]
    return ",".join(sorted(rows))


def eligible(files):
    return {name for name in files if pathlib.PurePosixPath(name).suffix in (".py", ".pyw")
            and not set(pathlib.PurePosixPath(name).parts[:-1]) & SKIP_DIRS
            and not fnmatch.fnmatchcase(pathlib.PurePosixPath(name).name, "test_*.py")
            and not fnmatch.fnmatchcase(pathlib.PurePosixPath(name).name, "*_test.py")}


def allowed_root(path, root):
    exact(path)
    require(path.is_dir() and (path == root / "bandit-control"
            or path.parent == root / "skills" and NAME.fullmatch(path.name)
            and (path / "SKILL.md").is_file()), "INTEGRATED_BANDIT_ROOT")
    return path


def contract(args, root, ini):
    exact(root)
    if args == ["--version"]:
        return None, [], set(), None
    require(10 <= len(args) <= MAX_TARGETS + 9 and
            args[-9:-5] == ["-f", "json", "-q", "-ll"] and
            args[-5] == "--exclude" and args[-3] == "--ini" and
            args[-2] == str(ini) and args[-1] == "--ignore-nosec",
            "INTEGRATED_BANDIT_ARGUMENTS")
    targets, exclude = args[:-9], args[-4]
    raw_ini = read_file(ini, 16384)
    ini_ok(raw_ini)
    if targets[0] == "-r":
        require(len(targets) == 2, "INTEGRATED_BANDIT_TARGETS")
        skill = allowed_root(pathlib.Path(targets[1]), root)
        require(exclude == exclusions(skill), "INTEGRATED_BANDIT_EXCLUDES")
        files, dirs = snapshot(skill)
        expected = eligible(files)
        translated = ["-r", TARGET, "-f", "json", "-q", "-ll",
                      "--exclude", exclusions(pathlib.Path(TARGET))]
    else:
        require(exclude == "", "INTEGRATED_BANDIT_EXCLUDES")
        paths = [exact(pathlib.Path(x)) for x in targets]
        roots = set()
        for path in paths:
            rel = path.relative_to(root)
            require(len(rel.parts) >= 2, "INTEGRATED_BANDIT_TARGET")
            candidate = root.joinpath(*rel.parts[:2]) if rel.parts[0] == "skills" else root / rel.parts[0]
            roots.add(allowed_root(candidate, root))
        require(len(roots) == 1, "INTEGRATED_BANDIT_ROOT")
        skill = next(iter(roots))
        files, dirs = snapshot(skill)
        selected = [path.relative_to(skill).as_posix() for path in paths]
        expected = set(selected)
        require(len(expected) == len(selected) and expected <= eligible(files),
                "INTEGRATED_BANDIT_TARGET")
        translated = [TARGET + "/" + x for x in selected] + ["-f", "json", "-q", "-ll", "--exclude", ""]
    require(0 < len(expected) <= MAX_TARGETS, "INTEGRATED_BANDIT_COVERAGE")
    return skill, translated + ["--ini", "/stage/bandit.ini", "--ignore-nosec"], expected, raw_ini


def remap(name, expected, skill):
    require(isinstance(name, str) and name.startswith(TARGET + "/"), "INTEGRATED_BANDIT_REPORT_PATH")
    rel = name[len(TARGET)+1:]
    require(rel in expected, "INTEGRATED_BANDIT_REPORT_PATH")
    return rel, str(skill / rel)


def sanitize(rc, raw, expected, skill, files):
    require(len(raw) < MAX_OUTPUT and rc in (0, 1), "INTEGRATED_BANDIT_EXIT")
    doc = json.loads(raw)
    require(isinstance(doc, dict) and doc.get("errors") == [] and
            isinstance(doc.get("results"), list) and isinstance(doc.get("metrics"), dict),
            "INTEGRATED_BANDIT_REPORT")
    metrics = {}
    for name, row in doc["metrics"].items():
        rel = name if name == "_totals" else remap(name, expected, skill)[0]
        require(rel not in metrics and isinstance(row, dict) and
                type(row.get("loc")) is int and row["loc"] >= 0, "INTEGRATED_BANDIT_METRICS")
        metrics[rel] = {"loc": row["loc"]}
    require(len(doc["results"]) <= 10000, "INTEGRATED_BANDIT_REPORT")
    findings = []
    relative = []
    for row in doc["results"]:
        require(isinstance(row, dict), "INTEGRATED_BANDIT_ROW")
        rel, host_path = remap(row.get("filename"), expected, skill)
        rule, title, message = (row.get(k) for k in ("test_id", "test_name", "issue_text"))
        severity, confidence, line = (row.get(k) for k in ("issue_severity", "issue_confidence", "line_number"))
        cwe = row.get("issue_cwe", {})
        require(isinstance(rule, str) and re.fullmatch(r"B[0-9]{3}", rule)
                and isinstance(title, str) and re.fullmatch(r"[a-zA-Z0-9_]{1,128}", title)
                and isinstance(message, str) and 0 < len(message) <= 8192
                and isinstance(severity, str) and severity in LEVELS
                and isinstance(confidence, str) and confidence in LEVELS
                and type(line) is int and 1 <= line <= max(1, len(files[rel].splitlines()))
                and isinstance(cwe, dict) and ("id" not in cwe or
                type(cwe["id"]) is int and 0 <= cwe["id"] <= 100000), "INTEGRATED_BANDIT_ROW")
        item = {"test_id": rule, "test_name": title, "issue_text": message,
                "issue_severity": severity, "issue_confidence": confidence, "line_number": line,
                "issue_cwe": {"id": cwe["id"]} if "id" in cwe else {}, "filename": host_path}
        findings.append(item)
        relative.append({**item, "filename": rel})
    summarize({"errors": [], "results": relative, "metrics": metrics}, rc, expected)
    # NVIDIA consumes findings and errors only; omit raw source/code and metrics.
    return json.dumps({"errors": [], "results": findings}, ensure_ascii=True).encode("ascii") + b"\n"


def docker_args(name, stage, package_root, args):
    return ["create", "--name", name, "--pull=never", "--platform=linux/amd64",
            "--log-driver=none", "--network=none", "--read-only", "--cap-drop=ALL",
            "--security-opt=no-new-privileges=true", "--user=65534:65534", "--ipc=private",
            "--memory=512m", "--memory-swap=512m", "--cpus=2", "--pids-limit=64", "--ulimit=core=0:0",
            "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=32m,mode=1777", "--env=HOME=/tmp",
            "--mount", f"type=bind,source={stage},target=/stage,readonly",
            "--mount", f"type=bind,source={package_root},target=/packages,readonly",
            "--workdir", "/stage", "--entrypoint=/usr/local/bin/python3", IMAGE, "-I", "-B", "-c", ENTRY, *args]


def run_container(stage, home, package_root, args):
    name = "tessera-integrated-bandit-" + uuid.uuid4().hex
    started = time.monotonic()
    created = False
    try:
        rc, _ = invoke(docker_args(name, stage, package_root, args), home, 15)
        require(rc == 0, "INTEGRATED_BANDIT_CREATE")
        created = True
        remaining = DEADLINE - (time.monotonic() - started)
        require(remaining > 0, "INTEGRATED_BANDIT_TIMEOUT")
        return invoke(["start", "--attach", name], home, remaining)
    finally:
        rc, _ = invoke(["rm", "--force", name], home, 10)
        if rc != 0:
            check, listing = invoke(["ps", "-a", "--filter", "name=^/" + name + "$",
                                     "--format", "{{.Names}}"], home, 5)
            require(not created and check == 0 and not listing.strip(), "INTEGRATED_BANDIT_CLEANUP")


def accept(args, root, package_root, ini):
    require(sys.platform == "linux" and os.getuid() != 0, "INTEGRATED_BANDIT_RUNNER")
    require(all("," not in str(p) and "\n" not in str(p) for p in (root, package_root)),
            "INTEGRATED_BANDIT_MOUNT_PATH")
    skill, translated, expected, raw_ini = contract(args, root, ini)
    package_digest = packages(package_root)
    files, dirs = snapshot(skill) if skill else ({}, set())
    require(expected <= eligible(files), "INTEGRATED_BANDIT_COVERAGE")
    with tempfile.TemporaryDirectory(prefix="tessera-bandit-adapter-", dir=root) as folder:
        home = pathlib.Path(folder)
        stage = home / "stage"
        stage.mkdir()
        if skill:
            dest = stage / "input"
            dest.mkdir()
            for rel in sorted(dirs):
                (dest / rel).mkdir()
            for rel, content in files.items():
                path = dest / rel
                path.write_bytes(content)
                path.chmod(0o444)
            (stage / "bandit.ini").write_bytes(raw_ini)
            (stage / "bandit.ini").chmod(0o444)
        rc, raw = run_container(stage, home, package_root, translated if skill else ["--version"])
        if skill:
            raw = sanitize(rc, raw, expected, skill, files)
            require(snapshot(skill) == snapshot(dest) == (files, dirs)
                    and read_file(ini, 16384) == raw_ini
                    and read_file(stage / "bandit.ini", 16384) == raw_ini, "INTEGRATED_BANDIT_MUTATED")
        else:
            require(rc == 0 and re.search(rb"(?m)^bandit 1\.9\.4(?:\s|$)", raw),
                    "INTEGRATED_BANDIT_VERSION")
    require(packages(package_root) == package_digest, "INTEGRATED_BANDIT_PACKAGE_MUTATED")
    if skill:
        # One receipt per successful scan, outside the mounted source tree.
        receipt = root / "bandit-receipts" / (skill.name + "-" + uuid.uuid4().hex)
        with receipt.open("x", encoding="ascii") as out:
            out.write(str(len(expected)) + "\n")
    return rc, raw


def main(args, root, package_root, ini):
    try:
        rc, raw = accept(args, pathlib.Path(root), pathlib.Path(package_root), pathlib.Path(ini))
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        print("BLOCKED: INTEGRATED_BANDIT_FAILED", file=sys.stderr)
        return 2
    sys.stdout.buffer.write(raw)
    return rc
