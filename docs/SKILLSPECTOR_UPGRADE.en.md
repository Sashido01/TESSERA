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


## T12.03.05 — finding localization (candidate)

The pinned `Finding.to_dict()` implementation in `src/skillspector/models.py` contains a primary `location` and a separate `occurrences` list. The wrapper now emits only validated primary coordinates: rule, severity, relative inventory path, start and optional end line. Unknown, absolute or malformed paths/coordinates are not emitted; their count is recorded in `primary_locations_unresolved`. Beyond 1000 rows, `primary_locations_omitted` increases. Overall finding counts are unchanged. The byte-based limit is an upper bound on line count, not exact line verification. Code snippets, messages, context and occurrences are not emitted. This is diagnostic preparation, not finding remediation; live CI acceptance is required.

## TD13 — pre-install wheel to source tree comparison

`tools/check_skillspector_wheel.py` reads the ZIP without installing, extracting files or importing it. The official [NVIDIA v2.13.7 page](https://github.com/NVIDIA/SkillSpector/releases/tag/v2.13.7) shows signed and verified commit `c323ad4c43e3c8f2de051572cc25b2711d11e648`; the GitHub Release API reports a 1,342,092-byte wheel with SHA-256 `e2356aa11f0d484f789543f25da6208fe2408641c8b16e7b59bc6600c5c39ffb`. These values matched independently downloaded bytes. On Windows 11 / Python 3.14.3, the checker matched 169 package files to Git blobs at that source commit; all 174 wheel entries and 174 RECORD rows were accounted for, and RECORD, metadata, license and console entry point passed. Result: `source_blob_match=PASS`, `record=PASS`, `execution=NOT_RUN`; 9/9 checker tests passed.

[OSV MAL-2026-6561](https://osv.dev/vulnerability/MAL-2026-6561) includes version 2.13.7 of the PyPI `skillspector` package and describes an injected telemetry module. The verified GitHub wheel contains no extra module and its files match the official source tree. This distinguishes distribution sources, but does not prove the scanner is generally safe or establish runtime behavior.

The workflow candidate downloads the asset from the pinned HTTPS URL, runs preflight before installation, then gives pip that same local `file://` wheel with `--require-hashes`; the package has no remote URL fallback. Local Windows workflow-security checks: 39 PASS, 1 Linux-only SKIP; negative cases for a removed gate, late ordering, remote wheel and permissive off-domain redirect are rejected. PR/main CI for this workflow change remains required; TD13 and Issue #76 remain PARTIAL until it completes.
