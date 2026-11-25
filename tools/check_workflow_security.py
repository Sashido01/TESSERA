#!/usr/bin/env python3
"""Проверяет защитные требования к workflow TESSERA без сетевых запросов."""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


# Required status check keeps its existing public name. Only the three explicit
# successful job results can satisfy it; no source or artifact is executed here.
PARALLEL_GATE = "  validate:\n    name: validate\n    needs: [catalog_checks, history_checks, source_secret_checks]\n    if: ${{ always() }}\n    runs-on: ubuntu-latest\n    timeout-minutes: 2\n    steps:\n      - name: Подтвердить все обязательные группы\n        env:\n          CATALOG_RESULT: ${{ needs.catalog_checks.result }}\n          HISTORY_RESULT: ${{ needs.history_checks.result }}\n          SOURCE_RESULT: ${{ needs.source_secret_checks.result }}\n        shell: bash\n        run: |\n          set -euo pipefail\n          test \"$CATALOG_RESULT\" = success\n          test \"$HISTORY_RESULT\" = success\n          test \"$SOURCE_RESULT\" = success\n"
CHECKED_SHA_STEP = "      - name: Проверить точный SHA кандидата\n        env:\n          CHECKED_SHA: ${{ github.sha }}\n        run: test \"$(git rev-parse HEAD)\" = \"$CHECKED_SHA\"\n"
DOCKER_STEP = "      - name: Проверить живой Linux Docker preflight\n        run: python tools/check_docker_preflight.py\n"
GITLEAKS_DOWNLOAD = "      - name: Скачать и проверить официальный Gitleaks 8.30.1\n        shell: bash\n        run: |\n          set -euo pipefail\n          umask 077\n          archive=\"$RUNNER_TEMP/gitleaks_8.30.1_linux_x64.tar.gz\"\n          curl --fail --location --silent --show-error --retry 2 --connect-timeout 10 --max-time 120 \\\n            --proto '=https' --tlsv1.2 --output \"$archive\" \\\n            https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz\n          echo \"551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb  $archive\" | sha256sum --check --\n          tar --extract --gzip --to-stdout --file \"$archive\" gitleaks > \"$RUNNER_TEMP/gitleaks-8.30.1\"\n          chmod 700 \"$RUNNER_TEMP/gitleaks-8.30.1\"\n"
HISTORY_STEPS = "      - name: Проверить достижимые исторические Git-объекты Gitleaks\n        shell: bash\n        run: |\n          set -euo pipefail\n          umask 077\n          python tools/check_gitleaks_history.py --repo . --cli \"$RUNNER_TEMP/gitleaks-8.30.1\" > \"$RUNNER_TEMP/gitleaks-history-host.jsonl\"\n      - name: Сопоставить изолированную проверку истории Gitleaks\n        run: python tools/check_gitleaks_history_container.py --repo . --cli \"$RUNNER_TEMP/gitleaks-8.30.1\" --host-report \"$RUNNER_TEMP/gitleaks-history-host.jsonl\"\n"

SOURCE_STEPS = "      - name: Проверить отслеживаемые текстовые файлы Gitleaks\n        shell: bash\n        run: |\n          set -euo pipefail\n          umask 077\n          python tools/check_gitleaks_review.py --repo . --cli \"$RUNNER_TEMP/gitleaks-8.30.1\" > \"$RUNNER_TEMP/gitleaks-host-report.jsonl\"\n      - name: Сопоставить изолированный Gitleaks с проверкой хоста\n        run: python tools/check_gitleaks_container.py --repo . --cli \"$RUNNER_TEMP/gitleaks-8.30.1\" --host-report \"$RUNNER_TEMP/gitleaks-host-report.jsonl\"\n\n      - name: Проверить пять правил Gitleaks, зависящих от имени файла\n        shell: bash\n        run: |\n          set -euo pipefail\n          umask 077\n          python tools/check_gitleaks_paths.py --repo . --cli \"$RUNNER_TEMP/gitleaks-8.30.1\" > \"$RUNNER_TEMP/gitleaks-path-host.jsonl\"\n      - name: Сопоставить изолированную проверку правил Gitleaks по пути\n        run: python tools/check_gitleaks_paths_container.py --repo . --cli \"$RUNNER_TEMP/gitleaks-8.30.1\" --host-report \"$RUNNER_TEMP/gitleaks-path-host.jsonl\"\n"


