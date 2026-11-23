#!/usr/bin/env python3
"""T09.03: отчёт из наблюдаемых Git, preflight и remote-доказательств.

Без --verify-remote и --execute-checks не использует сеть и не запускает
проектные команды. Даже полный PASS не объявляет приложение RELEASED.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

try:
    from .release_inspect import InspectionError, canonical_repo, inspect, resolve_commit
    from .release_preflight import preflight
    from .release_remote import verify_remote_tag
    from .release_ci import verify_github_ci
    from .release_state import evidence_stage
except ImportError:
    from release_inspect import InspectionError, canonical_repo, inspect, resolve_commit
    from release_preflight import preflight
    from release_remote import verify_remote_tag
    from release_ci import verify_github_ci
    from release_state import evidence_stage


def build_report(
    repo: pathlib.Path,
    version: str,
    *,
    prefix: str = "",
    commit: str | None = None,
    config: str = "release-checks.json",
    remote: str = "origin",
    verify_remote: bool = False,
    execute_checks: bool = False,
    verify_ci: bool = False,
    github_repo: str | None = None,
    run_id: int | None = None,
) -> dict[str, Any]:
    if verify_ci and (not github_repo or run_id is None):
        raise InspectionError("CI_REQUIRES_GITHUB_REPO_AND_RUN_ID")
    root = canonical_repo(repo)
    local = inspect(root, version, prefix=prefix, commit=commit)
    target_sha = local["expected_commit_sha"]
    head_sha = resolve_commit(root, None)
    problems: list[str] = list(local["problems"])

    if target_sha != head_sha:
        if execute_checks:
            problems.append("HISTORICAL_CHECKS_UNSUPPORTED")
        preflight_status = "NOT_CHECKED_HISTORICAL"
        checks_status = "NOT_RUN"
        check_results: list[dict[str, Any]] = []
    else:
        try:
            checks = preflight(
                root, version, config=config, expected_commit=target_sha,
                execute=execute_checks and local["inspection_status"] == "PASS",
            )
            preflight_status = checks["preflight_status"]
            checks_status = checks["checks_status"]
            check_results = checks["executed_checks"]
            problems.extend(checks["problems"])
        except (InspectionError, OSError):
            preflight_status = "BLOCKED"
            checks_status = "NOT_RUN"
            check_results = []
            problems.append("PREFLIGHT_ERROR")

    remote_info: dict[str, Any] | None = None
    remote_status = "NOT_CHECKED"
    if verify_remote:
        if local["inspection_status"] != "PASS":
            remote_status = "SKIPPED_LOCAL_TAG_INVALID"
        else:
            remote_info = verify_remote_tag(
                root, version, prefix=prefix, commit=commit, remote=remote,
            )
            remote_status = remote_info["remote_tag_status"]
            problems.extend(remote_info["problems"])

    ci_info: dict[str, Any] | None = None
    ci_status = "NOT_CHECKED"
    if verify_ci:
        assert github_repo is not None and run_id is not None
        ci_info = verify_github_ci(github_repo, run_id, target_sha)
        ci_status = ci_info["ci_status"]
        problems.extend(ci_info["problems"])

    problems = list(dict.fromkeys(problems))
    stage = evidence_stage(
        problems=problems,
        local_tag_status=local["inspection_status"],
        remote_tag_status=remote_status,
        checks_status=checks_status,
        ci_status=ci_status,
    )
    return {
        "schema_version": 1,
        "requested_version": version,
        "requested_tag": local["requested_tag"],
        "target_commit_sha": target_sha,
        "is_historical_commit": target_sha != head_sha,
        "local_tag_status": local["inspection_status"],
        "local_tag_object_sha": local["tag_object_sha"],
        "local_tag_target_commit_sha": local["tag_target_commit_sha"],
        "preflight_status": preflight_status,
        "checks_status": checks_status,
        "executed_checks": check_results,
        "remote_tag_status": remote_status,
        "ci_status": ci_status,
        "ci_run_id": run_id if verify_ci else None,
        "ci_repository": github_repo if verify_ci else None,
        "ci_observed_commit_sha": ci_info.get("observed_commit_sha") if ci_info else None,
        "ci_run_attempt": ci_info.get("run_attempt") if ci_info else None,
        "remote_tag_object_sha": remote_info["remote_tag_object_sha"] if remote_info else None,
        "remote_publication": remote_info["remote_publication"] if remote_info else "NOT_CHECKED",
        "github_release": "NOT_CHECKED",
        "stage": stage,
        "evidence_status": "PASS" if stage != "BLOCKED" else "BLOCKED",
        "release_readiness": "NOT_VERIFIED",
        "problems": problems,
        "limitations": [
            "Нет независимого подтверждения выпущенного приложения или защищённого доказательства полноты тестов",
            "Аннотированный тег и remote-ref не доказывают публикацию готового ПО",
            "Данные исполняемых тестов не сохраняются как подписанные доказательства",
        ],
    }


def markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Отчёт о проверке доказательств релиза",
        "",
        f"- Версия: {result['requested_version']}",
        f"- Git-тег: {result['requested_tag']}",
        f"- Коммит: {result['target_commit_sha']}",
        f"- Локальный тег: {result['local_tag_status']}",
        f"- Preflight: {result['preflight_status']}",
        f"- Реальные проверки: {result['checks_status']}",
        f"- Удалённый тег: {result['remote_tag_status']}",
        f"- Завершённый CI: {result['ci_status']}",
        f"- CI run ID: {result['ci_run_id']}",
        f"- Доказательства: {result['evidence_status']}",
        f"- Этап: {result['stage']}",
        f"- Готовность релиза: {result['release_readiness']}",
        "",
        "## Подтверждённые результаты шагов",
    ]
    for step in result["executed_checks"]:
        lines.append(f"- {step['id']} ({step['kind']}): {step['status']} (exit={step['exit_code']})")
    if not result["executed_checks"]:
        lines.append("- Команды сборки и тестов в этом отчёте не запускались.")
    lines.extend(["", "## Проблемы"])
    lines.extend(f"- {code}" for code in result["problems"])
    if not result["problems"]:
        lines.append("- Нарушений запрошенных проверок не обнаружено.")
    lines.extend(["", "## Ограничения"])
    lines.extend(f"- {item}" for item in result["limitations"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=pathlib.Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--prefix", default="")
    parser.add_argument("--commit", help="Полный SHA; для исторического релиза проверки не выполняются")
    parser.add_argument("--config", default="release-checks.json")
    parser.add_argument("--remote", default="origin", help="Имя доверенного Git remote")
    parser.add_argument("--verify-remote", action="store_true", help="Явно разрешить сетевую проверку тега")
    parser.add_argument("--execute-checks", action="store_true", help="Явно запустить проверенные команды проекта")
    parser.add_argument("--verify-ci", action="store_true", help="Явно разрешить запрос к GitHub Actions API")
    parser.add_argument("--github-repo", help="Доверенный владелец/репозиторий GitHub, например owner/repository")
    parser.add_argument("--run-id", type=int, help="Идентификатор уже завершённого запуска GitHub Actions")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()
    try:
        result = build_report(
            args.repo, args.version, prefix=args.prefix, commit=args.commit,
            config=args.config, remote=args.remote,
            verify_remote=args.verify_remote, execute_checks=args.execute_checks,
            verify_ci=args.verify_ci, github_repo=args.github_repo, run_id=args.run_id,
        )
    except (InspectionError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(markdown(result) if args.format == "markdown" else json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["evidence_status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
