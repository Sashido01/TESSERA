# Integrating Microversion Release with multi-agent systems

[Русский — оригинал](INTEGRATION.md) | **English — translation**

## Portable foundation

The `SKILL.md + scripts/ + references/` layout follows the Agent Skills convention. The skill does not inherently depend on Codex, DeepSeek Harness, Claude Code, Hermes, MCP, a separate server, or network credentials. Helper scripts require Python 3; release tagging requires Git and appropriate permissions.

Different environments use different skill directories, discovery rules, trust prompts, and enforcement mechanisms. Having a `SKILL.md` file does not itself guarantee execution after each change.

## Minimum tool scope (LP3)

| Operation | Required access and boundary |
| --- | --- |
| Version calculation | Python, no project writes |
| Release tag verification | Read selected repository, trusted Git |
| Project checks | Only approved project commands |
| Installation | Explicit --apply, write only a new skill directory |
| Commit and tag creation | Authorized writes to selected repository, leave existing tag unchanged |
| Publication | Separate authorization, trusted remote, minimum token scope |

The experimental allowed-tools field in the [Agent Skills specification](https://agentskills.io/specification) describes preapproved tools, not a permission ceiling. It is not added to clear LP3. This table documents intent and does not create an OS sandbox. Actual Codex, Harness and other host permission enforcement requires separate verification. A hook does not replace independent Git/CI acceptance; hook failure is not proof of a successful check.

## Safe installation

From the root of a cloned TESSERA repository (replace `<project-root>` with the destination project directory):

```bash
python skills/microversion-release/scripts/install.py --platform codex --project-root <project-root>
python skills/microversion-release/scripts/install.py --platform codex --project-root <project-root> --apply
```

Without `--apply`, the installer **only previews** the destination. With `--apply`, it copies the complete skill directory and refuses to overwrite an existing installation.

Available choices: `--platform codex|harness|claude|hermes|shared`. The `shared` option installs into `<project-root>/.agents/skills/`, which Codex and Hermes can both discover. For custom profiles and other platforms, use `--platform generic --target-root <skills-dir> --apply`. Verify the actual active user-level skills directory before using that mode.

## Native distribution

The official **GitHub CLI 2.105.0** has passed isolated CI checks for `gh skill publish --dry-run`, local installation, public remote installation pinned to a full tag/commit SHA, and staged re-pin/rollback. This is not evidence of installation or activation in a real agent profile. Local installation may replace files in an existing target; inspect the destination first and use an isolated staging directory for updates. The minimal Python installer remains the offline fallback and refuses an existing destination. Catalog-wide details are available in the public TESSERA repository: [GH_SKILL_INSTALL](https://github.com/Sashido01/TESSERA/blob/v0.0.30/docs/GH_SKILL_INSTALL.en.md).

TESSERA does not require a third-party skill manager. `skills-ref`, NVIDIA SkillEvaluator Tier 1 and static scanners are development-quality tools rather than runtime dependencies. No mandatory paid AI API or Tier 2/3 evaluation. The skill includes its own [MIT license](../LICENSE.txt); the [catalog dependency policy](https://github.com/Sashido01/TESSERA/blob/v0.0.30/docs/DEPENDENCIES.en.md) is optional reading, not a local installation prerequisite.

## Codex (OpenAI)

Project: `<project-root>/.agents/skills/microversion-release/SKILL.md`. User: `<user-home>/.agents/skills/microversion-release/SKILL.md`. Codex can discover skills by description or through explicit selection. To require the workflow, use project-level `AGENTS.md` instructions and independent Git/CI checks. Skill discovery is not enforcement.

Official docs: https://developers.openai.com/codex/skills

### TD17 diagnostics (#81)

In the original Codex session, **without changing its environment**, run:

```bash
python -B scripts/release_tag.py context
```

Run from the installed skill directory or specify the path to a verified copy. The command does not execute Git, needs no project root, and writes nothing. Record only the JSON, exit code, client version and OS. GIT_CONTEXT_UNSAFE (exit 1) means blocked; NO_BLOCKING_CONTEXT_OBSERVED (exit 0) means no known blocking names were observed, not proof of safety. Do not remove variables or bypass policy when blocked. Arrange a separate verification run in a trusted environment outside the agent with the owner while preserving applicable restrictions; that run does not prove Codex compatibility. The exact trusted-context adapter contract and real client acceptance remain open.

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

T13 enforcement candidate: [Completion Gate and Guarded Run](ENFORCEMENT.en.md). External control mandatory, Stop provides additional feedback; actual Codex/Harness NOT_VERIFIED. No production enablement before acceptance.

Native fixture context guard candidate: mutating Git unit-test setup refuses inherited Git_* names except GIT_PAGER before creating a temporary directory or executing Git. Production authorization and context policy unchanged. No environment stripping to obtain PASS. Run positive real-Git fixture tests from an ordinary trusted terminal with a naturally acceptable context; on FIXTURE_GIT_CONTEXT_UNSAFE report BLOCKED, never treat refusal as client acceptance. A synthetic Linux two-repository reproduction confirmed Git -C alone does not prevent GIT_DIR redirection of a local config write; a missing indexed config tuple returned exit 128. This demonstrates the fixture risk, not the cause of every owner-reported error. New regression test requires CI.