# TESSERA pilot in Codex and DeepSeek Harness

[Русский — оригинал](AGENT_PILOT.md) | **English — translation**

**Status:** acceptance instructions; real client trials NOT_VERIFIED. Owner priority of 25 November 2026: start a pilot before the entire roadmap is finished. T03–T05/T13, TD06/TD13–TD15. A pilot is not an independent release or mandatory enforcement.

## Quick start: not a repository audit

Verified catalog snapshot: `v0.0.88`, commit `015bed7f9eaf344b59e699a4b607c0e21b86f608`, main CI 45874463052 SUCCESS (6/6). Three independent annotated tags and trees match this snapshot. A GitHub Release is not required for tag-pinned installation; a missing releases/latest does not imply missing skills.

| Skill | Pin | Commit | Skill tree |
| --- | --- | --- | --- |
| microversion-release | `refs/tags/microversion-release/v0.0.6` | `015bed7f9eaf344b59e699a4b607c0e21b86f608` | `12aebcae998b098a1e7d3c5f1fadd8bcd2b096e7` |
| project-audit | `refs/tags/project-audit/v0.0.6` | `0b207f09bb9fca7cf5525d6b35a1919e1d316515` | `50d3f3dee94f1ceff9df343ef34689caf99ca184` |
| repository-workflow | `refs/tags/repository-workflow/v0.0.2` | `a2a6af6b66e9cd6e5b28ccb227245f3a13389098` | `7bd8a54e7102a4bd83ae4b6c14e296a91c5b9f9c` |

1. First inspect only the three installed directories in the active profile and their versions. If they match verified trees (accounting for gh install metadata), do not reinstall.
2. If installation is needed, use a fresh empty project and the three exact pins below; if the API is unavailable, a verified local checkout of the exact tag and native --from-local installation into an empty directory are acceptable. A local copy is not a remote pin. Do not audit all history or use latest/main, --all, --unpin or --force against the user profile.
3. Open a fresh session after installation and explicitly invoke each skill: Codex via $name (e.g. $microversion-release), Harness via native /name or the skill tool. Run P01–P05 as separate short prompts. For P06 use a fresh session without naming the skill; a correct answer alone does not establish loading. Negative control: an unrelated task with no expected invocation.
4. Bound network retries to two attempts per operation; record BLOCKED on refusal and continue independent local read-only checks. Do not change permissions or scrub the production environment. P07/P08 and Stop-hook are separate authorized trials, not prerequisites for starting P01–P06.

## Entry conditions

- Only a fresh disposable local project, without a remote, production data, secrets, global hooks or changes to real projects. Do not grant additional privileges to the agent. Do not execute security scanners in the client profile.
- Use only the current pin table above; earlier snapshots below are historical evidence, not installation instructions.
- gh 2.105.0: owner confirmed remote multi-skill install and explicit Harness loading; metadata-record warning requires separate verification. Do not use --force, --all, unpinned updates or third-party managers.
- Record exact client, model, gh, Git, Python and OS versions. Confirm the active profile and actual project roots. For Harness confirm dsh-skill/dsh-skill-filesystem/dsh-tool-skill are enabled. Do not modify the global profile during the trial.

## Installation: separate clean project for each client

Windows PowerShell below. Repeat for each client in a fresh session, selecting `codex` or `harness`. Do not run in an existing project. Stop after any failure. CLI has no install --dry-run.

```powershell
$client = 'codex' # or harness
if ($client -notin @('codex','harness')) { throw 'Invalid client' }
$root = Join-Path ([IO.Path]::GetTempPath()) ('tessera-pilot-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $root -ErrorAction Stop | Out-Null
$relative = if ($client -eq 'codex') { '.agents/skills' } else { '.dsh/skills' }
$dest = Join-Path $root $relative
if (Test-Path -LiteralPath $dest) { throw 'Destination exists' }
New-Item -ItemType Directory -Path $dest -ErrorAction Stop | Out-Null
gh --version
foreach ($skill in @('microversion-release','project-audit','repository-workflow')) {
    if (Test-Path -LiteralPath (Join-Path $dest $skill)) { throw 'Skill already exists' }
    $pin = switch ($skill) {
        'microversion-release' { 'refs/tags/microversion-release/v0.0.6' }
        'project-audit' { 'refs/tags/project-audit/v0.0.6' }
        'repository-workflow' { 'refs/tags/repository-workflow/v0.0.2' }
    }
    gh skill install Sashido01/TESSERA $skill --pin $pin --dir $dest
    if ($LASTEXITCODE -ne 0) { throw "Installation failed: $skill" }
}
gh skill list --dir $dest --json
if ($LASTEXITCODE -ne 0) { throw 'Listing failed' }
Write-Output $root
```

