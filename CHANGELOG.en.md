# TESSERA changelog

[Русский — основной язык](CHANGELOG.md) | **English — translation**

This file tracks changes to the **shared catalog**. Individual skills may maintain their own version histories.

## 0.0.103 — Added crash interruption tests

- PR #109 passed CI 46122145983 and was merged. Main verification and tag pending.
- Added tests that forcibly terminate a child process at eight install/update boundaries. A fresh process reads the journal and inspects actual directories. Backup and neighboring skill preservation are checked. Three test methods; CI pending. Temporary fixtures only, no automatic recovery or power-loss proof.

## 0.0.102 — Test the complete update cycle

- PR #108 passed CI 46120392984 and was merged. Main verification and tag pending.
- Journal, move and recovery observation are integrated into one isolated fixture cycle. Install and update use automatically created temporary directories, including eight simulated interruption scenarios. Old tree remains in backup, neighboring skill unchanged. Six test methods. Not actual process termination, power-loss proof or a production updater. No arbitrary profile path or automatic rollback; ZIP unchanged.

## 0.0.101 — Move skills without overwriting

- PR #107 passed CI 46119327281 and was merged. Main verification and tag are pending.
- Added a verified-directory no-overwrite move library: Windows rename and Linux renameat2(RENAME_NOREPLACE). Unsupported platforms or missing support fail closed; no unsafe fallback. Checks expected fingerprint, disjoint same-device roots, absent destination and identity after move. Nine disposable-directory tests. This is a primitive for trusted exclusive roots, not an installer: ACLs, ancestor races, power-loss durability, journal integration and rollback remain open. CI does not touch real profiles; not yet in the ZIP.

## 0.0.100 — Append-only transaction phase journal

- 0.0.99 main 67ad5669abb80819b0183ed4cc9234b377f27802, CI 46118526414 SUCCESS, annotated tag object 4501f60a678567e4efdacdd78e4a52c9005a871b.
- UP02.03: append-only single-skill phase journal, separate canonical JSON records, strict phase sequence and immutable fields, O_CREAT|O_EXCL, file flush/fsync and postcheck. Partial records and unknown files block progress, existing records never overwritten. Nine fixture tests include collision and fsync failure. Library only for trusted exclusive directory: parent directory durability, ACL/races, actual crash, moves and rollback NOT_VERIFIED. No profile writes; not yet included in runtime ZIP.

## 0.0.99 — Read-only recovery classification

- PR #105 CI 46065687896 PASS, squash b94fd6855f2a32179f6804cd8e562f7f5ca1f2f4; main CI/tag pending.
- UP02.03: read-only single-skill recovery classifier. Compares a bounded strict journal with actual profile/stage/backup fingerprints, requires disjoint ordinary same-volume roots and rechecks observed identities. Distinguishes NOT_STARTED, OLD_IN_BACKUP, NEW_PRESENT, NEW_PRESENT_OLD_RETAINED; ambiguity and phase mismatch BLOCKED. Ten disposable fixture tests cover interruption between rename and phase record, local edit and missing stage. Does not create journals, rename/delete, authorize apply or prove durability. Next: separate writer with no-clobber primitives and crash recovery, fixtures first. Diagnostic candidate not included in runtime ZIP before acceptance.

## 0.0.98 — Verify gh staging metadata (0.0.98 candidate)

- 0.0.97 main 4f0e5ec0175e42bf67afceef3360497d1261d140, CI 46062411446 SUCCESS, annotated tag object 726389b4f834b243413ab84ef36d9379bbd1684d.
- UP02.02: read-only gh_stage binds supplied raw Git tree to installed staging and checks the exact five github-* metadata fields, original frontmatter fields, body, other file bytes, modes and stage fingerprint. Narrow YAML subset (plain/simple quoted scalars and >- without complex constructs); unsupported forms BLOCKED. Actual gh serialization, lockfile, live refs, apply authorization, atomicity and rollback NOT_VERIFIED. From 0.0.98 the tool is required in ZIP; 0.0.97 remains compatible. Ten fixture tests and package gate; native/full CI pending.

## 0.0.97 — Update tools in the source ZIP (0.0.97 candidate)

- Starting at 0.0.97 the ZIP contract requires CATALOG.json, both UPDATE and profile-plan documents, and the three read-only UP01/UP02 tools. Verification rejects missing/extra files and inconsistent catalog versions even with a recomputed manifest. Older ZIPs retain their legacy contract. The ZIP remains a runtime subset: skill tests are excluded, so it is not a raw Git tree or staging for skill_tree.py. Use verifier code from an independently trusted checkout, never execute code from an unverified ZIP. Attestation, live resolver, gh metadata, apply and rollback remain separate open tasks.
- PR #103 CI 46055009112 PASS, main 0.0.96 18611a86f6ce76749a9892c0c2779d7f0fb97576; exact main CI/tag pending. New contract tests require CI.

## 0.0.96 — Read-only profile planning and raw tree proof (UP02)

- main 0.0.95 b179d71f091083916a88067a895c85c6539bc480, CI 46053357417 6/6 PASS, annotated catalog and Cleanup tags 672f08ad6ae306f74410f4a6c62e813be89cb87f / c33bd2fe15aba1aeb35dadc80390820338720376, all four independent skill trees match.
- Integrate profile_plan, skill_tree and regression tests; 25/25 Linux per branch report, exact candidate native CI pending. No writes or apply authority. Live metadata, journal, rollback and client acceptance open.

## 0.0.95 — Stabilize Windows PC02 and batch CI history reads

- 0.0.94 PR #101 5/5 PASS, squash 346a28001263dffe09920f96821a2170de68a4be; main CI 46042052275 Windows job 140651970098 FAIL. No retroactive v0.0.94 tag. Verified baseline remains 0.0.93 until a new exact tag.
- Project Cleanup 0.0.3: fixed .git marker test without assuming immediate directory mtime; strengthened root/marker identity, disappearance, hardlink and nonzero inode checks. Four new regression methods, renewed native CI pending. CATALOG.json reflects candidate, not published pin.
- TD04: batch reads via existing checked_blob_batch, unchanged limits/scanner coverage, five additional regressions, full parity CI required. No weakening G09/#81/UP01/PC03–PC06. Historical branches preserved in ancestry; 0.1.0 not ready.

## 0.0.94 — Exact-version catalog and addressed install/update (UP01)

- CATALOG.json, UPDATE RU/EN, read-only catalog_index: independent annotated pins, matching subtrees, refusal on moved refs or missing index; explicit install/update and repeatable --skill or --all. No unselected pin requests or widening invalid selection. 15/15 isolated Linux PASS on exact source/test blobs, mocked API; native CI, live API, safe replacement and recovery still required.
- 0.0.93 main CI 46033970329 SUCCESS 6/6, exact commit 168ccae683e92ed13fba141c6654201765cb2e3a and two annotated tags. Microversion Release 0.0.7 accepted, Windows 81/81 PASS; #81 actual context remains OPEN. Four current pilot pins refreshed.
- Actual 0.0.92 one-link reports and Harness log recorded as bounded client evidence; least privilege/preservation/addressed update NOT_VERIFIED. UP01 required for 0.1.0, packaging the catalog and production updater still open. Historical Audit branch preserved in ancestry, source/test match main; CI and independent checks required.

## 0.0.93 — Harden unsafe Git-context refusal and synchronize the pilot

