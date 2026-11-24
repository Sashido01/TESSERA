# T12.02.02.03 — SkillSpector static review

[Русский — оригинал](SKILLSPECTOR_REVIEW.md) | **English — translation**

Selected [SkillSpector 2.13.6](https://github.com/NVIDIA/SkillSpector/releases/tag/v2.13.6), Apache-2.0, commit e2674da339b0bddc6e565d059c0577c6d9cd25da: the source pinned in SkillEvaluator 1.2.0 ci/requirements/skillspector.in. Newer 2.13.7 is not adopted automatically. Official wheel SHA-256 e7b46c55e726405b2a068d375d1ee8e799e15d86f3fc05f84feb5ba962198b15. Transitive dependencies are exported from immutable upstream uv.lock using already-pinned uv in offline/frozen mode; install only wheels with --require-hashes in a separate environment. No extras, Tier 2/3, API keys or agent clients required. The base package contains LLM client libraries even in static mode: a separate supply-chain and installation-size concern, not authorization for model calls.

Direct scan contract: temporary snapshot of each skill, explicit --no-llm, JSON in private temporary directory, version/no-inference validation, actual components and sizes, completeness and rule IDs, snapshot immutability. Synthetic clean and P1-negative fixtures are never loaded into an agent. No shipped baseline, transitive scan or inspect-dependencies. Only aggregates in logs, no raw lines or paths. Environment isolation is not a network sandbox. Partial coverage and caveats are retained as such, not evidence of skill security; execution failure and inconsistent reports block CI.

Run: `python tools/check_skillspector_review.py --repo . --cli <path-to-skillspector>`.

[CI 45370414762](https://github.com/Sashido01/TESSERA/actions/runs/45370414762) PASS: 454+19 tests; 16/16 files, 100% coverage, complete_with_caveats (4 reference_missing), risk 78/100 HIGH, exit 1 (threshold 50 exceeded), 12 findings (10 MEDIUM, 2 HIGH), zero suppressions, both synthetic fixtures PASS, 13.32 s. T12.02.02.03 COMPLETE within direct static execution scope; findings and full NVIDIA security acceptance remain open.


## Finding inventory

| Rule | Severity | Count |
| --- | --- | ---: |
| AE4 | MEDIUM | 6 |
| AST4 | MEDIUM | 3 |
| LP3 | MEDIUM | 1 |
| MP3 | HIGH | 1 |
| RA1 | HIGH | 1 |

The pinned upstream CLI exits 1 if the risk score exceeds 50 even when execution is successful. The first CI interpreted this as an execution failure. The corrected wrapper distinguishes the documented risk exit from execution errors (exit 2) and checks agreement with the score. Findings are advisory, not confirmed vulnerabilities. Four missing references require portability review. No LLM calls are requested or reported; network isolation remains NOT_IMPLEMENTED.