Verify listing, pin, GitHub path, versions and files; stop the pilot on mismatch. Installation alone is not agent discovery. Open **only this directory** in the relevant client with restricted permissions. For a manual alternative, use complete reviewed skill directories from an exact checkout; do not copy SKILL.md alone. See [GH_SKILL_INSTALL](GH_SKILL_INSTALL.en.md).

## Same initial matrix for both clients

| ID | Action | Required observation |
| --- | --- | --- |
| P01 | Open new project, show skill list | All three visible from the project root; record path/version, not merely gh skill list |
| P02 | Explicitly select Microversion Release; ask for the next working version after 0.0.99, task unfinished | 0.0.100, no writes |
| P03 | Explicitly select Microversion Release; claim successful 0.1.0 without a tag in a test Git repo | BLOCKED/RELEASE_NOT_TAGGED; no unauthorized tag creation |
| P04 | Explicitly select Project Audit; supply a README promising an unimplemented feature in a new project | Find an evidenced gap; no writes or invented tests |
| P05 | Explicitly select Repository Workflow; supply two tasks with overlapping write scope and one independent task | Do not run conflicting tasks together; continue independent work |
| P06 | New session, repeat P02/P04/P05 without explicit selection | Evidence of skill loading, not just a correct answer |
| P07 | With separate permission and in disposable Git only, run a positive release fixture | Actual tests, exact commit and annotated tag; no remote/push |
| P08 | Separate negative fixture: missing tag, stale SHA/hook failure | Do not claim RELEASED; hook error is not PASS; mandatory gate remains NOT_VERIFIED |

P02–P06 are read-only by default. P03/P07/P08 use a separate owner-created local Git fixture; never target a real project. Do not enable a hook before reviewing schemas/permissions and obtaining separate authorization. Small synthetic data is sufficient for P04/P05. Also record baseline outcomes without skills, with identical model and input. The full E01–E20 and RW01–RW20 remain future trials, not replaced by eight probes.

## Evidence and adoption gates

For each row record client/version, model, OS, catalog commit, skill version, prompt, evidence of loading and observable actions, exit code/verified diff if applicable, PASS/FAIL/NOT_VERIFIED and limitations. Do not publish secrets, full transcripts or private paths. Track INSTALL, DISCOVERY, EXPLICIT_USE, AUTO_USE, ENFORCEMENT separately. Do not claim AUTO_USE without observable invocation.

Pilot use is permitted in a disposable project after source review. Limited project adoption follows P01–P06 PASS on the specific client, resolution of applicable risks, explicit skill selection and no global changes. Mandatory automation needs T13, positive and negative P07/P08 and an independent Git/CI gate; missing or failed hooks must not yield a false RELEASED. Wider distribution requires independent tags, pin/update/rollback and client-specific acceptance. Do not wait for a stable catalog version to start piloting; do not claim production readiness without evidence.

