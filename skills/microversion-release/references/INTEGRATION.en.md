# Integrating Microversion Release with multi-agent systems

[Русский — оригинал](INTEGRATION.md) | **English — translation**

## Portable foundation

The `SKILL.md + scripts/ + references/` layout follows the Agent Skills convention. The skill does not inherently depend on Codex, DeepSeek Harness, Claude Code, Hermes, MCP, a separate server, or network credentials. Helper scripts require Python 3; release tagging requires Git and appropriate permissions.

Different environments use different skill directories, discovery rules, trust prompts, and enforcement mechanisms. Having a `SKILL.md` file does not itself guarantee execution after each change.

## Safe installation

From the root of a cloned TESSERA repository (replace `<project-root>` with the destination project directory):

```bash
python skills/microversion-release/scripts/install.py --platform codex --project-root <project-root>
python skills/microversion-release/scripts/install.py --platform codex --project-root <project-root> --apply
```

Without `--apply`, the installer **only previews** the destination. With `--apply`, it copies the complete skill directory and refuses to overwrite an existing installation.

Available choices: `--platform codex|harness|claude|hermes|shared`. The `shared` option installs into `<project-root>/.agents/skills/`, which Codex and Hermes can both discover. For custom profiles and other platforms, use `--platform generic --target-root <skills-dir> --apply`. Verify the actual active user-level skills directory before using that mode.

## Planned native distribution

The official **GitHub CLI 2.105.0** is now covered in CI for actual `gh skill publish --dry-run` and a separate isolated `gh skill install --from-local --dir`; see [GH_SKILL_INSTALL](../../../docs/GH_SKILL_INSTALL.en.md). Real installation from the public GitHub repository pinned to a tag or commit SHA is **NOT_VERIFIED**, so the CLI is not yet the fully accepted remote distribution method. Direct local `gh skill install` may overwrite existing files even without `--force`; use the minimal Python installer with explicit DRY-RUN and a no-overwrite guard for existing projects. It will remain as a minimal offline and custom-profile fallback.

TESSERA does not require a third-party skill package manager. See the [TESSERA dependency policy](../../../docs/DEPENDENCIES.en.md). Planned `skills-ref` and NVIDIA SkillEvaluator Tier 1 checks are development-quality tools, not required skill runtime dependencies. Paid Tier 2/3 are excluded.

## Codex (OpenAI)

Project: `<project-root>/.agents/skills/microversion-release/SKILL.md`. User: `<user-home>/.agents/skills/microversion-release/SKILL.md`. Codex can discover skills by description or through explicit selection. To require the workflow, use project-level `AGENTS.md` instructions and independent Git/CI checks. Skill discovery is not enforcement.

Official docs: https://developers.openai.com/codex/skills

## DeepSeek Harness

Project: `<project-root>/.dsh/skills/microversion-release/`. User: `<DSH_HOME>/skills/microversion-release/`, resolved from the actual runtime. Ensure that the `dsh-skill`, `dsh-skill-filesystem`, and `dsh-tool-skill` components are enabled. Verify that the skill appears in the session catalog. Strict completion checks require a separate tested Harness lifecycle hook.

Official docs: https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.md

## Claude Code (Anthropic)

Project: `<project-root>/.claude/skills/microversion-release/SKILL.md`. User: `<user-home>/.claude/skills/microversion-release/SKILL.md`. Claude may select the skill based on its description. For mandatory release checks, combine it with project `CLAUDE.md` instructions and independent Git/CI validation. No Claude-only YAML field is required in the canonical skill.

Official docs: https://code.claude.com/docs/en/skills

## Hermes Agent (Nous Research)

Project: `<project-root>/.hermes/skills/microversion-release/` or the shared `<project-root>/.agents/skills/microversion-release/`. Default user profile: `<user-home>/.hermes/skills/`; confirm alternate profiles independently. Hermes **does not trust skills from arbitrary new repositories automatically**; review them first and then use `hermes skills trust` within the project when appropriate.

The TESSERA GitHub catalog also matches Hermes tap distribution:

```bash
hermes skills tap add Sashido01/TESSERA
hermes skills search microversion-release
hermes skills install Sashido01/TESSERA/skills/microversion-release
```

These are documented Hermes CLI patterns, **not** proof of installation in a specific Desktop/CLI environment. Review the security scanner's results and the active profile.

Official docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills

## Other agents and orchestrators

Agents supporting the Agent Skills standard can use `--platform generic --target-root <skills-dir>`. Other environments need their own adapter to expose `SKILL.md` to the model and invoke the deterministic release checks.

For multi-agent repositories: maintain one canonical version source, serialize release operations, recheck HEAD and tags, never overwrite existing tags, and validate in CI. Neither an LLM nor Agent Skills provides distributed locking by itself.

## Integration acceptance

1. Verify the client version and active skills directory.
2. Install the entire skill and confirm that the agent can see it.
3. Check `0.0.99 → 0.0.100` for unfinished work.
4. Use an **isolated test Git repository** for a `0.1.0` release: real checks, a substantive commit, an annotated tag, and `release_tag.py verify`.
5. Confirm that missing or invalid tags produce `BLOCKED / RELEASE_NOT_TAGGED`.
6. Test automatic invocation separately when required.
7. Do not generalize a single successful CI test to every host platform.

## Official references

- https://agentskills.io/specification
- https://developers.openai.com/codex/skills
- https://code.claude.com/docs/en/skills
- https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.md
- https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
