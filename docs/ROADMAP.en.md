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

**T12.03.02:** [CI evidence network restriction](RELEASE_CI_SECURITY.en.md) — implementation prepared, actual CI pending. Other Bandit findings open.

**T12.03.03:** [SkillSpector 2.13.7 security upgrade](SKILLSPECTOR_UPGRADE.en.md) — candidate; live acceptance pending. Historical 2.13.6 results retained.
