#!/usr/bin/env python3
"""Restricted adapter for the pinned NVIDIA SecretsValidator directory contract."""
from __future__ import annotations
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import tomllib
import uuid

from check_docker_preflight import DOCKER, IMAGE
from check_gitleaks_container import binary_ok, BINARY_SHA
from check_nvidia_tier1 import NAME, require

MAX_FILE = 2 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
MAX_CONFIG = 256 * 1024
MAX_OUTPUT = 16 * 1024 * 1024
DEADLINE = 100
RULE_ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,99}\Z")
PREFIX = ["detect", "--source", ".", "--report-format", "json", "--report-path", "-", "--exit-code", "10", "--config"]


def exact(path):
    require(path.is_absolute() and path.resolve(strict=True) == path and not path.is_symlink(),
            "INTEGRATED_PATH_REDIRECTED")
    return path


def arguments(args, cwd, root):
    exact(root)
    if args in (["version"], ["--version"]):
        return None
    require(len(args) == 12 and args[:10] == PREFIX and args[11] == "--no-git",
            "INTEGRATED_ARGUMENTS")
    exact(cwd)
    require(cwd == root / "redaction-control" or
            (cwd.parent == root / "skills" and NAME.fullmatch(cwd.name)
             and (cwd / "SKILL.md").is_file()), "INTEGRATED_ROOT")
    config = exact(pathlib.Path(args[10]))
    require(config == root / "redaction-control.toml" and cwd == root / "redaction-control"
            or config.parent == root / "tmp"
            and re.fullmatch(r"skillevaluator_[A-Za-z0-9_-]+\.toml", config.name)
            and cwd.parent == root / "skills", "INTEGRATED_CONFIG_ROOT")
    return config


def require_secure_open():
    require(sys.platform == "linux" and hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_NONBLOCK"),
            "INTEGRATED_SECURE_OPEN_UNSUPPORTED")


