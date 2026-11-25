#!/usr/bin/env python3
"""Статическая защита отдельного workflow сборки/аттестации T09.08."""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "build-attested-catalog.yml"


def validate(text: str) -> list[str]:
    errors: list[str] = []
    if not text.lstrip().startswith("name:") or "\non:\n  workflow_dispatch:" not in text:
        errors.append("ATTEST_TRIGGER_INVALID")
    header = text.split("\njobs:", 1)[0]
    if re.search(r"(?m)^  (?:push|pull_request|pull_request_target|workflow_run|schedule):", header):
        errors.append("ATTEST_UNSAFE_TRIGGER")
    if "\npermissions:\n  contents: read" not in header or "contents: write" in text:
        errors.append("ATTEST_WRITE_ACCESS_INVALID")
    required = (
        "github.event_name == 'workflow_dispatch'",
        "github.ref_type == 'tag'",
        "github.repository == 'Sashido01/TESSERA'",
        "id-token: write",
        "attestations: write",
        "contents: read",
        "persist-credentials: false",
        "fetch-depth: 0",
        'if [[ "${GITHUB_REF}" != "refs/tags/${tag}" ]]',
        'git cat-file -t "refs/tags/${tag}"',
        "git merge-base --is-ancestor HEAD origin/main",
        "python tools/build_catalog_package.py --repo . --output-dir dist --require-tag --check-reproducible",
        "python -m unittest discover -s tests -q",
        "python tools/run_skill_tests.py -q",
        "subject-path: dist/*.zip",
        "if-no-files-found: error",
    )
    for required_text in required:
        if required_text not in text:
            errors.append("ATTEST_REQUIRED_CONTROL_MISSING")
    actions = ("actions/checkout", "actions/setup-python", "actions/attest", "actions/upload-artifact")
    for action in actions:
        matches = re.findall(r"(?m)^\s*uses:\s*" + re.escape(action) + r"@([^\s#]+)", text)
        if len(matches) != 1 or any(not re.fullmatch(r"[0-9a-f]{40}", sha) for sha in matches):
            errors.append("ATTEST_UNPINNED_OR_DUPLICATE_ACTION")
    used = re.findall(r"(?m)^\s*uses:\s*(\S+)", text)
    if len(used) != 4 or any(not value.startswith(prefix + "@") for value, prefix in zip(used, actions)):
        errors.append("ATTEST_UNEXPECTED_ACTION")
    for forbidden in ("git push ", "gh release create", "git tag -f", "pull_request_target:", "workflow_run:", "workflow_call:", "workflow_dispatch:\n    inputs:"):
        if forbidden in text:
            errors.append("ATTEST_FORBIDDEN_OPERATION")
    if "cancel-in-progress: false" not in text:
        errors.append("ATTEST_CONCURRENCY_UNSAFE")
    # Python imports from skills/*/scripts produce __pycache__ by default.
    # The runtime-file allowlist must stay strict rather than ignoring these files.
    if "    env:\n      PYTHONDONTWRITEBYTECODE: '1'\n" not in text:
        errors.append("ATTEST_PYCACHE_ISOLATION_MISSING")
    return sorted(set(errors))


def main() -> int:
    try:
        text = WORKFLOW.read_text(encoding="utf-8")
    except OSError:
        print("BLOCKED: ATTEST_WORKFLOW_MISSING", file=sys.stderr)
        return 1
    errors = validate(text)
    if errors:
        for item in errors:
            print("BLOCKED: " + item, file=sys.stderr)
        return 1
    print("Безопасность подписывающей сборки: PASS (статический анализ; подпись не создавалась)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
