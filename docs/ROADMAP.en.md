# TESSERA roadmap

[Русский — оригинал](ROADMAP.md) | **English — translation**

**Purpose:** incremental development of a shared public Agent Skills catalog with one verifiable microversioning core and thin adapters for different agent systems.

**TESSERA's own versioning:** mandatory microversions under the [version policy](VERSIONING.en.md). Roadmap stages do not reserve version numbers or justify dummy commits. The `.99` milestone permits a release only after completion and verification; unfinished work continues as `.100+`.

**Owner-approved constraints (23 November 2026):** do not add third-party skill package managers; never use NVIDIA SkillEvaluator Tier 2 or Tier 3; never require paid AI APIs. Official GitHub CLI is the preferred distribution mechanism once validated; a minimal Python installer remains an offline fallback. Russian is canonical; complete English translations must be updated in the same change. See [dependencies and boundaries](DEPENDENCIES.en.md).

## Status definitions

- `COMPLETE`: the actual files and required test results exist, with limitations reported.
- `PARTIAL`: some work exists but mandatory acceptance criteria are unmet.
- `NOT_VERIFIED`: code or instructions exist, but execution in the target environment has not been verified.
- `NOT_STARTED`: implementation has not begun; this roadmap is not evidence of completion.
- `BLOCKED`: a specific blocker and its cause have been recorded.

The current statuses below are based on GitHub source and a successful Linux GitHub Actions run for TESSERA `v0.0.21`. They do **not** prove execution in installed agent clients or local Windows environments.

## Product priority (25 November 2026)

**Practical adoption is a P0 priority (25 November 2026).** Start the [pilot of all three skills](AGENT_PILOT.en.md) in isolated Codex/Harness projects alongside T16 recovery and TD13/TD14 triage. Do not wait for all infrastructure; do not carry open risks into production profiles. T13: discovery and explicit use first, automatic activation next, and a separate mandatory gate. Historical snapshots below do not describe current client readiness. TD15 tracks status reconciliation.

The owner approved the staged evolution of Project Audit: I — usable skill; II — deterministic helper; III — extended audit; IV — incremental audit; V — advanced verification. A separate skill roadmap will accompany its sources. T12 remains PARTIAL: Semgrep, advisory applicability, races and native environments remain open; critical risks block affected operations, other work does not delay skill development. Existing mandatory checks remain in force. T13 and T16 are the next parallel product directions.

v0.0.64: main CI 45489532663 PASS, annotated tag verified (commit `2e09871bf1829d70cf314f05f5d0cbbf081aff20`). T02/T16 candidate: shared test runner for all skills, CI and signing; acceptance still requires CI. Independent skill versions and real activation remain open.

T16 candidate: independent Microversion Release VERSION/changelogs, first-parent transitions, metadata packaging and verification. CI still required; namespaced tags, actual updates and activation remain open. Project Audit is developed separately.

Project Audit 0.0.1: level I sources, its own [roadmap](../skills/project-audit/references/ROADMAP.en.md). Actual agent and independent release NOT_VERIFIED; tooling is a separate stage. CI required.

## Foundation stages T00–T07

| Stage | Goal | Verified status |
| --- | --- | --- |
| T00 | Public catalog, documentation, MIT license, contribution rules | COMPLETE — published |
| T01 | Microversion Release, version calculator, annotated tagging | COMPLETE for code and unit tests; host integration unverified |
| T02 | Structural checks, unit tests, GitHub Actions | COMPLETE for current CI; server-side Rulesets enabled separately in T08 |
| T03 | Install and discover the skill in actual DeepSeek Harness | NOT_VERIFIED |
| T04 | Event-driven mandatory workflow in Harness | NOT_STARTED |
| T05 | Installation guides and helper for Codex, Claude Code, Hermes, Harness | PARTIAL — prepared; real hosts NOT_VERIFIED |
| T05.1 | Verify installed skills in Codex, Claude Code, Hermes | NOT_VERIFIED |
| T05.2 | Verify a missing-tag release is blocked in a multi-agent environment | NOT_VERIFIED |
| T06 | Safe skill update management | PARTIAL — local copying exists; pin/provenance/update absent |
| T07 | Compatibility and reproducible release packages | NOT_STARTED |

## Priority stages T08–T17

Complete work as small verifiable changes, assigning a new microversion only to a genuinely finished unit of work. If a stage is blocked, an independent later stage may proceed when its prerequisites permit it.

### T08 — Git permissions and publication safety

**Priority P0 · Status PARTIAL (server protections active; some negative scenarios NOT_VERIFIED).** `Protect main` and `release tags` Rulesets are active. Pull Request #1 verified blocking of an invalid version, successful merge of the corrected version, and creation of annotated `v0.0.6`. [Instructions and evidence](GITHUB_SECURITY.en.md). Prepare validated GitHub Rulesets requiring CI checks before changes to a protected branch, preventing forced pushes and history deletion, protecting published tags against modification/deletion, and minimizing GitHub Actions permissions. Test ordinary PRs, administrator behavior, CI-based tagging, and concurrent updates. Changing repository settings requires separately authorized access; if permissions are unavailable, report BLOCKED rather than claiming protection.

**Acceptance:** controls are actually enforced by GitHub; bypassing mandatory checks or moving an existing tag is refused. Record settings and test evidence.

**T08.01 (CI maintenance):** pinned GitHub Actions upgraded to supported Node.js 24, with a required exact-SHA check and negative rollback tests. [Evidence and full pin table](GITHUB_SECURITY.en.md). This substage requires verified `main` CI and an annotated tag after merge. Actual administrative bypass and tag deletion tests remain NOT_VERIFIED; T08 overall is PARTIAL.