def parallel_gate_errors(section: str) -> list[str]:
    errors: list[str] = []
    jobs = section.split("\njobs:\n", 1)
    if len(jobs) != 2:
        return ["PARALLEL_JOB_LAYOUT_INVALID"]
    body = jobs[1]
    if re.findall(r"(?m)^  ([a-z][a-z0-9_]*):$", body) != [
            "catalog_checks", "history_checks", "source_secret_checks", "validate"]:
        return ["PARALLEL_JOB_LAYOUT_INVALID"]
    catalog, history_and_gate = body.split("\n  history_checks:\n", 1)
    history, source_and_gate = history_and_gate.split("\n  source_secret_checks:\n", 1)
    source, gate = source_and_gate.split("\n  validate:\n", 1)
    if ("  validate:\n" + gate).strip() != PARALLEL_GATE.strip():
        errors.append("PARALLEL_REQUIRED_GATE_INVALID")
    for group in (catalog, history, source):
        if (CHECKED_SHA_STEP not in group or DOCKER_STEP not in group
                or GITLEAKS_DOWNLOAD not in group or "fetch-depth: 0" not in group
                or "persist-credentials: false" not in group
                or "PYTHONDONTWRITEBYTECODE: '1'" not in group
                or re.search(r"(?m)^ +(?:if|continue-on-error|permissions|needs|concurrency):", group)
                or "persist-credentials: true" in group):
            errors.append("PARALLEL_CHECK_GROUP_UNSAFE")
    if HISTORY_STEPS not in history or any(
            name in catalog or name in source for name in
            ("tools/check_gitleaks_history.py", "tools/check_gitleaks_history_container.py")):
        errors.append("PARALLEL_HISTORY_SCOPE_INVALID")
    source_scripts = ("tools/check_gitleaks_review.py", "tools/check_gitleaks_container.py",
                      "tools/check_gitleaks_paths.py", "tools/check_gitleaks_paths_container.py")
    if SOURCE_STEPS not in source or any(name in catalog or name in history for name in source_scripts):
        errors.append("PARALLEL_SOURCE_SCOPE_INVALID")
    if "tools/run_skill_tests.py" not in catalog or "tools/check_nvidia_full_tier1.py" not in catalog:
        errors.append("PARALLEL_CATALOG_SCOPE_INVALID")
    return errors