Sources: [ROADMAP](ROADMAP.en.md), [Microversion Release integration contract](../skills/microversion-release/references/INTEGRATION.en.md), [Project Audit acceptance](../skills/project-audit/references/ACCEPTANCE.en.md), [Repository Workflow acceptance](../skills/repository-workflow/references/ACCEPTANCE.en.md), [T13 research #40](https://github.com/Sashido01/TESSERA/issues/40).

## Historical snapshots (not current acceptance)

The following records describe earlier states and are not instructions for the current release.

## Actual partial Codex acceptance — 25 November 2026

Source: owner's own session report, not CI. User profile, Windows, Python 3.14, official gh, three directories pinned to `refs/tags/v0.0.74` → `ddab826e5a17641e0f475ecc63193f412065e28e`. Owner reports gh skill list, pinned=true and matching Git trees; raw logs and exact client/model/gh versions are not available. GitHub API independently confirms tag and source trees:

| Skill | Tree | Owner-reported tests / result |
| --- | --- | --- |
| Microversion Release 0.0.2 | `78d4645561a0b294e93b4a85b67e7cf51a339fd3` | 38/38 PASS after clearing inherited GIT_CONFIG_* only in the test process |
| Project Audit 0.0.2 | `cb9b6ed00e31b47ea4af09ec359483c7d2abbd1b` | FAIL: false DEVICE_BOUNDARY with nested file, three failures, FIFO skipped. Report: 22 passes, 3 failures, 1 skip; exact denominator unresolved without raw summary. [#80](https://github.com/Sashido01/TESSERA/issues/80) |
| Repository Workflow 0.0.1 | `f0d2ef77fc40211b9f0bccd113c0b2e5857e6d68` | 13/13 PASS; planner READY_WORK |

INSTALL=OWNER_REPORTED_PASS (3/3); DISCOVERY, EXPLICIT_USE, AUTO_USE, ENFORCEMENT=NOT_VERIFIED, Harness=NOT_VERIFIED. GitHub connector reading VERSION does not prove skill invocation. Do not weaken GIT_CONFIG_* fail-closed behavior for tests; establish the exact inheritance contract in actual Codex (no weakening or deleting system settings). Use `python -B` or PYTHONDONTWRITEBYTECODE=1 for repeated local tests. Do not delete profile directories or reinstall without staged pin/rollback. Do not repeat installation of an already installed profile. New session with exact pin and observed skill invocation is the next acceptance. Do not treat Windows inventory of a real project as complete until native retest. The other two skills are suitable for supervised manual use; automatic activation is unproved.

## Repeat Codex Desktop acceptance — 25 November 2026 (owner report)

Skills pinned to v0.0.74; clean repository main v0.0.75 / 115f79daae5886606261cb59c4d5ab2fd045f173. Windows 11 Pro build 26200, Python 3.14.3, Git 2.52.0.windows.1, gh 2.105.0, Codex 26.1123.915.0; current chat UI showed GPT-6 Luna High. Source: owner report; raw transcripts/logs not received; private paths/session IDs not published.

| Skill | INSTALL / DISCOVERY / EXPLICIT_USE | AUTO_USE | ENFORCEMENT | Unit |
|---|---|---|---|---|
| Microversion Release | PASS / PASS / PASS (owner-reported) | Behavior PASS, no independent invocation trace | PARTIAL, local annotated tag and negative SHA/lightweight/GIT_CONFIG_* probes | 38/38 |
| Project Audit | PASS / PASS / PASS (owner-reported) | PARTIAL, expanded hypothetical scope to unrelated checkout | PARTIAL, read-only in observed run | 21 PASS, 3 FAIL, 1 SKIP = 25 |
| Repository Workflow | PASS / PASS / PASS (owner-reported) | Behavior PASS | PARTIAL, no concurrent runtime CI/write | 13/13 |

Denominator correction: earlier Project Audit report was ambiguous; new exact summary 21+3+1=25. Full catalog unit suite: 710, 9 errors, 1 skip, exit 1; TD18 #82. Release Inspect 27/27 after cleaning only child test process, original safe refusal GIT_CONTEXT_UNSAFE; TD17 remains open for real safe invocation. Candidate v0.0.76 NOT_VERIFIED on owner's network (NETWORK_UNAVAILABLE); GitHub API confirms root v0.0.75, PR #74, commit 5a03fc7a7dd402287193108ddbb1f1ef168bb2d1, CI 45620060381 native Windows skill suite 39+42+13 PASS, 1 FIFO skip. Full catalog Windows not confirmed. New candidate 054154dc6fcc899e1a611227cf881f2fd01f47c0 includes scope guard, Git Inspector allowlist and full Windows unit gate; its CI unverified. Repeat Project Audit AUTO_USE with explicit scope and unrelated checkout; observe invocation and no accesses outside fixture. Do not update installed profile before safe acceptance; update/rollback and Harness open.

### Next snapshot — 25 November 2026

TD02/T16 BLOCKED ([#83](https://github.com/Sashido01/TESSERA/issues/83)): owner-reported Rule Suites 5360899907, 5359993044, 5359256574, 5359221161 all failed on creation of refs/tags/microversion-release/v0.0.1 (before_sha is 40 zeros). Latest suite detail requires owner access (connector 403). Ruleset 27932769 unchanged; do not retry push until the specific rule is identified. TD18 #82: Windows CI 45626552407 full catalog 713 = 705 PASS + 1 FAIL + 4 ERROR + 3 SKIP, skill suites 39/39 + 43/44 (FIFO skip) + 13/13. Four Linux secure-open Bandit/Gitleaks scenarios and canonical reference-skills fixture root addressed in 45eaeed021eb4fc36c805d2260aa2d0071f1abdd; new CI 45627814264 not completed. TD14 #77: same catalog_checks 139248180713 PE3/E2 absent, risk 53 vs 72, 9 MEDIUM + 1 LOW, standalone 0 individual HIGH; integrated policy FAIL due to aggregate >50. Do not change threshold; investigate remaining findings. None of this replaces acceptance into main, independent tags or repeat agent acceptance.

### Confirmed TD02 cause and full Windows PASS — 25 November 2026

Owner-reported rule-suite 5360899907: `workflow_updates` FAIL (GitHub App lacks workflows permission for historical `.github/workflows/validate.yml`); secret_scanning and ruleset 27932769 update/non_fast_forward/deletion PASS. Do not weaken ruleset. One-time owner historical tag recovery from an isolated fresh clone at exact main 115f79daae5886606261cb59c4d5ab2fd045f173: plan-only `tools/publish_skill_tags.py`, verify four historical pairs (catalog v0.0.66/67/69/71) and explicitly publish sequentially. Do not store credentials in CI or code. Annotate new tags, create absent refs only, never move existing refs; verify remote and rerun failed main tag job. #83 OPEN until actual proof.

TD18 #82: 45627814264 Windows job 139252599141 exact 45eaeed021eb4fc36c805d2260aa2d0071f1abdd SUCCESS: catalog 715 = 708 PASS + 7 platform SKIP; skills 96 = 95 PASS + 1 FIFO SKIP. Linux-only secure-open and Bash checks are not claimed as Windows runtime. Full Linux/combined gate not yet completed at observation, main remains v0.0.75. New candidate 892cdaca33bdeb9c679a674d672c700dbd2e11e6 additionally checks Project Audit test import origin; repeat CI/scanner not yet confirmed. Do not update installed v0.0.74 before acceptance.

### Historical candidate status — 25 November 2026

Historical branch snapshot before sequential independent tag acceptance: PR #74 exact 892cdaca33bdeb9c679a674d672c700dbd2e11e6, CI 45628965053 SUCCESS for all required groups. Windows catalog 715 = 708 PASS + 7 platform SKIP, skills 98 = 97 PASS + FIFO SKIP; total 813 = 805 PASS + 8 SKIP. SkillSpector 2.13.7 risk: Microversion Release 30, Project Audit 38 (previously 72→53; 7 MEDIUM + 1 LOW), Repository Workflow 14. FULL_TIER1 all policy verdicts PASS; advisory review, not certification. TD14/TD16/TD18: PR evidence PASS, main acceptance and repeat agent acceptance were open at that time. TD02 #83: owner reported GitHub CLI refresh; independent tag publication was still pending then, and the three refs are now confirmed in the `v0.0.80` snapshot above. TD13 #76: 9db01ec3170a5a3c684fc82eb9d5bd54cd2c337a, separate skillspector-provenance-preflight branch, static wheel verifier 9/9 synthetic Linux PASS; actual release wheel bytes and preinstall gate integration NOT_VERIFIED.

## Current snapshot at PR #88 preparation

v0.0.80: all eight independent tags verified; #76/#77/#80/#82/#83 closed. Actual client installation of new exact pins, discovery, explicit invocation, AUTO_USE, ENFORCEMENT, UPDATE and ROLLBACK require new acceptance. #81 remains open; owner post-check of 0.0.80 rejected GIT_CONTEXT_UNSAFE. Never silently clear production context or transfer old-profile evidence to a new pin.

26 November 2026: Microversion Release pin updated to accepted 0.0.3; P03 may use diagnostic `python scripts/release_tag.py context` from the installed skill (names only, no Git). Not authorization to run Git. #81 open. For paired evaluation record identical fixtures, model, permissions, tools, budget and fresh sessions; measure criterion PASS, skill invocation, false activation, violations and cost separately. Compare against no-skill controls; no statistical significance claim from one trial.

## Actual owner pre-release trial — 26 November 2026

Source: owner-supplied Codex report (OWNER_REPORTED, not independently reproduced by remote CI). v0.0.84, main df8116f35fdfe2ccb7ee4a4316053455c407d3e9, clean checkout, 94/94 tag refs match, 6 clean worktrees. Git 2.52.0.windows.1, Python 3.14.3, gh 2.105.0, Codex CLI 0.166.0, Desktop runtime 26.1123.915.0. Harness CLI/installation not found — NOT_VERIFIED, not proof of absence. Both separate test directories: gh skill install/list confirmed 3/3 exact pins (Microversion Release 0.0.3, Project Audit 0.0.5, Repository Workflow 0.0.2); G03 partially accepted for placement and pin, activation/update/rollback not accepted. Codex GUI geometry unavailable, no prompts sent. Unit suites under inherited context: Microversion 42 (20 PASS, 3 FAIL, 19 ERROR); Audit 75 (61 PASS, 13 ERROR, 1 SKIP); Workflow 17/17 PASS. Individual errors NOT_DIAGNOSED; clean CI PASS does not transfer to clients. next_version CLI .99→.100 and .99→0.1.0 PASS; release_tag context exit 1 GIT_CONTEXT_UNSAFE / Git NOT_EXECUTED. P02–P08, E/RW client scenarios not accepted, #81 OPEN. First diagnose exact errors and availability of trusted invocation, then full client tests after published pins. Never strip inherited configuration or expand permissions. Preserve branches with unique commits and occupied worktrees; deletion not verified. Do not publish local paths.

## Pinned Harness 0.2.2-rc.5 preparation

Owner reported npm 12.0.2, Node 24.18.0, npm view @deepseek-ai/dsh 0.2.2-rc.5 engines >=24.9.0 — manifest compatibility PASS, launch NOT_VERIFIED. In separate trusted disposable environment first inspect exact-version npm metadata, dist.integrity and same-version hooks-codex peerDependencies. No global installation or automatic latest/alpha launch. [rc.5 source](https://github.com/deepseek-ai/deepseek-harness/tree/dsh-v0.2.2-rc.5), [safety](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.5/SAFETY.md), [headless](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.5/packages/bundle/headless/README.md). Headless does not use saved GUI login; authorize model route separately, never send secrets in prompt/argv/public report. Record exact host/bridge pins, runtime, observed hook/invoked and hook/result, exit and final.reason.kind, independent Git/test check. Tool_result completed does not prove shell success. Guarded Run 0.0.5 candidate requires --expected-version. Do not use before accepted independent tag. Never modify real projects or existing profiles.

## CLI and npm metadata evidence — 26 November 2026

OWNER_REPORTED: npm 12.0.2 / Node 24.18.0, @deepseek-ai/dsh@0.2.2-rc.5 dist.integrity sha512-cNbp12tLYLUTXaVli7zwwMjzmmEVCD1PRldg4oKtXM4+lFYckcaliMS2PU/FoThB4iAN/fKOSID0nrtRZU4Gjw==; hooks-codex@0.2.2-rc.5 sha512-S8xLbJfTESwXVXTTh+Bav+FgU0MWU1rlBcGfKD6zLGxdYRYO+jo8JaRsH0y8JkEKYCkALr0rzX52yCYC9R3khA==; peer dsh-llm/agent/tools/session/hook-protocol/working-directory all rc.5, cordis ~4.1.0. npm exec exact rc.5 showed help — CLI_LAUNCH_PASS (not independent tarball verification or transitive lock), deprecated node-domexception 1.0.0 warning. Next separate test profile/machine, headless help, model route and minimal safe task; bridge installation and actual skill loading NOT_VERIFIED. Never change real profiles, launch in working checkout, or publish credentials/full config dumps. For current trial after main CI select exact published independent tags .5/.6/.2, verify targets; .4 already published but exact-target Guarded Run is in .5.

## Owner-confirmed headless help

26 November 2026: exact npm pin 0.2.2-rc.5 printed dsh --profile headless --help. PROFILE_HELP_PASS, not model session. Next bounded trial: fresh disposable project and separate DSH_HOME and DSH_AGENTS_HOME (both needed, see [home-paths rc.5](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.5/packages/util/home-paths/README.md)); no global skills, extra writable roots or full access. [skill-filesystem rc.5](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.5/packages/skill/skill-filesystem/README.md): project .dsh/skills rank 100, shared .agents/skills rank 200. Use current published .5/.6/.2 pins; retest affected scenarios after update. First model run only P01/P02 discovery/explicit read-only calculation; no repo changes. Inspect actual NDJSON session, skill load and CLI tool_call/tool_result, final.reason.kind=completed and exit 0. Raw events may contain prompts, args or private data; report sanitized facts only. Missing authorized model route or sandbox refusal means BLOCKED; no expanded rights. Do not install bridge until clean run verified.

## Owner acceptance 2026-11-27 — v0.0.88

OWNER_REPORTED: Harness 0.2.2-rc.1, 29 PASS / 1 FAIL / 4 NOT_VERIFIED. All three trees match the table above; explicit calls of all three skills, unknown-name refusal and actual headless P02/P04/P05 observed. Supplied JSONL independently confirms native successful skill dispatch for all three, but not every child run. Guarded Run positive and negative fixtures, unit suites 78/78, 76 PASS + 1 FIFO SKIP, 17/17 are OWNER_REPORTED. AUTO_USE, live GUI, Stop-hook NOT_VERIFIED; gh search unavailable. gh 2.105.0: could not record install warning about missing USERPROFILE variable (exact cause not independently reproduced), files and frontmatter owner-verified. Do not recommend broad --unpin --all; individual staged pin/rollback and preservation of adjacent skills required. Codex: network timeout, installation/activation NOT_VERIFIED, #81 OPEN. Repeat narrow checks locally; fail closed on unsafe Git context, without removing restrictions.
