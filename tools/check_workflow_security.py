#!/usr/bin/env python3
"""Проверяет защитные требования к workflow TESSERA без сетевых запросов."""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


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
    if "persist-credentials: false" not in validate:
        errors.append("Проверка не отключает сохранение Git credentials")
    if "    env:\n      PYTHONDONTWRITEBYTECODE: '1'\n" not in validate:
        errors.append("Python bytecode caches не отключены в CI")
    try:
        tests = validate.index("run: python -m unittest discover -s skills/microversion-release/tests -v")
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
    if 'run: python tools/check_nvidia_static_review.py --repo . --cli "$RUNNER_TEMP/nvidia-tier1/bin/skillevaluator"' not in validate:
        errors.append("Нет обязательного статического обзора NVIDIA Tier 1")
    if 'run: python tools/check_bandit_review.py --repo . --cli "$RUNNER_TEMP/nvidia-tier1/bin/bandit"' not in validate:
        errors.append("Нет обязательной проверки Bandit")
    if "contents: write" in validate:
        errors.append("Право записи обнаружено в проверяющей задаче")
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
