# TESSERA 0.1.0 — first product release readiness criteria

[Русский — оригинал](RELEASE_0_1_0.md) | **English — translation**

Status: approved preparation plan (not a 0.1.0 release). On 26 November 2026 owner approved complete basic versions of all three skills, mandatory Codex/Harness enforcement and GitHub Immutable Release with attested ZIP. Baseline v0.0.84: commit df8116f35fdfe2ccb7ee4a4316053455c407d3e9, main CI 45834594641 SUCCESS 6/6, exact annotated tag object 7a1d8d334612fe6c8b60c63ecb4b73a75a763c08. No dummy microversions.

## Product boundary

Three standalone skills: Microversion Release, Project Audit, Repository Workflow. RU-first + EN, offline helpers, verifiable sources and official exact-tag distribution. Full local Git without GitHub. Codex and DeepSeek Harness are target actual acceptance environments. Do not claim Claude Code/Hermes compatibility without actual separate trials; no paid APIs, third-party managers or mandatory service. Extended graphs, automatic DELTA reuse, semantic level V, extra platforms and optimizations are outside minimum readiness of these three skills without separate owner agreement. Mandatory unfinished protection is not a future feature.

## Release gates

| ID | Mandatory outcome | Evidence / status |
|---|---|---|
| G01 | Sequential VERSION, RU/EN changelogs, exact annotated tags | 0.0.86 verified, 0.0.87 main CI and tag require verification; 0.1.0 NOT_VERIFIED |
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
| G12 | Independent evidence, instructions, supported/unverified environments; GitHub Immutable Release with verified ZIP | setting ENABLED (owner PUT204/GET true); publication and verification NOT_RUN |

All mandatory criteria for claimed scope must be evidenced. Any NOT_VERIFIED mandatory item blocks readiness claims. The owner may explicitly change product scope, not assign PASS to an unexecuted criterion. Do not compute a readiness percentage from row counts. Historical results do not transfer to changed files, skill trees, environments or policies.

## Sequence

1. Accept actual changes only; assign next component version when integration slot is free. [VERSIONING](VERSIONING.en.md) permits 0.0.99 → 0.1.0 after genuine readiness; unfinished work may continue at 0.0.100+. No empty commits to fill numbers and no policy weakening for deadlines.
2. First address release-critical CI profile, TD04 and RW05, reconcile #78. Never speed up by dropping scans. Then actual multi-skill pin/update/rollback, independent verification and minimal adapters with positive/negative trials. Run pilot in parallel.
3. Before assigning 0.1.0, agree exact scope, freeze optional changes, finish pre-release acceptance on exact SHA. After merge check main CI, annotated tags and exact trees; any failure leaves BLOCKED.
4. Dispatch `build-attested-catalog.yml` **on v0.1.0**, not main. Download artifact, verify actual bytes, reproducibility, signer workflow, source-ref and source digest with official gh. Check report/certificate, which is not itself a signature. See [Trusted Build](TRUSTED_BUILD.en.md).
5. Owner approved a GitHub Immutable Release with an attested ZIP: use existing tag, prepare draft with verified ZIP and RU/EN notes, verify everything before publication. Do not recreate/move tags. Immutable Releases protect assets and tag after publication; complement Rulesets and provenance verification, never replace them. After publication check metadata and actual bytes. [GitHub immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases), [verify release integrity](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/verify-release-integrity).

## Owner actions (necessary parallel checks)

