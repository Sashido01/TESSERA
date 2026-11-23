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

The **planned** preferred distribution channel is official GitHub CLI `gh skill`, after practical testing and version pinning. The current Python installer remains a minimal offline/custom-profile fallback. **Vercel Skills CLI is entirely excluded.**

The official `skills-ref` validator is planned for standard Agent Skills format checks, while TESSERA's own tools retain its microversioning and release invariants. NVIDIA SkillEvaluator is permitted **at Tier 1 only**, after isolated evaluation without paid API requirements and with measured resource usage. Tier 2/3 and mandatory paid AI APIs are excluded. See [DEPENDENCIES.en.md](DEPENDENCIES.en.md). These are target architecture decisions, not claims of finished integration.

## Installation

Identify the actual active skills directory in each agent system. Copy the complete skill directory. Use symlinks or junctions only after confirming that the agent supports them and that the path is safe. A file existing on disk does not prove the skill is automatically activated.

## Publication

A Git commit, an annotated tag, a GitHub Release, and a build artifact are different states; verify each separately.

## Portability

Working directories are defined in a user's environment. Do not hardcode personal absolute paths into public instructions, configuration, or executable scripts.
