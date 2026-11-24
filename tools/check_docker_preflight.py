#!/usr/bin/env python3
"""Synthetic Docker isolation preflight for the trusted disposable Linux CI runner."""
from __future__ import annotations
import json
import os
import pathlib
import socket
import subprocess
import sys
import tempfile
import uuid

IMAGE = "docker.io/library/python@sha256:48d884813cf44e927cf64c5529dd630dd3b18338c6dc727991eef9b71e934a20"
DOCKER = ["/usr/bin/docker", "--host", "unix:///var/run/docker.sock"]
PROBE = r'''
import errno, json, os, pathlib, socket, sys
def read(path):
    return pathlib.Path(path).read_text().strip()
status = dict(line.split(":", 1) for line in read("/proc/self/status").splitlines() if ":" in line)
root = next(line.split() for line in read("/proc/self/mountinfo").splitlines() if line.split()[4] == "/")
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.settimeout(1)
    blocked = s.connect_ex(("127.0.0.1", int(sys.argv[1]))) in (errno.ECONNREFUSED, errno.ENETUNREACH, errno.EHOSTUNREACH)
p = pathlib.Path("/tmp/probe")
p.write_text("synthetic")
print(json.dumps({"uid": os.getuid(), "pid": os.getpid(), "net": os.readlink("/proc/self/ns/net"),
    "interfaces": sorted(n for _, n in socket.if_nameindex()), "blocked": blocked,
    "root_readonly": "ro" in root[5].split(","), "tmp_writable": p.read_text() == "synthetic",
    "host_file_hidden": not pathlib.Path(sys.argv[2]).exists(),
    "docker_socket_hidden": not pathlib.Path("/var/run/docker.sock").exists(),
    "cap_effective": int(status["CapEff"].strip(), 16), "no_new_privs": int(status["NoNewPrivs"]),
    "seccomp": int(status["Seccomp"]),
    "memory": int(read("/sys/fs/cgroup/memory.max")),
    "swap": int(read("/sys/fs/cgroup/memory.swap.max")),
    "pids": int(read("/sys/fs/cgroup/pids.max")),
    "cpu": [int(x) for x in read("/sys/fs/cgroup/cpu.max").split()]}))
'''


def create_args(name, code, *args):
    return ["create", "--name", name, "--pull=never", "--platform=linux/amd64",
            "--network=none", "--read-only", "--cap-drop=ALL",
            "--security-opt=no-new-privileges=true", "--user=65534:65534",
            "--ipc=private", "--memory=128m", "--memory-swap=128m", "--cpus=0.5",
            "--pids-limit=32", "--ulimit=core=0:0",
            "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=16m,mode=1777",
            "--entrypoint=/usr/local/bin/python3", IMAGE, "-I", "-c", code, *args]


def invoke(args, home, timeout=30):
    env = {"PATH": "/usr/bin:/bin", "HOME": str(home), "LANG": "C", "LC_ALL": "C",
           "DOCKER_CONFIG": str(home / "docker-config")}
    # Only synthetic inputs; bound retained output, never print daemon stderr.
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        result = subprocess.run([*DOCKER, *args], env=env, cwd=home, stdin=subprocess.DEVNULL,
                                stdout=out, stderr=err, timeout=timeout, check=False)
        out.seek(0)
        data = out.read(8193)
        if len(data) > 8192:
            raise RuntimeError("DOCKER_PREFLIGHT_OUTPUT_LIMIT")
        return result.returncode, data


def required(args, home, code, timeout=30):
    rc, data = invoke(args, home, timeout)
    if rc != 0:
        raise RuntimeError(code)
    return data


def validate(report, parent_net):
    expected = {"uid": 65534, "pid": 1, "interfaces": ["lo"], "blocked": True,
                "root_readonly": True, "tmp_writable": True, "host_file_hidden": True,
                "docker_socket_hidden": True, "cap_effective": 0, "no_new_privs": 1,
                "seccomp": 2, "memory": 134217728, "swap": 0, "pids": 32}
    if not isinstance(report, dict) or any(report.get(k) != v for k, v in expected.items()):
        raise RuntimeError("DOCKER_PREFLIGHT_CONTROL_FAILED")
    net, cpu = report.get("net"), report.get("cpu")
    if (not isinstance(net, str) or not net.startswith("net:[") or net == parent_net
            or not isinstance(cpu, list) or len(cpu) != 2
            or not all(type(x) is int and x > 0 for x in cpu) or cpu[0] * 2 != cpu[1]):
        raise RuntimeError("DOCKER_PREFLIGHT_CONTROL_FAILED")


def probe(home, port, sentinel):
    name = "tessera-preflight-" + uuid.uuid4().hex
    required(create_args(name, PROBE, str(port), str(sentinel)), home, "DOCKER_PREFLIGHT_CREATE_FAILED")
    try:
        raw = required(["start", "--attach", name], home, "DOCKER_PREFLIGHT_START_FAILED", 20)
        validate(json.loads(raw), os.readlink("/proc/self/ns/net"))
    finally:
        required(["rm", "--force", name], home, "DOCKER_PREFLIGHT_CLEANUP_FAILED")


def main():
    if sys.platform != "linux" or os.getuid() == 0:
        raise RuntimeError("DOCKER_PREFLIGHT_RUNNER_SCOPE")
    with tempfile.TemporaryDirectory(prefix="tessera-docker-") as folder:
        home = pathlib.Path(folder)
        sentinel = home / "host-only"
        sentinel.write_text("synthetic")
        required(["pull", "--platform=linux/amd64", IMAGE], home, "DOCKER_PREFLIGHT_PULL_FAILED", 120)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            port = listener.getsockname()[1]
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                conn, _ = listener.accept()
                conn.close()
            probe(home, port, sentinel)
        if sentinel.read_text() != "synthetic":
            raise RuntimeError("DOCKER_PREFLIGHT_HOST_MUTATED")
    print("DOCKER_PREFLIGHT_PASS: " + json.dumps({"scope": "SYNTHETIC_LINUX_DOCKER_ONLY",
          "image": IMAGE, "network": "PASS", "pid": "PASS", "read_only_root": "PASS",
          "host_sentinel_hidden": "PASS", "nonroot": "PASS", "cgroup_configuration": "PASS",
          "no_new_privileges": "PASS", "seccomp": "PASS", "scanner_execution": "NOT_VERIFIED",
          "resource_exhaustion": "NOT_VERIFIED", "descendant_timeout": "NOT_VERIFIED"}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        known = {"DOCKER_PREFLIGHT_OUTPUT_LIMIT", "DOCKER_PREFLIGHT_CONTROL_FAILED",
                 "DOCKER_PREFLIGHT_CREATE_FAILED", "DOCKER_PREFLIGHT_START_FAILED",
                 "DOCKER_PREFLIGHT_CLEANUP_FAILED", "DOCKER_PREFLIGHT_PULL_FAILED",
                 "DOCKER_PREFLIGHT_RUNNER_SCOPE", "DOCKER_PREFLIGHT_HOST_MUTATED"}
        code = str(exc) if isinstance(exc, RuntimeError) and str(exc) in known else "DOCKER_PREFLIGHT_FAILED"
        print("BLOCKED: " + code, file=sys.stderr)
        sys.exit(1)
