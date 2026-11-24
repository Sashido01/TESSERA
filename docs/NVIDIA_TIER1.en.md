# T12.01 — NVIDIA SkillEvaluator focused Tier 1

[Русский — оригинал](NVIDIA_TIER1.md) | **English — translation**

## Decision and scope

As of 24 November 2026, reviewed the official [v1.2.0 release](https://github.com/NVIDIA/SkillEvaluator/releases/tag/v1.2.0), source commit `5625c2534bf266f810aea489ffbe69da0bb2645e`, Apache-2.0 license. Only the base wheel, no extras. Release metadata records SHA-256 `cd367d655b567bb6015aa79b0229d1f268ad4fa0429619f896f5dccef8e6948a`. The 19 direct/transitive dependencies for Linux x86_64 CPython 3.13 are pinned to wheel versions and hashes from the [commit's uv.lock](https://github.com/NVIDIA/SkillEvaluator/blob/5625c2534bf266f810aea489ffbe69da0bb2645e/uv.lock). Separate venv, pip --require-hashes --only-binary=:all and pip check. This is neither cryptographic signature verification of NVIDIA's release nor a complete dependency licensing/vulnerability audit.

The official [Tier 1 reference](https://docs.nvidia.com/skills/skillevaluator/tier1-reference) distinguishes static and LLM stages. Generic validate may enable other tiers by default and is forbidden. Only the focused command `skillevaluator tier1 PATH --no-llm --checks schema,quality --min-score 70 -r json -o REPORT_DIR` is permitted. Isolated HOME and environment; no provider keys or GitHub token passed; PIP_NO_INDEX and UV_OFFLINE during evaluation. This is not an OS network sandbox; downloading pinned wheels in CI requires network access. Never execute skill contents, LLM stages, Tier 2/3. Never install [all], [llm], [tier2], [tier3].

## Acceptance

`tools/check_nvidia_tier1.py` checks exact version, copied catalog, completion of both validators, JSON, disabled LLM, consistent exit code and verdict, score from 0 to 100. A separate malformed synthetic skill must fail schema. Report contents and local paths are not published: only check identifiers, severity and score. Original sources must remain unchanged.

**Initial policy is advisory:** a valid report with a quality/schema FAIL does not make the skill PASS. CI blocks missing execution, incomplete/inconsistent reports or a missed negative test. Findings require review rather than automatic suppression. Evaluate English-language quality heuristics separately against the Russian original.

**T12.01 result (24 November 2026): selected checks PASS.** [CI 45358283596](https://github.com/Sashido01/TESSERA/actions/runs/45358283596) confirmed `NVIDIA_TIER1_FOCUSED_EXECUTION_PASS`: official wheel and 19 dependencies installed with hashes, pip check PASS, schema PASSED, quality PASSED, score 75.0/100 at threshold 70, 18 findings (7 medium, 11 low), negative fixture PASS, LLM DISABLED. 393 catalog tests and 19 skill tests PASS. First CI 45358033088 failed because the expected validator display name differed from its actual machine identifier `QUALITY`; corrected and verified in the second run. Findings were not suppressed. Full security and language-specific false positives remain unassessed. T12.01 COMPLETE within schema/quality scope. Overall T12 PARTIAL: security, PII, license, code-integrity, unicode, lint, dependency and harness-check are untested; full Tier 1, client-agent compatibility, false positives, complete cost and dependency license audit remain NOT_VERIFIED. No paid AI APIs. CI resource costs are not necessarily zero.