- From ordinary trusted Windows terminal, not agent sandbox: inspect cleanliness, current branch, worktrees, Git/Python/gh versions; synchronize only fast-forward after checking. Never remove GIT_* or weaken permissions. Reconcile 0.0.82 / 0.0.83 after exact tag confirmation.
- Fresh disposable project for each client; [AGENT_PILOT](AGENT_PILOT.en.md) with verified pins. Record actual client versions, INSTALL, DISCOVERY, EXPLICIT_USE, AUTO_USE, ENFORCEMENT, UPDATE/ROLLBACK and exit codes. `python scripts/release_tag.py context` from installed Microversion Release invokes no Git; on unsafe context stop Git operation, return names and status only. Actual release fixtures only with authorization and without remote; no production data.
- Check old branches after preservation review: do not delete if occupied by a worktree or carrying unique changes. First project-audit-evidence-core (4/4 changed files matched main v0.0.82), then repository-workflow-planner-hardening and agent-pilot-readiness after separate semantic review. Do not publish paths/lock reasons. Delete only after checking current SHA again and authorization.
- Enable Immutable Releases in Settings (owner decision approved; status NOT_VERIFIED) and before first GitHub Release publication; align Ruleset allowed_merge_methods to squash only, do not modify required checks or tag protections. Do not restrict tag creation. At release tag dispatch workflow and independently verify; current connector lacks dispatch/delete ref/release publication. Manual actions, not current PASS.

## New research hypothesis