- Microversion Release 0.0.7: unknown/unapproved GIT_* blocked, names redacted, XDG_CONFIG_HOME preserved, local Git protocols/lazy fetching disabled. Four focused isolated Linux probes PASS on exact release_tag.py, including actual disposable positive/negative fixture. Full CI and #81 open.
- 0.0.92 main CI 46019956070 SUCCESS 6/6, commit 7ace18df60412f98cc84835a6ad81d4c36414683, both exact annotated tags. Project Cleanup Linux 49 PASS, Windows 47 PASS + 2 FIFO SKIP. Synchronize four pins across RU/EN quick start and PowerShell.
- TD04 separate candidate: batch Git object reads, synthetic speedup for reading only; limits and scanner coverage unchanged. 0.1.0 readiness remains BLOCKED.

## 0.0.92 — Account for Git in cleanup planning (PC02)

- Project Cleanup 0.0.2: bounded read-only plan from two HEAD/index/ignored/untracked captures; protect overlaps, staged deletions, gitlinks, sparse-index, nonportable paths and collisions. Recheck capture and ancestor metadata; no deletion authorization. 28/28 isolated Linux tests PASS on exact blobs; native CI required.
- 0.0.91 main CI 46006227100 SUCCESS 6/6, commit 85bd362067b5a2c8dc94ab0a550990281b80d1ee, both annotated tags verified. Repository Workflow Linux 41 PASS, Windows 40 PASS + FIFO SKIP; actual client use 0.0.3 NOT_VERIFIED.
- 0.1.0 preparation: CI is not client evidence, no weakening G09/#81; PC03–PC06 open.

## 0.0.91 — Add evidence-based worktree reconciliation (RW05)

- Repository Workflow 0.0.3: read-only Worktree Inventory, 21/21 Linux PASS, exact source/test blobs verified; stale/ref/OID/descriptor and Git context guard. Actual occupancy and deletion permission NOT_VERIFIED; native CI required.
- v0.0.90 accepted via PR #97, commit 79f369b6f817976c2d0b1f026ed86f00be045860, main CI 46001257853 SUCCESS 6/6; both exact annotated tags confirmed. Project Cleanup Linux 21 PASS, Windows 20 PASS + FIFO SKIP; exact pin recorded, client acceptance open.
- Unique RW05 work preserved on its existing branch, base updated without force. PC02 separate candidate, 19/19 Linux, no common version reserved. G09, #81 and actual worktrees remain open.

- Windows regression: separate path/fstat ctime semantics, retain same-method identity checks, add three tests; 24/24 Linux PASS, renewed Windows CI required.

## 0.0.90 — Add Project Cleanup and catalog storage guard

- Fourth independent skill 0.0.1: metadata-only inventory, scope protections, traversal budget, REVIEW classification, top-level/private details, cleanup and prevention workflow. Linux 18/18 PASS on exact blobs; native Windows and client acceptance open.
- TESSERA: exact committed tree check for generated paths, non-source entries and blob >1 MiB; dedicated ignored local-state directory. No automated deletion or weaker CI safeguards.
- Previous v0.0.89 main CI 45994903581 SUCCESS 6/6, exact annotated tag 1a904240fc2f1c17dc5bedfb2af2583e9f0bfa0a → efece8ad28fa6e5968d57c41ce68be195e932324. New candidate requires mandatory CI; #81 and branches with unique work remain open.
- Pre-merge hardening: protected-store exclusions, explicit profile/ancestor refusal, additional protected filename hints, three regression methods including no-content-access assertions. Prior 18-test evidence applies to the earlier source; renewed CI required. No scanner suppression.

## 0.0.89 — Pin the short pilot and Harness evidence

- Current independent pin/commit/tree, direct gh selector skills/<skill> (gh 2.105.0 source verified, actual run pending), short local checks without full repository audit; bounded network retries and separate explicit/automatic activation.
- Record verified v0.0.88 CI and tags, owner Harness rc.1 results, observed JSONL loading and open Codex/Stop-hook/AUTO_USE; gh metadata warning remains open. No skill changes or weaker safeguards.

## 0.0.88 — Harden version history and static-finding evidence

- Microversion Release 0.0.6: baseline CHANGELOG contains exactly one heading for baseline version; next commit introduces one heading for its version and preserves previous heading. Four Git regressions. Two old context CLI fixtures no longer copy all environment values, separate regression.
- SkillSpector: bounded projection of all reported HIGH/CRITICAL occurrences with checked coordinates and omission counts, no raw evidence, two regression methods. Verdicts, thresholds and suppressions unchanged.
- 0.0.86 main CI 45864624507 SUCCESS 6/6, three exact annotated tags. PR #94 45865200170 SUCCESS 5/5, host/container Gitleaks parity PASS (1551 blobs, 24116257 bytes, zero findings in scope). Main v0.0.87 acceptance required. Harness headless help owner-confirmed; actual session and #81 open. New tests require CI.

## 0.0.87 — Batch Git blob reads for Gitleaks (TD04)

- Bounded host batch: up to 32 blobs / 4 MiB, exact order, type/size/OID, UTF-8 and framing, no trailing bytes. Preserve individual scans, coverage and repeated inventory. Independent container path unchanged.
- Synthetic read benchmark 256 blobs: medians 0.508152/0.013793 s (~36.8x), not whole-CI speedup. New unit/actual Git fixture tests and full host/container parity require current CI. All 4 base blobs reconciled with main v0.0.86.
- v0.0.85 main 45859420735 SUCCESS 6/6 and both tags verified; PR #93 run 45860767387 SUCCESS 5/5, squash 0b207f09bb9fca7cf5525d6b35a1919e1d316515, main acceptance required. Immutable setting owner-confirmed, Harness rc.5 CLI help executed. G09 and #81 remain open.

## 0.0.86 — Require exact target and protect Git fixtures

- Microversion Release 0.0.5: required --expected-version in Guarded Run, schema 2; wrong target blocks before tests even if structurally valid. Four regression methods including actual release fixture with and without tag.
- Microversion Release and Project Audit 0.0.6: old mutating Git test setup refuses inherited Git_* except pager before any writes, two regression methods. New isolated fixtures use explicit system environment allowlist. Production policy unchanged.
- PR #92 CI 45852127083 5/5 PASS; SkillSpector 100% coverage, but Microversion 11 HIGH, Audit aggregate risk gate 1 HIGH, Workflow 0 HIGH. G09 open; advisory results do not establish clean security. Candidate native CI and actual client acceptance required.

## 0.0.85 — Independently enforce completion checks

- Microversion Release 0.0.4: Completion Gate validates linear version transitions, changelogs, exact annotated tags, cleanliness and index flags; repeats HEAD/ref checks. Basic root VERSION/changelog profile. Stop adapter requests at most one continuation per owner-selected marker, no automatic tagging.
- Guarded Run executes only explicitly selected owner commands after --execute; independently checks structure, actual agent exit, tests and final SHA/tag objects. No-op blocked by default. Not a sandbox or proof of activation.
- 26/26 local Linux / Python 3.13.5 / Git 2.47.3 test methods (16 Git/Stop + 10 subprocess fixtures), verified Git blobs. Full CI and actual client acceptance required.
- Owner approved basic versions of all three skills, mandatory Codex/Harness enforcement and a GitHub Immutable Release with an attested ZIP. v0.0.84 and squash-only setting verified. #81 stays open.

## 0.0.84 — Fix the mandatory 0.1.0 release checks

- Release Core: required CI jobs selected independently of API job presence. Current profile requires all six; historical TESSERA policy uses root VERSION of exact commit, not skill version. Missing groups block the report; regressions added.
- Isolated algorithm model 8/8 PASS, historical workflow boundaries verified. Full candidate CI required.
- Prepared G01–G12, product boundaries, owner steps, ZIP provenance verification and Immutable Releases research. Verified exact v0.0.83/project-audit/v0.0.5 and refreshed pilot pins. #78 closed by owner, #81 remains open.

## 0.0.83 — Plan DELTA audits and reconcile documentation