def read_file(path, maximum):
    require_secure_open()
    exact(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= maximum, "INTEGRATED_FILE_LIMIT")
        data = stream.read(maximum + 1)
        after = os.fstat(stream.fileno())
    require(len(data) == before.st_size and len(data) <= maximum and
            (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
            "INTEGRATED_FILE_CHANGED")
    return data


def snapshot(root):
    require_secure_open()
    exact(root)
    require(root.is_dir(), "INTEGRATED_SOURCE")
    files, dirs = {}, set()
    total = 0
    for base, names, filenames in os.walk(root, followlinks=False):
        for name in sorted(names):
            path = exact(pathlib.Path(base) / name)
            rel = path.relative_to(root).as_posix()
            require(name != ".git" and path.is_dir() and len(dirs) < 2048, "INTEGRATED_DIR")
            dirs.add(rel)
        for name in sorted(filenames):
            path = pathlib.Path(base) / name
            require(name != ".git" and len(files) < 2048, "INTEGRATED_FILE")
            data = read_file(path, MAX_FILE)
            total += len(data)
            require(total <= MAX_TOTAL, "INTEGRATED_TOTAL")
            files[path.relative_to(root).as_posix()] = data
    require(bool(files), "INTEGRATED_EMPTY")
    return files, dirs


def config_ok(raw):
    doc = tomllib.loads(raw.decode("utf-8"))
    require(set(doc) <= {"extend", "allowlist", "rules"}, "INTEGRATED_CONFIG_KEYS")
    if "extend" in doc:
        require(doc["extend"] == {"useDefault": True}, "INTEGRATED_CONFIG_EXTEND")
    if "allowlist" in doc:
        allow = doc["allowlist"]
        require(isinstance(allow, dict) and set(allow) <= {"description", "paths", "regexes"},
                "INTEGRATED_CONFIG_ALLOWLIST")
        for key, value in allow.items():
            require(isinstance(value, str) if key == "description" else
                    isinstance(value, list) and all(isinstance(x, str) for x in value),
                    "INTEGRATED_CONFIG_ALLOWLIST")
    rules = doc.get("rules", [])
    require(isinstance(rules, list) and 0 < len(rules) <= 16, "INTEGRATED_CONFIG_RULES")
    for rule in rules:
        require(isinstance(rule, dict) and set(rule) <= {"id", "description", "regex", "tags"}
                and all(isinstance(rule.get(k), str) for k in ("id", "description", "regex"))
                and RULE_ID.fullmatch(rule["id"]) and isinstance(rule.get("tags", []), list)
                and all(isinstance(x, str) for x in rule.get("tags", [])), "INTEGRATED_CONFIG_RULE")


def stage_input(stage, files, dirs, config, binary):
    stage.mkdir(mode=0o755)
    shutil.copyfile(binary, stage / "gitleaks")
    (stage / "gitleaks").chmod(0o555)
    binary_ok(stage / "gitleaks")
    if config is not None:
        target = stage / "input"
        target.mkdir(mode=0o755)
        for rel in sorted(dirs):
            (target / rel).mkdir(mode=0o755)
        for rel, content in files.items():
            path = target / rel
            path.write_bytes(content)
            path.chmod(0o444)
        (stage / "config.toml").write_bytes(config)
        (stage / "config.toml").chmod(0o444)


# Fixed in-container launcher, no caller-provided code or arguments.
LAUNCH = (
    "import hashlib,os,sys;"
    "p='/stage/gitleaks';"
    "assert hashlib.sha256(open(p,'rb').read()).hexdigest()=="
    + repr(BINARY_SHA) + ";"
    "os.execv(p,[p,'version'] if sys.argv[1]=='version' else "
    "[p,'detect','--source','.','--report-format','json','--report-path','-',"
    "'--exit-code','10','--config','/stage/config.toml','--no-git','--redact=100','--max-archive-depth','0'])"
)


def docker_args(name, stage, version):
    return ["create", "--name", name, "--pull=never", "--platform=linux/amd64",
            "--log-driver=none", "--network=none", "--read-only", "--cap-drop=ALL",
            "--security-opt=no-new-privileges=true", "--user=65534:65534",
            "--ipc=private", "--memory=512m", "--memory-swap=512m", "--cpus=2",
            "--pids-limit=64", "--ulimit=core=0:0",
            "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=32m,mode=1777",
            "--env=HOME=/tmp", "--env=GOMAXPROCS=2", "--env=CI=true",
            "--mount", f"type=bind,source={stage},target=/stage,readonly",
            "--workdir", "/stage" if version else "/stage/input",
            "--entrypoint=/usr/local/bin/python3", IMAGE, "-I", "-B", "-c", LAUNCH,
            "version" if version else "scan"]


def invoke(args, home, timeout):
    env = {"PATH": "/usr/bin:/bin", "HOME": str(home), "LANG": "C", "LC_ALL": "C",
           "DOCKER_CONFIG": str(home / "docker-config")}
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        result = subprocess.run(["/usr/bin/prlimit", f"--fsize={MAX_OUTPUT}:{MAX_OUTPUT}", "--",
                                 *DOCKER, *args], cwd=home, env=env, stdin=subprocess.DEVNULL,
                                stdout=out, stderr=err, timeout=timeout, check=False)
        out.seek(0)
        raw = out.read(MAX_OUTPUT + 1)
        require(len(raw) < MAX_OUTPUT and err.tell() < MAX_OUTPUT, "INTEGRATED_OUTPUT_LIMIT")
        return result.returncode, raw


def run_container(stage, home, version):
    name = "tessera-nvidia-gitleaks-" + uuid.uuid4().hex
    started = time.monotonic()
    created = False
    try:
        rc, _ = invoke(docker_args(name, stage, version), home, 15)
        require(rc == 0, "INTEGRATED_CREATE")
        created = True
        remaining = DEADLINE - (time.monotonic() - started)
        require(remaining > 0, "INTEGRATED_TIMEOUT")
        return invoke(["start", "--attach", name], home, remaining)
    finally:
        rc, _ = invoke(["rm", "--force", name], home, 10)
        # A failed create may never have produced a container. Verify absence
        # independently rather than interpreting arbitrary daemon error text.
        if rc != 0:
            absent_rc, listing = invoke(["ps", "-a", "--filter", "name=^/" + name + "$",
                                         "--format", "{{.Names}}"], home, 5)
            require(not created and absent_rc == 0 and not listing.strip(), "INTEGRATED_CLEANUP")


def sanitize(rc, raw, files):
    require(rc in (0, 10) and len(raw) < MAX_OUTPUT, "INTEGRATED_EXIT")
    rows = json.loads(raw) if raw.strip() else []
    if rows is None:
        rows = []
    require(isinstance(rows, list) and len(rows) <= 10000 and bool(rows) == (rc == 10),
            "INTEGRATED_REPORT")
    clean = []
    for row in rows:
        require(isinstance(row, dict), "INTEGRATED_ROW")
        rule, description, filename, line, tags = (row.get(k) for k in
            ("RuleID", "Description", "File", "StartLine", "Tags"))
        require(isinstance(rule, str) and RULE_ID.fullmatch(rule)
                and isinstance(description, str) and 0 < len(description) <= 1024
                and isinstance(filename, str) and len(filename) <= 4096
                and row.get("Secret") == "REDACTED"
                and type(line) is int and line >= 1
                and (tags is None or isinstance(tags, list) and len(tags) <= 64
                     and all(isinstance(x, str) and len(x) <= 128 for x in tags)), "INTEGRATED_ROW")
        rel = filename[2:] if filename.startswith("./") else filename
        require(rel in files and line <= max(1, len(files[rel].splitlines())), "INTEGRATED_FINDING_PATH")
        clean.append({"RuleID": rule, "Description": description, "File": filename,
                      "StartLine": line, "Tags": tags or [], "Secret": "REDACTED"})
    return json.dumps(clean, ensure_ascii=True).encode("ascii") + b"\n"


def accept(args, cwd, root, binary):
    require(sys.platform == "linux" and os.getuid() != 0, "INTEGRATED_RUNNER")
    config_path = arguments(args, cwd, root)
    binary_ok(binary)
    version = config_path is None
    files, dirs = ({}, set()) if version else snapshot(cwd)
    config = None if version else read_file(config_path, MAX_CONFIG)
    if config is not None:
        config_ok(config)
    with tempfile.TemporaryDirectory(prefix="tessera-integrated-", dir=root) as folder:
        home = pathlib.Path(folder)
        stage = home / "stage"
        stage_input(stage, files, dirs, config, binary)
        rc, raw = run_container(stage, home, version)
        binary_ok(stage / "gitleaks")
        if not version:
            require(snapshot(stage / "input") == (files, dirs)
                    and read_file(stage / "config.toml", MAX_CONFIG) == config
                    and snapshot(cwd) == (files, dirs)
                    and read_file(config_path, MAX_CONFIG) == config, "INTEGRATED_MUTATED")
            raw = sanitize(rc, raw, files)
        else:
            require(rc == 0 and raw.strip() == b"8.30.1", "INTEGRATED_VERSION")
    binary_ok(binary)
    return rc, raw


def main(args, root, binary):
    try:
        rc, raw = accept(args, pathlib.Path.cwd(), pathlib.Path(root), pathlib.Path(binary))
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        print("BLOCKED: INTEGRATED_GITLEAKS_FAILED", file=sys.stderr)
        return 2
    sys.stdout.buffer.write(raw)
    return rc
