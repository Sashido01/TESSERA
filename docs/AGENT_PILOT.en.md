# TESSERA pilot in Codex and DeepSeek Harness

[Русский — оригинал](AGENT_PILOT.md) | **English — translation**

**Status:** acceptance instructions; real client trials NOT_VERIFIED. Owner priority of 25 November 2026: start a pilot before the entire roadmap is finished. T03–T05/T13, TD06/TD13–TD15. A pilot is not an independent release or mandatory enforcement.

## Entry conditions

- Only a fresh disposable local project, without a remote, production data, secrets, global hooks or changes to real projects. Do not grant additional privileges to the agent. Do not execute security scanners in the client profile.
- Pinned catalog snapshot: annotated tag `refs/tags/v0.0.72` (main CI 45594813517). Verify the remote tag object and its commit, review all three SKILL.md and supporting files before use. Independent skill tags are not yet confirmed. Versions in this snapshot: Microversion Release 0.0.1, Project Audit 0.0.2, Repository Workflow 0.0.1. Project Audit has an open HIGH test-file finding (#77); do not interpret the pilot as permission for production use.
- Official gh 2.105.0 was verified for remote pin of one skill; remote multi-skill installation and actual host loading remain trials. Do not use --force, --all, unpinned updates or third-party managers. NVIDIA scanners are not runtime requirements.
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
    gh skill install Sashido01/TESSERA $skill --pin refs/tags/v0.0.72 --dir $dest
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

## Actual partial Codex acceptance — 25 November 2026

Source: owner's own session report, not CI. User profile, Windows, Python 3.14, official gh, three directories pinned to `refs/tags/v0.0.74` → `ddab826e5a17641e0f475ecc63193f412065e28e`. Owner reports gh skill list, pinned=true and matching Git trees; raw logs and exact client/model/gh versions are not available. GitHub API independently confirms tag and source trees:

| Skill | Tree | Owner-reported tests / result |
| --- | --- | --- |
| Microversion Release 0.0.1 | `78d4645561a0b294e93b4a85b67e7cf51a339fd3` | 38/38 PASS after clearing inherited GIT_CONFIG_* only in the test process |
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
