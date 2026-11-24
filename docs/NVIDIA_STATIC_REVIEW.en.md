# T12.02.01 — NVIDIA local static checks and profiles

[Русский — оригинал](NVIDIA_STATIC_REVIEW.md) | **English — translation**

Use pinned NVIDIA SkillEvaluator 1.2.0 from [T12.01](NVIDIA_TIER1.en.md), without additional packages. The official [source](https://github.com/NVIDIA/SkillEvaluator/tree/5625c2534bf266f810aea489ffbe69da0bb2645e) and profiles are pinned by commit. No LLM, Tier 2/3, generic validate, scanner auto-install or agent execution. PII, license, unicode and lint are explicitly selected by tier1 --no-llm --checks pii,license,unicode,lint. Check completion, PII/Unicode coverage and JSON/exit-code consistency. A synthetic Unicode BiDi override must produce HIGH/FAIL. Without a verified author/submitter identity, PII home-path detection has limited coverage. Skill license checking is not a full dependency license audit; a missing declaration is not verified compliance even when the advisory result passes.

## Russian quality

Retain the default score and every finding. A second run uses tools/nvidia-quality-ru.json (JSON is a YAML subset), adding Russian alternatives for prerequisites, limitations and troubleshooting headings and Russian error/validation terms. Keep the English terms, 5 points per heading and 25% reliability weight. Reconcile all four dimensions with the composite score. No threshold reduction, disabled rules or SKILL.md edits just to raise a score. Schema and hardcoded English heuristics and real documentation issues need manual review. Unknown findings stay UNCLASSIFIED; no raw messages, paths or PII values in CI logs.

## Compatibility

Actual harness-check uses vendor static profiles and **does not launch any client**. Compare copies of the same skill in isolated simulated roots: Codex (.agents/skills), Claude Code (.claude/skills), Copilot CLI (.github/skills), Hermes (.hermes/skills), OpenClaw (skills), OpenCode (.opencode/skills). Additional Codex custom-provider and explicit-invocation scenarios; negative Codex test in the wrong .claude/skills root. JSON records loads/degraded/not_loaded, profile versions/dates and finding IDs. DeepSeek Harness has no upstream profile in 1.2.0; it needs a separate project test. Actual discovery, loading, execution and hooks remain NOT_VERIFIED for every client.

## Acceptance

NVIDIA_TIER1_STATIC_REVIEW_EXECUTION_PASS proves completion of selected checks, not absence of findings. First live CI confirmed. All inputs are disposable, HOME isolated and API keys not passed. Monotonic elapsed review time is not actual billing. T12.02.02: isolate and assess external SkillSpector/Gitleaks scanners, Bandit/code-integrity, dependencies and CVEs. Full Tier 1 remains NOT_VERIFIED; T12 PARTIAL.

**Live acceptance:** [CI 45360122208](https://github.com/Sashido01/TESSERA/actions/runs/45360122208) SUCCESS; NVIDIA_TIER1_STATIC_REVIEW_EXECUTION_PASS. 403 catalog + 19 skill tests passed. 5.70 s is measured elapsed review time in the first run, excluding dependency installation and the rest of CI; actual billing was not measured. T12.02.01 COMPLETE within local assessment; T12.02 remains PARTIAL.

### Microversion Release results

| Dimension (weight) | Default | RU overlay |
|---|---:|---:|
| Correctness (35%) | 65 | 65 |
| Discoverability (25%) | 80 | 80 |
| Reliability (25%) | 75 | 90 |
| Efficiency (15%) | 90 | 90 |
| Total | 75.0 | 78.8 |

0.35×65 + 0.25×80 + 0.25×75 + 0.15×90 = 75.0; reliability 90 gives 78.75 (rounded to 78.8). Schema PASS in both runs. Threshold 70 and other dimensions unchanged. 18 original findings (7 medium, 11 low), 16 after localization (7 medium, 9 low). Skill files unchanged.

| Original reason code | Count | Conclusion and decision |
|---|---:|---|
| EN_INSTRUCTIONS_HEADING / EN_EXAMPLES_HEADING | 2 | Recommended English headings; Agent Skills body format is unrestricted. Improve explicit instructions/examples rather than changing language for a heuristic. |
| BILINGUAL_README | 1 | README.en.md is intentional bilingual structure; retain it. |
| AUTHOR_METADATA_MISSING | 2 | One fact repeated in schema and quality; agree on public attribution, never require email/personal data. |
| SCHEMA_DESCRIPTION_TRIGGER / EN_DESCRIPTION_TRIGGER | 2 | Russian opening already gives usage context; English-language heuristics. Separately assess Hermes truncation; shorten and put trigger first. |
| SCRIPT_TABLE_MISSING | 1 | Add readable script/argument/limit table or list. |
| NONSTANDARD_RUN_SCRIPT_HEURISTIC | 1 | Python invocation examples exist. run_script is not a universal interface; do not require it. |
| EXAMPLE_FORMAT_HEURISTIC | 1 | Inline command examples exist; add clear scenarios including failures. |
| TAGS_METADATA_MISSING | 1 | Recommended field; test type and portability against skills-ref before adding. |
| DESCRIPTION_LENGTH | 1 | Longer than quality recommendation; shorten without losing invocation conditions. |
| EN_PURPOSE_HEADING | 1 | Purpose is already documented in Russian. |
| EN_ERROR_TERMS | 1 | Language bias; resolved by overlay (10 reliability points). |
| PREREQUISITES_HEADING_MISSING | 1 | Explicitly document Git, Python for scripts, permissions and inputs. |
| LIMITATIONS_HEADING_MISSING | 1 | Existing Russian purpose/limitations section recognized by overlay (5 reliability points). |
| TROUBLESHOOTING_HEADING_MISSING | 1 | Separate failure and recovery scenarios. |
| NESTED_REFERENCE_LINK | 1 | Some links are intentional bilingual navigation; references/INTEGRATION.md and its translation also link to ../../../docs which may be absent after standalone installation. Fix portability without removing translations. |

18 records, not 18 independent defects. Only EN_ERROR_TERMS and LIMITATIONS_HEADING_MISSING disappear in the locale overlay. Other findings remain visible. Separate substantive skill improvements with regression tests from evaluator acceptance.

### Static checks

- Unicode: PASSED, 16 files, zero findings, negative BiDi fixture PASS.
- PII: PASSED, 16 files, one medium ip_addresses finding, two warnings. Independent inspection of all 16 source files found one IPv4-shaped literal in an invalid-version test at tests/test_next_version.py:67, matching NVIDIA's regex. Strong evidence of a false positive, but the location in raw JSON was not independently verified. Do not suppress the rule. Home-identity coverage NOT_VERIFIED.
- License: PASSED with warning, license_status=not_detected. Repository root LICENSE is MIT; standalone skill has neither license declaration nor license file. Standalone portability requires an explicit license; PASS does not establish license compliance.
- SCRIPT_LINT: PASSED, two low magic_numbers findings. Not full lint or all-language coverage; raw locations were not retained; review constants rather than mechanically replacing them.

### Static profiles

Upstream profile dates are 1 November 2026; these are compatibility model versions, not detected client versions.

| Profile | Version | Result | Limits |
|---|---|---|---|
| Codex | 0.166.0 | loads | Custom provider degraded (CX-SHELL-READ); explicit invocation loads. Wrong root not_loaded, CX-ROOT negative test PASS. |
| Claude Code | 2.1.316 | loads | No profile findings in the simulated setup. |
| Copilot CLI | 1.0.105 | loads | CP-RELOAD, account for skill reload. |
| Hermes | main c419cf7c864a (binary 2026.9.24) | loads | HM-TRUST, HM-DESC-60, HM-LINKED-LAYOUT: project trust, description truncation, files outside typical folders. |
| OpenClaw | 2026.10.9 | loads | No profile findings in the simulated setup. |
| OpenCode | 1.19.5 | loads | OC-RELOAD, account for caching. |
| DeepSeek Harness | no profile | NOT_VERIFIED | Separate project matrix required. |

SKILL.md has 6712 Unicode characters, 11266 UTF-8 bytes in commit e4fef7a12b733d2fde0d212de9a9bad0820ef2b9. The custom-provider CX-SHELL-READ profile threshold is 10000 bytes, so the warning has a concrete basis; verify the actual installed client separately. Move detail to references while retaining mandatory rules. Real agent execution/compliance remains NOT_VERIFIED.

Next: T12.02.02 external scanners and CVEs; T12.03 substantive remediation of confirmed findings, portable license, link checks, smaller mandatory context and reevaluation; separate live client test T13. Never enable Tier 2/3 or paid AI APIs.
