# Microversion Release — English reference translation

[Русский — основной язык](../SKILL.md) | **English — translation**

**This is documentation only.** Agent Skills loaders must use the canonical Russian `../SKILL.md`, whose frontmatter defines skill activation. This document is not a second skill and deliberately has no skill frontmatter.

## When to use

Apply this skill to every verifiable change in a software project: preparing commits, tags, version changes, releases, and before declaring a task complete. Do not create new versions for research or responses without file changes. Avoid reloading the skill unnecessarily during the same turn.

## Fundamental rule

**One independent verified change, one microversion.** Updating metadata for that same microversion must not create another microversion. Read the actual current version from the project and Git; never guess.

### Version-number algorithm

- New projects start at `0.0.0`. Discover the current version from project files and Git; do not make it up.
- **Working microversion:** increment PATCH by one for each verified, substantive commit: `0.0.1`, `0.0.2`, …, `0.0.99`.
- **Release milestone:** once PATCH reaches 99, if the task is complete and verified, prepare `MAJOR.(MINOR + 1).0` when MINOR < 99, or `(MAJOR + 1).0.0` when MINOR = 99. For example: `0.0.99 → 0.1.0`, `0.1.99 → 0.2.0`, `0.99.99 → 1.0.0`.
- **Never interrupt an unfinished task just to release at .99.** Continue creating only real, independently verified changes: `.100`, `.101`, `.102`, and beyond as needed. At the first three-digit PATCH where the task is genuinely complete and verified, commit the actual final change and **then** prepare the `...0` release.
- For example, `0.0.99 → 0.0.100` while the task continues, followed by `0.0.100 → 0.1.0` once it is complete and tested. If completion requires `0.0.107`, release `0.1.0` only afterward.
- Do not create an artificial `.100` if the task finished and was verified at `.99`. No dummy commits to obtain a preferred number.
- If the release build fails, remain at the last confirmed microversion, fix the cause with new justified changes (`.101`, `.102`, etc. where appropriate), and never declare the release complete before verification.
- A version number is not proof of production readiness. Explain known limitations, especially around `1.0.0`.
- For existing projects with PATCH > 99, never rewrite history. Continue PATCH+1 and prepare the next milestone only after completion and verification under the project's adopted policy.
- The read-only calculator prints `0.0.100` for `python scripts/next_version.py 0.0.99 --mode work`, and `0.1.0` for `python scripts/next_version.py 0.0.99 --mode release`. Release mode **only calculates a number**, not task readiness.

## Before starting

1. Discover the real Git root, current branch, Git status, versions and tags, metadata files, `AGENTS.md`, and release policy.
2. Do not treat unknown repositories as trusted for automatic modifications. Stay within the authorized workspace. Do not push, reset, force-update, or delete Git history without separate permission.
3. If the project uses an incompatible versioning policy, do not silently change it. Report the conflict and agree on migration. Even if the owner explicitly adopts the new rules, apply them only going forward.
4. If you cannot determine the current version reliably, report `NOT_VERIFIED` instead of guessing.

## Workflow for one microversion

1. Complete a concrete change and describe the observed result.
2. Run the required tests, builds, and checks. Do not release if a mandatory check fails.
3. Recheck Git state; do not stage another person's unfinished changes, and do not blindly execute `git add -A`.
4. Calculate the next unused number in work mode for a working change or in release mode only after the milestone, task completion, and required verification. Ensure the tag does not already exist and version sources agree.
5. Update only managed metadata fields. Do not rewrite historical version references in archives, old documentation, or tests.
6. Update the concise changelog entry for the current microversion. After the final substantive task commit, build the distinct `.0` release: run all required tests, produce verified artifacts, and write truthful release notes.
7. Create a substantive working commit with its microversion; the last verified working commit may be `.100+`. Then, if needed, create a separate `.0` release commit for build and version metadata. Do not rewrite old commits.
8. Create a local **annotated** Git tag `vMAJOR.MINOR.PATCH` with a clear description and verify it points to the correct commit. Remote push, GitHub Release creation, and artifact publication require the project's authorization.
9. Verify the resulting version, HEAD, working tree, tag, changelog, and artifacts. Report COMPLETE only with actual evidence.
10. For partially finished work, version only independently completed and verified parts; mark the rest PARTIAL or BLOCKED.

## Mandatory release milestone

At `PATCH >= 99 → next ...0 release`, changing the version string alone is not enough. Find and execute the real build command and required checks; inspect and explain the result. If a project has no build, do not fabricate artifacts: report RELEASE_BLOCKED unless a documentation-only release mode was already approved.

## Natural writing style

For detailed examples, see [STYLE.en.md](STYLE.en.md).

- Write in plain, specific Russian unless a project explicitly requires another language.
- A commit says what changed and why—not which command an agent ran.
- Tag names remain machine-readable (`v0.1.0`); annotate them with a human-readable description.
- Release title format: `Версия 0.1.0 — <конкретный результат>`.
- Changelogs contain facts: what changed, how it was checked, and known limitations.
- Avoid vague phrases like “chore: bump version,” “misc fixes,” “the system has been improved,” or “AI-generated.”
- Never invent passing tests.

## Final report

Include COMPLETE / PARTIAL / BLOCKED / NOT_VERIFIED, the old and new versions, a plain-language summary, actual checks and results, commit and tag SHA if created, build/publication status, and limitations. If there was no release, say exactly why. Do not promise asynchronous work.

## Safety and repeatability

Do not release one change twice. Never move existing tags. Concurrent agents and Git worktrees require release-operation synchronization; without it, avoid automatic release. Do not discard other people's work to get a clean Git status. Interrupted operations must be safely resumable.

**Limitation:** `SKILL.md` contains instructions, not an enforced background event handler. Discovery depends on the agent environment. Strict enforcement requires separate project rules or an event-driven integration.
