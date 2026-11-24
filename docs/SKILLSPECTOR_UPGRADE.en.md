# T12.03.03 — SkillSpector security upgrade

[Русский — оригинал](SKILLSPECTOR_UPGRADE.md) | **English — translation**

## Rationale

In the verified 2.13.6 environment [CI 45375135316](https://github.com/Sashido01/TESSERA/actions/runs/45375135316), OSV returned entries for cryptography 49.0.0, langgraph 1.2.6 and pyasn1 0.6.4. The [official v2.13.7 release](https://github.com/NVIDIA/SkillSpector/releases/tag/v2.13.7) documents upstream dependency advisory updates. Its pinned uv.lock selects cryptography 50.0.2, langgraph 1.2.20, pyasn1 0.6.5. This is a remediation candidate, not evidence of zero CVEs.

## Contract

- Exact commit c323ad4c43e3c8f2de051572cc25b2711d11e648, official wheel SHA-256 e2356aa11f0d484f789543f25da6208fe2408641c8b16e7b59bc6600c5c39ffb.
- Separate environment, offline/frozen lock export, hash-verified wheels and pip check.
- Preserve explicit --no-llm, no baseline or transitive scan, component and byte validation, clean/negative controls, threshold 50 and exit consistency checks. Nonzero suppressions now block execution.
- Repeat OSV for actual installed versions and pinned upstream commit; review license metadata.
- [Release notes](https://github.com/NVIDIA/SkillSpector/blob/c323ad4c43e3c8f2de051572cc25b2711d11e648/docs/release/skillspector-2.13.7.md) describe the transition from the maintenance branch to main. The analyzer changed, so cross-version risk scores do not prove source remediation. Retain the historical 2.13.6 acceptance. Never tune rules or thresholds to obtain a desired result.

Status PARTIAL, actual CI required. Gitleaks/gh, legal compatibility, confirmed CVE reachability, native components and network sandbox remain separate tasks. No Tier 2/3 or paid APIs.

[CI 45376675127](https://github.com/Sashido01/TESSERA/actions/runs/45376675127) PASS: 494+19 tests; SkillSpector 2.13.7, 17/17 files, complete, 100%, 16 MEDIUM (AE4 6, AST3 6, AST4 3, LP3 1), zero HIGH, risk 53/100 HIGH, exit 1, zero suppressions, both fixtures PASS, 11.37 s. OSV: 74 Python distributions, zero packages with entries, zero source-commit entries; cryptography 50.0.2, langgraph 1.2.20, pyasn1 0.6.5. T12.03.03 COMPLETE within upgrade and repeat OSV scope; new AST3 and threshold exceedance remain open. Release awaits sequential acceptance.
