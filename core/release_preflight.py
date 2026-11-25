#!/usr/bin/env python3
"""T09.02: preflight релиза и явно разрешённый запуск обязательных проверок.

По умолчанию только чтение. --execute запускает команды доверенного проекта:
без shell, без Git-записи и без публикации. PASS не означает RELEASED.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import time
from typing import Any

try:
    from .release_inspect import InspectionError, VERSION, SKILL_NAME, regular_commit_file, canonical_repo, git, resolve_commit
except ImportError:  # Запуск как отдельного Python-скрипта
    from release_inspect import InspectionError, VERSION, SKILL_NAME, regular_commit_file, canonical_repo, git, resolve_commit

MAX_CONFIG_BYTES = 65536
MAX_STEPS = 12
ALLOWED_KEYS = {"schema_version", "version_file", "release_notes", "build", "tests"}
STEP_KEYS = {"id", "argv", "cwd", "timeout_seconds"}
IDENTIFIER = re.compile(r"[a-z][a-z0-9_-]{0,47}\Z")


class PreflightError(InspectionError):
    """Невалидная конфигурация или неподтверждённые данные проекта."""


def project_path(root: pathlib.Path, name: str, *, directory: bool = False) -> pathlib.Path:
    if not isinstance(name, str) or not name or "\\" in name or ":" in name or "\x00" in name:
        raise PreflightError("CONFIG_UNSAFE_PATH")
    if name != ".":
        if name.startswith("/") or any(part in ("", ".", "..", ".git") for part in name.split("/")):
            raise PreflightError("CONFIG_UNSAFE_PATH")
    try:
        path = (root / name).resolve(strict=True)
    except OSError as exc:
        raise PreflightError("CONFIG_PATH_MISSING") from exc
    if not path.is_relative_to(root):
        raise PreflightError("CONFIG_PATH_ESCAPE")
    if directory and not path.is_dir():
        raise PreflightError("CONFIG_CWD_INVALID")
    if not directory and (not path.is_file() or path.is_symlink()):
        raise PreflightError("CONFIG_FILE_INVALID")
    return path


def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PreflightError("CONFIG_DUPLICATE_KEY")
        result[key] = value
    return result


def validated_steps(root: pathlib.Path, value: Any, kind: str, seen: set[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list) or (kind == "tests" and not value) or len(value) > MAX_STEPS:
        raise PreflightError("CONFIG_CHECKS_INVALID")
    steps: list[dict[str, Any]] = []
    for step in value:
        if not isinstance(step, dict) or set(step) != STEP_KEYS:
            raise PreflightError("CONFIG_STEP_FIELDS")
        ident, argv, cwd, timeout = (step[k] for k in ("id", "argv", "cwd", "timeout_seconds"))
        if not isinstance(ident, str) or not IDENTIFIER.fullmatch(ident) or ident in seen:
            raise PreflightError("CONFIG_STEP_ID")
        seen.add(ident)
        if not isinstance(argv, list) or not 1 <= len(argv) <= 24 or any(
            not isinstance(x, str) or not x or len(x) > 1024 or "\x00" in x
            for x in argv
        ):
            raise PreflightError("CONFIG_ARGV_INVALID")
        if type(timeout) is not int or not 1 <= timeout <= 900:
            raise PreflightError("CONFIG_TIMEOUT_INVALID")
        project_path(root, cwd, directory=True)
        steps.append({"id": ident, "argv": argv, "cwd": cwd, "timeout_seconds": timeout, "kind": kind})
    return steps


def load_plan(root: pathlib.Path, filename: str) -> dict[str, Any]:
    file = project_path(root, filename)
    if file.stat().st_size > MAX_CONFIG_BYTES:
        raise PreflightError("CONFIG_TOO_LARGE")
    try:
        cfg = json.loads(file.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)
    except (UnicodeError, OSError, json.JSONDecodeError) as exc:
        raise PreflightError("CONFIG_JSON_INVALID") from exc
    if not isinstance(cfg, dict) or set(cfg) != ALLOWED_KEYS or type(cfg["schema_version"]) is not int or cfg["schema_version"] != 1:
        raise PreflightError("CONFIG_SCHEMA_INVALID")
    project_path(root, cfg["version_file"])
    notes = cfg["release_notes"]
    if not isinstance(notes, list) or not notes or len(notes) > 8 or len(notes) != len(set(map(str, notes))):
        raise PreflightError("CONFIG_RELEASE_NOTES_INVALID")
    for entry in notes:
        project_path(root, entry)
    seen: set[str] = set()
    builds = cfg["build"]
    build_reason: str | None = None
    if isinstance(builds, dict):
        if set(builds) != {"not_applicable_reason"} or not isinstance(builds["not_applicable_reason"], str):
            raise PreflightError("CONFIG_BUILD_INVALID")
        build_reason = builds["not_applicable_reason"].strip()
        if len(build_reason) < 15:
            raise PreflightError("CONFIG_BUILD_REASON_REQUIRED")
        build_steps: list[dict[str, Any]] = []
    else:
        build_steps = validated_steps(root, builds, "build", seen)
        if not build_steps:
            raise PreflightError("CONFIG_BUILD_REASON_REQUIRED")
    tests = validated_steps(root, cfg["tests"], "tests", seen)
    if len(build_steps) + len(tests) > MAX_STEPS:
        raise PreflightError("CONFIG_TOO_MANY_STEPS")
    return {
        "version_file": cfg["version_file"],
        "release_notes": notes,
        "build_steps": build_steps,
        "build_not_applicable_reason": build_reason,
        "test_steps": tests,
    }


def run_step(root: pathlib.Path, step: dict[str, Any]) -> dict[str, Any]:
    location = project_path(root, step["cwd"], directory=True)
    started = time.monotonic()
    status = "FAIL"
    exit_code: int | None = None
    try:
        completed = subprocess.run(
            step["argv"], cwd=location, shell=False,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=step["timeout_seconds"], check=False,
        )
        exit_code = completed.returncode
        status = "PASS" if exit_code == 0 else "FAIL"
    except subprocess.TimeoutExpired:
        status = "TIMEOUT"
    except OSError:
        status = "START_FAILED"
    return {
        "id": step["id"],
        "kind": step["kind"],
        "status": status,
        "exit_code": exit_code,
        "duration_ms": round((time.monotonic() - started) * 1000),
    }


def preflight(
    repo: pathlib.Path, version: str, config: str = "release-checks.json",
    *, execute: bool = False, expected_commit: str | None = None,
    skill: str | None = None,
) -> dict[str, Any]:
    if not isinstance(version, str) or VERSION.fullmatch(version) is None:
        raise PreflightError("VERSION_INVALID")
    root = canonical_repo(repo)
    head = resolve_commit(root, None)
    wanted = resolve_commit(root, expected_commit) if expected_commit else head
    plan = load_plan(root, config)
    problems: list[str] = []
    if skill is not None:
        if not isinstance(skill, str) or not SKILL_NAME.fullmatch(skill):
            raise PreflightError("SKILL_SCOPE_INVALID")
        base = f"skills/{skill}/"
        notes = {base + "CHANGELOG.md", base + "CHANGELOG.en.md"}
        if plan["version_file"] != base + "VERSION" or set(plan["release_notes"]) != notes:
            raise PreflightError("SKILL_PLAN_SCOPE_MISMATCH")
        if not all(regular_commit_file(root, wanted, p) for p in
                   (base + "SKILL.md", base + "VERSION", *sorted(notes), config)):
            raise PreflightError("SKILL_PLAN_COMMITTED_FILES_INVALID")
    status = git(root, "status", "--porcelain=v1", "--untracked-files=all").stdout
    clean_before = not bool(status.strip())
    if not clean_before:
        problems.append("WORKTREE_DIRTY")
    if wanted != head:
        problems.append("HEAD_CHANGED")
    if git(root, "show", f"{head}:{config}", allow_failure=True).returncode != 0:
        problems.append("CONFIG_NOT_COMMITTED")

    version_content = git(root, "show", f"{wanted}:{plan['version_file']}", allow_failure=True)
    recorded = version_content.stdout.strip() if version_content.returncode == 0 else None
    if recorded is None:
        problems.append("VERSION_MISSING_IN_COMMIT")
    elif recorded != version:
        problems.append("VERSION_MISMATCH")

    for note in plan["release_notes"]:
        contents = git(root, "show", f"{wanted}:{note}", allow_failure=True)
        if contents.returncode != 0:
            problems.append("RELEASE_NOTES_MISSING")
        elif not re.search(r"(?m)^## " + re.escape(version) + r"(?:\s|$)", contents.stdout):
            problems.append("RELEASE_NOTES_VERSION_MISSING")

    report: dict[str, Any] = {
        "schema_version": 1,
        "expected_commit_sha": wanted,
        "actual_head_sha": head,
        "requested_version": version,
        "version_in_commit": recorded,
        "config_file": config,
        "worktree_clean_before": clean_before,
        "mode": "EXECUTE" if execute else "PLAN",
        "preflight_status": "BLOCKED" if problems else "PASS",
        "checks_status": "NOT_RUN",
        "build_status": "NOT_APPLICABLE" if plan["build_not_applicable_reason"] else "NOT_RUN",
        "build_not_applicable_reason": plan["build_not_applicable_reason"],
        "tests_status": "NOT_RUN",
        "stage": "BLOCKED" if problems else "PREPARED",
        "release_readiness": "NOT_VERIFIED",
        "remote_publication": "NOT_CHECKED",
        "executed_checks": [],
        "planned_checks": [{"id": step["id"], "kind": step["kind"]} for step in plan["build_steps"] + plan["test_steps"]],
        "problems": problems,
    }
    if problems or not execute:
        return report

    for step in plan["build_steps"] + plan["test_steps"]:
        if resolve_commit(root, None) != wanted:
            problems.append("HEAD_CHANGED_DURING_CHECKS")
            break
        result = run_step(root, step)
        report["executed_checks"].append(result)
        if result["status"] != "PASS":
            problems.append("CHECK_" + result["status"])
            break

    if resolve_commit(root, None) != wanted:
        problems.append("HEAD_CHANGED_DURING_CHECKS")
    clean_after = not bool(git(root, "status", "--porcelain=v1", "--untracked-files=all").stdout.strip())
    report["worktree_clean_after"] = clean_after
    if not clean_after:
        problems.append("WORKTREE_DIRTY_AFTER_CHECKS")

    completed = report["executed_checks"]
    report["build_status"] = (
        "NOT_APPLICABLE" if plan["build_not_applicable_reason"] else
        ("PASS" if all(x["status"] == "PASS" for x in completed if x["kind"] == "build")
         and len([x for x in completed if x["kind"] == "build"]) == len(plan["build_steps"]) else "BLOCKED")
    )
    report["tests_status"] = (
        "PASS" if len([x for x in completed if x["kind"] == "tests"]) == len(plan["test_steps"])
        and all(x["status"] == "PASS" for x in completed if x["kind"] == "tests")
        else "BLOCKED"
    )
    report["checks_status"] = "BLOCKED" if problems else "PASS"
    report["stage"] = "BLOCKED" if problems else "VALIDATED"
    report["preflight_status"] = "BLOCKED" if problems else "PASS"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=pathlib.Path, required=True, help="Корень целевого Git-проекта")
    parser.add_argument("--version", required=True, help="Проверяемая версия MAJOR.MINOR.PATCH")
    parser.add_argument("--config", default="release-checks.json", help="Файл доверенного плана внутри проекта")
    parser.add_argument("--skill", help="Независимый навык; требует явного плана с его VERSION и CHANGELOG")
    parser.add_argument("--expected-commit", help="Полный SHA целевого коммита")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true", help="Только проверка плана (по умолчанию)")
    mode.add_argument("--execute", action="store_true", help="Явно запустить указанные в конфигурации команды")
    args = parser.parse_args()
    try:
        result = preflight(
            args.repo, args.version, args.config,
            execute=args.execute, expected_commit=args.expected_commit, skill=args.skill,
        )
    except (InspectionError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["preflight_status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
