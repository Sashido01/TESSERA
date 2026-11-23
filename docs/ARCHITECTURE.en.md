# TESSERA architecture

[Русский — основной язык](ARCHITECTURE.md) | **English — translation**

## Core principle

One public repository, many standalone skills. Each skill lives in `skills/<slug>/` with `SKILL.md` as its entry point, plus its own instructions, examples, and optional scripts for reading or modifying data.

## System layers

1. **Catalog** — README, contribution rules, security information, and shared tests.
2. **Skills** — portable instructions and supporting files without a mandatory shared runtime.
3. **Integrations** — future adapters for Harness, Codex, and other systems, verified independently.
4. **Checks** — local commands and GitHub Actions; they check structure and tests, not the quality of a model's answers.

## Cross-platform skills

Each skill uses the common Agent Skills format without requiring one particular agent runtime. Codex, DeepSeek Harness, Claude Code, and Hermes can read standard `SKILL.md` bundles but have different discovery, trust, and lifecycle-hook rules. The first skill now has integration instructions and a safe installer. Actual client installations remain `NOT_VERIFIED` until tested. Mandatory release tagging is independently checked by a deterministic Git helper.

## Approved architectural direction

Keep the existing `skills/<slug>/` layout. The [roadmap](ROADMAP.en.md) defines **one independent Release Core** (versioning, real checks, Git/tags, evidence) with **thin host adapters** for Codex, DeepSeek Harness, Claude Code, and Hermes. Create new directories only when implementing real functionality, not as empty placeholders.

The **planned** preferred distribution channel is official GitHub CLI `gh skill`, after practical testing and version pinning. The current Python installer remains a minimal offline/custom-profile fallback.

The official `skills-ref` validator is planned for standard Agent Skills format checks, while TESSERA's own tools retain its microversioning and release invariants. NVIDIA SkillEvaluator is permitted **at Tier 1 only**, after isolated evaluation without paid API requirements and with measured resource usage. Tier 2/3 and mandatory paid AI APIs are excluded. See [DEPENDENCIES.en.md](DEPENDENCIES.en.md). These are target architecture decisions, not claims of finished integration.

## Initial independent Release Core

T09.01 introduces the [read-only Git evidence inspector](RELEASE_CORE.en.md). It reads the version and validates an annotated tag against an exact, possibly historical, commit. It does **not** run builds or execute `git push`, and it does not claim RELEASED status. Its JSON output is agent-independent and intended for future adapters.

## Completed CI verification (T09.04)

[Release CI](RELEASE_CI.en.md) documents independent GitHub Actions API verification of a fully completed workflow run, with no automatic network access. The pure stage reducer considers only requested and actually verified evidence and **never** claims RELEASED. Self-verification of a still-running workflow is prohibited to avoid circular dependencies.

## Source publication and T09.05 certificate

[RELEASE_PUBLICATION](RELEASE_PUBLICATION.en.md) documents separate verification of published GitHub Release metadata and a deterministic unsigned certificate. A Git tag plus passing CI do not establish a GitHub Release, and a GitHub Release does not prove downloaded artifact bytes. API calls remain explicit; Git access is read-only. The module never publishes a release by itself.

## Independent asset byte verification T09.06

[RELEASE_ASSETS](RELEASE_ASSETS.en.md) documents streaming real public GitHub Release assets and checking byte size/SHA-256 against REST API metadata. Download requires explicit `--verify-assets` and `--verify-publication`. Redirects are limited to known GitHub CDN hosts; no local file writes or application installation occur. Matching bytes does not establish build provenance or application readiness.

## Cryptographic artifact provenance — T09.07

[RELEASE_PROVENANCE](RELEASE_PROVENANCE.en.md) uses the **official GitHub CLI** to verify a Sigstore/SLSA attestation for an exact local artifact tied to the expected source SHA, release tag and trusted signing workflow. Network verification requires explicit `--verify-provenance`. The Release Core JSON certificate itself remains unsigned and does not establish software safety or functionality.

## Deterministic catalog package and trusted build — T09.08

[TRUSTED_BUILD](TRUSTED_BUILD.en.md) defines a genuine catalog source ZIP with a SHA-256 manifest and exact source commit. Its GitHub Actions signing workflow is dispatched manually **after** an annotated tag exists and never runs on PR code. TESSERA distributes Agent Skills source, not an executable application. The new [branch policy](BRANCHING.en.md) does not require a new branch for intermediate commits.

## Installation

Identify the actual active skills directory in each agent system. Copy the complete skill directory. Use symlinks or junctions only after confirming that the agent supports them and that the path is safe. A file existing on disk does not prove the skill is automatically activated.

## Publication

A Git commit, an annotated tag, a GitHub Release, and a build artifact are different states; verify each separately.

## Portability

Working directories are defined in a user's environment. Do not hardcode personal absolute paths into public instructions, configuration, or executable scripts.