- Project Audit 0.0.5: recheck planning for two explicitly supplied DAGs; changed and unknown fingerprints invalidate dependents, incomplete graphs or context changes require full rechecks. No project reads or PASS reuse.
- 14/14 isolated Linux tests; source and test Git blobs verified. Full CI and actual activation required.
- TD15/#78: reconciled RU/EN README, Inventory, Git Inspector, Evidence Core and roadmap. Verified accepted v0.0.82 and microversion-release/v0.0.3; CI does not establish client acceptance.

## 0.0.82 — Diagnose inherited Git context

- Microversion Release 0.0.3: report blocking variable names without values or Git execution; orphaned indexed GIT_CONFIG_* also block local tagging and inspection. No removal of host configuration or permission bypass.
- TD17/#81: four new test methods and an extended negative regression; full CI and actual Codex acceptance required. Isolated extracted-logic check 6/6 PASS, not the full suite.
- Reconciled v0.0.81 evidence; recorded research on Codex/Harness, safe Git batch reads, DELTA and evals. Prototype results do not replace scanner acceptance.

## 0.0.81 — Refresh the Codex and Harness pilot guide

- Added current RU/EN criteria for disposable Codex and DeepSeek Harness pilots with separate skill tags `microversion-release/v0.0.2`, `project-audit/v0.0.4` and `repository-workflow/v0.0.2`.
- Pinned the catalog snapshot to `v0.0.80`; installation, discovery, explicit use, automatic use and enforcement are tracked separately. Actual client trials remain NOT_VERIFIED until observed in each client.

- TD04: raised bounded host history review deadline from 300 to 480 s; added deadline checks before/after reads/scans and final inventory, five regressions. Full coverage and container parity remain mandatory.

- TD15: reconciled the skill table, pilot link, security status and last verified release in RU/EN; historical evidence is not current client acceptance.

## 0.0.80 — Reconcile the accepted 0.0.79 release

- Updated the bilingual catalog status after PR #86: local and GitHub `main` matched by full SHA and version 0.0.79; main CI 45663571704 completed successfully.
- Confirmed annotated `v0.0.79` and `repository-workflow/v0.0.2` at the exact commit. The separate local post-run `--verify-ci` stopped with `GIT_CONTEXT_UNSAFE`; #81 tracks this limit.

## 0.0.79 — Harden the Repository Workflow planner

- The planner now normalizes Unicode scopes, rejects reserved Windows names and duplicate JSON keys, and validates the DAG in O(V+E); regressions cover long chains, cycles and path conflicts.
- Repository Workflow tests passed 17/17 on Windows 11 / Python 3.14.3. The full suite and mandatory static checks govern catalog acceptance; tests do not prove actual skill use by agent hosts.
- Reconciled the debt snapshot after accepted TESSERA `0.0.78`: main `be6a126f08ffbb49b721b50e030b2a6d82c7d4f3`, CI 45658775191 SUCCESS, exact annotated `v0.0.78` and `project-audit/v0.0.4`.

## 0.0.78 — Project Audit evidence register

- Added a local Evidence Core for an explicit JSON register: strict schema and references, exact scopes, snapshot/fingerprint binding, preserved PASS/FAIL conflicts, and STALE/UNBOUND/INDIRECT classifications.
- The tool validates only the supplied register: it does not read a project, run checks, or authenticate source, integrity, or completeness. On Windows 11 / Python 3.14.3, the Project Audit suite ran 61 tests with 1 platform skip; the full catalog suite passed 725 with 7 skips. `GIT_*` was removed only from the test process for Git fixtures; the owner's environment was not changed.
- Reconciled the debt snapshot: local and remote main both matched version 0.0.77 at `ff4cb9ee12ce0fdf4923670c3d81f31718ebd287`; CI 45651340205 and annotated tag `v0.0.77` were confirmed. Codex runtime acceptance remains NOT_VERIFIED.

## 0.0.77 — Pre-install SkillSpector provenance check

- Added a pre-install comparison of the official SkillSpector 2.13.7 wheel against the pinned upstream Git tree; installation uses that same verified local file.
- Exact release asset, RECORD, metadata and entry point checks passed on Windows 11 / Python 3.14.3; nine wheel-checker tests and 39 workflow-security tests passed, with one Linux-only test skipped.
- Full PR/main CI and an annotated tag for this version remain required; this does not establish general safety or runtime acceptance of SkillSpector.

## 0.0.76 — Project Audit and mandatory Windows skill checks

