# TESSERA architecture

[Русский — основной язык](ARCHITECTURE.md) | **English — translation**

## Core principle

One public repository, many standalone skills. Each skill lives in `skills/<slug>/` with `SKILL.md` as its entry point, plus its own instructions, examples, and optional scripts for reading or modifying data.

## System layers

1. **Catalog** — README, contribution rules, security information, and shared tests.
2. **Skills** — portable instructions and supporting files without a mandatory shared runtime.
3. **Integrations** — future adapters for Harness, Codex, and other systems, verified independently.
4. **Checks** — local commands and GitHub Actions; they check structure and tests, not the quality of a model's answers.

## Installation

Identify the actual active skills directory in each agent system. Copy the complete skill directory. Use symlinks or junctions only after confirming that the agent supports them and that the path is safe. A file existing on disk does not prove the skill is automatically activated.

## Publication

A Git commit, an annotated tag, a GitHub Release, and a build artifact are different states; verify each separately.

## Portability

Working directories are defined in a user's environment. Do not hardcode personal absolute paths into public instructions, configuration, or executable scripts.
