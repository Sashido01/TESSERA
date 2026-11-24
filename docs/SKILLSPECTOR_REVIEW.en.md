# T12.02.02.03 — SkillSpector static review

[Русский — оригинал](SKILLSPECTOR_REVIEW.md) | **English — translation**

Selected [SkillSpector 2.13.6](https://github.com/NVIDIA/SkillSpector/releases/tag/v2.13.6), Apache-2.0, commit e2674da339b0bddc6e565d059c0577c6d9cd25da: the source pinned in SkillEvaluator 1.2.0 ci/requirements/skillspector.in. Newer 2.13.7 is not adopted automatically. Official wheel SHA-256 e7b46c55e726405b2a068d375d1ee8e799e15d86f3fc05f84feb5ba962198b15. Transitive dependencies are exported from immutable upstream uv.lock using already-pinned uv in offline/frozen mode; install only wheels with --require-hashes in a separate environment. No extras, Tier 2/3, API keys or agent clients required. The base package contains LLM client libraries even in static mode: a separate supply-chain and installation-size concern, not authorization for model calls.

Direct scan contract: temporary snapshot of each skill, explicit --no-llm, JSON in private temporary directory, version/no-inference validation, actual components and sizes, completeness and rule IDs, snapshot immutability. Synthetic clean and P1-negative fixtures are never loaded into an agent. No shipped baseline, transitive scan or inspect-dependencies. Only aggregates in logs, no raw lines or paths. Environment isolation is not a network sandbox. Partial coverage and caveats are retained as such, not evidence of skill security; execution failure and inconsistent reports block CI.

Run: `python tools/check_skillspector_review.py --repo . --cli <path-to-skillspector>`.

Status: implementation awaits actual acceptance. Full NVIDIA security, CVEs and final Tier 1 acceptance are unverified.
