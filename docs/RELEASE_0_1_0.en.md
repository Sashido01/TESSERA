# TESSERA 0.1.0 — first product release readiness criteria

[Русский — оригинал](RELEASE_0_1_0.md) | **English — translation**

Status: preparation plan (not a 0.1.0 release). Baseline 26 November 2026: v0.0.83 / Project Audit 0.0.5 merged in PR #90, main CI 45778355203 SUCCESS (6/6), exact commit d830dc03c2c6575f69ae45a00fd6f7f22ef4feb4, annotated objects v0.0.83 efc73a7313c0ec7ac0715abc5e512fae482e2b67 and project-audit/v0.0.5 b0b5fa73b64f87022520ca3f447616fa9b408e00. Owner priority: finished 0.1.0 without dummy microversions.

## Product boundary

Three standalone skills: Microversion Release, Project Audit, Repository Workflow. RU-first + EN, offline helpers, verifiable sources and official exact-tag distribution. Full local Git without GitHub. Codex and DeepSeek Harness are target actual acceptance environments. Do not claim Claude Code/Hermes compatibility without actual separate trials; no paid APIs, third-party managers or mandatory service. Extended graphs, automatic DELTA reuse, semantic level V, extra platforms and optimizations are outside minimum readiness of these three skills without separate owner agreement. Mandatory unfinished protection is not a future feature.

## Release gates

| ID | Mandatory outcome | Evidence / status |
|---|---|---|
| G01 | Sequential VERSION, bilingual changelog, immutable annotated catalog and independent tags | v0.0.83 verified; future v0.1.0 NOT_VERIFIED |
| G02 | All 6 main jobs on exact commit and attempt, full catalog, native Windows/Linux | fixed CI profile candidate; new CI required |
| G03 | Safe install of each skill by separate pin into clean directory, duplicate refusal | historical single pin and local multi-skill PASS; current remote multi-skill open |
| G04 | Safe update/rollback of individual skill, preservation of others and local edits | historical fixture PASS; current three independent refs and actual profile open |
| G05 | Codex and Harness: discovery, explicit and automatic use of every skill, P01–P08 and relevant E/RW | current client pilot NOT_VERIFIED; #81 open |
| G06 | Microversion Release: positive/negative release fixture, exact tag, no false COMPLETE on hook/CI failure | deterministic tests PASS; actual least-privilege invocation and enforcement open |
| G07 | Project Audit: selected-project boundary, conflicting evidence, incomplete scope, truthful report | sources/tests accepted; actual E01–E20 open |
| G08 | Repository Workflow: LOCAL/GitHub, conflicting scopes, independent tasks, safe hygiene, recovery | planner accepted; worktree candidate and actual RW01–RW20 open |
| G09 | Security: no unresolved blocking risk for claimed operations; unchanged required checks; justified known limits and nonapplicability | T12 PARTIAL; advisory/TOCTOU/resource risks scoped, no sandbox claim |
| G10 | Separate reproducible ZIP from exact v0.1.0, SHA-256, manifest, verified Sigstore/SLSA attestation | v0.0.21 historical PASS; v0.1.0 NOT_RUN |
| G11 | Close #78/#81 by criteria, no unfinished release PR/CI; remove preserved/unused branches after verification | OPEN; local worktrees require owner |
| G12 | Final independent evidence, instructions, supported/unverified environments, known limits; agreed GitHub Release decision | NOT_STARTED; no GitHub Releases at baseline |

All mandatory criteria for claimed scope must be evidenced. Any NOT_VERIFIED mandatory item blocks readiness claims. The owner may explicitly change product scope, not assign PASS to an unexecuted criterion. Do not compute a readiness percentage from row counts. Historical results do not transfer to changed files, skill trees, environments or policies.

## Sequence

1. Accept actual changes only; assign next component version when integration slot is free. [VERSIONING](VERSIONING.en.md) permits 0.0.99 → 0.1.0 after genuine readiness; unfinished work may continue at 0.0.100+. No empty commits to fill numbers and no policy weakening for deadlines.
2. First address release-critical CI profile, TD04 and RW05, reconcile #78. Never speed up by dropping scans. Then actual multi-skill pin/update/rollback, independent verification and minimal adapters with positive/negative trials. Run pilot in parallel.
3. Before assigning 0.1.0, agree exact scope, freeze optional changes, finish pre-release acceptance on exact SHA. After merge check main CI, annotated tags and exact trees; any failure leaves BLOCKED.
4. Dispatch `build-attested-catalog.yml` **on v0.1.0**, not main. Download artifact, verify actual bytes, reproducibility, signer workflow, source-ref and source digest with official gh. Check report/certificate, which is not itself a signature. See [Trusted Build](TRUSTED_BUILD.en.md).
5. If owner agrees to GitHub Release, use existing tag, prepare draft with verified ZIP and RU/EN notes, verify everything before publication. Do not recreate/move tags. Immutable Releases protect assets and tag after publication; complement Rulesets and provenance verification, never replace them. After publication check metadata and actual bytes. [GitHub immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases), [verify release integrity](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/verify-release-integrity).

## Owner actions (necessary parallel checks)

- From ordinary trusted Windows terminal, not agent sandbox: inspect cleanliness, current branch, worktrees, Git/Python/gh versions; synchronize only fast-forward after checking. Never remove GIT_* or weaken permissions. Reconcile 0.0.82 / 0.0.83 after exact tag confirmation.
- Fresh disposable project for each client; [AGENT_PILOT](AGENT_PILOT.en.md) with verified pins. Record actual client versions, INSTALL, DISCOVERY, EXPLICIT_USE, AUTO_USE, ENFORCEMENT, UPDATE/ROLLBACK and exit codes. `python scripts/release_tag.py context` from installed Microversion Release invokes no Git; on unsafe context stop Git operation, return names and status only. Actual release fixtures only with authorization and without remote; no production data.
- Check old branches after preservation review: do not delete if occupied by a worktree or carrying unique changes. First project-audit-evidence-core (4/4 changed files matched main v0.0.82), then repository-workflow-planner-hardening and agent-pilot-readiness after separate semantic review. Do not publish paths/lock reasons. Delete only after checking current SHA again and authorization.
- If needed enable Immutable Releases in Settings after owner decision and before first GitHub Release publication; align Ruleset allowed_merge_methods to squash only, do not modify required checks or tag protections. Do not restrict tag creation. At release tag dispatch workflow and independently verify; current connector lacks dispatch/delete ref/release publication. Manual actions, not current PASS.

## New research hypothesis

Harness capability seams separate skill provider, model invocation and shell/permission; explicit skill loading may differ from automatic invocation. Do not judge one text response alone. Use observable criteria from [Harness skills subsystem](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/skills.md), [capability seams](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/capability-seams.md) and [OpenAI skill evals](https://developers.openai.com/blog/eval-skills): fresh isolated sessions, explicit/implicit triggers, identical task without skill, negative tests and least permissions. Upstream review does not prove TESSERA integration.

Reconciliation 26 November 2026: #78 CLOSED (completed) by owner, subsequent main CI and both v0.0.83 tags verified; #81 OPEN. Do not reopen without newly demonstrated remaining work.
