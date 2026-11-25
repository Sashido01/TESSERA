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

## Eighth snapshot — 25 November 2026

TD04: main v0.0.72 CI 45594813517 PASS; exact annotated tag 4dbbde7b0083398319837e97363e13aebb9444f8 → fab2aadb3d293f6d52ac457ea8097d52459a0623. 455 s through validate (10:25:17–10:32:52 UTC), catalog 347, history 451, source 186 s; vs v0.0.71 589 s, observed 22.8% reduction, different snapshots. PR #73 564 s, history 558 s, timing variability observed, history bottleneck. TD02: PR #73 CI 45595846652 PASS, merged as cd37acd7d17797a8849073a58f01d3caf16dadb5; main v0.0.73 CI and four independent tags still unverified. TD03 configuration COMPLETE. TD08: Git Inspector candidate v0.0.74 / 0.0.3, 13/13 local tests, four verified Git blobs; Evidence Core remains next component. TD09: Repository Workflow 0.0.2 candidate on repository-workflow-planner-hardening, e1b448a51253b3b151f38d1414bb493491bbdd91, 17/17 local Linux tests (13+4), NFC, Windows device names, duplicate JSON keys, linear DAG; independent local preflight, full acceptance open. Merged branches auto-delete; retain historical runs.
