# TESSERA roadmap

[Русский — оригинал](ROADMAP.md) | **English — translation**

**Purpose:** incremental development of a shared public Agent Skills catalog with one verifiable microversioning core and thin adapters for different agent systems.

**TESSERA's own versioning:** mandatory microversions under the [version policy](VERSIONING.en.md). Roadmap stages do not reserve version numbers or justify dummy commits. The `.99` milestone permits a release only after completion and verification; unfinished work continues as `.100+`.

**Owner-approved constraints (23 November 2026):** exclude Vercel Skills CLI entirely; never use NVIDIA SkillEvaluator Tier 2 or Tier 3; never require paid AI APIs. Official GitHub CLI is the preferred distribution mechanism once validated; a minimal Python installer remains an offline fallback. Russian is canonical; complete English translations must be updated in the same change. See [dependencies and boundaries](DEPENDENCIES.en.md).

## Status definitions

- `COMPLETE`: the actual files and required test results exist, with limitations reported.
- `PARTIAL`: some work exists but mandatory acceptance criteria are unmet.
- `NOT_VERIFIED`: code or instructions exist, but execution in the target environment has not been verified.
- `NOT_STARTED`: implementation has not begun; this roadmap is not evidence of completion.
- `BLOCKED`: a specific blocker and its cause have been recorded.

The current statuses below are based on GitHub source and a successful Linux GitHub Actions run for TESSERA `v0.0.2`. They do **not** prove execution in installed agent clients or local Windows environments.

## Foundation stages T00–T07

| Stage | Goal | Verified status |
| --- | --- | --- |
| T00 | Public catalog, documentation, MIT license, contribution rules | COMPLETE — published |
| T01 | Microversion Release, version calculator, annotated tagging | COMPLETE for code and unit tests; host integration unverified |
| T02 | Structural checks, unit tests, GitHub Actions | COMPLETE for present CI; branch protection still missing |
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

**Priority P0 · Status NOT_STARTED.** Prepare validated GitHub Rulesets requiring CI checks before changes to a protected branch, preventing forced pushes and history deletion, protecting published tags against modification/deletion, and minimizing GitHub Actions permissions. Test ordinary PRs, administrator behavior, CI-based tagging, and concurrent updates. Changing repository settings requires separately authorized access; if permissions are unavailable, report BLOCKED rather than claiming protection.

**Acceptance:** controls are actually enforced by GitHub; bypassing mandatory checks or moving an existing tag is refused. Record settings and test evidence.

### T09 — Independent Release Core

**Priority P0 · Status NOT_STARTED.** Separate `inspect`, `next`, `preflight`, `verify-build`, `tag`, `verify-tag`, `verify-remote`, and `report`. Read actual build/test commands only from target-project configuration. Check version/changelog consistency, exact release commit SHA, unexpected changes, Git permissions, and annotated tagging. Model WORKING, PREPARED, VALIDATED, TAGGED, RELEASED, and BLOCKED as distinct states. A tag is not evidence of a passing build or a published release.

**Acceptance:** negative tests for missing, lightweight, wrongly targeted, and reused tags; historical release verification without assuming current HEAD; reproducible recovery from failures. Any mandatory check failure blocks the release.

### T10 — Official GitHub CLI distribution

**Priority P1 · Requires T08 for safe publication · Status NOT_STARTED.** In a sandbox, verify the available `gh skill` version against TESSERA: discovery, preview, installation, `--pin` by tag/SHA, `--dir`, updates, dry-run, and multi-skill repositories with namespaced tags. Pin the verified GitHub CLI version and account for preview API changes.

**Acceptance:** reproducible installation from GitHub without Vercel CLI, preservation of local changes on updates, and verifiable source revision. Keep the custom Python installer minimal for offline and unusual skill directories.

### T11 — Reference Agent Skills standard

**Priority P1 · Status NOT_STARTED.** Integrate the official `skills-ref` format validation and verify repository publication readiness using `gh skill publish --dry-run`. Pin tested tool versions. Keep TESSERA's custom validator focused on project-specific invariants: independent versions, Russian originals, English translations, privacy, tags, and safety.

**Acceptance:** invalid YAML/frontmatter, incorrect names, and damaged skills fail CI; dry-run never publishes a release.

### T12 — Free NVIDIA SkillEvaluator assessment

**Priority P1 · Requires T11 · Status NOT_STARTED.** Evaluate **Tier 1 only** in isolation, covering static quality and compatibility checks without mandatory LLM API usage. Measure dependencies, real runtime, output formats, exit codes, and false positives on TESSERA. Distinguish supported agent hosts; keep a separate DeepSeek Harness acceptance matrix.

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
- Do not include Vercel Skills CLI as a dependency, fallback installer, supported stack component, or CI tool.
- Never use NVIDIA SkillEvaluator Tier 2/3, paid modes, or mandatory paid AI APIs.
- A SKILL.md file being present is not proof of automatic activation.
- One microversioning core, not four independent implementations; keep host adapters thin.
- Unknown or unverified behavior must be marked NOT_VERIFIED rather than guessed.
