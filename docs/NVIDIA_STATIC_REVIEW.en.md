# T12.02.01 — NVIDIA local static checks and profiles

[Русский — оригинал](NVIDIA_STATIC_REVIEW.md) | **English — translation**

Use pinned NVIDIA SkillEvaluator 1.2.0 from [T12.01](NVIDIA_TIER1.en.md), without additional packages. The official [source](https://github.com/NVIDIA/SkillEvaluator/tree/5625c2534bf266f810aea489ffbe69da0bb2645e) and profiles are pinned by commit. No LLM, Tier 2/3, generic validate, scanner auto-install or agent execution. PII, license, unicode and lint are explicitly selected by tier1 --no-llm --checks pii,license,unicode,lint. Check completion, PII/Unicode coverage and JSON/exit-code consistency. A synthetic Unicode BiDi override must produce HIGH/FAIL. Without a verified author/submitter identity, PII home-path detection has limited coverage. Skill license checking is not a full dependency license audit; a missing declaration is not verified compliance even when the advisory result passes.

## Russian quality

Retain the default score and every finding. A second run uses tools/nvidia-quality-ru.json (JSON is a YAML subset), adding Russian alternatives for prerequisites, limitations and troubleshooting headings and Russian error/validation terms. Keep the English terms, 5 points per heading and 25% reliability weight. Reconcile all four dimensions with the composite score. No threshold reduction, disabled rules or SKILL.md edits just to raise a score. Schema and hardcoded English heuristics and real documentation issues need manual review. Unknown findings stay UNCLASSIFIED; no raw messages, paths or PII values in CI logs.

## Compatibility

Actual harness-check uses vendor static profiles and **does not launch any client**. Compare copies of the same skill in isolated simulated roots: Codex (.agents/skills), Claude Code (.claude/skills), Copilot CLI (.github/skills), Hermes (.hermes/skills), OpenClaw (skills), OpenCode (.opencode/skills). Additional Codex custom-provider and explicit-invocation scenarios; negative Codex test in the wrong .claude/skills root. JSON records loads/degraded/not_loaded, profile versions/dates and finding IDs. DeepSeek Harness has no upstream profile in 1.2.0; it needs a separate project test. Actual discovery, loading, execution and hooks remain NOT_VERIFIED for every client.

## Acceptance

NVIDIA_TIER1_STATIC_REVIEW_EXECUTION_PASS proves completion of selected checks, not absence of findings. CI evidence pending. All inputs are disposable, HOME isolated and API keys not passed. Monotonic elapsed review time is not actual billing. T12.02.02: isolate and assess external SkillSpector/Gitleaks scanners, Bandit/code-integrity, dependencies and CVEs. Full Tier 1 remains NOT_VERIFIED; T12 PARTIAL.
