# Microversion Release

[Русский — основной язык](README.md) | **English — translation**

A portable Agent Skill for incremental versioning, release verification, and clear Russian-language Git history. This is the first skill in [TESSERA](../../README.en.md).

## Rules

- A new project starts at `0.0.0`.
- Every independently verified change increments PATCH by one.
- `.99` is a planned release milestone, not a cap on work commits.
- When work is finished and checks have passed: `0.0.99 → 0.1.0`, `0.1.99 → 0.2.0`, `0.99.99 → 1.0.0`.
- If work is unfinished at `.99`: `0.0.99 → 0.0.100 → 0.0.101 → …`. After the first verified three-digit PATCH at which the task is really complete, prepare the next `.0` release.
- Never create fictitious commits or unverified releases.
- Commits, annotated tags, CHANGELOG entries, and release descriptions use clear, natural **Russian**.

## Installation

1. Copy the **entire** `microversion-release` directory, including `SKILL.md`, `references/`, and `scripts/`.
2. For DeepSeek Harness, use a verified active `<DSH_HOME>/skills/microversion-release/` directory or the project directory `<project>/.dsh/skills/microversion-release/`. Do not guess the actual DSH_HOME value.
3. Verify skill discovery in the active profile. Manual invocation as `/microversion-release` may be available only when the Agent Skills loader is enabled.
4. For Codex and other agents, verify their current skill locations separately. Installation and automatic activation in those environments have not been tested.
5. To enforce checks for every commit, add project-level rules to AGENTS.md or a separate event-based integration. A SKILL.md file alone cannot enforce anything.

## Verification

From the skill directory:

```bash
python scripts/next_version.py 0.0.99 --mode work
python scripts/next_version.py 0.0.100 --mode release
python -m unittest discover -s tests -v
```

Expected calculated values: `0.0.100` and `0.1.0`. The calculator only reads its input and **does not modify Git or files**. It does not validate that the task is ready.

## Existing projects

If a project already has tags and a different versioning policy, never rewrite its history. Adopt the new policy for future changes only after checking the existing configuration.

## Limitations

This skill provides instructions and a version-number calculator, **not** an installed plugin hook, a complete Git transaction manager, or an automated build pipeline. The actual target Harness environment still needs verification.

## Skill instructions

The canonical agent entry point is [SKILL.md](SKILL.md) in Russian. For reference, a [full English translation](references/SKILL.en.md) is provided; agent loaders should continue to use the canonical file.
