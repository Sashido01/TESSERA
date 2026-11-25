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
