# TESSERA

[Русский — основной язык](README.md) | **English — translation**

**A shared library of skills for AI agents.** Each skill is a standalone module that can be used, tested, and developed independently.

TESSERA is not a fork of Harness or Codex. It stores portable [Agent Skills](https://agentskills.io/) instructions, scripts, and integration examples. Compatibility and automatic activation must be verified for each specific agent environment.

## Skill catalog

| Skill | Purpose | Status |
| --- | --- | --- |
| [Microversion Release](skills/microversion-release/README.en.md) | Microversions, mandatory annotated release tags, portable use across agents | Standard skill and local helpers prepared; individual agent clients are not yet verified |

## Repository layout

```text
skills/                 Independent skills, each with a SKILL.md
tools/                  Shared validation tools
docs/                   Rules, architecture, and roadmap
.github/workflows/      Automated checks on changes
```

## Getting started

1. Open the skill you need under `skills/` and read its `README.en.md` or the canonical `README.md` in Russian.
2. Install the **entire skill directory** into your agent's skills directory—not just its `SKILL.md`.
3. Verify that your agent discovers the skill. Automatic activation depends on the agent's configuration.
4. Review repository rules and permissions before allowing an agent to create commits, tags, or published releases.

For Microversion Release, see the [installation guide](skills/microversion-release/README.en.md).

## Validation

Python 3 is required; there are no third-party Python dependencies.

```bash
python tools/validate_skills.py
python tools/check_public_paths.py
python tools/check_translations.py
python tools/check_repository_version.py
python -m unittest discover -s tests -v
python -m unittest discover -s skills/microversion-release/tests -v
```

The following version calculator has no side effects:

```bash
python skills/microversion-release/scripts/next_version.py 0.0.99 --mode work
python skills/microversion-release/scripts/next_version.py 0.0.100 --mode release
```

These commands print `0.0.100` and `0.1.0`, respectively. **The second command only calculates a number**; it does not confirm task completion or a successful build.

## Versioning

**Current catalog version:** see [`VERSION`](VERSION). From this point forward, every independently verified change to TESSERA must increment the catalog microversion, update both changelogs, and use a clear, human-readable Russian commit title. After successful GitHub Actions checks, an annotated `vX.Y.Z` Git tag is created. GitHub Releases are not published automatically.

- **The TESSERA catalog** and **each skill** have independent version histories.
- Work microversions increase PATCH by one. After `.99`, work may continue with `.100`, `.101`, and so on if the task is unfinished.
- After completion and successful mandatory checks, planned milestones are `0.0.99 → 0.1.0`, `0.1.99 → 0.2.0`, and `0.99.99 → 1.0.0`.
- Do not create dummy commits or releases to reach a preferred number. New projects start at `0.0.0`; never rewrite published tags or history.
- Individual skill tags may use namespaces such as `microversion-release/v0.1.0` to avoid collisions with catalog-wide tags.

See the [version policy](docs/VERSIONING.en.md). The historical `0.0.0` baseline is preserved. Mandatory versioning begins at `0.0.1` without rewriting previous commits. No separate build artifacts or GitHub Releases have been published.

## Support for different agent hosts

The first skill uses the common Agent Skills format and can be installed into **Codex, DeepSeek Harness, Claude Code, Hermes**, and other compatible environments. See the [integration guide](skills/microversion-release/references/INTEGRATION.en.md) and the safe installer with a default preview mode. Hermes can also use TESSERA as a skills tap.

An application release **is not complete without a verified annotated Git tag**. Check it with `python skills/microversion-release/scripts/release_tag.py verify 0.1.0 --repo <project-root>`. The script does not replace build and test verification. Actual auto-activation in all agent clients has not been confirmed.

## Roadmap and constraints

The [complete T00–T17 roadmap](docs/ROADMAP.en.md) sets out verifiable steps for Git protection, one shared Release Core, skill distribution, and agent integration. The [dependency policy](docs/DEPENDENCIES.en.md) defines the approved stack: official GitHub CLI as the **planned preferred distribution mechanism after real-world verification**, plus a minimal Python installer for offline use and custom profiles.

NVIDIA SkillEvaluator is permitted **only at Tier 1**, after compatibility and resource evaluation without paid AI APIs. Tier 2 and Tier 3 must not be used. The reference `skills-ref` validator is planned for standard-format checks; TESSERA's own microversion and tagging tests remain mandatory.

## GitHub protection

The [Rulesets setup guide](docs/GITHUB_SECURITY.en.md) documents branch and tag protection. **Rulesets are active:** Pull Requests, `validate`, and an up-to-date branch are required, and published tags are protected. The negative CI acceptance test behaved as expected. Both negative and positive Pull Request cases and creation of a new annotated tag are verified. Destructive tag-rewrite tests have not been performed.

## Independent release verification

T09 begins with a [read-only Git evidence inspector](docs/RELEASE_CORE.en.md). It validates a version and annotated tag against an exact commit without modifying the repository. **It does not establish build success or release readiness**; those checks are future work.

## Release preflight

A [Release Preflight](docs/RELEASE_PREFLIGHT.en.md) and a `release-checks.json` plan are available. By default it only validates configuration, version, and release notes: `python core/release_preflight.py --repo . --version 0.0.8 --plan`. Running build/test commands requires explicit `--execute` with a trusted configuration. The result **does not prove publication of a release**.

## Evidence reports and remote tags

[T09.03](docs/RELEASE_REPORT.en.md) documents verification of an annotated tag object SHA on a Git remote and machine/human-readable evidence reports. By default, reporting is local and runs no project commands; network queries require `--verify-remote`, and build/test execution requires `--execute-checks`. **PASS covers only explicitly requested checks, not application release readiness.**

## Completed GitHub Actions verification

[T09.04](docs/RELEASE_CI.en.md) adds independent verification of a completed GitHub Actions run by exact commit SHA and required jobs. Explicit `--verify-ci`, a trusted repository and run ID are required. No paid AI APIs are involved; network queries are disabled by default. `CI_VERIFIED` is not RELEASED.

## Contributing

See [contribution guidelines](CONTRIBUTING.en.md), [security policy](SECURITY.en.md), [changelog](CHANGELOG.en.md), [community rules](CODE_OF_CONDUCT.en.md), and the [MIT license](LICENSE).

**Important:** neither SKILL.md nor the version calculator guarantees execution after every agent action. Enforced checks require project-level rules or an event-based integration.

## Languages

**Russian is the source of truth.** Create and review the Russian documentation first, then update the corresponding English translation within the same change. See the [translation policy](docs/I18N.en.md).

---
Original project: [Sashido01/TESSERA](https://github.com/Sashido01/TESSERA).