### T09 — Independent Release Core

**Priority P0 · Status PARTIAL (T09.01–T09.10 implemented; live signed ZIP acceptance T09.10 — COMPLETE).** Existing [local inspection](RELEASE_CORE.en.md), [Preflight](RELEASE_PREFLIGHT.en.md), [remote proof](RELEASE_REPORT.en.md), [completed CI](RELEASE_CI.en.md), [GitHub Release metadata](RELEASE_PUBLICATION.en.md), [asset bytes](RELEASE_ASSETS.en.md), [provenance verification](RELEASE_PROVENANCE.en.md) now include [trusted deterministic catalog source packaging](TRUSTED_BUILD.en.md). T09.08 creates reproducible ZIP content from an exact Git commit. A separate workflow can **manually, from a verified annotated tag**, generate a GitHub/Sigstore attestation and provide the artifact via GitHub Actions Artifacts. GitHub Releases are not auto-published. Live attestation and end-to-end source ZIP verification passed for v0.0.21. Application readiness and concurrent release coordination remain NOT_VERIFIED. Continue by separating `inspect`, `next`, `preflight`, `verify-build`, `tag`, `verify-tag`, `verify-remote`, and `report`. Read actual build/test commands only from target-project configuration. Check version/changelog consistency, exact release commit SHA, unexpected changes, Git permissions, and annotated tagging. Model WORKING, PREPARED, VALIDATED, TAGGED, RELEASED, and BLOCKED as distinct states. A tag is not evidence of a passing build or a published release.

**T09.09:** the new [offline ZIP verifier](CATALOG_VERIFICATION.en.md) inspects package contents without extraction. It checks internal integrity against MANIFEST.json and independently supplied version/commit values, not GitHub attestation. The signed ZIP v0.0.21 was verified separately in T09.10; overall T09 stays PARTIAL.

