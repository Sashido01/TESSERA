#!/usr/bin/env python3
"""Synthetic Linux namespace/rlimit preflight; not a scanner sandbox."""
from __future__ import annotations
import json
import os
import pathlib
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time

LIMITS = {"CPU": 10, "AS": 1073741824, "FSIZE": 16777216, "NOFILE": 256, "CORE": 0}
PROBE = r'''
import errno, json, os, resource, socket, sys
limits = {key: list(resource.getrlimit(getattr(resource, "RLIMIT_" + key)))
          for key in ("CPU", "AS", "FSIZE", "NOFILE", "CORE")}
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.settimeout(1)
    rc = sock.connect_ex(("127.0.0.1", int(sys.argv[1])))
print(json.dumps({"pid": os.getpid(), "network": os.readlink("/proc/self/ns/net"),
                  "blocked": rc in (errno.ENETUNREACH, errno.EHOSTUNREACH, errno.ECONNREFUSED),
                  "limits": limits}))
'''
TIMEOUT_PROBE = r'''
import os, pathlib, time
child = os.fork()
if child == 0:
    os.setsid()
    pathlib.Path("ready").write_text("forked")
    time.sleep(1.5)
    pathlib.Path("escaped").write_text("child survived")
    os._exit(0)
time.sleep(10)
'''


def command(code, *args):
    return ["/usr/bin/unshare", "--user", "--map-root-user", "--net", "--pid", "--fork",
            "--kill-child=SIGKILL", "--", "/usr/bin/prlimit",
            *[f"--{key.lower()}={val}:{val}" for key, val in LIMITS.items()],
            "--", str(pathlib.Path(sys.executable).resolve()), "-I", "-c", code, *args]


def diagnostic_code(stderr):
    # Fixed classifications only; never log raw diagnostics, filenames or env.
    for line in stderr.splitlines():
        if line.startswith(b"unshare:"):
            if b"Operation not permitted" in line or b"Permission denied" in line:
                return "NAMESPACE_UNSHARE_PERMISSION_DENIED"
            return "NAMESPACE_UNSHARE_FAILED"
        if line.startswith(b"prlimit:"):
            if b"Operation not permitted" in line or b"Permission denied" in line:
                return "NAMESPACE_PRLIMIT_PERMISSION_DENIED"
            return "NAMESPACE_PRLIMIT_FAILED"
    return "NAMESPACE_EXECUTION_FAILED"


def runner_policy():
    values = {}
    for name in ("kernel/unprivileged_userns_clone", "kernel/apparmor_restrict_unprivileged_userns",
                 "user/max_user_namespaces", "user/max_net_namespaces", "user/max_pid_namespaces"):
        try:
            raw = (pathlib.Path("/proc/sys") / name).read_text(encoding="ascii").strip()
            values[name] = int(raw) if re.fullmatch(r"[0-9]{1,20}", raw) else "UNKNOWN"
        except (OSError, UnicodeError, ValueError):
            values[name] = "UNAVAILABLE"
    return values


def run_control(argv, folder, timeout, *, ready=None):
    env = {"PATH": "/usr/bin:/bin", "HOME": str(folder), "LANG": "C", "LC_ALL": "C"}
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        with subprocess.Popen(argv, cwd=folder, env=env, stdin=subprocess.DEVNULL,
                              stdout=stdout, stderr=stderr, close_fds=True, start_new_session=True) as proc:
            try:
                if ready is not None:
                    deadline = time.monotonic() + 5
                    while not ready.is_file() and proc.poll() is None and time.monotonic() < deadline:
                        time.sleep(0.02)
                    if not ready.is_file():
                        if proc.poll() not in (None, 0):
                            stderr.seek(0)
                            raise RuntimeError(diagnostic_code(stderr.read(4096)))
                        raise RuntimeError("NAMESPACE_CHILD_NOT_READY")
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=5)
                return None
            finally:
                if proc.poll() is None:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait(timeout=5)
            if proc.returncode != 0:
                stderr.seek(0)
                raise RuntimeError(diagnostic_code(stderr.read(4096)))
        stdout.seek(0)
        raw = stdout.read(4097)
        if len(raw) > 4096:
            raise RuntimeError("NAMESPACE_REPORT_LIMIT")
        return json.loads(raw)


def validate(report, parent_net):
    if (not isinstance(report, dict) or report.get("pid") != 1
            or not isinstance(report.get("network"), str)
            or not re.fullmatch(r"net:\[\d+\]", report["network"]) or report["network"] == parent_net
            or report.get("blocked") is not True
            or report.get("limits") != {k: [v, v] for k, v in LIMITS.items()}):
        raise RuntimeError("NAMESPACE_CONTROL_FAILED")


def main():
    if sys.platform != "linux":
        raise RuntimeError("NAMESPACE_LINUX_REQUIRED")
    print("NAMESPACE_RUNNER_POLICY: " + json.dumps(runner_policy(), sort_keys=True), flush=True)
    with tempfile.TemporaryDirectory(prefix="tessera-namespace-") as tmp:
        folder = pathlib.Path(tmp)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            port = listener.getsockname()[1]
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                conn, _ = listener.accept()
                conn.close()
            report = run_control(command(PROBE, str(port)), folder, 5)
            validate(report, os.readlink("/proc/self/ns/net"))
        if run_control(command(TIMEOUT_PROBE), folder, 0.2, ready=folder / "ready") is not None:
            raise RuntimeError("NAMESPACE_TIMEOUT_CONTROL_FAILED")
        time.sleep(1.7)
        if (folder / "escaped").exists():
            raise RuntimeError("NAMESPACE_DESCENDANT_SURVIVED")
    print("NAMESPACE_PREFLIGHT_PASS: " + json.dumps({"scope": "SYNTHETIC_LINUX_ONLY",
          "ipv4_loopback": "PASS", "pid": "PASS", "rlimits": LIMITS,
          "timeout_descendant": "PASS", "filesystem": "NOT_VERIFIED",
          "aggregate_resources": "NOT_VERIFIED", "scanner_execution": "NOT_VERIFIED"}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        known = {"NAMESPACE_LINUX_REQUIRED", "NAMESPACE_CHILD_NOT_READY",
                 "NAMESPACE_EXECUTION_FAILED", "NAMESPACE_REPORT_LIMIT",
                 "NAMESPACE_CONTROL_FAILED", "NAMESPACE_TIMEOUT_CONTROL_FAILED",
                 "NAMESPACE_DESCENDANT_SURVIVED", "NAMESPACE_UNSHARE_PERMISSION_DENIED",
                 "NAMESPACE_UNSHARE_FAILED", "NAMESPACE_PRLIMIT_PERMISSION_DENIED",
                 "NAMESPACE_PRLIMIT_FAILED"}
        code = str(exc) if isinstance(exc, RuntimeError) and str(exc) in known else "NAMESPACE_PREFLIGHT_FAILED"
        print("BLOCKED: " + code, file=sys.stderr)
        sys.exit(1)