- Project Audit 0.0.3 candidate: Git Inspector, false DEVICE_BOUNDARY correction (#80), stronger metadata-only regression (#77), native Windows Python 3.14 CI for all three skills, retained fail-closed validate and evidence checks. Previous report: 21/21 Linux Inventory Engine tests; full acceptance of current SHA and Windows still required. Version provisional until integration slot; T16 BLOCKED, ordinary merge prohibited until independent tags recover.

- Microversion Release 0.0.2: encoding and canonical test path fix after Windows CI 45614436502; native retest required.

## 0.0.75 — Verified sequential tag publication

- T16/TD02: v0.0.74 main validate and exact catalog tag PASS, actual atomic push FAIL (PUSH:1:UNCLASSIFIED), zero independent refs. New strategy explicitly selected before writes: one new tag at a time, exact full ref reconciliation before/after, stop on rejection without bypassing Rulesets. Preserve atomic mode and no automatic retry after ambiguous failure. 23/23 local Linux tests; GitHub CI and actual tags required.

## 0.0.74 — Recover independent skill tag publication

- Required checks and exact catalog v0.0.73 tag passed; independent publication failed twice. Safe operation/exit/category diagnostics, single remote identity, dry-run atomic capability probe, verified sequential new-tag fallback only for explicit unsupported capability. No change to existing tags or required gates. 19/19 local Linux tests; live recovery required.

## 0.0.73 — Protected independent skill tag publication

- TD03 configuration verified. Add read-only first-parent tag planner and explicit publication in existing main tag job; exact historical backfill, current verified changes only, atomic non-force push and remote object verification. 13/13 local Linux controls; live main publication remains pending.

## 0.0.72 — Third independent required CI group

- T19.03: move four Gitleaks source/path checks into source_secret_checks; retain full checkout, SHA, pinned tools and host/container pairs. History and tag jobs unchanged; validate requires all three groups. Gate, scope and independent report regressions added; live CI and timing required.

## 0.0.71 — Local Project Audit Inventory Engine

- Project Audit 0.0.2: bounded metadata-only traversal, counters, markers, exclusions, metadata SHA-256, refusal of known redirects and cross-device traversal; separate local test/preflight plan. 17/17 Linux tests of original helper; new structural regression requires CI. Git Inspector prepared separately (13/13 Linux), not included in this release. Windows, agent acceptance and independent tags remain open.

## 0.0.70 — Independent skill checks and test time bounds

- Release Core: explicit --skill for committed VERSION, exact annotated tag, preflight and remote report; separate trusted Microversion Release plan. Shared runner bounds each immediate skill test process and continues independent checks after timeout. 13/13 local runner tests, additional Release Core regressions await CI. Independent tags and protection TD03 WAIT_OWNER; descendant/output limits and Windows TD12 PARTIAL. Full CI required.

## 0.0.69 — Repository Workflow and continuous development protocol

- Third skill 0.0.1: LOCAL/GITHUB, optional independent task planner, 20 acceptance scenarios, 13 local regressions. Bilingual research materials, T18–T20, technical debt register, late version assignment, native tools and CI speed priority. Actual activation and independent release remain open; full CI required.

## 0.0.68 — Parallel required CI groups

- Separate Gitleaks history host/Docker pair from remaining catalog checks; same SHA, pinned tools, fail-closed required validate and unchanged tag gate. Independent CI evidence checks both parallel jobs when present, preserving historical reports. Local Bash truth-table control 16/16, missing results 2/2 rejected; full GitHub CI and measured speedup required.

## 0.0.67 — Project Audit level I

- Correct restricted Bandit adapter for a tests-only skill: real recursive scan of zero eligible runtime targets, exact result validation, live control and regressions; full CI required.

- Second independent skill 0.0.1: bilingual methodology, 30 directions, 20 behavioral scenarios and structural tests. Behavioral trials and independent tags remain open; full CI required.

## 0.0.66 — Independent skill version accounting

- VERSION and two changelogs per skill; compare against the first Git parent, reject skipped versions and metadata-only bumps. Include and validate metadata in ZIP; older archives without these files remain readable. Microversion Release starts independent accounting at 0.0.1; its own tag and actual clients remain unverified. T16 PARTIAL; full CI required.

## 0.0.65 — Universal skill test runner

- Separate-process unittest discovery for all skills; reject suites with no ordinary successful tests. Validation CI, signing and preflight share the runner. Ten regression scenarios; full CI required.
- Five-stage Project Audit evolution approved; T12 remains PARTIAL.

## 0.0.64 — Integrated SkillSpector Docker (T12.03.32)

- Static-only NVIDIA adapter, report validation and receipts, five regressions. CI required; T12 PARTIAL.

## 0.0.63 — Standalone SkillSpector Docker (T12.03.31)

- Isolated static SkillSpector, 74 distribution pins, host/container parity, eight regressions. CI required; T12 PARTIAL.

## 0.0.62 — Safe Bandit coordinates (T12.03.30)

- Bounded finding locations, host/container parity, six regressions. CI required; T12 PARTIAL.

## 0.0.61 — Scanner configuration SHA-256 (T12.03.29)

- Pin exact Semgrep and Bandit configuration SHA-256 instead of SHA-1; retain Git blob provenance. Two regression tests, no suppression. CI required; T12 PARTIAL.

## 0.0.60 — Integrated Bandit Docker (T12.03.28)

- Restricted NVIDIA adapter, INI, coverage and report verification, six regressions. CI required; T12 PARTIAL.

## 0.0.59 — Standalone Bandit Docker (T12.03.27)

- Minimal pinned runtime, read-only snapshot, host parity, four regressions. CI required; T12 PARTIAL.

## 0.0.58 — Integrated Gitleaks Docker (T12.03.26)

- Isolated NVIDIA adapter, skill snapshot, restricted TOML and report, eight regressions. CI required; T12 PARTIAL.

## 0.0.57 — Bounded Gitleaks concurrency (T12.03.25)

- Two TSG1 workers, unchanged limits, full coverage, three regression tests. CI required; T12 PARTIAL.

## 0.0.56 — Semgrep license evidence (T12.03.24)

- Three pinned upstream LICENSE texts, existing wheel/RECORD verification, two regression tests. CI required; T12 PARTIAL.

## 0.0.55 — Containerized path check (T12.03.23)

- TSP1, five rules, ten categories, host parity and nine regressions. CI required, T12 PARTIAL.

## 0.0.54 — Containerized history scanning (T12.03.22)

- Batched blob transport, OID checks and host parity; seven regressions. CI required, T12 PARTIAL.

## 0.0.53 — Isolated Gitleaks (T12.03.21)

- Tracked UTF-8 host/container parity, TSG1, pinned binary, nine regressions. CI required, T12 PARTIAL.

## 0.0.52 — Linux namespace preflight (T12.03.20)

- Required synthetic network, PID, rlimits and timeout preflight; five offline regressions. Local unshare PASS, GitHub unshare BLOCKED; explicit required Docker synthetic preflight, CI required; not a complete sandbox.

## 0.0.51 — Clarified Russian skill terminology (T12.03.19)

- 22 editorial substitutions in six files, meaning and algorithms retained, independent mixed-token count 22→0; CI required, no suppressions.

## 0.0.50 — Simplified skill test imports (T12.03.18)

- Ordinary imports of three checkout modules, origin and conflicting cache checks, three regressions. CI required; no threshold or suppression changes.

## 0.0.49 — Hardened skill Git helper (T12.03.17)

- Absolute executable, timeout, closed stdin, safe diagnostics and post-capture output limit; six regressions. CI required; trusted configuration and environment limitations remain.

## 0.0.48 — Pinned Semgrep in NVIDIA Tier 1 (T12.03.16)

- Upstream lock, local rules, live controls and required scanner report, OSV/licenses; five regressions. CI required, sandbox and certification open.

## 0.0.47 — Tier 1 aggregate HIGH finding attribution (T12.03.15)

- Separate aggregate_risk_gate and other_high counts, original severity and policy unchanged; three regressions. Live CI acceptance required.

## 0.0.46 — Live Tier 1 Gitleaks redaction control (T12.03.14)

- Real shim clean and synthetic finding controls, stdout/stderr redaction and fixture preservation; five regressions. CI required; upstream completeness and sandbox not verified.

## 0.0.45 — Integrated static NVIDIA Tier 1 (T12.03.13)

- Explicit complete check-group lineup, pinned scanners and bounded Gitleaks adapter, aggregate-only reports, seven regressions. CI required; Semgrep and certification not verified.

## 0.0.44 — Hardened remote Release Core inspection (T12.03.12)

- One named remote, transport scope, fixed upload-pack, minimal environment and consistent evidence. Ten regressions; CI required, live network acceptance separate.

## 0.0.43 — Hardened Release Core local inspection (T12.03.11)

- Fixed tag object and direct commit, rechecks, minimal environment, no Git replace objects, timeout. Eight regressions; CI required. Remote and concurrency locking remain separate.

## 0.0.42 — Shared Gitleaks safe launch contract (T12.03.10)

- Fixed stdout/redact and archive-depth options; bounded temporary-file invariants, four regressions. CI required; not an OS sandbox.

## 0.0.41 — Minimum tool scope and Go audit evidence (T12.03.09)

- Explicit skill access boundaries without preapproved tools, independent Git/CI verification; actual v0.0.40 evidence and OSV/Govulncheck ID comparison. No LP3 suppression; CI required.

## 0.0.40 — Go binary review using Govulncheck (T12.03.08)

- Candidate: pinned source, isolated CI build, extract and binary mode, explicit distinction between fallback and extracted symbols, scanner OSV self-audit and before/after SHA-256, eight offline regressions and two upstream local-database controls; live acceptance required. Call reachability not proven.

## 0.0.39 — Bind tag to the exact verified commit (T12.03.07)

- Candidate: explicit target SHA, immutable object verification, direct commit and tag name, `--expected-head`, ref recheck; seven regressions, including rejection of inherited Git context/config overrides and child environment minimization. CI required; concurrent locking is not implemented.

## 0.0.38 — Installed license content verification (T12.03.06)

- Candidate: bounded license record checks for two exact Python versions, RECORD SHA-256 and size, upstream comparison; original metadata preserved. Four regressions; CI required. Go license confirmed at upstream level, not binary level.

## 0.0.37 — Evidence-bound SkillSpector finding locations (T12.03.05)

- Candidate: primary locations only for known relative paths in the inspected skill inventory; bounded output with explicit unresolved and omitted counts. No snippets, raw messages or occurrence metadata; unchanged rules and thresholds. Three regressions; real CI acceptance required.

## 0.0.36 — Offline installer path hardening (T12.03.04)

- Candidate: reject redirection of standard project paths and links/special files in the source; recheck destination after creating parent directories. Regressions for external links, dangling links and source links. CI not yet accepted; TOCTOU races and Windows junctions NOT_VERIFIED.

## 0.0.35 — SkillSpector security upgrade (T12.03.03)

- Candidate 2.13.7, pinned commit/wheel/lock, unchanged static no-LLM contract and zero-suppression enforcement, repeat CVE review. [CI 45376675127](https://github.com/Sashido01/TESSERA/actions/runs/45376675127) PASS: 494+19 tests; SkillSpector 2.13.7, 17/17 files, complete, 100%, 16 MEDIUM (AE4 6, AST3 6, AST4 3, LP3 1), zero HIGH, risk 53/100 HIGH, exit 1, zero suppressions, both fixtures PASS, 11.37 s. OSV: 74 Python distributions, zero packages with entries, zero source-commit entries; cryptography 50.0.2, langgraph 1.2.20, pyasn1 0.6.5. T12.03.03 COMPLETE within upgrade and repeat OSV scope; new AST3 and threshold exceedance remain open. Release awaits sequential acceptance.

## 0.0.34 — Restrict CI evidence API redirects (T12.03.02)

- Exact GitHub Actions API endpoints, reject redirects before following, verify exact response URL, four regressions. [CI 45376483433](https://github.com/Sashido01/TESSERA/actions/runs/45376483433) PASS: 493+19 tests, four new regressions PASS, Bandit B310 absent in the repeat review; 110 findings (no HIGH), no rule suppression. T12.03.02 COMPLETE within implemented control and CI scope; live network execution separately NOT_VERIFIED.

- Before merge, a shared get_public_json regression was found: the original strict URL allowlist blocked the existing GitHub Release metadata call. Permit only the canonical /releases/tags/vMAJOR.MINOR.PATCH route and one namespace encoded as %2F; arbitrary escaping, extra paths and parameters remain forbidden. Three regressions exercise verify_github_publication through the actual shared transport (ordinary and namespaced tag), changed response URL rejection and invalid routes. Only networking is mocked, validation and response handling are real. Historical PASS missed this defect; repeat acceptance is required.

## 0.0.33 — Portable Microversion Release license and references (T12.03.01)

- Standalone MIT license, portable references, corrected distribution guidance, ZIP and official local installation regressions. Canonical SKILL.md compacted to 8876 UTF-8 bytes; explicit authorization, script table and troubleshooting. [CI 45373618225](https://github.com/Sashido01/TESSERA/actions/runs/45373618225): 486+19 tests PASS. SkillSpector 2.13.6: complete, 17/17 files, 100%, reference_missing 4→0, risk 78→36 (HIGH→MEDIUM), HIGH 2→0, MEDIUM 10, zero suppressions, both fixtures PASS, 19.40 s. NVIDIA: license allowed, RU quality 80.0 (65×0.35 + 80×0.25 + 95×0.25 + 90×0.15), Codex custom provider degraded→loads. Overall CI FAIL only at inherited Go review; release and real activation NOT_VERIFIED.

## 0.0.32 — Dependency CVE and license metadata review (T12.02.02.04)

- Exact installed Python inventory, OSV queries with pagination and negative control, license metadata; Go binary build info for gh/Gitleaks, module and toolchain OSV queries, deps.dev license metadata. Advisory findings, fail-closed execution, no LLM. [CI 45375135316](https://github.com/Sashido01/TESSERA/actions/runs/45375135316) PASS: 477+19 tests; 97 Python package checks, 3 packages with OSV entries; 212 distinct Go modules (gh 155, Gitleaks 66), 8 affected modules across the binaries, Gitleaks stdlib/toolchain and one source-commit entry; 211 Go licenses reported by deps.dev, one NOT_INDEXED. T12.02.02.04 COMPLETE within inventory/query execution scope; CVE remediation, code reachability and legal compatibility remain open.

## 0.0.31 — Direct static SkillSpector review (T12.02.02.03)

- Pinned SkillSpector 2.13.6 source and official wheel, offline lock export, wheel/hash-only separate environment, no LLM, strict scan report and completeness checks, synthetic clean and P1 fixtures, CI and bilingual documentation. [CI 45370414762](https://github.com/Sashido01/TESSERA/actions/runs/45370414762) PASS: 454+19 tests; 16/16 files, 100% coverage, complete_with_caveats (4 reference_missing), risk 78/100 HIGH, exit 1 (threshold 50 exceeded), 12 findings (10 MEDIUM, 2 HIGH), zero suppressions, both synthetic fixtures PASS, 13.32 s. T12.02.02.03 COMPLETE within direct static execution scope; findings and full NVIDIA security acceptance remain open.

## 0.0.30 — Reachable Git history content review (T12.02.02.02)

- Gitleaks scans each distinct reachable UTF-8 blob from local refs and HEAD via stdin; validates complete object inventory, byte coverage, immutable inventory and synthetic removed-secret fixture. [CI 45368434188](https://github.com/Sashido01/TESSERA/actions/runs/45368434188) PASS: 437+19 tests; 585/585 distinct UTF-8 blobs, 5431003 bytes, zero findings, removed-marker fixture PASS, 128.81 s. [CI 45369335974](https://github.com/Sashido01/TESSERA/actions/runs/45369335974) PASS: 443+19 tests; 598 distinct UTF-8 blobs, 5639755 bytes, zero findings; five synthetic rule fixtures PASS; 4 current YAML files and 28 historical rule/blob pairs across 37 commits, zero findings. T12.02.02.02 COMPLETE within declared scope. Unavailable refs and unreachable objects not covered.

## 0.0.29 — Gitleaks text snapshot review (T12.02.02.02)

- Official SHA-256 pinned Gitleaks 8.30.1, separate stdin per tracked UTF-8 file, byte coverage, redaction and exit code checks, negative allow-comment fixture, CI and bilingual documentation. [CI 45367459045](https://github.com/Sashido01/TESSERA/actions/runs/45367459045) PASS: 428+19 tests, 144/144 tracked UTF-8 files, 998544 bytes, zero findings, positive/negative and redaction fixtures PASS; 65.29 s. Snapshot acceptance COMPLETE; history/path-specific rules NOT_VERIFIED; T12.02.02.02 remains PARTIAL.

## 0.0.28 — Direct Bandit static review (T12.02.02.01)

- Isolated review of all tracked Python files with pinned Bandit 1.9.4, strict coverage and report validation, synthetic positive and negative cases, safe aggregates, mandatory CI and bilingual documentation. [CI 45365133732](https://github.com/Sashido01/TESSERA/actions/runs/45365133732) PASS: 414+19 tests, 60 Python files, 87 findings (45 runtime, 42 tests; 2 medium, 85 low, 0 high); clean and negative fixtures PASS; direct review 1.69 s. Direct scan execution COMPLETE; full NVIDIA code-integrity, Gitleaks, SkillSpector and CVEs remain NOT_VERIFIED.

## 0.0.27 — NVIDIA static review and language alternatives (T12.02.01)

- Compare default and localized quality, sanitized finding codes and four dimensions. PII/license/unicode/lint, negative Unicode fixture, six static profiles and Codex scenarios. No LLM, Tier 2/3 or external scanners. [CI 45360122208](https://github.com/Sashido01/TESSERA/actions/runs/45360122208) PASS, 403+19 tests, 75.0/78.8, 18/16 findings, Unicode negative PASS, static profiles confirmed, license not_detected and PII/lint warnings retained. T12.02.01 COMPLETE within fixture scope; T12 PARTIAL. Updated bilingual docs.

## 0.0.26 — Focused NVIDIA SkillEvaluator Tier 1 evaluation (T12.01)

- Pinned official 1.2.0 wheel and 19 dependencies from uv.lock by SHA-256, separate Linux CPython 3.13 environment, schema/quality only without LLM or extras. Verify JSON, exit code and negative case. Findings advisory; execution failure blocks CI. Live acceptance [CI 45358283596](https://github.com/Sashido01/TESSERA/actions/runs/45358283596): schema/quality PASS, 75/100, 18 findings, 393+19 tests PASS; corrected first-run JSON validator name mismatch (QUALITY). T12.01 COMPLETE within stated scope.
- Updated bilingual docs. Full Tier 1, scanners and agent compatibility NOT_VERIFIED; no Tier 2/3.

## 0.0.25 — Isolated multi-skill and independent tag acceptance (T10.03.02)

- Temporary Git repository with two synthetic skills, five annotated tags and independent Git tree checks. Actual local snapshot installs with gh 2.105.0, scoped replacement and rollback, namespace collisions and duplicate refusal. 7 offline tests plus a mandatory CI guard test.
- Clarified low-level InstallLocal versus CLI checkOverwrite; retained defensive guard. Local fixture PASS: [CI 45354011607](https://github.com/Sashido01/TESSERA/actions/runs/45354011607), GH_SKILL_MULTI_FIXTURE_PASS, 383+19 tests. T10.03.02 PARTIAL pending separate remote acceptance. Remote namespaced pin and T16 remain unverified. Updated bilingual docs.

## 0.0.24 — Actual update and guarded re-pin (T10.03.01)

- Actual gh 2.105.0 update --unpin --dry-run and --unpin --all harness against disposable synthetic local edits; verify new Git tree and directory replacement behavior.
- Independently install two exact pins, refuse local edits or staged mutation, retain backup, test injected failure and explicit rollback. 12 offline scenario tests plus mandatory CI guard test.
- T10.03.01 COMPLETE within the harness: [live CI 45352932764](https://github.com/Sashido01/TESSERA/actions/runs/45352932764), GH_SKILL_UPDATE_PASS, 375+19 tests passed; native removal of synthetic local edits confirmed; T10.03.02 (multi-skill collisions and independent tags), crash recovery, concurrent writes and client activation remain unverified. Updated bilingual docs.

## 0.0.23 — Verify remote skill installation at exact tag and SHA (T10.02)

- Added actual official gh 2.105.0 CI acceptance: install from public TESSERA by refs/tags/v0.0.22 and full commit SHA, verify independent Git tree, file inventory and bytes, pin metadata and gh skill list discovery.
- Verify duplicate installation refusal without --force and pinned update --dry-run skipping without file mutation. Isolated HOME and GH_CONFIG_DIR, read-only CI token only, offline negative tests.
- T10.02 COMPLETE: [live CI 45351217500](https://github.com/Sashido01/TESSERA/actions/runs/45351217500) confirmed GH_SKILL_REMOTE_PIN_PASS; 362+19 tests passed. Overall T10 PARTIAL. Applied updates, multi-skill behavior and client activation remain unverified. Updated bilingual docs and ROADMAP.

## 0.0.22 — Record live independent acceptance of the signed ZIP (T09.10)

- At annotated tag `v0.0.21` (commit `0c83ae9ef119a0cfc9d07c83dbae91e5d026e407`), [signing run 45348928593](https://github.com/Sashido01/TESSERA/actions/runs/45348928593) completed SUCCESS; [Attestation 71489191](https://github.com/Sashido01/TESSERA/attestations/71489191), [Actions Artifact 14898798605](https://github.com/Sashido01/TESSERA/actions/runs/45348928593/artifacts/14898798605). Independent verification checked the 105849-byte ZIP, SHA-256 `55db489f0219739e9296fc941fa51fa58d23c3277878fe5e3a352642947eeb73` and all 17 manifest files. The owner on Windows confirmed that digest and supplied official `gh 2.105.0` output: `Verification succeeded!`, one attestation matched SLSA v1, exact repository, commit, tag, signer workflow, OIDC issuer and GitHub-hosted runner. T09.10 COMPLETE, `SIGNED_ARTIFACT=PASS` only for the verified v0.0.21 ZIP.
- Updated bilingual ROADMAP, TRUSTED_BUILD, README and AGENTS. This microversion records evidence; it does not claim a new signature of its own. No GitHub Release was created; overall T09 remains PARTIAL.

## 0.0.21 — Fix ZIP preparation before Sigstore attestation (T09.10)

- Live signing run `45347443989` for `v0.0.19` failed: tag checks and 333+19 tests passed, but the source ZIP builder refused `PACKAGE_RUNTIME_FILE_INVALID`. Sigstore and artifact upload were SKIPPED; no downloadable artifacts exist.
- Root cause: Python imports runtime modules from `skills/microversion-release/scripts/` during tests, creating `__pycache__` which the strict runtime ZIP allowlist correctly rejects.
- Enabled `PYTHONDONTWRITEBYTECODE=1` in both signing and main CI validation jobs. Main CI now performs a mandatory **post-test** reproducible ZIP smoke into `dist/post-tests`, matching the signing order.
- Added negative regression tests for missing bytecode isolation, missing post-test smoke and cache contamination. The strict ZIP allowlist remains unchanged.
- Updated bilingual ROADMAP, TRUSTED_BUILD, README and AGENTS. A fresh live signing run on the newly confirmed annotated version is still required: no attestation has been verified.

**T09.10 status:** PARTIAL / SIGNED_ARTIFACT_NOT_VERIFIED until a real successful signing workflow, downloaded ZIP and independent Sigstore verification.

## 0.0.20 — Safe local Agent Skill installation via official GitHub CLI (T10.01)

- Added real `gh skill install --from-local --dir` and `gh skill list --dir` CI scenarios for `microversion-release`, confined to temporary directories with no access to user profiles.
- Reused SHA-256-verified official `gh 2.105.0`. New `tools/check_official_local_install.py` verifies original source integrity, Markdown body, references and injected source-tracking metadata.
- Checks that `--from-local` cannot combine with `--pin`, refuses preexisting targets before calling the CLI and never publishes a release. Added negative tests.
- Official CLI source review reveals a local `InstallLocal` overwrite risk even without `--force`. Direct repeat local install into a user's existing directory must not be treated as safe; TESSERA's offline fallback remains no-overwrite.
- Updated bilingual roadmap and policies. Actual **remote** pinned installation by tag/SHA and client integration remain NOT_VERIFIED.

**Acceptance:** T10.01 COMPLETE only after a successful live CI run with the real `gh`. Overall T10 PARTIAL, signed ZIP T09.10 remains OPEN.

## 0.0.19 — Actual isolated gh skill publish --dry-run

- Added an official `gh skill publish --dry-run` CI check on a temporary copy of all skills with no GitHub remote or inherited tokens. The exact `gh 2.105.0` release binary is downloaded and SHA-256 verified before execution.
- `tools/run_publish_dry_run.py` verifies CLI identity, positive and negative validation, no remote, and unchanged source files with a SHA-256 tree fingerprint. Errors fail closed without exposing secrets or private paths.
- Added regression tests and bilingual documentation, and updated ROADMAP, README and AGENTS.
- Live GitHub topic/release checks and authenticated remotes are explicitly **out of scope**. T09.10 and agent-client integration remain separate.

**Acceptance:** T11.02 local format validation requires an actually successful CI run; an unsigned package or mocked CLI cannot establish publication readiness.

## 0.0.18 — Upgraded GitHub Actions to Node.js 24

- Pinned official `actions/checkout` v7.0.1, `actions/setup-python` v7.1.0 and `actions/upload-artifact` v7.0.2 by full SHA in the validation and signing workflows. Independently confirmed that the existing pinned `actions/attest` SHA is v4.2.2 and already uses Node.js 24; no needless change was made.
- Added the mandatory `tools/check_actions_runtime.py` check for exact approved SHAs, counts and action inventory in both workflows, plus negative regression tests rejecting rollbacks, floating tags and unknown actions.
- Preserved main protection, annotated tags, separate signing workflow, least privilege, credential removal and ancestry checking.
- Updated bilingual documentation and roadmap. Live signing and independent GitHub attestation remain NOT_VERIFIED.

**Acceptance:** T08.01 needs verified PR/main CI success, a matching annotated tag, and no legacy Node.js 20 warnings from the updated actions. T08 overall remains PARTIAL.

## 0.0.17 — Reference Agent Skills format verification in CI

- Integrated upstream `skills-ref validate` from official `agentskills/agentskills`, pinned to exact SHA `83021e2be457a9b6679148719c1f6074f0ad975e`. The extra checkout runs after TESSERA's own tests and source packaging.
- Pinned `skills-ref` runtime dependencies to versions and wheel SHA-256 hashes; no installation of an unrelated same-named PyPI distribution.
- Added a defensive all-skills wrapper that rejects invalid names, symlinks, missing tooling, timeouts, and unexpected results, with new unit tests.
- Added the bilingual [AGENT_SKILLS_STANDARD](docs/AGENT_SKILLS_STANDARD.en.md) guide and updated the project roadmap and agent rules.

**Limits:** the upstream reference library is expressly for demonstration, not production. Live `gh skill publish --dry-run` and actual client integration remain NOT_VERIFIED. T11 PARTIAL; T11.01 requires a successful CI run.

## 0.0.16 — Reject vulnerable GitHub CLI versions during attestation verification

- Added a mandatory installed `gh` version preflight before `gh attestation verify`. Minimum `2.102.0` includes fixes for GHSA-wjmr-j3rp-mh2g and GHSA-4mq3-hpgx-9cx8 (30 September 2026).
- Unknown, outdated, malformed, or unavailable CLI versions produce `BLOCKED`, never a false `PASS`. The probe has a bounded timeout, and stderr/user paths are not included in reports.
- Added positive/negative regression tests; updated bilingual provenance, trusted-build, and roadmap documentation.
- No claim of an actual signing run or verified publication: T09.10 remains PARTIAL and attestation NOT_VERIFIED.

## 0.0.15 — Offline verification of actual catalog ZIP bytes

- Added `tools/verify_catalog_package.py` to validate archive structure, required files, manifest, every member SHA-256, exact version, and externally supplied full source commit SHA.
- Unsafe paths, symlinks, duplicates, unsupported encoding/compression, limits, and tampered bytes fail closed; ZIP contents are never extracted or executed.
- Added negative unit tests and a bilingual [CATALOG_VERIFICATION](docs/CATALOG_VERIFICATION.en.md) guide.
- Archive internal integrity is distinct from independently verified cryptographic attestation; signing and publication remain NOT_VERIFIED.

**Limits:** live signing, publishing, and agent-client integration remain NOT_VERIFIED; T09 PARTIAL. CI acceptance for this version must be checked after the PR is opened.

## 0.0.14 — Deterministic catalog package and trusted attestation preparation

- Added `tools/build_catalog_package.py`: genuine Agent Skills catalog source ZIP with fixed ZIP metadata, LICENSE, VERSION, runtime skill files, SHA-256 manifest, and exact source Git commit.
- Added separate `build-attested-catalog.yml` **manually dispatched at an annotated tag**, with read-only source permissions and limited GitHub/Sigstore attestation rights. All third-party Actions are pinned to full SHAs; GitHub Releases are not auto-published.
- `release-checks.json` now requires the actual catalog build rather than NOT_APPLICABLE. Ordinary PR CI builds and checks determinism without OIDC signing.
- Added security checks for the signing workflow and negative tests for wrong refs/tags, unsafe files, and source modifications.
- Simplified Git policy: **one working branch per coherent goal and one PR**, not one branch for every intermediate correction. Documented in bilingual [BRANCHING](docs/BRANCHING.en.md).
- Updated canonical Russian and complete English translations of roadmap, VERSIONING, GITHUB_SECURITY, architecture, README, and AGENTS.

**Limits:** executing the workflow against a real tag and validating a genuine signed attestation remain NOT_VERIFIED. The ZIP is stored as a GitHub Actions Artifact, not a GitHub Release; the workflow does not sign executable applications. T09 remains PARTIAL.

## 0.0.13 — Signed release artifact provenance verification

- Added `core/release_provenance.py` to independently hash a local file against GitHub Release metadata and cryptographically verify a Sigstore/SLSA attestation via official `gh attestation verify`.
- Enforced exact repository, source commit SHA, Git tag, specific signing workflow, and SLSA provenance v1 predicate; an arbitrary workflow's claim is not trusted.
- Added fail-closed handling for tampered file bytes, missing publication, unavailable CLI, failed signatures, malformed JSON, and file changes during verification.
- Extended `core/release_report.py` with `--verify-provenance --artifact-file --signer-workflow`; this is disabled by default and excludes local file paths from reports.
- `core/release_certificate.py` separates a verified signed GitHub attestation from **TESSERA's unsigned evidence certificate**; application readiness stays NOT_VERIFIED.
- Added 33 test scenarios, canonical Russian `docs/RELEASE_PROVENANCE.md` and complete English translation, and updated architecture, roadmap, README, AGENTS and technical documentation.

**Limits:** TESSERA does not have a real published and signed artifact. Tests mock the official CLI's outputs; they do not prove live artifact attestation. Trusted build workflow, actual publication, and concurrency controls are future work. T09 remains PARTIAL.

## 0.0.12 — Stream-verified actual release asset bytes

- Added independent `core/release_assets.py`: streaming byte count and SHA-256 verification of attached GitHub Release assets against official API metadata.
- Added bounded-memory streaming, explicit per-file limits, untrusted URL/redirect rejection, and strict matching of repository/tag/filename.
- Extended `core/release_report.py`: `--verify-assets` requires explicit `--verify-publication`; no byte verification is performed by default.
- Preserved the distinction between downloaded byte integrity, build provenance, and application readiness in `core/release_certificate.py`; the certificate SHA-256 remains unsigned.
- Added 32 test scenarios, including corrupted/truncated/oversized bytes, untrusted URLs, missing digests, and unverified publication.
- Added canonical Russian `docs/RELEASE_ASSETS.md` and complete English translation; updated roadmap, architecture, README, AGENTS, reports, and changelogs.

**Limits:** no published TESSERA GitHub Releases existed at inspection time, so a live end-to-end download remains NOT_VERIFIED. Independent build provenance, digital signatures, and executable application readiness are also NOT_VERIFIED; T09 stays PARTIAL.

## 0.0.11 — Verified GitHub Release publication metadata and an evidence certificate

- Added `core/release_publication.py`: read-only verification of published GitHub Release metadata, including exact tag, draft/prerelease flags, publish date, GitHub URL, and asset states.
- Bound the named trusted Git remote to `github.com/owner/repository` so an unrelated URL, local bare Git, or hostname lookalike is not mistaken for GitHub publication.
- Added `core/release_certificate.py`: structured unsigned evidence with reproducible SHA-256 of its own fields and distinct source-publication vs application-readiness statuses.
- Extended `core/release_report.py` with `--verify-publication` and `--format certificate`; publication is neither queried nor created automatically.
- Added 39 positive/negative cases covering metadata, unrelated remotes, missing evidence, unsigned checksums, and report integration.
- Updated roadmap, architecture, README, AGENTS, and bilingual T09.01–T09.05 documentation.

**Limits:** TESSERA had no GitHub Releases at the time of inspection. The implementation does not create one. Live source-publication acceptance is NOT_VERIFIED; asset bytes, signatures, and executable application readiness are not checked. Overall T09 remains PARTIAL.

## 0.0.10 — Independent completed GitHub Actions and evidence-state verification

- Added `core/release_ci.py`: validates a completed GitHub Actions run using the official REST API and exact commit SHA, expected workflow, push to main, and both required jobs.
- Mismatching attempts, missing/skipped/failed required jobs, incomplete API responses, and network failures result in BLOCKED, never a false PASS.
- Added a pure `core/release_state.py` evidence-stage reducer without an invented RELEASED state.
- Extended `core/release_report.py` with explicit `--verify-ci`, trusted GitHub repository and completed run ID, and new CI fields in JSON/Markdown.
- Added 32 positive/negative scenarios covering GitHub API responses, incomplete pagination, SHA/attempt mismatch, and disabled-by-default network access.
- Updated canonical Russian documents and complete English translations, including previously stale branch-protection descriptions.

**Limits:** public workflows can be queried without a mandatory token only on explicit request. A workflow cannot independently confirm its own completed state while still running. T09.04 does not prove application publication; overall T09 remains PARTIAL.

## 0.0.9 — Remote annotated-tag verification and evidence-based reporting

- Added `core/release_remote.py` to check the exact remote `refs/tags/<version>` and compare the **annotated tag object SHA**, rejecting missing refs, mismatches, and network errors.
- Added `core/release_report.py` for structured JSON/Markdown evidence reports combining local Git, Release Preflight, and explicitly requested remote verification.
- By default, reporting performs no publication, build/test execution, or network access. Remote queries and executing project commands require separate explicit flags.
- Added 20 unit tests using temporary local Git repositories, including same-commit/different-tag-object, historical release, and incomplete-evidence cases.
- Added independent remote verification to the automated tagging job after annotated-tag creation.
- Updated canonical Russian docs and full English translations of ROADMAP, README, AGENTS, and the dedicated reporting guide.

**Limits:** `evidence_status=PASS` verifies only requested checks; `release_readiness` remains `NOT_VERIFIED`. External CI/artifact attestation, test adequacy, final RELEASED state and concurrency are not implemented. T09 remains PARTIAL.

## 0.0.8 — Added release preflight and explicitly authorized build/test checks

- Implemented `core/release_preflight.py`: checks VERSION and release notes in the exact commit, worktree cleanliness, and declared build/test configuration.
- Added safe default `--plan` mode, which executes no commands, and explicit `--execute` mode running only approved project-configured argv with `shell=False`.
- Added TESSERA's `release-checks.json`; the missing build artifact is explicitly NOT_APPLICABLE with an explanation, while two test suites are required.
- Added 22 test scenarios for wrong versions, missing release notes, dirty worktrees, invalid configurations, failed checks, and timeouts.
- CI performs `--plan` only, never executing arbitrary PR-supplied commands; `--execute` tests use isolated temporary Git repositories.
- Added canonical Russian documentation, complete English translations, and updated the roadmap.

**Limits:** passing checks only proves locally executed steps returned success; external CI, signatures, remote tags, and GitHub Releases are not verified. T09 remains PARTIAL and `release_readiness=NOT_VERIFIED`. T08 remains PARTIAL pending risky negative-protection tests.

## 0.0.7 — Introduced independent release evidence inspection

- Added `core/release_inspect.py`: read-only inspection of Git history, the `VERSION` file in a specific commit, and annotated tags.
- Added verification of **historical** releases using full commit SHA, without incorrectly requiring the tag to match current HEAD.
- Explicitly reports missing, lightweight, wrongly targeted tags and version mismatches.
- Added 13 unit scenarios, including checks that inspection does not modify Git state.
- Recorded the complete T08 acceptance cycle: invalid PR — FAIL, corrected PR — PASS, squash merge, verified annotated `v0.0.6`.
- Updated canonical Russian documentation, complete English translations, roadmap, and limitations.

**Limits:** the inspector does not run builds/tests or check remotes. PASS proves only tag/recorded-version consistency, not release readiness. T09 remains PARTIAL; T08 remains PARTIAL pending risky administrator and tag-protection negative tests.

## 0.0.6 — Verified rejection of invalid changes through Pull Requests

- Confirmed two active GitHub Rulesets through the API, protecting the main branch and existing tags.
- Created Pull Request #1 with an intentionally incorrect `0.0.99` version rather than `0.0.6`; `validate` failed due to a broken version transition and missing changelog entries.
- Confirmed that tagging was skipped after FAIL and the Pull Request was blocked.
- Prepared the corrected `0.0.6` and bilingual documentation for repeat validation and squash merge.
- Updated public documentation to reflect actual server-side controls without claiming unperformed tests.

**Outstanding validation:** successfully merge the corrected Pull Request and create the annotated `v0.0.6` tag; T08 remains PARTIAL until verified.

## 0.0.5 — Hardened GitHub Actions and documented Git protection

- Pinned official GitHub Actions to full commit SHAs; the validation job no longer persists Git credentials.
- Annotated tag creation now stops if remote `main` changed or existing tags cannot be checked.
- Added a static workflow-security validator and six positive/negative unit tests.
- Documented branch and tag GitHub Rulesets in canonical Russian and complete English translation.
- T08 is PARTIAL/BLOCKED: Rulesets are neither applied nor verified, and concurrent releases are not fully serialized.

## 0.0.4 — Clarified public dependency documentation

- Removed names of excluded third-party products from the current public documentation and the changelog as shown on the main branch.
- Documentation now covers only the approved stack: official GitHub CLI, minimal first-party Python tools, and free validation tools.
- Adopted a rule not to list rejected products by name in public materials.
- Kept canonical Russian documents and full English translations aligned without modifying executable components.

**Limitation:** already published Git commits were not rewritten; older document revisions remain in the repository history.

## 0.0.3 — Architecture and roadmap approved

- Expanded the single roadmap with T08–T17, priorities, prerequisites, and verifiable acceptance criteria.
- Adopted one independent Release Core with thin Codex, Harness, Claude Code, and Hermes adapters.
- Selected official GitHub CLI as the planned preferred distribution tool; retained a minimal Python offline fallback.
- Defined a minimal GitHub CLI and Python distribution stack; limited NVIDIA SkillEvaluator to free Tier 1 after isolated evaluation; excluded Tier 2/3 and mandatory paid AI APIs.
- Planned reference Agent Skills validation with `skills-ref` and separate measurement of NVIDIA Tier 1 quality and resource usage.
- Updated architecture, repository rules, and complete English translations without changing executable scripts.

**Status:** documentation and policy changes only. Planned external tools have not been installed and cross-agent integrations remain unverified.

## 0.0.2 — Skill made portable across agent hosts

- Removed the Harness-only scope of Microversion Release and documented Codex, Claude Code, Hermes, and other compatible hosts.
- Added a safe local installer with preview-first behavior and refusal to overwrite existing skills.
- Made annotated Git tags mandatory for every release, with verification of tag type, message, and target commit.
- Added a release-tag creation/verification helper and tests for missing, lightweight, and incorrect tags.
- Updated canonical Russian documentation and complete English translations. Integration with specific installed agent clients remains NOT_VERIFIED.

## 0.0.1 — Mandatory catalog microversioning introduced

- Applied the same rules to TESSERA itself as to Microversion Release: PATCH+1 for verified changes, planned `.99` release milestones, and continued `.100+` microversions for unfinished tasks.
- Introduced the canonical `VERSION` file and validation of each version transition.
- Configured automated annotated Git tags after successful validation of commits on `main`.
- Updated both Russian and English development and release instructions.
- Preserved previously added English translations, language rules, and published Git history.

**Limitation:** tag creation depends on GitHub Actions permissions. Build artifacts and GitHub Releases are not published automatically.

## 0.0.0 — Initial library (23 November 2026)

- Created the public catalog of portable Agent Skills.
- Added the first skill, Microversion Release, with rules for working microversions and release milestones.
- Documented clear, human-readable Russian commit, tag, and release descriptions.
- Added tests for version calculation and catalog structure.
- Added contribution, security, and roadmap documentation.

**Status:** initial repository state. Automatic integration with an installed Harness, build publication, and GitHub Release publication have not been verified.
