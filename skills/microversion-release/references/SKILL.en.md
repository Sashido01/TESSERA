# Microversion Release — English reference translation

[Русский — оригинал](../SKILL.md) | **English — translation**

**For reference only:** the single Agent Skills entry point is the canonical Russian `../SKILL.md`. This file is not an independently loadable skill and intentionally has no YAML skill frontmatter.

## Purpose and limits

Use this skill when preparing a verified software change, Git commit, tag, or release, and before reporting task completion. It uses the same platform-neutral workflow in Codex, DeepSeek Harness, Claude Code, Hermes, and other Agent Skills readers. It does not depend on one model, provider, operating system, or agent runtime. See [INTEGRATION.en.md](INTEGRATION.en.md) for platform-specific installation.

A SKILL.md file cannot enforce execution after each commit by itself. Discovery and activation depend on the host platform. For enforcement, use repository-level instructions, Git/CI checks, or an audited lifecycle hook. Never describe skill discovery as proof of mandatory execution.

## Microversion rules

1. New projects start at `0.0.0`. Read the actual project's Git history and metadata. Do not guess the current version or rewrite published tags.
2. Each independently verified substantive change increments PATCH: `0.0.0 → 0.0.1`, …, `0.0.98 → 0.0.99`.
3. `.99` is a planned release milestone, not a PATCH limit. When the task has actually finished and mandatory checks have passed, prepare `0.0.99 → 0.1.0`, `0.1.99 → 0.2.0`, or `0.99.99 → 1.0.0`.
4. If the task remains unfinished at `.99`, continue meaningful verified changes with `.100`, `.101`, and beyond. Release only after task completion and the necessary checks—for example, `0.0.107 → 0.1.0`.
5. Do not manufacture commits to reach a number. Version metadata, changelogs, and release documents are part of the same release operation.
6. If mandatory build or test checks fail, do not claim the release succeeded. Fix the issue in a justified verified change and rerun validation.
7. Do not force this non-standard SemVer workflow onto an existing project with incompatible requirements or rewrite historical releases.

The read-only calculator returns `0.0.100` for `python scripts/next_version.py 0.0.99 --mode work`, and `0.1.0` for `python scripts/next_version.py 0.0.107 --mode release`. Release calculation alone does **not** establish readiness.

## Workflow

1. Inspect the actual repository root, HEAD, branch, worktree, tags, current version, repository rules, and authorization for release operations.
2. Make a concrete change and run the required tests and build. Do not describe unverified work as complete.
3. Recheck Git and concurrent release activity before committing. Never blindly stage other people's files using `git add -A`.
4. Compute the next work microversion, update controlled metadata and the Russian changelog, and update the English translation within the same change when required.
5. Create a substantive, human-readable Russian commit. Work microversions may have tags according to the project's policy; **release tags are mandatory**.
6. When the milestone is reached and the task is genuinely complete, prepare the `MAJOR.MINOR.0` or `MAJOR.0.0` release and run the real required build and tests.
7. **MUST create an annotated Git tag for every successful release**, such as `v0.1.0`. Give it a specific Russian annotation. In shared repositories, use a namespaced tag like `<skill>/v0.1.0` when required. Verify that the Git ref points to a tag object with an annotation and resolves to the exact release commit.
8. Run `python scripts/release_tag.py verify 0.1.0 --repo <project-root>` for verification. After tests and authorized Git writes, use `python scripts/release_tag.py create 0.1.0 --repo <project-root> --message "Релиз 0.1.0 — <actual result>"` to create it. This does **not** push. See [RELEASE_TAGS.en.md](RELEASE_TAGS.en.md).
9. If the mandatory tag is missing or wrong, report **BLOCKED / RELEASE_NOT_TAGGED** instead of COMPLETE. If you claim remote publication, separately confirm that the remote contains the annotated tag targeting the same release commit.
10. A local tag, a remote tag, a GitHub Release, and a build artifact are separate outcomes. Verify each independently.
11. Before final reporting, verify versions, Git refs, tests, build results, both documentation languages, and limitations.

## Human-readable history

Use plain, specific **Russian** in commit subjects, tag annotations, changelogs, and release titles unless a particular project explicitly requires another language. Describe what actually changed, not the tooling action. Avoid vague “chore: bump version” titles or invented verification claims. See [STYLE.en.md](STYLE.en.md).

## Multi-agent safety

Use one canonical version source per project. Parallel agents require serialized release operations and repeated HEAD/tag checks. Never duplicate version numbers, force-move a tag, force-push, or delete history. If reliable locking or coordination is unavailable, block automatic release and explain why.

## Final report

Report COMPLETE, PARTIAL, BLOCKED, or NOT_VERIFIED; previous/new version; actual changes; test/build evidence; commit SHA and annotated tag SHA; local/remote publication status; whether a GitHub Release exists; and limitations. Without a verified tag, a release is not complete. Do not promise background execution.

**Limit:** this skill specifies mandatory release tagging but a separate trusted Git/CI enforcement mechanism is needed to prevent an agent from bypassing the instructions.