**T09.10 — live failure and mitigation (24 November 2026):** [Run 45347443989](https://github.com/Sashido01/TESSERA/actions/runs/45347443989) at annotated `v0.0.19` finished FAILURE: tests passed, ZIP build `PACKAGE_RUNTIME_FILE_INVALID`, signing and upload SKIPPED, artifacts 0. The tests generate `__pycache__` in runtime `scripts/`. T09.10.01 disables bytecode emission during CI/signing, adds a post-test ZIP build in main CI, retains strict allowlisting and adds negative regression checks. The correction was released in 0.0.21. See [TRUSTED_BUILD](TRUSTED_BUILD.en.md).

**T09.10 — COMPLETE (24 November 2026):** at annotated tag `v0.0.21`, commit `0c83ae9ef119a0cfc9d07c83dbae91e5d026e407`, [signing run 45348928593](https://github.com/Sashido01/TESSERA/actions/runs/45348928593) completed SUCCESS. [Attestation 71489191](https://github.com/Sashido01/TESSERA/attestations/71489191), [Actions Artifact 14898798605](https://github.com/Sashido01/TESSERA/actions/runs/45348928593/artifacts/14898798605). Independent download: 105849-byte ZIP, SHA-256 `55db489f0219739e9296fc941fa51fa58d23c3277878fe5e3a352642947eeb73`, all 17 manifest files verified. On Windows the owner independently confirmed the same SHA-256 and ran official `gh 2.105.0` `gh attestation verify`: `Verification succeeded!`, one attestation matched SLSA v1, exact repository, commit, tag, signer workflow, OIDC issuer and GitHub-hosted runner. The owner confirmation is based on supplied CLI output; ZIP and hash were verified separately. `SIGNED_ARTIFACT=PASS` **only for this v0.0.21 file**. [Issue #11](https://github.com/Sashido01/TESSERA/issues/11) acceptance criteria have been met. No GitHub Release was created; integration of Actions Artifacts into Release Core, executable application verification and concurrent releases remain unfinished.

**Acceptance:** negative tests for missing, lightweight, wrongly targeted, and reused tags; historical release verification without assuming current HEAD; reproducible recovery from failures. Any mandatory check failure blocks the release.

### T10 — Official GitHub CLI distribution

**Priority P1 · Requires T08 for safe publication · Status PARTIAL (T10.01–T10.02 COMPLETE within stated scope).** Implemented [isolated official `gh` local installation validation](GH_SKILL_INSTALL.en.md) with a SHA-256-pinned binary, discovery via `gh skill list`, source integrity checks and a no-overwrite guard. `--from-local` and `--pin` are mutually exclusive, and low-level InstallLocal lacks an overwrite check; CLI checks existing destinations, and TESSERA keeps its own guard. T10.02 will separately cover remote tag/SHA pinning, update safety and monorepo behavior. Original plan: In a sandbox, verify the available `gh skill` version against TESSERA: discovery, preview, installation, `--pin` by tag/SHA, `--dir`, updates, dry-run, and multi-skill repositories with namespaced tags. Pin the verified GitHub CLI version and account for preview API changes. T10.02 checks official gh 2.105.0 remote installation from fully qualified annotated tag v0.0.22 and exact commit SHA, Git tree, metadata, bytes, pinned update --dry-run and duplicate refusal. [Live CI 45351217500](https://github.com/Sashido01/TESSERA/actions/runs/45351217500) confirmed GH_SKILL_REMOTE_PIN_PASS. T10.03.01 implements real update --unpin in a disposable copy and guarded re-pin with local-edit refusal and rollback; [CI 45352932764](https://github.com/Sashido01/TESSERA/actions/runs/45352932764) confirmed GH_SKILL_UPDATE_PASS; T10.03.01 COMPLETE within the harness, native local-edit removal confirmed. T10.03.02 local Git fixture for independent versions, actual gh CLI multi-skill installs, collisions and scoped rollback; [CI 45354011607](https://github.com/Sashido01/TESSERA/actions/runs/45354011607) confirmed GH_SKILL_MULTI_FIXTURE_PASS; local fixture PASS, T10.03.02 PARTIAL pending separate remote acceptance. Remote namespaced pin and production T16 independent releases remain unverified. Client activation is a separate acceptance task.

**Acceptance:** reproducible installation from GitHub using official GitHub CLI, preservation of local changes on updates, and verifiable source revision. Keep the custom Python installer minimal for offline and unusual skill directories.

### T11 — Reference Agent Skills standard

**Priority P1 · Status PARTIAL (T11.01 and local T11.02).** Added the [official gh CLI dry-run](GH_SKILL_PUBLISH_DRY_RUN.en.md) at SHA-256-pinned version 2.105.0, run on an isolated skill snapshot without remote or tokens. Real CI success is required for local T11.02 COMPLETE. Remote topics, GitHub Release publication and authenticated publish behavior remain NOT_VERIFIED. **Previous status:** Added a separate upstream `skills-ref` format check pinned to an immutable source SHA with hashed dependencies in CI; a real successful run is required before T11.01 is COMPLETE. Upstream explicitly calls the reference library demonstration-only, so the custom TESSERA checks remain mandatory. Local `gh skill publish --dry-run` is included in CI; without an actual passing run it remains NOT_VERIFIED. Remote publication checks remain separate and NOT_VERIFIED. Original plan: integrate the official `skills-ref` format validation and verify repository publication readiness using `gh skill publish --dry-run`. Pin tested tool versions. Keep TESSERA's custom validator focused on project-specific invariants: independent versions, Russian originals, English translations, privacy, tags, and safety.

**Acceptance:** invalid YAML/frontmatter, incorrect names, and damaged skills fail CI; dry-run never publishes a release.

### T12 — Free NVIDIA SkillEvaluator assessment

**Priority P1 · Requires T11 · Status PARTIAL.** T12.01: [focused NVIDIA 1.2.0 evaluation](NVIDIA_TIER1.en.md), schema/quality, no LLM, hash-locked wheels, [live CI PASS](https://github.com/Sashido01/TESSERA/actions/runs/45358283596), T12.01 COMPLETE within schema/quality (75/100, 18 findings). T12.02.01: [local static checks and profiles](NVIDIA_STATIC_REVIEW.en.md), original findings review, Russian configuration with unchanged threshold, PII/license/unicode/lint and six profiles: [live CI PASS](https://github.com/Sashido01/TESSERA/actions/runs/45360122208), 75.0/78.8, 18/16 findings; T12.02.01 COMPLETE within fixture scope. T12.02.02: external scanners and CVEs. T12.02.02.01: [direct Bandit 1.9.4](BANDIT_REVIEW.en.md), COMPLETE within direct scan execution scope; [CI 45365133732](https://github.com/Sashido01/TESSERA/actions/runs/45365133732) PASS: 414+19 tests, 60 Python files, 87 findings (45 runtime, 42 tests; 2 medium, 85 low, 0 high); clean and negative fixtures PASS; direct review 1.69 s.; T12.02.02.02 [Gitleaks](GITLEAKS_REVIEW.en.md) — COMPLETE within declared scope, [CI 45367459045](https://github.com/Sashido01/TESSERA/actions/runs/45367459045) PASS: 428+19 tests, 144/144 tracked UTF-8 files, 998544 bytes, zero findings, positive/negative and redaction fixtures PASS; 65.29 s. Snapshot acceptance COMPLETE; history/path-specific rules NOT_VERIFIED; T12.02.02.02 remains PARTIAL.; [CI 45368434188](https://github.com/Sashido01/TESSERA/actions/runs/45368434188) PASS: 437+19 tests; 585/585 distinct UTF-8 blobs, 5431003 bytes, zero findings, removed-marker fixture PASS, 128.81 s. [CI 45369335974](https://github.com/Sashido01/TESSERA/actions/runs/45369335974) PASS: 443+19 tests; 598 distinct UTF-8 blobs, 5639755 bytes, zero findings; five synthetic rule fixtures PASS; 4 current YAML files and 28 historical rule/blob pairs across 37 commits, zero findings. T12.02.02.02 COMPLETE within declared scope. T12.02.02.03 [direct SkillSpector 2.13.6](SKILLSPECTOR_REVIEW.en.md) — [CI 45370414762](https://github.com/Sashido01/TESSERA/actions/runs/45370414762) PASS: 454+19 tests; 16/16 files, 100% coverage, complete_with_caveats (4 reference_missing), risk 78/100 HIGH, exit 1 (threshold 50 exceeded), 12 findings (10 MEDIUM, 2 HIGH), zero suppressions, both synthetic fixtures PASS, 13.32 s. T12.02.02.03 COMPLETE within direct static execution scope; findings and full NVIDIA security acceptance remain open.  T12.02.02.04 [dependency and license review](DEPENDENCY_REVIEW.en.md), [CI 45375135316](https://github.com/Sashido01/TESSERA/actions/runs/45375135316) PASS: 477+19 tests; 97 Python package checks, 3 packages with OSV entries; 212 distinct Go modules (gh 155, Gitleaks 66), 8 affected modules across the binaries, Gitleaks stdlib/toolchain and one source-commit entry; 211 Go licenses reported by deps.dev, one NOT_INDEXED. T12.02.02.04 COMPLETE within inventory/query execution scope; CVE remediation, code reachability and legal compatibility remain open.  T12.02.02.05 overall acceptance. T12.03: remediate confirmed findings, portable license/links, compactness and reevaluation. T12.03.01 [portable license, links and compact instructions](SKILL_PORTABILITY.en.md) — [CI 45373618225](https://github.com/Sashido01/TESSERA/actions/runs/45373618225): 486+19 tests PASS. SkillSpector 2.13.6: complete, 17/17 files, 100%, reference_missing 4→0, risk 78→36 (HIGH→MEDIUM), HIGH 2→0, MEDIUM 10, zero suppressions, both fixtures PASS, 19.40 s. NVIDIA: license allowed, RU quality 80.0 (65×0.35 + 80×0.25 + 95×0.25 + 90×0.15), Codex custom provider degraded→loads. Overall CI FAIL only at inherited Go review; release and real activation NOT_VERIFIED. T12 remains PARTIAL. Evaluate **Tier 1 only** in isolation, covering static quality and compatibility checks without mandatory LLM API usage. Measure dependencies, real runtime, output formats, exit codes, and false positives on TESSERA. Distinguish supported agent hosts; keep a separate DeepSeek Harness acceptance matrix.

**Acceptance:** reproducible Tier 1 reports including environment, findings, and measured CI costs. **Tier 2, Tier 3, and mandatory paid APIs are explicitly out of scope.**

### T13 — Thin Codex and DeepSeek Harness adapters

**Priority P1 · Requires T09 · Status NOT_STARTED.** Keep one core. Adapters only receive relevant events/context, invoke the shared verifier, and block unsupported release completion to the extent each host permits. Audit Codex project instructions/hooks and DeepSeek Harness native events/plugin compatibility. Never auto-install third-party plugins.

**Acceptance:** actual client versions demonstrate discovery, verifier calls, missing-tag failure, preservation of external changes, and truthful reporting. Unsupported behavior is marked NOT_VERIFIED or BLOCKED.

### T14 — Thin Claude Code and Hermes adapters

**Priority P1 · Requires T09 · Status NOT_STARTED.** Apply the same core interface. Use documented project instructions and Hooks in Claude Code, and audit Hermes' current trust/event mechanisms. Where no blocking hook can be verified, rely on independent Git/CI validation.

**Acceptance:** tested behavior on specific installed versions, positive and negative release cases, and no implicit trust changes.

### T15 — Concurrent multi-agent safety

**Priority P1 · Requires T09 and T13–T14 · Status NOT_STARTED.** Maintain a single version authority, serialize releases across agents, worktrees, and CI, recheck Git HEAD and refs before writing, support idempotency and bounded retries, and recover safely after partial operations. Never force-move published tags.

**Acceptance:** concurrency tests show no duplicate release versions, tag overwrites, or loss of unrelated work; missing synchronization blocks releases with a clear error.

### T16 — Independent versions for multiple skills

**Priority P2 · Requires T09–T11 · Status NOT_STARTED.** Introduce per-skill version sources, namespaced tags like `<skill>/vX.Y.Z`, installed-revision detection, backward compatibility, and migration rules, independent of the TESSERA catalog version. Do not require one common runtime for every skill.

**Acceptance:** two skills can release and update independently without tag collisions, from the same repository.

### T17 — Verifiable public releases

**Priority P2 · Requires T08–T12 and T16 for independent skill releases · Status NOT_STARTED.** Create reproducible packages and GitHub Releases only when justified. Evaluate immutable GitHub releases, SHA checks, and supply-chain provenance. Do not publish a GitHub Release merely because a working microcommit was created.

**Acceptance:** an actual published version has a traceable source Git SHA, annotated tag, CI evidence, available archive/package when applicable, and verified release visibility.

## Definition of done for every task

1. A concrete completed change with purpose and boundaries.
2. The next valid TESSERA microversion and a specific Russian-language Git commit.
3. Updated canonical Russian documentation and a complete English translation in the same commit.
4. Actual test commands/results including PASS, FAIL, SKIP and unverified platforms.
5. Annotated Git tag under TESSERA rules, with exact release-commit verification for release milestones.
6. Updated roadmap and a clear COMPLETE / PARTIAL / BLOCKED / NOT_VERIFIED report.
7. No private absolute paths, secrets, forced Git history changes, or unauthorized publication.

## Non-negotiable architecture rules

- Do not reimplement an existing GitHub CLI package manager if the native mechanism meets the requirement.
- Do not add third-party skill package managers to dependencies, fallback installation, or CI. Public docs should describe approved tools only.
- Never use NVIDIA SkillEvaluator Tier 2/3, paid modes, or mandatory paid AI APIs.
- A SKILL.md file being present is not proof of automatic activation.
- One microversioning core, not four independent implementations; keep host adapters thin.
- Unknown or unverified behavior must be marked NOT_VERIFIED rather than guessed.

**T12.03.02:** [CI evidence network restriction](RELEASE_CI_SECURITY.en.md) — [CI 45376483433](https://github.com/Sashido01/TESSERA/actions/runs/45376483433) PASS: 493+19 tests, four new regressions PASS, Bandit B310 absent in the repeat review; 110 findings (no HIGH), no rule suppression. T12.03.02 COMPLETE within implemented control and CI scope; live network execution separately NOT_VERIFIED.

**T12.03.03:** [SkillSpector 2.13.7 security upgrade](SKILLSPECTOR_UPGRADE.en.md) — [CI 45376675127](https://github.com/Sashido01/TESSERA/actions/runs/45376675127) PASS: 494+19 tests; SkillSpector 2.13.7, 17/17 files, complete, 100%, 16 MEDIUM (AE4 6, AST3 6, AST4 3, LP3 1), zero HIGH, risk 53/100 HIGH, exit 1, zero suppressions, both fixtures PASS, 11.37 s. OSV: 74 Python distributions, zero packages with entries, zero source-commit entries; cryptography 50.0.2, langgraph 1.2.20, pyasn1 0.6.5. T12.03.03 COMPLETE within upgrade and repeat OSV scope; new AST3 and threshold exceedance remain open. Release awaits sequential acceptance.


**T12.03.02 regression correction:** Before merge, a shared get_public_json regression was found: the original strict URL allowlist blocked the existing GitHub Release metadata call. Permit only the canonical /releases/tags/vMAJOR.MINOR.PATCH route and one namespace encoded as %2F; arbitrary escaping, extra paths and parameters remain forbidden. Three regressions exercise verify_github_publication through the actual shared transport (ordinary and namespaced tag), changed response URL rejection and invalid routes. Only networking is mocked, validation and response handling are real. Historical PASS missed this defect; repeat acceptance is required.


**T12.03.04 — candidate:** offline installer path hardening. Previously a standard project path could traverse an external link and `copytree` followed source links. Reject redirected components and inspect the source tree, recheck the destination, add negative tests. Network sandbox, TOCTOU and Windows junctions remain NOT_VERIFIED. Real CI acceptance is required. AST3 in 2.13.7: pinned upstream `canonical_sink.py` includes `module_from_spec` and `exec_module`; three tests load fixed local files. Static reading explains six AST3 findings, individual finding attribution remains unverified; do not replace safer fixed-path loading with less reliable imports merely to improve the score, and do not suppress rules.


**T12.03.05 — candidate:** primary SkillSpector finding coordinates based on the pinned upstream 2.13.7 `Finding.to_dict()` contract (location.file/start_line/end_line). Only known relative inventory paths and bounded integer coordinates, at most 1000 rows, explicit unresolved and omitted counts; no raw messages or source snippets. The file size line bound is a defensive upper bound, not exact line verification. Not all occurrences; not automatic triage. Three regressions; live CI required. T12.03.04: [CI 45383567669](https://github.com/Sashido01/TESSERA/actions/runs/45383567669) PASS, 497+22 tests; all three link regressions passed without SKIP, risk 53/100, 16 MEDIUM, zero suppressions. Native Windows acceptance and TOCTOU remain open.


**T12.03.07 — candidate:** AST4 review found that `release_tag.py create` used implicit HEAD and verify repeatedly read a mutable ref. Capture the SHA, add optional `--expected-head`, inspect the immutable object and direct target commit with exact tag name; observed conflicts block without automatic removal or movement. Four regressions. Full concurrent-writer locking T15 remains open. [CI 45384715814](https://github.com/Sashido01/TESSERA/actions/runs/45384715814): 500+22 tests PASS, 16/16 primary locations, zero omissions and suppressions; classification does not change original scanner output. AE4: hyphenated mixed-script tokens in six files (e.g. Git-тег), AST3: six fixed-local test loader calls, AST4: three subprocess calls (one runtime, two tests), LP3: missing scope declaration; do not add preapproved tools to improve score. Full T12 acceptance remains open.

Within the same T12.03.07 candidate: `git -C` does not isolate inherited GIT_DIR/GIT_WORK_TREE and other context variables. Reject these before executing Git; two regressions (two repositories and config/namespace/object overrides). Do not alter the owner's environment or disable local signing policies or hooks. Trusted configuration, PATH and lack of full concurrent locking remain limitations.

[CI 45387991659](https://github.com/Sashido01/TESSERA/actions/runs/45387991659): 504+28 tests PASS, but SkillSpector 81/100 CRITICAL (21 findings including HIGH E2 for full environment copying and MEDIUM EA2 for wording of the prohibition on tag changes). Candidate not accepted. Replace full copying with fixed variable allowlist, retain context rejection and local identity/signing context, add arbitrary-marker exclusion test. Clarify explicit requirement to leave the tag unchanged. Seven regressions in current candidate, CI rerun required; no presumed risk score.


**T12.03.08 — candidate:** Govulncheck v1.10.0 exact SHA, CI build with lock and isolated environment. Extract + binary, archive/config/SBOM checks and explicit fallback when symbols are absent. Five regressions. Network sandbox, live positive control, symbol completeness, scanner vulnerabilities and call reachability remain open. Not a runtime dependency. CI 45386658684: 504+22 PASS, both Python license records matched upstream.

T12.03.08 extended with Govulncheck self-audit (OSV of exact modules/toolchain/commit and before/after SHA-256); two additional tests, seven total. Live acceptance remains open.

T12.03.08 extended with two actual upstream Govulncheck controls with a local synthetic DB, Git blob ID checks and an eighth regression; public DB positive control remains open. CI not yet run.


**Unified remaining work (replacing separate issues #36/#40):** T12.03.08 PARTIAL: first run 45389727364 BLOCKED GO_ROOT_MISMATCH after successful build; retry with verified upstream tag. Python license evidence v0.0.38 PASS, tqdm redistribution conditions and Go binary license correspondence NOT_VERIFIED; GO-2026-6278 advisory range conflicts with source, do not close without analysis; classify all Go advisories, source/call reachability, public DB positive control, network sandbox and full Tier 1 acceptance remain open. T13 NOT_STARTED: [research and acceptance #40](https://github.com/Sashido01/TESSERA/issues/40), pinned Codex/Harness schemas, Stop bridge not fail-closed; shared read-only core, explicit root/SHA, bounded JSON, no transcript reads, bounded repeat Stop, independent Git/CI gate; fixture and actual client acceptance. Administrative issue consolidation does not complete technical tasks. v0.0.39 CI 45388943208 504+29 PASS, E2/EA2 absent, 19 MEDIUM, 53/100, zero suppressions; main CI 45390253290 PASS, tag verified.

T12.03.08: CI 45391798766 — 513+29 PASS, GOVULN_CONTROL_VERSION BLOCKED; new candidate uses JSON build info of historical controls and verifies GoVersion against SBOM, tenth regression. Govulncheck before long Gitleaks history checks. Re-acceptance open.

**T12.03.08 execution COMPLETE:** v0.0.40 main CI 45395642625 PASS, tag verified. [Actual review](DEPENDENCY_REVIEW.en.md): 74 fallback IDs, Gitleaks 117 OSV IDs (73 shared, 44 OSV-only), separate source CVE; reachability PARTIAL. **T12.03.09 candidate:** minimum LP3 scope documented in SKILL and INTEGRATION RU/EN, no allowed-tools added; host permissions NOT_VERIFIED, CI required. T12 PARTIAL. Close finished issues/PRs and remove merged branches; track remaining work here without false COMPLETE.

**T12.03.09:** PR CI 45397038655 PASS, 514+29, SkillSpector 19 MEDIUM, 53/100, zero suppressions; host enforcement NOT_VERIFIED. **T12.03.10 candidate:** [Gitleaks contract](GITLEAKS_REVIEW.en.md), stdout, redact=100, explicit archive depth 0, bounded side-effect checks and four regressions. CVE-2026-124039 STATIC_MITIGATION_PRESENT for the exercised scenario, not NOT_AFFECTED for the binary. CI required. T12 PARTIAL.

**T12.03.11 candidate:** [Release Core local inspection](RELEASE_CORE.en.md): fixed tag SHA, direct target/name, ref/HEAD recheck, minimal Git environment, no replace objects and timeout; eight regressions, CI required. T12.03.10 PR CI 45398390191 PASS, 518+29, all four regressions, 168 files and 738 blobs without findings, five path controls PASS. T12 PARTIAL.

**T12.03.11:** PR CI 45399800597 PASS, 526+29 tests, eight regressions PASS, SkillSpector 19 MEDIUM, 53/100, zero suppressions. **T12.03.12 candidate:** [remote inspection](RELEASE_CORE.en.md), one named remote, transport scope, fixed upload-pack, minimal environment, URL/object/commit rechecks, 10 regressions; CI required. T12 PARTIAL.

**T12.03.12:** PR CI 45401945520 PASS, 536+29, ten regressions; actual HTTPS/SSH NOT_VERIFIED. **T12.03.13 candidate:** [integrated NVIDIA Tier 1](NVIDIA_TIER1.en.md), 11 groups/13 validators, pinned scanners, fixed redaction adapter, seven regressions; Semgrep NOT_RUN, certification NOT_VERIFIED, CI required. T12 PARTIAL.

**T12.03.13:** [CI 45403712350](https://github.com/Sashido01/TESSERA/actions/runs/45403712350) PASS, 543+29, execution PASS, policy FAIL (1 HIGH, 19 MEDIUM). **T12.03.14 — candidate:** [live Gitleaks shim control](NVIDIA_TIER1.en.md) with a custom synthetic rule, clean and positive controls, stdout/stderr verification and five offline regressions; live CI required. T12 PARTIAL.

**T12.03.14:** [CI 45405865725](https://github.com/Sashido01/TESSERA/actions/runs/45405865725) PASS, 548+29 tests; live shim control PASS, policy FAIL. **T12.03.15 — candidate:** [HIGH attribution](NVIDIA_TIER1.en.md) by exact upstream category/check_name, no suppressions or threshold changes; three regressions, live CI required. T12 PARTIAL.

**T12.03.15:** [CI 45418208676](https://github.com/Sashido01/TESSERA/actions/runs/45418208676) PASS, 551+29, aggregate_risk_gate=1, other_high=0, policy FAIL. **T12.03.16 — candidate:** [Semgrep 1.182.0](NVIDIA_TIER1.en.md), upstream lock, local rules and live controls, required scanner row, OSV/licenses, five regressions; CI required. T12 PARTIAL.

**T12.03.16:** [CI 45419767513](https://github.com/Sashido01/TESSERA/actions/runs/45419767513) PASS, 585 tests, Semgrep EXECUTED; 8 OSV IDs in 3 packages and 3 UNKNOWN license metadata open. **T12.03.17 — candidate:** skill Git helper hardening, timeout, absolute executable, safe errors, six regressions, no suppressions. T12 PARTIAL; CI required.

**T12.03.17:** [CI 45421559705](https://github.com/Sashido01/TESSERA/actions/runs/45421559705) PASS, 591 tests, 53/100 and 19 MEDIUM without suppressions. **T12.03.18 — candidate:** ordinary imports in three test modules, origin and conflicting cache checks, three regressions; CI required. T12 PARTIAL.

**T12.03.18:** [CI 45423325658](https://github.com/Sashido01/TESSERA/actions/runs/45423325658) PASS, 594 tests, AST3 6→0, SkillSpector 36/100, policy PASS, no suppressions. **T12.03.19 — candidate:** 22 editorial substitutions in six skill files, mixed tokens 22→0 by independent count; CI required. T12 PARTIAL, Semgrep CVEs and isolation open.

**T12.03.19:** [CI 45425640926](https://github.com/Sashido01/TESSERA/actions/runs/45425640926) PASS, 594 tests, AE4=0, SkillSpector 22/100, 7 MEDIUM, policy PASS. **T12.03.20 — candidate:** required Linux namespace preflight, five offline regressions; live local synthetic PASS, GitHub CI required; scanner/file isolation and aggregate resources NOT_VERIFIED. T12 PARTIAL.

**T12.03.20:** unshare BLOCKED on GitHub Ubuntu 26.04 (CI 45427736161); explicit required Docker synthetic preflight selected without changing AppArmor, with cgroup and access boundary checks. CI required; not scanner isolation. T12 PARTIAL.

**T12.03.20:** CI 45428224320 PASS, 604 tests, Docker synthetic PASS. **T12.03.21 — candidate:** Gitleaks tracked UTF-8 stdin in Docker, host comparison, TSG1, nine regressions; CI required, history/path not isolated. T12 PARTIAL.

**T12.03.21:** CI 45432568241 PASS, 613 tests, 177 files and 1,404,601 bytes, Docker Gitleaks parity PASS. **T12.03.22 — candidate:** batched isolation of reachable historical blobs, OID, snapshot, host parity, seven regressions; CI required. T12 PARTIAL.

**T12.03.22:** CI 45434506035 PASS, 620 tests, 878 blobs / 10,952,864 bytes, 4 batches, 316.56s. **T12.03.23 — candidate:** TSP1 path rules, 10 categories, host parity, nine regressions. CI required. T12 PARTIAL.

**T12.03.23:** CI 45439256012 PASS, 629 tests, three standalone Docker Gitleaks scopes PASS. **T12.03.24 — candidate:** three exact Semgrep upstream LICENSE pins, two offline tests, wheel/RECORD awaits CI; OSV and legal compliance remain open. T12 PARTIAL.

**T12.03.24:** CI 45442813029 PASS, 631 tests, 3/3 upstream license + RECORD MATCH. **T12.03.25 — candidate:** two TSG1 workers under unchanged resource profile, three regressions, host parity retained. CI required; T12 PARTIAL.

**T12.03.25:** CI 45448926511 PASS, 634 tests, history 243.73s/911 blobs. **T12.03.26 — candidate:** integrated Gitleaks Docker, exact NVIDIA contract, staged snapshot, bounded output, cleanup, eight regressions; CI required. T12 PARTIAL.

**T12.03.26:** CI 45453412802 PASS, 642 tests, integrated Gitleaks Docker controls PASS. **T12.03.27 — candidate:** standalone Bandit Docker, seven wheels, exact host parity, four regressions. CI required; T12 PARTIAL.

**T12.03.27:** CI 45460535618 PASS, 649 tests, Bandit Docker host parity PASS. **T12.03.28 — candidate:** NVIDIA Bandit Docker, exact contract and coverage, receipt, six regressions; CI required. T12 PARTIAL.

**T12.03.28:** CI 45465436002 PASS, 655 tests, integrated Bandit Docker controls PASS. **T12.03.29 — candidate:** SHA-256 for two configurations instead of SHA-1, no suppressions, two regressions; CI required. T12 PARTIAL.

**T12.03.29:** CI 45468107315 PASS, 657 tests, Bandit HIGH 2→0. **T12.03.30 — candidate:** safe Bandit coordinates and exact parity, six regressions; CI required. T12 PARTIAL.

**T12.03.30:** CI 45470763020 PASS, 663 tests, all 173 coordinates. **T12.03.31 — candidate:** standalone SkillSpector Docker, 74 packages, exact parity, eight regressions; CI required. T12 PARTIAL.

**T12.03.31:** CI 45475253034 PASS, 671 tests, standalone SkillSpector Docker exact parity. **T12.03.32 — candidate:** NVIDIA SkillSpector Docker, exact contract and receipts, five regressions; CI required. T12 PARTIAL.

## T19 — Speed up required checks

T19.02 candidate: [parallel CI checks](CI_PERFORMANCE.en.md), required validate retained. Assess speed from actual wall-clock, queue and runner-minutes; no existing required checks removed. Full CI and measured result still required. Accept only after v0.0.67 and its exact tag are verified.

## T18–T20 — continuous work, speed and the third skill

Owner decision 25 November 2026: develop catalog and all approved skills in parallel, continue independent tasks while waiting, prioritize GitHub speed, native tools and simplicity; all skills support local mode. Repository Workflow approved. See [PARALLEL_WORKFLOW](PARALLEL_WORKFLOW.en.md), [TECHNICAL_DEBT](TECHNICAL_DEBT.en.md), [RESEARCH_REGISTER](RESEARCH_REGISTER.en.md).

| Stage | Goal and acceptance | Candidate status |
|---|---|---|
| T18.01 | Independent tasks, one integration queue; exact SHA, late VERSION, worktree preservation | PARTIAL — local probes; GitHub in progress |
| T18.02 | Debt register, review tasks/PR/branches/CI/tags each cycle; evidence-based closure | PARTIAL — protocol and snapshot |
| T18.03 | Native Issue dependencies and GitHub profile without duplication; local register | NOT_VERIFIED |
| T19.01 | GitHub Actions timing baseline, critical path and queues | PARTIAL — two measured runs |
| T19.02 | Parallel history and other check jobs; fail-closed validate, preserve full acceptance | PARTIAL — PR #68 PASS and merged; main CI pending |
| T19.03 | Measure p50/p95, first feedback, runner-minutes, cache/affected checks only with evidenced equivalence | NOT_STARTED |
| T20.01 | Repository Workflow 0.0.1, bilingual method, local planner and tests | PARTIAL — candidate sources |
| T20.02 | Bootstrap, actual Codex/Harness, Windows/Linux, GitHub/LOCAL, evals and independent release | NOT_VERIFIED |

T06: pin/update checked in bounded T10 scenarios; actual hosts and independent tags remain open. T07: source ZIP and independent verification implemented in T09; live attestation applies to v0.0.21, later packages and platforms are not automatically verified. T12 PARTIAL. T16: independent VERSION/changelogs and CI v0.0.66 confirmed; namespaced tags, protection and independent release open. Project Audit PR #67 being corrected; not accepted until full CI. Do not preassign future microversions.

**Reconciliation 25 November 2026:** v0.0.67 main CI 45579382735 PASS and exact annotated tag; PR #68 CI 45580026868 PASS, merged as a8d54510b06d47da2b0d872cb067caee99ad598d. v0.0.68 main CI and tag still required. Project Audit 0.0.1 already in main; actual agent and separate tag NOT_VERIFIED. Repository Workflow 0.0.1 is a candidate, not an independent release.

**T16/T19/T20 reconciliation:** main v0.0.68 CI and exact tag PASS; PR #69 PASS and merged. Repository Workflow accepted in catalog, main v0.0.69 CI pending. v0.0.70 candidate: independent skill preflight/report, bounded test process (13/13 locally). T16 PARTIAL: namespaced tag protection WAIT_OWNER, actual independent tagging and publication not performed. T19.02 accepted and verified; T19.03 open. TD12 PARTIAL, see [register](TECHNICAL_DEBT.en.md). Project Audit inventory 0.0.2 is next candidate.

**Reconciliation:** T20.01 Repository Workflow source accepted, main v0.0.69 CI and exact tag PASS. T16/TD12 PR #70 PASS and merged; independent tags and runtime open. Project Audit 0.0.2 / v0.0.71 candidate [Inventory Engine](../skills/project-audit/references/INVENTORY.en.md), separate check plan, Git Inspector separate level II candidate (13/13 Linux); full CI required. TD04: main v0.0.69 625 s, catalog longer than history; investigate actual critical path.

**v0.0.72 reconciliation:** v0.0.70 main CI and exact tag PASS; PR #71 accepted, Project Audit 0.0.2 in catalog (v0.0.71 main CI and tag still required). T19.03 — three required groups candidate retaining validate; see [CI_PERFORMANCE](CI_PERFORMANCE.en.md). T16/TD03 WAIT_OWNER; local plans and tag inspection accepted, independent tagging not performed. Next Project Audit component — Git Inspector. Actual speed and full candidate CI remain open.

**v0.0.73 reconciliation:** TD03 configuration COMPLETE after owner change. T16 independent publication candidate in existing tag job (13/13 local tests), actual refs and CI pending. T19.03 PR #72 PASS and merged, 579 s vs 589 s on different snapshots, main CI and repeated measurement required. Project Audit 0.0.2 / v0.0.71 verified, Git Inspector 0.0.3 separately prepared; next integration slot after T16.

**Recovery reconciliation:** v0.0.73 required checks and catalog tag PASS; independent tags FAIL twice, T16/TD02 BLOCKED. Narrow v0.0.74 candidate, 19/19 local, full CI and actual refs required; do not weaken TD03. Git Inspector PR #74 (CI PASS) deferred with branch retained, assign next number after recovery. Evidence Core 15/15 Linux separately prepared. Repository Workflow 0.0.2 17/17 Linux next independent slot. Native Windows and agent acceptance open.

**Actual Codex acceptance:** 3/3 installations OWNER_REPORTED_PASS, Microversion Release 38/38 and Repository Workflow 13/13 Windows; Project Audit Windows FAIL #80, correction candidate 91765d47e978aa9f968b1589746131d165dab669, local Linux 21/21; native retest, agent discovery, invocation, auto-use and mandatory gate NOT_VERIFIED. [Evidence](AGENT_PILOT.en.md). TD06/T05 PARTIAL, TD16 OPEN; Harness pilot remains open.

25 November 2026: TD17 #81 remains OPEN (safe Git context refusal, actual invocation); TD18 #82 OPEN (full Windows catalog suite: 710 / 9 errors / 1 skip on v0.0.75); TD06/TD15 PARTIAL (3/3 install/discovery/explicit use owner-reported; automatic behavior 2 pass / 1 partial; enforcement incomplete); candidate 5a03fc7a7dd402287193108ddbb1f1ef168bb2d1 CI 45620060381 native skill suites 94 pass / 1 skip, Linux catalog 712 tests run; Project Audit E2 HIGH remains policy FAIL, PE3 absent; correction + scope guard + full Windows suite candidate 054154dc6fcc899e1a611227cf881f2fd01f47c0 pending CI. [Evidence](AGENT_PILOT.en.md). No new tag or merge while independent publication remains blocked.
