#!/usr/bin/env python3
"""Path-constrained rules of pinned Gitleaks 8.30.1, current and reachable history."""
from __future__ import annotations

import argparse
import collections
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time

from check_gitleaks_history import OID, MAX_OBJECTS, git, inventory as history_inventory, checked_blob
from check_gitleaks_review import VERSION, FINDINGS_EXIT, inventory, parse_scan
from check_nvidia_tier1 import require
from check_official_local_install import InstallCheckError, fixture_env

# Exact path predicates from v8.30.1 config/gitleaks.toml, not arbitrary custom rules.
RULES = (
    ("freemius-secret-key", re.compile(r"\.php$", re.I), "input.php"),
    ("hashicorp-tf-password", re.compile(r"\.(?:tf|hcl)$", re.I), "input.tf"),
    ("kubernetes-secret-yaml", re.compile(r"\.ya?ml$", re.I), "input.yml"),
    ("nuget-config-password", re.compile(r"nuget\.config$", re.I), "nuget.config"),
    ("pkcs12-file", re.compile(r"(?:^|/)[^/]+\.p(?:12|fx)$", re.I), "input.p12"),
)
CANONICAL = {name: filename for name, _, filename in RULES}


def matching(path):
    return [rule for rule, regex, _ in RULES if regex.search(path)]


def tree_pairs(raw, blobs):
    result = set()
    require(not raw or raw.endswith(b"\0"), "PATH_TREE_INVALID")
    for record in raw.split(b"\0")[:-1]:
        head, sep, name = record.partition(b"\t")
        require(sep and len(head.split()) == 3, "PATH_TREE_INVALID")
        mode, kind, oid = head.decode("ascii").split()
        path = name.decode("utf-8", errors="strict")
        require(OID.fullmatch(oid) and kind in {"blob", "commit"}, "PATH_TREE_INVALID")
        for rule in matching(path):
            require(kind == "blob" and mode in {"100644", "100755"} and oid in blobs,
                    "PATH_TARGET_UNSUPPORTED")
            result.add((rule, oid))
    return result


def historical_pairs(repo, env, blobs):
    commits = git(repo, env, "rev-list", "--all", "HEAD").decode("ascii").splitlines()
    require(0 < len(commits) <= min(MAX_OBJECTS, 1000)
            and len(set(commits)) == len(commits) and all(OID.fullmatch(c) for c in commits),
            "PATH_COMMIT_INVENTORY_INVALID")
    pairs = set()
    for commit in commits:
        pairs.update(tree_pairs(git(repo, env, "ls-tree", "-r", "-z", "--full-tree", commit),
                                blobs))
        require(len(pairs) <= 2048, "PATH_PAIR_LIMIT")
    return pairs, len(commits)


def scan_rule(cli, temp, env, rule, data):
    # A fixed canonical filename satisfies the pinned predicate without the
    # upstream archive-like filename skipping bug; no real filename is logged.
    require(rule in CANONICAL, "PATH_RULE_INVALID")
    with tempfile.TemporaryDirectory(prefix="path-", dir=temp) as folder:
        root = pathlib.Path(folder)
        path = root / CANONICAL[rule]
        path.write_bytes(data)
        result = subprocess.run(
            [str(cli), "dir", str(path), "--enable-rule", rule, "--no-banner",
             "--no-color", "--log-level", "info", "--redact=100",
             "--ignore-gitleaks-allow", "--exit-code", str(FINDINGS_EXIT),
             "--report-format", "json", "--report-path", "-", "--timeout", "15"],
            cwd=temp, env=env, stdin=subprocess.DEVNULL, capture_output=True,
            timeout=20, check=False)
        counts = parse_scan(result.stdout, result.stderr, result.returncode, len(data))
        require(set(counts) <= {rule}, "PATH_UNEXPECTED_RULE")
        return counts[rule]


def fixtures(cli, temp, env):
    # Fabricated test-only data; never authentic credentials.
    values = {
        "freemius-secret-key": b"'secret_key' => 'sk_" + b"x7p4" * 7 + b"z'\n",
        "hashicorp-tf-password": b'password = "' + b"F7a3X2q6P5m8" + b'"\n',
        "kubernetes-secret-yaml": b"kind: Secret\ndata:\n  fixture: " + b"c3ludGhldGlj" + b"\n",
        "nuget-config-password": b'<add key="Password" value="' + b"fixture7X2m5Q" + b'" />\n',
        "pkcs12-file": b"synthetic filename-only fixture\n",
    }
    for rule, data in values.items():
        require(scan_rule(cli, temp, env, rule, data) > 0, "PATH_NEGATIVE_NOT_DETECTED")


def accept(repo, cli):
    repo, cli = repo.resolve(strict=True), cli.resolve(strict=True)
    require(cli.is_file() and os.access(cli, os.X_OK), "PATH_CLI_MISSING")
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="tessera-gitleaks-paths-") as folder:
        temp = pathlib.Path(folder)
        env = fixture_env(temp)
        env.update({"PATH": str(cli.parent) + os.pathsep + env["PATH"],
                    "GIT_NO_LAZY_FETCH": "1", "CI": "true"})
        version = subprocess.run([str(cli), "version"], cwd=temp, env=env,
                                 stdin=subprocess.DEVNULL, capture_output=True, timeout=10, check=False)
        require(version.returncode == 0 and version.stdout.strip() == VERSION.encode(),
                "PATH_VERSION_MISMATCH")
        fixtures(cli, temp, env)
        current = inventory(repo)
        blobs = history_inventory(repo, env)
        pairs, commits = historical_pairs(repo, env, blobs)
        counters = collections.Counter()
        coverage = collections.Counter()
        for name, data in current.items():
            for rule in matching(name):
                require(time.monotonic() - started < 120, "PATH_TIMEOUT")
                coverage["current", rule] += 1
                counters["current", rule] += scan_rule(cli, temp, env, rule, data)
        for rule, oid in sorted(pairs):
            require(time.monotonic() - started < 120, "PATH_TIMEOUT")
            coverage["history", rule] += 1
            counters["history", rule] += scan_rule(cli, temp, env, rule,
                                                   checked_blob(repo, env, oid, blobs[oid]))
        require(inventory(repo) == current and history_inventory(repo, env) == blobs
                and historical_pairs(repo, env, blobs) == (pairs, commits), "PATH_SOURCE_MUTATED")
    return {"execution": "PASS", "scanner": "gitleaks", "version": VERSION,
            "scope": "FIVE_PINNED_PATH_CONSTRAINED_RULES",
            "history_commits": commits, "negative_fixtures": len(RULES),
            "results": [{"scope": scope, "rule": rule, "targets": coverage[scope, rule],
                         "findings": counters[scope, rule]}
                        for scope in ("current", "history") for rule, _, _ in RULES],
            "policy": "ADVISORY_FINDINGS", "elapsed_seconds": round(time.monotonic() - started, 2),
            "path_allowlist_semantics": "CONSERVATIVE_CANONICAL_PATHS",
            "unreachable_objects": "NOT_SCANNED", "remote_unfetched_refs": "NOT_SCANNED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=pathlib.Path, required=True)
    parser.add_argument("--cli", type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        result = accept(args.repo, args.cli)
    except (InstallCheckError, OSError, UnicodeError, ValueError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + (str(exc) if isinstance(exc, InstallCheckError)
                              else "PATH_RUNTIME_FAILED"), file=sys.stderr)
        return 1
    print("GITLEAKS_PATH_EXECUTION_PASS: " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
