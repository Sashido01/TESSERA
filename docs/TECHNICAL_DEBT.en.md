# TESSERA technical debt register

[Русский — оригинал](TECHNICAL_DEBT.md) | **English — translation**

Observation snapshot 25 November 2026: main v0.0.66, SHA a550e0e638ca51a8a9b034773930da7ba5c25796, CI 45572387469 PASS and exact annotated tag verified. Branch/CI status changes; reconcile API and local Git rather than treating this snapshot as live. Close records only with fact, SHA, check and residual limits. Active branches are not abandoned branches. Do not delete work to reach a zero Issues/PR count.

| ID | Priority | Debt and closure criterion | Snapshot state |
|---|---|---|---|
| TD01 | P0 | PR #67 FULL_TIER1_SCANNER_VERSION:bandit: verify tests-only runtime coverage in live CI; no threshold reduction | CI_FAILED, correction a2d4b25f04ecc277d646e673b8c09189fad20914 sent |
| TD02 | P0 | Independent skill tag: its VERSION, exact annotated commit, remote/report/preflight, legacy compatibility | IN_PROGRESS, t16-skill-tag-inspection |
| TD03 | P0 | Ruleset refs/tags/v* does not cover namespaced skill tags; agree on extension and verify without destroying published tags | OPEN |
| TD04 | P0 | CI bottleneck: 488/943 s and 345/700 s history; split independent jobs, fail-closed required aggregate, measure wall-clock and runner-minutes | OPEN |
| TD05 | P0 | T12: Semgrep host isolation, advisory applicability (mcp, opentelemetry-api, wcmatch), Go reachability, TOCTOU/junction, output/resource bounds; close specific risks with evidence | PARTIAL |
| TD06 | P0 | T03–T05/T13: actual Microversion Release installation, discovery and enforcement in Codex/Harness; local OS and multi-agent behavior | NOT_VERIFIED |
| TD07 | P1 | Sync roadmap with T09/T10: pin/update and ZIP partly verified; distinguish local checks from actual host | OPEN |
| TD08 | P1 | Project Audit level I: PR #67 and E01–E20; separate Inventory Engine candidate, integration and Windows check | PARTIAL |
| TD09 | P1 | Repository Workflow: approved methodology, local planner, actual evals, portability, bootstrap | PARTIAL |
| TD10 | P1 | Late version assignment, DAG, resource isolation, base update and revalidation without force-push; live GitHub parallel branch trial | PARTIAL |
| TD11 | P1 | T17: independent releases, current artifact-specific attestation, safe update/rollback; Git tag is not GitHub Release | OPEN |
| TD12 | P1 | Runner: time/output/descendant bounds, error classification, no ordinary successful tests blocks PASS; Windows regression | PARTIAL |
| TD13 | P0 | [#76](https://github.com/Sashido01/TESSERA/issues/76): MAL-2026-6561; verify official wheel bytes, sources and isolation without suppression | OPEN — digest and upstream tree confirmed, wheel NOT_VERIFIED |
| TD14 | P0 | [#77](https://github.com/Sashido01/TESSERA/issues/77): Project Audit HIGH PE3, establish synthetic nature and repeat validation | OPEN — exact rule located |
| TD15 | P1 | [#78](https://github.com/Sashido01/TESSERA/issues/78): unified current RU/EN state including practical pilot | IN_PROGRESS — candidate instructions |
| TD16 | P0 | [#80](https://github.com/Sashido01/TESSERA/issues/80): Windows DirEntry.stat identity; native Windows 3.14 retest | OPEN — RED→GREEN Linux, 21/21; candidate 91765d47e978aa9f968b1589746131d165dab669 |

## Hygiene each cycle
Check open Issues separately from PRs, branches and worktrees, active tasks/dependencies, failed/cancelled/stale checks, missing tags, docs, TODOs/duplication, dependencies and risks. For each finding record source/priority/criterion; do not duplicate. Correction → relevant check → evidence → close original record. Owner action means WAIT_OWNER while independent work continues. After squash do not declare a branch redundant by ancestry alone; verify accepted diff/PR and local data. Remove only authorized merged branches, without force. Do not hide debt or close it formally. See [ROADMAP](ROADMAP.en.md), [parallel work](PARALLEL_WORKFLOW.en.md).

## Status review of 25 November 2026 — second snapshot

- main v0.0.67, SHA 9700c0f0a2dab9180cbb442538541242dcb5d5d7, PR #67 merged; PR CI 45576826805 PASS, main CI 45579382735 IN_PROGRESS, v0.0.67 tag absent. Last fully verified catalog v0.0.66.
- TD01: Bandit correction verified by PR CI 45576826805 and merged; main check still in progress. Do not retry resolved failure 45573171262 without reason; historical FAIL remains evidence, not an active run.
- TD04: [PR #68](https://github.com/Sashido01/TESSERA/pull/68), SHA 1fa59f822ced9da2250a3e014b3dad32ad294b13, CI 45580026868 PASS. catalog_checks 366 s, history_checks 425 s, aggregate validate 4 s. Group start 08:51:50Z to validate completion 08:59:01Z — 431 s. Prior PR #66 700 s; observed reduction (700−431)/700=38.4%. Different snapshots, not a controlled comparison. Merge awaits exact v0.0.67 tag; sustained speedup NOT_VERIFIED.
- TD02: independent preflight, report, remote and four additional regressions — commit ec114cebfd0d616bea080f788bc0c7f6a9c3ca27 on t16-skill-tag-inspection; tests of that exact commit not run. Independent tag publication and protection remain open.
- TD08: Inventory Engine, 17/17 Linux unit tests; four Git blobs match locally tested bytes; commit 47f590f84780e0d3d274c703c4d19dff555c95d0 on project-audit-inventory. Version assignment and integration pending.
- TD09: Repository Workflow 13/13 local planner tests; Git blobs match, full CI and agent acceptance open.
- Zero ordinary open Issues; one open PR #68; main plus ci-parallel-history, repository-workflow-level-i, t16-skill-tag-inspection, project-audit-inventory. Merged project-audit-level-i absent. Do not delete four work branches before completion; reconcile live state again.

Rule: retain closed or corrected historical CI. Do not delete workflow runs, logs, artifacts or Issues for cosmetic metrics. Cancel only demonstrably obsolete unfinished checks with permission and without breaking the gate; never cancel unique main/release checks.

## Third snapshot — 25 November 2026

TD01: COMPLETE in scoped CI — corrected PR #67 and main v0.0.67 CI 45579382735 PASS, exact tag d4697fa65ca77a687d8dea66e80a71089303b961 points directly to 9700c0f0a2dab9180cbb442538541242dcb5d5d7. TD04: PR #68 PASS and merged as a8d54510b06d47da2b0d872cb067caee99ad598d; main CI and tag pending, repeat timing required. TD08: audit level I accepted in catalog, independent release/runtime not verified; inventory branch pending. TD09: candidate integrated for PR checks, not yet accepted. Historical observations above retained as evidence, not current state.

## Fourth snapshot — 25 November 2026

TD04: main v0.0.68 CI 45582720006 PASS; exact annotated tag 561e32bedd42fb520997d2e7af13f8add77d8b34 → a8d54510b06d47da2b0d872cb067caee99ad598d. Both groups and validate passed. Group start 09:09:31Z to validate completion 09:18:46Z — 555 s, compared with 1004 s main v0.0.67 (08:47:33Z–09:04:17Z). Observed reduction 44.7%, not a controlled benchmark. CI split accepted; further optimization and p50/p95 remain open.

TD09: PR #69 CI 45583029569 PASS, accepted into main 7fd8f698f818cbfabd7986d7c5e536d711f158b7. Repository Workflow 0.0.1 in catalog; main v0.0.69 CI and tag pending, actual activation and independent release NOT_VERIFIED.

TD02: v0.0.70 candidate includes independent inspect/preflight/remote/report, separate Microversion Release plan; tests for these changes still require CI. TD03 WAIT_OWNER: existing Ruleset does not cover one-level skill tags; procedure in VERSIONING. TD12: 13/13 Linux runner tests (three new), tested Git blobs 935a7321f10adf7de28092594be715978fbac4a4 and f790e0e31943d886687ac164b6277b3f59f7f7af; immediate process timeout, independent skills continue. Descendants, output volume and Windows remain open. TD08: Inventory Engine 0.0.2 on separate work branch, next integration slot after this candidate is verified.

## Fifth snapshot — 25 November 2026

TD09: main v0.0.69 CI 45584865396 PASS, exact annotated tag fec4f7059312009388c1322b42a31a558f2cc981 → 7fd8f698f818cbfabd7986d7c5e536d711f158b7. Repository Workflow source accepted; actual agent trials and independent release open. TD02/TD12: PR #70 CI 45585153819 PASS, accepted as 5787940fdc50122707a4456a232e2c37023eaed3; main v0.0.70 CI and tag pending. TD08: v0.0.71 / Project Audit 0.0.2 candidate, inventory 17/17 locally, separate local plan; Git Inspector candidate 13/13 locally, not included. TD03 WAIT_OWNER unchanged. TD04: main v0.0.69 through validate 625 s (09:23:03Z–09:33:28Z), catalog 621 s, history 401 s; snapshots, queues and catalog expansion affect timings. Catalog is now the longer job in this run; choose optimizations based on step timings. Do not reduce coverage.

## Sixth snapshot — 25 November 2026

TD02/TD12: main v0.0.70 CI 45586815303 PASS, exact annotated tag 4a2f4046ffdbd01fb848f7ced14627db183a7495 → 5787940fdc50122707a4456a232e2c37023eaed3. Independent preflight/remote/report and immediate-process timeout accepted and CI-verified; independent publication, descendants, output and Windows remain open. TD08: PR #71 CI 45587061192 PASS, merge 0983994f1fb21b79b8592351d6308c4acdc1ce13, Project Audit 0.0.2 in main; main CI and tag pending. Git Inspector remains a separate candidate. TD03: API Ruleset 27932769 still active, include refs/tags/v*, no bypass/exclusions; owner must add */v* to Target tags, leave Restrict creations off, retain existing restrictions. TD04: v0.0.70 main 634 s through validate (09:35:19–09:45:53 UTC), PR #71 591 s (09:36:52–09:46:43 UTC). v0.0.72 candidate moves four source/path checks into a third job; actual result not measured yet. Retain historical CI.

## Seventh snapshot — 25 November 2026

TD03: COMPLETE (configuration); API Ruleset 27932769 updated 13:22:56 +03:00, active, refs/tags/v* and refs/tags/*/v*, empty exclusions/bypass, deletion/non_fast_forward/update retained; creation unrestricted. No destructive tests on actual tags. TD02/T16: automatic publication candidate, local 13/13 (1.486 s) on disposable Git/bare remote; four historical sources verified, live GitHub publication pending. TD08: v0.0.71 CI 45589558047 PASS, exact tag 5979332e6eb1f107c61f2dd3c4684335df95c3d6 → 0983994f1fb21b79b8592351d6308c4acdc1ce13; inventory accepted, Git Inspector ready on separate branch. TD04: PR #72 CI 45589799232 PASS, merge fab2aadb3d293f6d52ac457ea8097d52459a0623; 579 s through validate, catalog 297 s, history 575 s, source 244 s. Main v0.0.71 589 s; observed improvement only 10 s on different snapshots, runner-minutes may rise, sustained benefit NOT_VERIFIED. Main v0.0.72 and tag pending.

## Eighth snapshot (recovery) — 25 November 2026

TD02 BLOCKED: main v0.0.73 run 45597537888, attempts 1 and 2, validate PASS, exact catalog tag 7887314fad80eac721ae83daf813d15d86c431a9 → cd37acd7d17797a8849073a58f01d3caf16dadb5, publish skill tags FAIL SKILL_TAG_GIT_FAILED; 0 independent refs. Jobs 139152988127 and 139153843655. Cause NOT_VERIFIED, do not claim GitHub lacks atomic support. Retried once; no further unchanged retries. v0.0.74 candidate: 19/19 (13+6) Linux, safe diagnostics, atomic probe and controlled sequential fallback; live GitHub requires full CI. TD03 configuration COMPLETE unchanged. TD08: Git Inspector PR #74 CI 45597789543 PASS, not merged, branch preserved 6008b86a75e174fe6f5b33913ac63bee5b76d2a6, version released for narrow repair; Evidence Core separate branch project-audit-evidence-core 48ad1278629a0be5ea824dfb7a9e068b7e7c045c, 15/15 Linux, excluded. TD09: Repository Workflow 0.0.2 candidate e1b448a51253b3b151f38d1414bb493491bbdd91, 17/17 local. No ordinary merges until publication recovery; only narrow recovery PR with full CI, protection unchanged and previous exact catalog tag verified. TD04: v0.0.72 main 455 s through validate vs 589 s v0.0.71, observed 22.8% reduction on different snapshots; history bottleneck. Retain failed-run history.

**Actual Codex acceptance:** 3/3 installations OWNER_REPORTED_PASS, Microversion Release 38/38 and Repository Workflow 13/13 Windows; Project Audit Windows FAIL #80, correction candidate 91765d47e978aa9f968b1589746131d165dab669, local Linux 21/21; native retest, agent discovery, invocation, auto-use and mandatory gate NOT_VERIFIED. [Evidence](AGENT_PILOT.en.md). TD06/T05 PARTIAL, TD16 OPEN; Harness pilot remains open.

25 November 2026: TD17 #81 remains OPEN (safe Git context refusal, actual invocation); TD18 #82 OPEN (full Windows catalog suite: 710 / 9 errors / 1 skip on v0.0.75); TD06/TD15 PARTIAL (3/3 install/discovery/explicit use owner-reported; automatic behavior 2 pass / 1 partial; enforcement incomplete); candidate 5a03fc7a7dd402287193108ddbb1f1ef168bb2d1 CI 45620060381 native skill suites 94 pass / 1 skip, Linux catalog 712 tests run; Project Audit E2 HIGH remains policy FAIL, PE3 absent; correction + scope guard + full Windows suite candidate 054154dc6fcc899e1a611227cf881f2fd01f47c0 pending CI. [Evidence](AGENT_PILOT.en.md). No new tag or merge while independent publication remains blocked.

### Next snapshot — 25 November 2026

TD02/T16 BLOCKED ([#83](https://github.com/Sashido01/TESSERA/issues/83)): owner-reported Rule Suites 5360899907, 5359993044, 5359256574, 5359221161 all failed on creation of refs/tags/microversion-release/v0.0.1 (before_sha is 40 zeros). Latest suite detail requires owner access (connector 403). Ruleset 27932769 unchanged; do not retry push until the specific rule is identified. TD18 #82: Windows CI 45626552407 full catalog 713 = 705 PASS + 1 FAIL + 4 ERROR + 3 SKIP, skill suites 39/39 + 43/44 (FIFO skip) + 13/13. Four Linux secure-open Bandit/Gitleaks scenarios and canonical reference-skills fixture root addressed in 45eaeed021eb4fc36c805d2260aa2d0071f1abdd; new CI 45627814264 not completed. TD14 #77: same catalog_checks 139248180713 PE3/E2 absent, risk 53 vs 72, 9 MEDIUM + 1 LOW, standalone 0 individual HIGH; integrated policy FAIL due to aggregate >50. Do not change threshold; investigate remaining findings. None of this replaces acceptance into main, independent tags or repeat agent acceptance.

### Confirmed TD02 cause and full Windows PASS — 25 November 2026

Owner-reported rule-suite 5360899907: `workflow_updates` FAIL (GitHub App lacks workflows permission for historical `.github/workflows/validate.yml`); secret_scanning and ruleset 27932769 update/non_fast_forward/deletion PASS. Do not weaken ruleset. One-time owner historical tag recovery from an isolated fresh clone at exact main 115f79daae5886606261cb59c4d5ab2fd045f173: plan-only `tools/publish_skill_tags.py`, verify four historical pairs (catalog v0.0.66/67/69/71) and explicitly publish sequentially. Do not store credentials in CI or code. Annotate new tags, create absent refs only, never move existing refs; verify remote and rerun failed main tag job. #83 OPEN until actual proof.

TD18 #82: 45627814264 Windows job 139252599141 exact 45eaeed021eb4fc36c805d2260aa2d0071f1abdd SUCCESS: catalog 715 = 708 PASS + 7 platform SKIP; skills 96 = 95 PASS + 1 FIFO SKIP. Linux-only secure-open and Bash checks are not claimed as Windows runtime. Full Linux/combined gate not yet completed at observation, main remains v0.0.75. New candidate 892cdaca33bdeb9c679a674d672c700dbd2e11e6 additionally checks Project Audit test import origin; repeat CI/scanner not yet confirmed. Do not update installed v0.0.74 before acceptance.

### Latest verified candidate — 25 November 2026

PR #74 exact 892cdaca33bdeb9c679a674d672c700dbd2e11e6, CI 45628965053 SUCCESS for all required groups. Windows catalog 715 = 708 PASS + 7 platform SKIP, skills 98 = 97 PASS + FIFO SKIP; total 813 = 805 PASS + 8 SKIP. SkillSpector 2.13.7 risk: Microversion Release 30, Project Audit 38 (previously 72→53; 7 MEDIUM + 1 LOW), Repository Workflow 14. FULL_TIER1 all policy verdicts PASS; advisory review, not certification. TD14/TD16/TD18: PR evidence PASS, main acceptance and repeat agent acceptance open. TD02 #83: owner reported GitHub CLI refresh, repo/workflow scopes were previously present; independent refs still 0, actual one-time publication required. TD13 #76: 9db01ec3170a5a3c684fc82eb9d5bd54cd2c337a, separate skillspector-provenance-preflight branch, static wheel verifier 9/9 synthetic Linux PASS; actual release wheel bytes and preinstall gate integration NOT_VERIFIED. Main and green PR unchanged; no new catalog version reserved on the branch before sequential merge slot.