Harness capability seams separate skill provider, model invocation and shell/permission; explicit skill loading may differ from automatic invocation. Do not judge one text response alone. Use observable criteria from [Harness skills subsystem](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/skills.md), [capability seams](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/capability-seams.md) and [OpenAI skill evals](https://developers.openai.com/blog/eval-skills): fresh isolated sessions, explicit/implicit triggers, identical task without skill, negative tests and least permissions. Upstream review does not prove TESSERA integration.

Reconciliation 26 November 2026: #78 CLOSED (completed) by owner, subsequent main CI and both v0.0.83 tags verified; #81 OPEN. Do not reopen without newly demonstrated remaining work.

## Approved enforcement and publication architecture

T13/G06: independent [Completion Gate and Guarded Run](../skills/microversion-release/references/ENFORCEMENT.en.md) candidate 0.0.4. Local 26/26 PASS, native/client NOT_VERIFIED. For each client observe Stop invocation and real outer control (positive/negative); never accept only agent text or change permissions. Harness bridge partly fail-open and cannot provide veto. External controller does not replace observed activation; GUI not automatically accepted. G02 fixed CI profile accepted at v0.0.84. G12 Immutable Release now mandatory; see [publication](IMMUTABLE_RELEASE.en.md). Protect main Ruleset verified allowed_merge_methods=[squash]. Immutability unverified, #81 OPEN; TD04/RW05 awaiting integration.

## Actual owner pre-release trial — 26 November 2026

Source: owner-supplied Codex report (OWNER_REPORTED, not independently reproduced by remote CI). v0.0.84, main df8116f35fdfe2ccb7ee4a4316053455c407d3e9, clean checkout, 94/94 tag refs match, 6 clean worktrees. Git 2.52.0.windows.1, Python 3.14.3, gh 2.105.0, Codex CLI 0.166.0, Desktop runtime 26.1123.915.0. Harness CLI/installation not found — NOT_VERIFIED, not proof of absence. Both separate test directories: gh skill install/list confirmed 3/3 exact pins (Microversion Release 0.0.3, Project Audit 0.0.5, Repository Workflow 0.0.2); G03 partially accepted for placement and pin, activation/update/rollback not accepted. Codex GUI geometry unavailable, no prompts sent. Unit suites under inherited context: Microversion 42 (20 PASS, 3 FAIL, 19 ERROR); Audit 75 (61 PASS, 13 ERROR, 1 SKIP); Workflow 17/17 PASS. Individual errors NOT_DIAGNOSED; clean CI PASS does not transfer to clients. next_version CLI .99→.100 and .99→0.1.0 PASS; release_tag context exit 1 GIT_CONTEXT_UNSAFE / Git NOT_EXECUTED. P02–P08, E/RW client scenarios not accepted, #81 OPEN. First diagnose exact errors and availability of trusted invocation, then full client tests after published pins. Never strip inherited configuration or expand permissions. Preserve branches with unique commits and occupied worktrees; deletion not verified. Do not publish local paths.

## Reconciliation 26 November 2026 — #92 accepted, next guard candidate

PR #92, exact head 5e770ebf66af9d2758b9df026229794e2932c15b, run 45852127083: all five mandatory PR jobs PASS. Squash commit feaa3d211221ef0301edf45571f312d2637b0341; main run 45859420735 still needs verification and two exact annotated tags. SkillSpector 26/26 Microversion Release files fully inspected, 100%; integrated Tier 1 execution PASS, policy verdict Microversion FAIL (11 HIGH, 24 MEDIUM, 0 CRITICAL), Audit FAIL (1 HIGH — aggregate risk gate, direct 55, 0 direct HIGH), Workflow PASS (0 HIGH, direct risk 30). G09 OPEN: execution PASS is not findings remediation, no suppression. Owner reported Node 24.18.0 / npm 12.0.2; npm manifest @deepseek-ai/dsh 0.2.2-rc.5 requires Node >=24.9.0. Actual Harness not launched. GET immutable-releases returned enabled:false, enforced_by_owner:false — G12 BLOCKED pending enable and repeated verification. G06 Microversion 0.0.5 candidate requires exact --expected-version; 4 new test methods. G07 Audit 0.0.6 protects mutating fixture setup, likewise Microversion; 2 regression methods total. New isolated fixtures pass only explicit allowlist. All new tests require CI; actual client acceptance #81 open. TD04/RW05 separate candidates; preserve occupied branches/worktrees.

## Post-#93 reconciliation

0.0.85 main CI 45859420735 SUCCESS 6/6; exact commit feaa3d211221ef0301edf45571f312d2637b0341, tag objects dc893d0ac9fc5291d53023f0dd5967a8e17d1222 (catalog) and 4cab74df967d2a6f8abd98737b67da84dd30fd4e (microversion-release/v0.0.4), both direct target. #93 run 45860767387 SUCCESS 5/5, squash 0b207f09bb9fca7cf5525d6b35a1919e1d316515. G09 remains OPEN: direct coverage 100% all three; Microversion 9 HIGH (was 11), Audit 1 direct HIGH (was aggregate gate), Workflow 0. No severity changes or exclusions. G12 owner setting ENABLED, publication NOT_RUN. Harness rc.5 CLI help executed (owner-reported), actual session and hook NOT_VERIFIED. TD04 integration candidate 0.0.87; live Gitleaks parity required. #81 OPEN.

## Post-#94 reconciliation

0.0.86 main CI 45864624507 SUCCESS 6/6, commit 0b207f09bb9fca7cf5525d6b35a1919e1d316515; exact tag objects c270a15e48552fbb7dbed47f46126c33c30a6aef (v0.0.86), 853133f0dd4b54ef72e6dda0cccce9b956bdb58a (microversion-release/v0.0.5), f1ab06d7abf4f1a1147df4217708fde079ec9953 (project-audit/v0.0.6). #94 run 45865200170 SUCCESS 5/5, squash 75f27ca40d90aa46c387c5c81d38f3ff064200c2. TD04 host/container parity PASS (1551/1551 distinct blobs, 24116257 bytes, zero findings; container 323.1s), main 0.0.87 still requires acceptance. Do not extrapolate local read-only benchmark to entire CI. Owner confirmed exact rc.5 headless help: --json, session-id, permission-mode, approval-policy ask/never, add-dir. PROFILE_HELP_PASS, model, actual execution, hook and #81 remain NOT_VERIFIED/OPEN. G09: next candidate exports bounded reported HIGH/CRITICAL occurrence coordinates, no verdict changes. Microversion Release 0.0.6 requires newly introduced changelog heading, not mere presence. RW05 and actual client acceptance open.

## 2026-11-27 — verified v0.0.88 and owner pilot

Main CI 45874463052 SUCCESS 6/6; catalog tag 3be87bc90d9745aa2b074c9022cd4656e241010d and microversion-release/v0.0.6 tag 49eb12134036b1c33e3e3a9198eea76cfde6d057 both target 015bed7f9eaf344b59e699a4b607c0e21b86f608. All three independent skill trees match catalog v0.0.88. G03/G04/G05/G06–G08 PARTIAL: owner Harness rc.1 positive trials and observed native skill dispatch (see pilot); automatic selection, Stop-hook, full E/RW matrices and Codex remain open. Metadata-record warning under gh requires reproduction, not a bypass. G09: 7+1 direct HIGH occurrences, no CRITICAL finding; Tier 1 policy FAIL for two skills, do not suppress. G11 #81 remains open. G10/G12 publication NOT_RUN. No claim of v0.1.0 readiness.

## 2026-11-27 — fourth skill authorized by owner

Project Cleanup 0.0.1 candidate is an independent component for storage hygiene. The previously approved three-skill G01–G12 matrix remains valid only for those skills; it cannot establish Project Cleanup acceptance. Before a catalog release containing it, verify PC01–PC06 in its roadmap at the declared scope, native Windows/Linux, exact tree pin, no unsafe cleanup and explicit client use. Any unimplemented automation must remain explicitly labeled. Do not shift the original three-skill gates or claim full four-skill readiness from this candidate. No destructive operation in the initial helper.

## Current 0.1.0 readiness review — 27 November 2026

Last fully accepted engineering release v0.0.91, main 85bd362067b5a2c8dc94ab0a550990281b80d1ee, CI 46006227100 6/6 PASS; annotated catalog tag be2a4605bee0772454c4690c9b3dcfe51e39b323 and repository-workflow/v0.0.3 ce833071628b1bc60d70b9806de9651d9dc6d4e5 → exact main. Four skills: Microversion 0.0.6, Audit 0.0.6, Workflow 0.0.3, Cleanup 0.0.1. PC02 candidate 0.0.2 (28/28 isolated Linux PASS). Original matrix above contains historical criteria, not current statuses. The four-skill product release also requires PC01–PC06 without weakening G01–G12.

| Group | Current assessment | Closure condition |
| --- | --- | --- |
| G01/G02 | PASS for v0.0.91, 0.1.0 NOT_RUN | exact candidate/main/tags, full CI |
| G03/G04 | PARTIAL | scoped pin/update/rollback in both clients, preserve local edits/other skills, gh metadata warning |
| G05/G06 | BLOCKED on client evidence | fresh Codex explicit/implicit, actual authorized Git fixture without scrubbing GIT_*, Harness AUTO_USE and Stop/guard, owner-approved isolated hook only |
| G07/G08 | PARTIAL | actual client E/RW scenarios, independent work, actual occupancy, recovery |
| G09 | OPEN | 18 direct HIGH (7 Microversion + 1 Audit + 1 Workflow + 9 Cleanup), 0 CRITICAL occurrences in v0.0.91; all four raw policies FAIL, independent disposition of each cause, no suppression |
| G10/G12 | NOT_RUN | exact v0.1.0 dispatch, attested ZIP, independent gh verification, draft→immutable publication; owner setting ENABLED reported, recheck before release |
| G11 | OPEN | #81, three old branches: result preservation/actual occupancy, no destructive shortcuts |
| PC01–PC06 | PARTIAL | PC01 native CI, PC02 advisory 28/28 Linux pending native CI; PC03 execution/recovery, PC04 counters, PC05 budgets, PC06 client NOT_VERIFIED |

Do not assign 0.1.0 before readiness conditions are fulfilled. 0.0.99 is not a deadline. Priority: PC02 native CI, verifiable PC03 execution (explicitly authorized disposable fixtures only), G09 dispositions, focused client acceptance, Git/GitHub storage and prevention, independent release preflight. History scan approaching cap: PR #98 1642/2048 distinct blobs (406 reserve), container 274.9 s, parity PASS, zero findings in scope. Change limits only after measured capacity and regression, never reduce coverage. Parallel work allowed, common versions assigned sequentially.

## 2026-11-27 — current 0.0.92 / TD17 review

Main 0.0.92 7ace18df60412f98cc84835a6ad81d4c36414683, CI 46019956070 6/6 PASS; annotated catalog tag 4545d85dfc5e9336423f72c3729eb748603d6d14 and project-cleanup/v0.0.2 96626f96dd73d40e72f813502e5412b0ad6ebfd2 → exact main. PC02 native CI Linux 49/49 PASS for full skill, Windows 47 PASS + 2 FIFO SKIP, actual sparse/staged fixtures PASS; execution/recovery/client NOT_VERIFIED. G09: 20 HIGH (7+1+1+11), 0 CRITICAL occurrences, raw policies FAIL; new Cleanup AR3 in negative safety wording and E2 in names-only fixture guard, exact underlying YR4 unresolved. TD17 candidate 0.0.7: four focused isolated Linux probes PASS on exact release_tag.py, three new regression methods, full CI and Codex not accepted. #81 OPEN. Fixed pin table/PowerShell drift; guard checks all four RU/EN mappings. Main history 1651/2048 distinct blobs, 26511012 bytes, container parity PASS 457.05 s, zero findings; separate TD04 batch candidate 09c47faefc643f9deb1b2cb4b0d618f404376f13. 0.1.0 BLOCKED until actual G01–G12 + PC01–PC06. Do not remove historical branches or real worktrees without evidence.

## 2026-11-27 — actual one-link pilot and mandatory UP01

Owner supplied Codex/Harness reports and Harness JSONL. Both user profiles reported current contents of four skills at catalog v0.0.92 (7ace18df60412f98cc84835a6ad81d4c36414683); GitHub independently confirms trees Microversion 0.0.6 12aebcae998b098a1e7d3c5f1fadd8bcd2b096e7, Audit 0.0.6 50d3f3dee94f1ceff9df343ef34689caf99ca184, Cleanup 0.0.2 cb41049a3ff565ae3f2fb7e5582837cc620c1477, Workflow 0.0.3 747474aff7e872c31285c1053f59eabd652fe9be. Installed bytes/backup owner-reported, not independent profile access. Codex used named --unpin --all and some main installs; local-edit preservation unproved. gh metadata or up-to-date is insufficient; actual Codex automatic invocation NOT_VERIFIED. Harness rc.1: log 687 records, 1 completed turn seq 11–685, 1661.002 s (27m41s), 41 steps, 43 top-level tool calls, 113 nested dispatches, 85 pwsh, 16 model retries (14 TIMEOUT, 2 TRANSPORT). Successful native skill loads seq 567/569/571/572 including Cleanup; catalog suite 754=747 PASS+7 SKIP; per-skill tests and actual bytes in report. Session mode changed workspace-write→danger-full-access before turn, least-privilege NOT_VERIFIED; do not recommend that as an update method. One user scope may be shared between clients; independence of the two installs NOT_VERIFIED. Do not publish raw session or local paths.

UP01 — mandatory separate 0.1.0 acceptance: one short link-only request, no history/full unit suite, fresh clients in naturally authorized context, exact pins, repeated no-op, missing skill, old pin, local edit, unrelated same-name skill, network/permission failure and recovery. Goal: minimal request and short report; measure elapsed, API calls, tool calls, retries, actual discovery, bytes and preservation, no invented fixed SLA. Proposed CATALOG.json + UPDATE.en.md + read-only catalog_index.py: exact source 6531e6790398b8dbb7554206f98f08b0754b5f61, tests fcb5def96289ebfd2f45fefd7c20d2d7f7e87323, index 258e8b62e57628e20c239dfc7685907f49e46377. 10/10 isolated Linux tests PASS (0.006 s, mocked API and temporary minimal source tree); all three blob SHAs match, separate remote source check of four VERSION files PASS. Not live API acceptance or production updater. After tag publication test actual resolver via official gh and exact skill trees, then staged per-skill updater/recovery in disposable native Windows/Linux; do not use CI swap on a working profile. G03/G04/G05 remain PARTIAL; G06–G09, PC03–PC06, G10/G12 open.
