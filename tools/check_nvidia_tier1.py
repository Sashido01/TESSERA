#!/usr/bin/env python3
"""T12.01: bounded NVIDIA SkillEvaluator Tier 1 schema/quality acceptance.

Advisory findings are reported, not silently converted to a skill PASS.
Never execute skill content, generic validate, Tier 2/3 or LLM stages.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

from check_official_local_install import fixture_env, tree_fingerprint, InstallCheckError

VERSION = "1.2.0"
CHECKS = ("Schema & Repository Governance", "QUALITY")
REPORT = "skillevaluator-tier1.json"
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
MAX_REPORT = 4 * 1024 * 1024


def require(ok, code):
    if not ok:
        raise InstallCheckError(code)


def checked_report(report, returncode):
    require(isinstance(report, dict) and report.get("version") == VERSION,
            "NVIDIA_REPORT_VERSION_INVALID")
    require(report.get("workflow") == {
        "tier": 1, "stages": {
            "validation": {"status": "passed" if returncode == 0 else "failed"},
            "llm": {"status": "skipped", "reason": "LLM checks disabled by --no-llm."},
        }
    }, "NVIDIA_REPORT_SCOPE_INVALID")
    rows = report.get("results")
    require(isinstance(rows, list) and len(rows) == 2 and all(isinstance(r, dict) for r in rows),
            "NVIDIA_REPORT_CHECKS_INVALID")
    require({r.get("validator") for r in rows} == set(CHECKS),
            "NVIDIA_REPORT_CHECKS_INVALID")
    require(report.get("incomplete_scans") == [] and report.get("total_skipped") == 0,
            "NVIDIA_REPORT_INCOMPLETE")
    states = {}
    for row in rows:
        status = row.get("status")
        require(status in ("passed", "failed") and row.get("skipped") is False
                and row.get("incomplete_scans") == [] and isinstance(row.get("passed"), bool)
                and row.get("passed") == (status == "passed"),
                "NVIDIA_CHECK_INCOMPLETE")
        states[row["validator"]] = status
    passed = all(s == "passed" for s in states.values())
    require(returncode in (0, 1) and (returncode == 0) == passed
            and report.get("overall_passed") is passed
            and report.get("overall_status") == ("passed" if passed else "failed"),
            "NVIDIA_REPORT_EXIT_MISMATCH")
    quality = next(r.get("quality") for r in rows if r["validator"] == CHECKS[1])
    require(isinstance(quality, dict), "NVIDIA_SCORE_MISSING")
    score = quality.get("overall_score")
    require(type(score) in (int, float) and math.isfinite(score) and 0 <= score <= 100,
            "NVIDIA_SCORE_INVALID")
    findings = []
    for row in rows:
        items = row.get("findings")
        require(isinstance(items, list) and len(items) <= 2000, "NVIDIA_FINDINGS_INVALID")
        for item in items:
            require(isinstance(item, dict), "NVIDIA_FINDINGS_INVALID")
            # Only bounded identifiers, never raw finding text, paths or content.
            check = item.get("check") or item.get("check_name")
            severity = item.get("severity")
            if isinstance(check, str) and re.fullmatch(r"[a-zA-Z0-9_.-]{1,100}", check) and isinstance(severity, str) and severity.lower() in ("critical", "high", "medium", "low", "info"):
                findings.append({"check": check, "severity": severity.lower()})
    return {"schema": states[CHECKS[0]].upper(), "quality": states[CHECKS[1]].upper(),
            "quality_score": score, "findings": findings,
            "focused_verdict": "PASS" if passed else "FAIL"}


def accept(repo, cli):
    repo = repo.resolve(strict=True)
    cli = cli.resolve(strict=True)
    require(cli.is_file() and os.access(cli, os.X_OK), "NVIDIA_CLI_MISSING")
    original = repo / "skills"
    before = tree_fingerprint(original)
    with tempfile.TemporaryDirectory(prefix="tessera-nvidia-tier1-") as folder:
        temp = pathlib.Path(folder)
        env = fixture_env(temp)
        env.update({"PATH": str(cli.parent) + os.pathsep + env["PATH"],
                    "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONSAFEPATH": "1", "CI": "true", "PIP_NO_INDEX": "1",
                    "UV_OFFLINE": "1"})
        def run(*args):
            return subprocess.run([str(cli), *args], cwd=temp, env=env,
                                  stdin=subprocess.DEVNULL, capture_output=True,
                                  encoding="utf-8", timeout=120, check=False)
        ver = run("--version")
        require(ver.returncode == 0 and ver.stdout.strip() == "skillevaluator, version " + VERSION,
                "NVIDIA_CLI_VERSION_INVALID")
        source = temp / "skills"
        shutil.copytree(original, source)
        require(tree_fingerprint(source) == before, "NVIDIA_SNAPSHOT_MISMATCH")
        children = sorted(source.iterdir())
        require(0 < len(children) <= 100, "NVIDIA_SKILL_COUNT_INVALID")
        def evaluate(skill, out):
            require(skill.is_dir() and not skill.is_symlink()
                    and NAME.fullmatch(skill.name) and (skill / "SKILL.md").is_file(),
                    "NVIDIA_SKILL_INVALID")
            result = run("tier1", str(skill), "--no-llm", "--checks", "schema,quality",
                         "--min-score", "70", "-r", "json", "-o", str(out))
            report = out / REPORT
            require(report.is_file() and not report.is_symlink()
                    and report.stat().st_size <= MAX_REPORT, "NVIDIA_REPORT_MISSING")
            return checked_report(json.loads(report.read_text(encoding="utf-8")), result.returncode)

        results = {}
        for skill in children:
            results[skill.name] = evaluate(skill, temp / "reports" / skill.name)
        require(tree_fingerprint(source) == before and tree_fingerprint(original) == before,
                "NVIDIA_SOURCE_MUTATED")
        # A real malformed fixture must fail schema; a clean launch alone is
        # not evidence the evaluator detected invalid input.
        negative = temp / "negative" / "fixture-invalid"
        negative.mkdir(parents=True)
        (negative / "SKILL.md").write_text("---\nname: wrong-name\n---\n\nFixture only.\n",
                                           encoding="utf-8")
        bad = evaluate(negative, temp / "negative-report")
        require(bad["schema"] == "FAILED" and bad["focused_verdict"] == "FAIL",
                "NVIDIA_NEGATIVE_NOT_DETECTED")
    return {"execution": "PASS", "version": VERSION, "checks": ["schema", "quality"],
            "min_score": 70, "policy": "ADVISORY_FINDINGS",
            "skills": results, "negative_schema": "PASS", "llm": "DISABLED",
            "full_tier1": "NOT_VERIFIED", "external_scanners": "NOT_RUN",
            "tier2": "NOT_RUN", "tier3": "NOT_RUN", "agent_activation": "NOT_VERIFIED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=pathlib.Path, required=True)
    parser.add_argument("--cli", type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        result = accept(args.repo, args.cli)
    except (InstallCheckError, OSError, UnicodeError, ValueError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + (str(exc) if isinstance(exc, InstallCheckError)
                             else "NVIDIA_RUNTIME_FAILED"), file=sys.stderr)
        return 1
    print("NVIDIA_TIER1_FOCUSED_EXECUTION_PASS: " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
