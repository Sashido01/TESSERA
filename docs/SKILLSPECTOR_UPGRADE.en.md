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

Candidate `tools/check_skillspector_wheel.py`: archive read only, no installation, extraction or import. Pin SHA-256 and 1,342,092 bytes of the official GitHub release asset 2.13.7; Git tree commit c323ad4c43e3c8f2de051572cc25b2711d11e648 contains 169 src/skillspector files (5,201,401 bytes) and two license/notice files. Verify each package file against Git blob, missing/extra entries, RECORD SHA-256/size/coverage, metadata and sole expected console entrypoint. Reject traversal, links, case-insensitive duplicate names, unexpected startup/.data files. Limits: 512 entries, 8 MiB per file and 16 MiB total. 9/9 synthetic Linux Python 3.13.5 tests PASS. Actual release wheel bytes not yet obtained; WHEEL_PROVENANCE NOT_VERIFIED; neither safety nor absence of MAL-2026-6561 is established. Next: independently check the downloaded official wheel before pip install using the same verified local file and hash pin, then native Windows/Linux unit tests and full CI. No main change or gate weakening.
