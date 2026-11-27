# Project Cleanup changelog

[Русский — оригинал](CHANGELOG.md) | **English — translation**

## 0.0.2 — Git-aware cleanup plan

- Optional comparison of two Git capture sets and metadata, HEAD/index/untracked protection, explicit scopes, resource bounds, opt-in private details. No deletion or Git execution. 28/28 Linux PASS, including staged deletion and sparse-index actual Git fixtures. Native CI and client acceptance open.
- PC01 0.0.1 verified by independent annotated tag; Linux 21 PASS, Windows 20 PASS + FIFO SKIP in v0.0.90.

## 0.0.1 — Safe inventory and cleanup workflow

- Initial independent skill, metadata-only inventory, traversal bounds, REVIEW classification, aggregates and private details.
- Local, Git and GitHub cleanup verification, growth prevention and measurable acceptance. No automated deletion; CI and client acceptance required.

Isolated Linux evidence: 18/18 tests PASS; source and test Git blobs matched exactly. Synthetic fixture: 10000 files × 128 bytes = 1280000 logical bytes, three inventory passes 104/114/103 ms, median 104 ms. Not a Windows or actual project benchmark; native CI and client tests pending.

- Pre-merge hardening: protected-store exclusions, explicit profile/ancestor refusal, additional protected filename hints, three regression methods including no-content-access assertions. Prior 18-test evidence applies to the earlier source; renewed CI required. No scanner suppression.
