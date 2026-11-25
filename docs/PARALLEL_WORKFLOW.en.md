# Continuous parallel development in TESSERA

[Русский — оригинал](PARALLEL_WORKFLOW.md) | **English — translation**

## Owner decision of 25 November 2026

GitHub work speed is an explicit requirement. Prefer native GitHub features; avoid excess complexity, mandatory external services and paid APIs. Every skill must operate locally without GitHub. Repository Workflow is the approved third skill; do not add other skills without owner approval. Never stop independent work because one stream awaits CI or a blocker.

## Practical cycle
1. Reconcile main, exact tag, all active PR/CI and work branches. Update the [technical debt register](TECHNICAL_DEBT.en.md).
2. Process completed checks; correct a specific failure on the same branch. One integration slot for shared VERSION/CHANGELOG; do not assign the next shared version until the slot is free. Draft branches without a new root VERSION are allowed; do not submit them to mandatory release CI until prepared as a candidate.
3. Stream 0 — infrastructure; then Microversion Release, Project Audit, Repository Workflow; new approved skills in catalog order. Check each stream; advance independent work with non-overlapping write scopes/resources. Preserve incomplete work. If all streams are busy, research an open roadmap/debt question rather than adding scanners for quantity.
4. Bind checks to exact SHA, current base and previous verified tag; squash only after required checks; confirm main CI and tag before next acceptance. Merge is not release. Do not remove a branch before verifying preservation of its result.
5. Record changes and blockers; GitHub Actions continues already started CI independently. Without a running executor, code does not evolve automatically between sessions.

## Speed
Measured validate baseline: main 45568501762 — 943 s, including 488 s for two Gitleaks history checks; PR 45569400436 — 700 s, including 345 s history. Source: jobs API, completion minus start. Shares 51.7% and 49.3%. First-stage goal: separate history job (host + Docker parity stay together), remaining checks in another job, final required validate succeeds only if both groups succeed. Preserve pinned Actions, read-only access, full coverage and tag gate. Demonstrate rejection on skipped/cancelled/failure, test negative cases, repeat CI on comparable snapshots. Do not claim acceleration from a calculated estimate. Next: measure queue, p50/p95 and runner-minutes; fast local checks, affected tests for feedback, verified artifact caching after audit. Reducing full critical path and time to first error matters more than job count.

## Native GitHub
The personal public repository does not support the organization-only Merge Queue; migration is unnecessary. Use one coordinator and expected HEAD checks (gh pr merge --match-head-commit), existing Rulesets, strict required checks and automatic removal of accepted branches. Issues with dependencies are optional for active work; the existing roadmap remains the stage register. Do not duplicate tasks or close them to obtain a zero counter. GitHub Projects optional. Concurrency only for appropriate CI groups, never cancel an unfinished unique release. Native templates and reusable workflows are preferred where beneficial. Ruleset/tag settings require a separate authorized operation.

## Local project profiles
Git without a remote, local branches/worktrees, native checks, VERSION/CHANGELOG under project policy, local task register and tags. Do not introduce GitHub, external services, telemetry or mandatory dependencies. Test Codex/Harness integration in actual environments. See [research](RESEARCH_REGISTER.en.md), [Repository Workflow](../skills/repository-workflow/README.en.md).

First measured parallel PR CI 45580026868: PASS, 431 s from group start to validate. 38.4% less than the previous PR #66 700 s; not a controlled benchmark. See second [debt register](TECHNICAL_DEBT.en.md) snapshot. Main v0.0.67 still awaits full CI and tag; optimization not accepted until then.