def validate_workflow(workflow: str) -> list[str]:
    errors: list[str] = []
    for action in ("actions/checkout", "actions/setup-python"):
        versions = re.findall(r"(?m)^\s*uses:\s*" + re.escape(action) + r"@([^\s#]+)", workflow)
        if not versions:
            errors.append(f"Не найдено действие {action}")
        for version in versions:
            if not re.fullmatch(r"[0-9a-f]{40}", version):
                errors.append(f"{action} не привязан к 40-символьному SHA")
    for bad in ("pull_request_target:", "workflow_run:", "git push --force", "git tag -f"):
        if bad in workflow:
            errors.append(f"Запрещённый элемент workflow: {bad}")
    if "permissions:\n  contents: read" not in workflow:
        errors.append("Не задано общее право contents: read")
    if "\n  tag_microversion:" not in workflow:
        errors.append("Отсутствует отдельная задача публикации тега")
        return errors
    validate, tagging = workflow.split("\n  tag_microversion:", 1)
    errors.extend(parallel_gate_errors(validate))
    if '      - name: Проверить живой Linux Docker preflight\n        run: python tools/check_docker_preflight.py\n' not in validate:
        errors.append("Нет обязательного Linux Docker preflight")
    if "persist-credentials: false" not in validate:
        errors.append("Проверка не отключает сохранение Git credentials")
    if "    env:\n      PYTHONDONTWRITEBYTECODE: '1'\n" not in validate:
        errors.append("Python bytecode caches не отключены в CI")
    try:
        tests = validate.index("run: python tools/run_skill_tests.py")
        post_test_build = validate.index(
            "run: python tools/build_catalog_package.py --repo . --output-dir dist/post-tests --check-reproducible"
        )
        if post_test_build <= tests:
            errors.append("Post-test ZIP smoke должен выполняться после тестов навыка")
    except ValueError:
        errors.append("Нет обязательной проверки ZIP после тестов")
    remote_step = (
        "        env:\n"
        "          GH_TOKEN: ${{ github.token }}\n"
        '        run: python tools/check_official_remote_install.py --repo . --cli "$RUNNER_TEMP/gh_2.105.0_linux_amd64/bin/gh"'
    )
    if remote_step not in validate:
        errors.append("Нет обязательной удалённой проверки с ограниченным read-only токеном CI")
    update_step = (
        "        env:\n"
        "          GH_TOKEN: ${{ github.token }}\n"
        '        run: python tools/check_official_skill_update.py --repo . --cli "$RUNNER_TEMP/gh_2.105.0_linux_amd64/bin/gh"'
    )
    if update_step not in validate:
        errors.append("Нет обязательной проверки обновления с read-only токеном CI")
    multi_step = (
        '        run: python tools/check_official_multi_skill.py --repo . --cli "$RUNNER_TEMP/gh_2.105.0_linux_amd64/bin/gh"'
    )
    if multi_step not in validate:
        errors.append("Нет обязательной проверки нескольких навыков")
    if '--require-hashes -r tools/nvidia-tier1-requirements.txt' not in validate or 'run: python tools/check_nvidia_tier1.py --repo . --cli "$RUNNER_TEMP/nvidia-tier1/bin/skillevaluator"' not in validate:
        errors.append("Нет обязательной ограниченной проверки NVIDIA Tier 1")
    if 'run: python tools/check_nvidia_full_tier1.py --repo . --cli "$RUNNER_TEMP/nvidia-tier1/bin/skillevaluator" --skillspector "$RUNNER_TEMP/skillspector/bin/skillspector" --bandit "$RUNNER_TEMP/nvidia-tier1/bin/bandit" --gitleaks "$RUNNER_TEMP/gitleaks-8.30.1" --semgrep "$RUNNER_TEMP/semgrep/bin/semgrep" --semgrep-rules "$RUNNER_TEMP/nvidia-tier1/lib/python3.13/site-packages/skillevaluator/config/semgrep_rules.yaml" --bandit-packages "$RUNNER_TEMP/bandit-isolated" --sp-packages "$RUNNER_TEMP/skillspector/lib/python3.13/site-packages"' not in validate:
        errors.append("Нет обязательной интегрированной проверки NVIDIA Tier 1")
    if ('11859086088d6720e5f4f303de0740a4830b065b' not in validate
            or '--require-hashes -r "$RUNNER_TEMP/semgrep-requirements.txt"' not in validate
            or 'tools/check_dependency_review.py --root semgrep==1.182.0' not in validate):
        errors.append("Нет обязательной закреплённой проверки Semgrep")
    if 'run: python tools/check_nvidia_static_review.py --repo . --cli "$RUNNER_TEMP/nvidia-tier1/bin/skillevaluator"' not in validate:
        errors.append("Нет обязательного статического обзора NVIDIA Tier 1")
    if 'python tools/check_bandit_review.py --repo . --cli "$RUNNER_TEMP/nvidia-tier1/bin/bandit" > "$RUNNER_TEMP/bandit-host.jsonl"' not in validate:
        errors.append("Нет обязательной проверки Bandit")
    if 'run: python tools/check_bandit_container.py --repo . --packages "$RUNNER_TEMP/bandit-isolated" --host-report "$RUNNER_TEMP/bandit-host.jsonl"' not in validate:
        errors.append("Нет обязательной контейнерной проверки Bandit")
    if '551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb' not in validate or 'python tools/check_gitleaks_review.py --repo . --cli "$RUNNER_TEMP/gitleaks-8.30.1" > "$RUNNER_TEMP/gitleaks-host-report.jsonl"' not in validate:
        errors.append("Нет обязательной закреплённой проверки Gitleaks")
    if 'run: python tools/check_gitleaks_container.py --repo . --cli "$RUNNER_TEMP/gitleaks-8.30.1" --host-report "$RUNNER_TEMP/gitleaks-host-report.jsonl"' not in validate:
        errors.append("Нет обязательной контейнерной проверки Gitleaks")
    if 'python tools/check_gitleaks_history.py --repo . --cli "$RUNNER_TEMP/gitleaks-8.30.1" > "$RUNNER_TEMP/gitleaks-history-host.jsonl"' not in validate:
        errors.append("Нет обязательной проверки истории Gitleaks")
    if 'run: python tools/check_gitleaks_history_container.py --repo . --cli "$RUNNER_TEMP/gitleaks-8.30.1" --host-report "$RUNNER_TEMP/gitleaks-history-host.jsonl"' not in validate:
        errors.append("Нет обязательной контейнерной проверки истории Gitleaks")
    if 'python tools/check_gitleaks_paths.py --repo . --cli "$RUNNER_TEMP/gitleaks-8.30.1" > "$RUNNER_TEMP/gitleaks-path-host.jsonl"' not in validate:
        errors.append("Нет обязательной проверки правил Gitleaks по пути")
    if 'run: python tools/check_gitleaks_paths_container.py --repo . --cli "$RUNNER_TEMP/gitleaks-8.30.1" --host-report "$RUNNER_TEMP/gitleaks-path-host.jsonl"' not in validate:
        errors.append("Нет обязательной контейнерной проверки правил Gitleaks по пути")
    if 'c323ad4c43e3c8f2de051572cc25b2711d11e648' not in validate or 'e2356aa11f0d484f789543f25da6208fe2408641c8b16e7b59bc6600c5c39ffb' not in validate or 'python tools/check_skillspector_review.py --repo . --cli "$RUNNER_TEMP/skillspector/bin/skillspector" > "$RUNNER_TEMP/skillspector-host.jsonl"' not in validate:
        errors.append("Нет обязательной закреплённой проверки SkillSpector")
    if 'run: python tools/check_skillspector_container.py --repo . --packages "$RUNNER_TEMP/skillspector/lib/python3.13/site-packages" --host-report "$RUNNER_TEMP/skillspector-host.jsonl"' not in validate:
        errors.append("Нет обязательной контейнерной проверки SkillSpector")
    if ('tools/check_dependency_review.py --locked tools/skills-ref-requirements.txt' not in validate
            or 'tools/check_dependency_review.py --root skillevaluator==1.2.0' not in validate
            or 'tools/check_dependency_review.py --root skillspector==2.13.7' not in validate
            or 'run: python tools/check_go_dependency_review.py' not in validate):
        errors.append("Нет обязательного аудита CVE и лицензий")
    if "contents: write" in validate:
        errors.append("Право записи обнаружено в проверяющей задаче")
    if ("ef4cb2f7cae47fe3e21fc596455f694951867b29" not in validate
            or "go build -mod=readonly -buildvcs=true" not in validate
            or "tools/check_go_binary_review.py" not in validate):
        errors.append("Нет закреплённой проверки Go-бинарников Govulncheck")
    if "needs: validate" not in tagging:
        errors.append("Публикация тега не зависит от успешного validate")
    if "permissions:\n      contents: write" not in tagging:
        errors.append("Отсутствует ограниченное право записи для тегирования")
    if "github.event_name == 'push' && github.ref == 'refs/heads/main'" not in tagging:
        errors.append("Не ограничен запуск публикации push в main")
    if 'remote_head="$(git ls-remote --heads origin refs/heads/main' not in tagging:
        errors.append("Нет проверки актуального удалённого main")
    if 'existing="$(git ls-remote --tags --refs origin ' not in tagging:
        errors.append("Нет безопасной проверки существования удалённого тега")
    if 'git push origin "refs/tags/' not in tagging:
        errors.append("Нет публикации строго одного нового тега")
    skill_publish = "      - name: Опубликовать и проверить независимые аннотированные теги навыков\n        env:\n          CHECKED_SHA: ${{ github.sha }}\n        run: python -B tools/publish_skill_tags.py --repo . --expected-commit \"$CHECKED_SHA\" --publish --strategy sequential\n"
    if (skill_publish not in tagging or "tools/publish_skill_tags.py --repo . --expected-commit" in validate
            or not tagging.strip().endswith(skill_publish.strip())
            or "github.repository == 'Sashido01/TESSERA'" not in tagging):
        errors.append("SKILL_TAG_PUBLICATION_GATE_INVALID")
    if "git ls-remote --exit-code --tags" in tagging:
        errors.append("Сетевая ошибка не должна интерпретироваться как отсутствие тега")
    return errors


def main() -> int:
    workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
    errors = validate_workflow(workflow)
    if errors:
        for error in errors:
            print(f"ОШИБКА: {error}", file=sys.stderr)
        return 1
    print("Проверка безопасности CI: PASS (только статический анализ файла)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
