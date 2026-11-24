#!/usr/bin/env python3
"""T12.02.01: local static review and versioned harness profiles only.

No generic validate, model calls, scanner auto-install, external CVE audit,
or agent execution. Raw reports remain in an ephemeral isolated directory.
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
import time

from check_nvidia_tier1 import (
    VERSION, REPORT, MAX_REPORT, NAME, checked_report, require,
)
from check_official_local_install import fixture_env, tree_fingerprint, InstallCheckError

STATIC_NAMES = ("PII Scan", "License Compliance", "Unicode Smuggling Detection", "SCRIPT_LINT")
ROOTS = {"codex": ".agents/skills", "claude-code": ".claude/skills",
         "copilot-cli": ".github/skills", "hermes": ".hermes/skills",
         "openclaw": "skills", "opencode": ".opencode/skills"}
DIMENSIONS = {"correctness": .35, "discoverability": .25, "reliability": .25, "efficiency": .15}
SEVERITIES = {"critical", "high", "medium", "low", "info"}
REASONS = (
    ("Missing recommended section: '## Instructions'", "EN_INSTRUCTIONS_HEADING"),
    ("Missing recommended section: '## Examples'", "EN_EXAMPLES_HEADING"),
    ("Unexpected 'README.en.md'", "BILINGUAL_README"),
    ("Unexpected 'tests'", "ROOT_TESTS_DIRECTORY"),
    ("No documented scripts in table format", "SCRIPT_TABLE_MISSING"),
    ("Instructions don't mention 'run_script'", "NONSTANDARD_RUN_SCRIPT_HEURISTIC"),
    ("No examples provided", "EXAMPLE_FORMAT_HEURISTIC"),
    ("SKILL_SPEC recommended field missing: 'metadata.author'", "AUTHOR_METADATA_MISSING"),
    ("SKILL_SPEC recommended field missing: 'metadata.tags'", "TAGS_METADATA_MISSING"),
    ("Description very long", "DESCRIPTION_LENGTH"),
    ("Description doesn't mention WHEN", "EN_DESCRIPTION_TRIGGER"),
    ("No '## Purpose' section", "EN_PURPOSE_HEADING"),
    ("No mention of error handling or validation", "EN_ERROR_TERMS"),
    ("No prerequisites/requirements documented", "PREREQUISITES_HEADING_MISSING"),
    ("No limitations documented", "LIMITATIONS_HEADING_MISSING"),
    ("No troubleshooting section documented", "TROUBLESHOOTING_HEADING_MISSING"),
    ("Deeply nested references", "NESTED_REFERENCE_LINK"),
    ("Large skill", "ESTIMATED_TOKEN_BUDGET"),
)


def reason(item):
    check = item.get("check") or item.get("check_name")
    message = item.get("message")
    if isinstance(message, str):
        for prefix, code in REASONS:
            if message.startswith(prefix):
                return code
    return {"author_missing": "AUTHOR_METADATA_MISSING",
            "description_trigger": "SCHEMA_DESCRIPTION_TRIGGER",
            "unexpected_file": "UNEXPECTED_ROOT_ENTRY"}.get(check, "UNCLASSIFIED")


def sanitized_findings(rows, *, explain=False):
    found = []
    for row in rows:
        items = row.get("findings")
        require(isinstance(items, list) and len(items) <= 2000, "NVIDIA_REVIEW_FINDINGS_INVALID")
        for item in items:
            require(isinstance(item, dict), "NVIDIA_REVIEW_FINDINGS_INVALID")
            check = item.get("check") or item.get("check_name")
            severity = item.get("severity")
            require(isinstance(severity, str) and severity.lower() in SEVERITIES,
                    "NVIDIA_REVIEW_SEVERITY_INVALID")
            # Never log raw finding messages, matched values, source lines or local paths.
            if not isinstance(check, str) or not re.fullmatch(r"[a-zA-Z0-9_.-]{1,100}", check):
                check = "OTHER_CHECK"
            entry = {"check": check, "severity": severity.lower()}
            if explain:
                entry["reason"] = reason(item)
            found.append(entry)
    return found


def quality_review(report, rc):
    base = checked_report(report, rc)
    quality = next(row["quality"] for row in report["results"] if row["validator"] == "QUALITY")
    dims = quality.get("dimensions")
    require(isinstance(dims, dict) and set(dims) == set(DIMENSIONS), "NVIDIA_DIMENSIONS_INVALID")
    scores = {}
    for name, weight in DIMENSIONS.items():
        data = dims[name]
        score = data.get("score")
        require(type(score) in (int, float) and math.isfinite(score)
                and 0 <= score <= 100 and data.get("weight") == weight,
                "NVIDIA_DIMENSION_SCORE_INVALID")
        scores[name] = score
    computed = sum(scores[key] * DIMENSIONS[key] for key in scores)
    require(abs(computed - base["quality_score"]) <= .11, "NVIDIA_SCORE_RECONCILIATION_FAILED")
    return {"schema": base["schema"], "quality": base["quality"],
            "score": base["quality_score"], "dimensions": scores,
            "findings": sanitized_findings(report["results"], explain=True)}


def static_review(report, rc, expected=STATIC_NAMES):
    require(isinstance(report, dict) and report.get("version") == VERSION
            and rc in (0, 1), "NVIDIA_STATIC_VERSION_OR_EXIT")
    require(report.get("workflow") == {"tier": 1, "stages": {
        "validation": {"status": "passed" if rc == 0 else "failed"},
        "llm": {"status": "skipped", "reason": "LLM checks disabled by --no-llm."}}},
        "NVIDIA_STATIC_SCOPE_INVALID")
    rows = report.get("results")
    require(isinstance(rows, list) and len(rows) == len(expected)
            and all(isinstance(row, dict) for row in rows)
            and {row.get("validator") for row in rows} == set(expected),
            "NVIDIA_STATIC_CHECKS_INVALID")
    require(report.get("incomplete_scans") == [] and report.get("total_skipped") == 0,
            "NVIDIA_STATIC_INCOMPLETE")
    result = {}
    for row in rows:
        status = row.get("status")
        require(status in ("passed", "failed") and row.get("skipped") is False
                and row.get("incomplete_scans") == []
                and row.get("passed") is (status == "passed"), "NVIDIA_STATIC_INCOMPLETE")
        summary = row.get("summary")
        require(isinstance(summary, dict), "NVIDIA_STATIC_SUMMARY_INVALID")
        counts = {}
        for key in ("files_scanned", "checks_performed", "warnings", "errors"):
            value = summary.get(key)
            require(type(value) is int and 0 <= value <= 100000, "NVIDIA_STATIC_COUNT_INVALID")
            counts[key] = value
        if row["validator"] in ("PII Scan", "Unicode Smuggling Detection"):
            require(counts["files_scanned"] > 0, "NVIDIA_STATIC_NO_SCAN_COVERAGE")
        result[row["validator"]] = {"status": status.upper(), **counts,
                                    "findings": sanitized_findings([row])}
        if row["validator"] == "License Compliance":
            detail = next((d for d in row.get("success_details", [])
                           if d.get("check") == "license_compliance"), {})
            license_status = (detail.get("metadata") or {}).get("license_status")
            result[row["validator"]]["license_status"] = (
                license_status if isinstance(license_status, str)
                and re.fullmatch(r"[a-z_]{1,60}", license_status) else "UNDETERMINED")
    passed = all(row["status"] == "PASSED" for row in result.values())
    require((rc == 0) == passed and report.get("overall_passed") is passed
            and report.get("overall_status") == ("passed" if passed else "failed"),
            "NVIDIA_STATIC_EXIT_MISMATCH")
    return result


def harness_review(report, skill, name):
    require(isinstance(report, dict) and set(report) == {"harness_compatibility"},
            "NVIDIA_HARNESS_REPORT_INVALID")
    block = report["harness_compatibility"]
    require(isinstance(block, dict) and set(block) == {str(skill)},
            "NVIDIA_HARNESS_TARGET_INVALID")
    rows = block[str(skill)]
    require(isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict),
            "NVIDIA_HARNESS_ROWS_INVALID")
    row = rows[0]
    require(row.get("harness") == name and name in ROOTS
            and row.get("status") in ("loads", "degraded", "not_loaded"),
            "NVIDIA_HARNESS_STATUS_INVALID")
    version, date = row.get("verified_version"), row.get("verified_date")
    require(isinstance(version, str) and 0 < len(version) <= 100
            and re.fullmatch(r"[a-zA-Z0-9 .@()_-]+", version)
            and isinstance(date, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", date),
            "NVIDIA_HARNESS_VERSION_INVALID")
    findings = []
    require(isinstance(row.get("findings"), list) and len(row["findings"]) <= 200,
            "NVIDIA_HARNESS_FINDINGS_INVALID")
    for finding in row["findings"]:
        require(isinstance(finding, dict) and isinstance(finding.get("id"), str)
                and re.fullmatch(r"[A-Z0-9_-]{1,80}", finding["id"])
                and finding.get("effect") in ("advisory", "degraded", "not_loaded"),
                "NVIDIA_HARNESS_FINDING_INVALID")
        findings.append({"id": finding["id"], "effect": finding["effect"]})
    return {"profile_version": version, "profile_date": date,
            "status": row["status"], "findings": findings, "live_agent": "NOT_VERIFIED"}


def read_report(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= MAX_REPORT,
            "NVIDIA_REVIEW_REPORT_MISSING")
    return json.loads(path.read_text(encoding="utf-8"))


def accept(repo, cli):
    repo, cli = repo.resolve(strict=True), cli.resolve(strict=True)
    require(cli.is_file() and os.access(cli, os.X_OK), "NVIDIA_REVIEW_CLI_MISSING")
    original = repo / "skills"
    before = tree_fingerprint(original)
    config = repo / "tools/nvidia-quality-ru.json"
    require(config.is_file() and not config.is_symlink(), "NVIDIA_LOCALE_CONFIG_MISSING")
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="tessera-nvidia-review-") as folder:
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
                "NVIDIA_REVIEW_CLI_VERSION")
        source = temp / "source" / "skills"
        shutil.copytree(original, source)
        require(tree_fingerprint(source) == before, "NVIDIA_REVIEW_SNAPSHOT_MISMATCH")

        def tier(skill, checks, out, *args):
            result = run("tier1", str(skill), "--no-llm", "--checks", checks,
                         "--min-score", "70", "-r", "json", "-o", str(out), *args)
            return read_report(out / REPORT), result.returncode

        def harness(skill, name, out, *args):
            result = run("harness-check", str(skill), "--harness", name, "--json", str(out), *args)
            require(result.returncode == 0, "NVIDIA_HARNESS_EXECUTION_FAILED")
            return harness_review(read_report(out), skill, name)

        skills = {}
        children = sorted(source.iterdir())
        require(0 < len(children) <= 100, "NVIDIA_REVIEW_SKILL_COUNT")
        for skill in children:
            require(skill.is_dir() and NAME.fullmatch(skill.name)
                    and (skill / "SKILL.md").is_file(), "NVIDIA_REVIEW_SKILL_INVALID")
            out = temp / "reports" / skill.name
            out.mkdir(parents=True)
            default = quality_review(*tier(skill, "schema,quality", out / "default"))
            localized = quality_review(*tier(skill, "schema,quality", out / "localized",
                                              "--quality-config", str(config)))
            # The locale overlay must not hide schema findings or change other dimensions.
            require(default["schema"] == localized["schema"]
                    and all(default["dimensions"][d] == localized["dimensions"][d]
                            for d in ("correctness", "discoverability", "efficiency")),
                    "NVIDIA_LOCALE_UNRELATED_CHANGE")
            require(default["dimensions"]["reliability"] <= localized["dimensions"]["reliability"],
                    "NVIDIA_LOCALE_RELIABILITY_REGRESSION")
            checks = static_review(*tier(skill, "pii,license,unicode,lint", out / "static"))
            profiles = {}
            for name, root in ROOTS.items():
                installed = temp / "profiles" / name / root / skill.name
                shutil.copytree(skill, installed)
                require(tree_fingerprint(installed) == tree_fingerprint(skill),
                        "NVIDIA_PROFILE_COPY_MISMATCH")
                profiles[name] = harness(installed, name, out / (name + ".json"))
                if name == "codex":
                    profiles["codex_custom_provider"] = harness(
                        installed, name, out / "codex-custom.json", "--custom-provider")
                    profiles["codex_explicit_custom_provider"] = harness(
                        installed, name, out / "codex-explicit.json",
                        "--custom-provider", "--explicit-invocation")
            wrong_root = temp / "profiles" / "claude-code" / ROOTS["claude-code"] / skill.name
            wrong = harness(wrong_root, "codex", out / "codex-wrong-root.json")
            require(wrong["status"] == "not_loaded"
                    and any(f["id"] == "CX-ROOT" for f in wrong["findings"]),
                    "NVIDIA_HARNESS_NEGATIVE_NOT_DETECTED")
            skills[skill.name] = {"default_quality": default, "localized_quality": localized,
                                  "static": checks, "harness_profiles": profiles,
                                  "wrong_root_negative": "PASS"}

        negative = temp / "negative" / "fixture-unicode"
        negative.mkdir(parents=True)
        (negative / "SKILL.md").write_text(
            "---\nname: fixture-unicode\ndescription: Synthetic fixture only\n---\n\n"
            "Synthetic bidi marker " + chr(0x202e) + "abc\n", encoding="utf-8")
        bad = static_review(*tier(negative, "unicode", temp / "negative-unicode"),
                            expected=("Unicode Smuggling Detection",))
        unicode = bad["Unicode Smuggling Detection"]
        require(unicode["status"] == "FAILED" and any(f["check"] == "bidi_override"
                and f["severity"] == "high" for f in unicode["findings"]),
                "NVIDIA_UNICODE_NEGATIVE_NOT_DETECTED")
        require(tree_fingerprint(source) == before and tree_fingerprint(original) == before,
                "NVIDIA_REVIEW_SOURCE_MUTATED")
    return {"execution": "PASS", "version": VERSION, "skills": skills,
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "negative_unicode": "PASS", "policy": "ADVISORY_FINDINGS",
            "deepseek_harness": "NO_UPSTREAM_PROFILE", "live_agents": "NOT_VERIFIED",
            "home_identity_pii_coverage": "NOT_VERIFIED",
            "license_dependency_audit": "NOT_RUN", "external_scanners": "NOT_RUN",
            "full_tier1": "NOT_VERIFIED", "llm": "DISABLED", "tier2": "NOT_RUN", "tier3": "NOT_RUN"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=pathlib.Path, required=True)
    parser.add_argument("--cli", type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        result = accept(args.repo, args.cli)
    except (InstallCheckError, OSError, UnicodeError, ValueError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + (str(exc) if isinstance(exc, InstallCheckError)
                             else "NVIDIA_REVIEW_RUNTIME_FAILED"), file=sys.stderr)
        return 1
    print("NVIDIA_TIER1_STATIC_REVIEW_EXECUTION_PASS: " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
