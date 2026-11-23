# T11.01 — Agent Skills reference validator

[Русский — оригинал](AGENT_SKILLS_STANDARD.md) | **English — translation** ([this file](AGENT_SKILLS_STANDARD.en.md))

## Purpose and boundaries

TESSERA follows the published [Agent Skills specification](https://agentskills.io/specification). In addition to the custom `tools/validate_skills.py` checks, every pull request and push to `main` runs the upstream `skills-ref validate` from [agentskills/agentskills](https://github.com/agentskills/agentskills).

**Important:** upstream explicitly describes `skills-ref` as a demonstration library, **not for production use**. TESSERA's mandatory privacy, versions, tags, bilingual documentation, and integrity checks are retained. A passing format check does not demonstrate activation in real Codex, Harness, Claude Code, or Hermes environments.

## Immutable inputs

- Source: `agentskills/agentskills` at exact commit `83021e2be457a9b6679148719c1f6074f0ad975e`, the reviewed snapshot for T11.01, not an automatically changing default branch.
- The second checkout is independently checked with `git rev-parse HEAD`. No installation of a possibly unrelated PyPI `skills-ref` distribution is used.
- Runtime dependencies from upstream `skills-ref/uv.lock` are pinned by version and wheel SHA-256 in `tools/skills-ref-requirements.txt`. Missing or changed packages must make CI fail.
- The external checkout occurs **after** TESSERA's existing build and unit tests: it is a temporary untracked directory, never committed or included in the product ZIP.
- The CI validation job has read-only repository permissions and neither checkout retains credentials. Skill scripts are not executed.

After preparing the pinned upstream checkout and dependencies in a separate, trusted Python environment, run:

~~~bash
python tools/check_reference_skills.py --repo . --reference-src .external/agentskills/skills-ref/src
~~~

The wrapper runs `python -P -m skills_ref.cli validate` for every skill, using an explicit source directory and a 30-second per-skill timeout. Missing tools, invalid folders, symlinks, parsing failures, timeouts, and unexpected output fail closed. The wrapper itself performs no network requests or GitHub Release publication.

**Evidence:** only a successfully completed GitHub Actions workflow confirms the actual pinned upstream validator was executed on Linux. Static wrapper tests and instructions are insufficient.

## Separate publication readiness

The official GitHub CLI provides `gh skill publish --dry-run` to validate without creating a GitHub Release, but the command remains in preview. **T11.01 does not run this command.** Its real behavior, installed CLI version, side effects, and monorepo compatibility belong to T11.02/T10.

Do not use `gh skill publish` **without `--dry-run`** as an automated check: it may create a release, modify repository topics, or prompt for input.

## Acceptance

T11.01 is COMPLETE only after mandatory CI successfully performs the external checkout and upstream reference check. Overall T11 remains PARTIAL until T11.02 and real agent-client behavior are verified separately under T03/T05.
