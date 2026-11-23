# TESSERA dependencies and constraints

[Русский — оригинал](DEPENDENCIES.md) | **English — translation**

## Approved policy

This document records the owner's decision of 23 November 2026. The Russian document is canonical. These are **allowed tools and constraints**, not proof that tools are installed or tested in the owner's local environment.

## Approved foundation

| Tool | Status | Purpose |
| --- | --- | --- |
| Git | Required for Git operations | Commits, history, annotated tags |
| Python 3 standard library | Core custom tooling | Version calculation, checks, minimal offline installer |
| Official GitHub CLI (`gh skill`) | Preferred planned distribution after testing | Discovery, installation, SHA/tag pinning, updates |
| Agent Skills | Skill publishing standard | Portable SKILL.md and directory layout |
| Official `skills-ref` | Planned reference validator | Standard-format verification |
| NVIDIA SkillEvaluator **Tier 1** | Only after isolated evaluation | Free baseline static checks; not a runtime dependency |
| Custom Codex/Harness/Claude/Hermes adapters | Planned | Shared core invocation and enforcement |

The description of Tier 1 as free refers to not requiring paid AI APIs. CI infrastructure may still incur its normal operational limitations and costs. Verify commands, pinned versions, and actual resource use before adoption.

## Explicit exclusions

- **Vercel Skills CLI (`npx skills`) is entirely excluded** — not a primary or fallback installer, dependency, update mechanism, or CI tool. Do not reintroduce it without a new explicit owner decision.
- **NVIDIA SkillEvaluator Tier 2 and Tier 3 are excluded.** Do not run, configure, or list them as future mandatory stages.
- Paid AI APIs, external embeddings, and cloud LLM services **must not be mandatory** for installation, validation, release, or use of skills.
- Do not automatically install third-party agent plugins. Audit origin, license, version, permissions, and necessity first.
- Do not implement separate versioning cores for each agent: build one independent TESSERA core with thin adapters.
- Do not reimplement GitHub CLI's native package-management functionality without a demonstrated technical need.

## How to evaluate any new tool

1. Verify official origin and current version.
2. Inspect license and executable dependencies.
3. Confirm no paid keys are required and that the tool performs the necessary function.
4. Test in isolation, without access to private credentials or unrelated projects.
5. Measure runtime, dependency footprint, results, and side effects.
6. Pin verified versions and add reproducible tests/CI.
7. Record findings in canonical Russian and full English translation. Mark untested behavior NOT_VERIFIED.

## Offline installer

The existing Python `install.py` remains a minimal offline and custom-profile option. It must not compete with `gh skill` as a universal package manager. Copying into a project requires explicit authorization and must not silently overwrite an installed skill.

## Related documentation

- [Roadmap](ROADMAP.en.md)
- [Architecture](ARCHITECTURE.en.md)
- [Version policy](VERSIONING.en.md)
- [Language policy](I18N.en.md)
