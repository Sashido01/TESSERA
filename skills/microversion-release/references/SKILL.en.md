# Microversion Release — English reference translation

[Русский — оригинал](../SKILL.md) | **English — translation**

The canonical Russian SKILL.md is the only loadable entry point. This translation intentionally has no YAML skill frontmatter.

## Purpose and prerequisites

One workflow for Codex, Harness, Claude Code, Hermes and other Agent Skills-compatible agents. Independent of model, provider and OS. Requires the target Git repository, its versioning policy and checks; Python 3 for helper scripts. Installation: [INTEGRATION.en.md](INTEGRATION.en.md).

## Limits and authorization

Work only in the explicitly selected project. Reading Git and calculating a version do not authorize writes. Commits, tags and publication require appropriate authorization and adherence to project rules; publication needs separate authorization. Keep the installed skill, security settings, agent memory and other people's files unchanged. Do not bypass checks, move existing tags or force-push. Report BLOCKED if authorization conflicts.

SKILL.md cannot enforce automatic activation. Mandatory execution requires project instructions and independent Git/CI checks or a tested lifecycle hook.

## Microversion rules

1. New projects start at 0.0.0. For existing projects, establish the version from metadata and Git; preserve published versions.
2. Each independently verified substantive change increments PATCH by 1.
3. .99 is a milestone, not a limit. If the task is complete and mandatory checks pass, prepare 0.0.99 → 0.1.0, 0.1.99 → 0.2.0, or 0.99.99 → 1.0.0.
4. If unfinished at .99, continue .100, .101 and beyond. Release after actual completion and checks, e.g. 0.0.107 → 0.1.0.
5. Do not manufacture empty changes for version numbers. VERSION, CHANGELOG and release documents belong to one substantive operation.
6. Failed builds or mandatory tests mean the release is not ready. Fix the cause and rerun checks.
7. This is a custom policy, not standard SemVer. Do not impose it on an incompatible project.

## Instructions

1. Inspect Git root, HEAD, branch, worktree status, tags, version, rules and authorization.
2. Make a concrete change. Run required builds and tests; do not describe unverified work as complete.
3. Recheck HEAD and tags. With multiple agents, serialize release operations; block release writes if reliable coordination is unavailable. Do not stage other people's files or the whole worktree blindly.
4. Calculate the next microversion; update metadata, CHANGELOG and roadmap. Update translations alongside originals when required.
5. Create a substantive Russian commit unless the project specifies another language. Work microversion tags follow project rules.
6. After completing the task at the milestone, prepare a MAJOR.MINOR.0 or MAJOR.0.0 release and run actual mandatory checks.
7. Every successful release requires an annotated Git tag, e.g. v0.1.0 or microversion-release/v0.1.0. Its annotation describes the real outcome. Verify tag object type, nonempty annotation and exact release commit.
8. Without a valid release tag, report BLOCKED / RELEASE_NOT_TAGGED. For a claimed authorized publication, separately verify the remote tag and identical commit.
9. A local tag, remote tag, GitHub Release and artifact are separate outcomes. Before reporting, recheck versions, Git, tests, builds, RU/EN documentation and limitations.

## Scripts

Run from the installed skill directory.

| Script | Action | Boundary |
| --- | --- | --- |
| scripts/next_version.py | work / release | Calculation only |
| scripts/release_tag.py | verify / create | create writes a local annotated tag after checks and authorization; no push |
| scripts/install.py | --platform, --apply | DRY-RUN by default; no overwrite |

## Examples

- Unfinished task: python scripts/next_version.py 0.0.99 --mode work → 0.0.100.
- Completion after .107: python scripts/next_version.py 0.0.107 --mode release → 0.1.0. Calculation does not establish readiness.
- Verify: python scripts/release_tag.py verify 0.1.0 --repo <project-root>.
- After successful checks and authorization: python scripts/release_tag.py create 0.1.0 --repo <project-root> --message "Релиз 0.1.0 — исправлен запуск".
- Missing tag or wrong commit: BLOCKED / RELEASE_NOT_TAGGED. Do not automatically replace an incorrect tag.

See [RELEASE_TAGS.en.md](RELEASE_TAGS.en.md), [STYLE.en.md](STYLE.en.md). Describe the outcome in commits, CHANGELOG, annotations and releases, not formal actions: a specific description of repaired recovery rather than "chore: bump version".

## Troubleshooting

Failed build/test: fix and rerun. Version or HEAD conflict: coordinate changes. Existing tag: verify the target, do not move it. Missing authorization or evidence: BLOCKED or NOT_VERIFIED. Missing automatic activation: verify instructions and independent enforcement for the actual agent.

## Final report

Report COMPLETE, PARTIAL, BLOCKED or NOT_VERIFIED; prior/new versions, actual changes, tests and build, commit SHA and annotated tag object SHA, local/remote publication, GitHub Release/artifact presence and limitations. A release without a verified tag is incomplete. Do not promise background execution.
