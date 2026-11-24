# T12.02.02.01 — direct Python static review

[Русский — оригинал](BANDIT_REVIEW.md) | **English — translation**

Bandit 1.9.4 is already SHA-256 locked in tools/nvidia-tier1-requirements.txt. [Upstream](https://github.com/PyCQA/bandit), Apache-2.0. No new dependencies, paid APIs, LLMs or Tier 2/3. Direct Bandit execution does not accept the combined NVIDIA code-integrity check: other scanners and CVEs remain separate tasks.

## Contract

- Scan a snapshot of all Git-tracked Python files from the current working tree (the checked-out commit in CI); tests and runtime are separated in the aggregate. No target files are executed.
- Dedicated temporary directory and environment without inherited API keys or tokens; target configuration is not copied. Verify CLI version, actual file coverage in JSON, errors, exit codes and source immutability.
- Use --ignore-nosec, without rule exclusions, a baseline or --exit-zero. Positive and negative synthetic cases are mandatory: B307 must be detected even with nosec.
- Exit 1 with valid findings is retained as findings, not a clean scan. Incomplete scans, missing JSON, malformed data, timeout or coverage mismatch block CI.
- Logs contain only counts, rule IDs, severity/confidence, runtime/tests category and elapsed time. Raw lines, paths, messages and reports are not published. Analysis is static; environment isolation is not a network sandbox.

## Execution and acceptance

Use the existing hash-locked Tier 1 environment; command: `python tools/check_bandit_review.py --repo . --cli <path-to-bandit>`. BANDIT_REVIEW_EXECUTION_PASS means the execution contract passed, not that vulnerabilities are absent. Findings require manual review before introducing a blocking policy; no findings does not prove security.

T12.02.02.01 status: COMPLETE within direct scan execution scope. T12.02.02 and T12 remain PARTIAL. Next: Gitleaks, SkillSpector, CVEs and dependency licenses; do not allow automatic external scanner installation without a separate audit.

## Actual acceptance

[CI 45365133732](https://github.com/Sashido01/TESSERA/actions/runs/45365133732) PASS: 414+19 tests, 60 Python files, 87 findings (45 runtime, 42 tests; 2 medium, 85 low, 0 high); clean and negative fixtures PASS; direct review 1.69 s.

| Rule | Runtime | Tests | Severity |
| --- | ---: | ---: | --- |
| B101 | 5 | 0 | LOW |
| B108 | 0 | 1 | MEDIUM |
| B310 | 1 | 0 | MEDIUM |
| B404 | 17 | 14 | LOW |
| B603 | 13 | 14 | LOW |
| B607 | 9 | 13 | LOW |

Findings are not confirmed vulnerabilities. Review URL scheme/host/redirect restrictions (B310), temporary-path fixture (B108), assert use and subprocess executable resolution/arguments; no blanket suppressions. Full NVIDIA code-integrity, CVEs and live agent execution remain unverified.
