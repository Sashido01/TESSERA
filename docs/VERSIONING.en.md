# Versioning policy for TESSERA and its skills

[Русский — основной язык](VERSIONING.md) | **English — translation**

## Two independent version histories

The TESSERA catalog has its own version. Each skill may also have an independent version. Do not confuse either with the version of an application consuming a skill.

A new project starts at `0.0.0`. Namespaced skill tags may look like `microversion-release/v0.1.0`. Catalog-wide tags may use `v0.1.0` when there is no conflict.

## Independent skill versions

Each skill directory contains its own `VERSION`, `CHANGELOG.md` and `CHANGELOG.en.md`. The first working version is `0.0.1`; historical commits are not rewritten. Validation compares substantive skill changes against the first Git parent; unrelated catalog changes leave the skill version unchanged. Changes to only the three metadata files are not a new substantive result, except initial migration. Removing a previously versioned skill requires a separate retirement policy. ZIP archives include independent metadata; legacy archives without it remain verifiable. Metadata validation does not create tags or prove independent release or activation.

## Applying these rules to TESSERA itself

**TESSERA must follow these rules**, independently of the versions of its individual skills. Its historical baseline is `0.0.0`; the already published history without a mandatory `VERSION` file remains unchanged. The new policy begins with `0.0.1`.

- The canonical machine-readable catalog version lives in the root [`VERSION`](../VERSION) file.
- Every independently verified repository change must be recorded in one commit that advances the catalog microversion and updates both `CHANGELOG.md` and `CHANGELOG.en.md`.
- CI verifies the transition against the parent commit: normally PATCH+1, or a release transition to the next `.0` only once PATCH≥99. The initial migration record must be `0.0.1`.
- Commit titles are specific, natural Russian text rather than `bump` / `chore` templates. After a `main` commit passes CI, GitHub Actions creates an **annotated** `vX.Y.Z` tag with a Russian title. Existing tags must never be reused or moved.
- A `.0` release of TESSERA is a release of the catalog, documents, and scripts; no binary distribution is inherently required. Release readiness requires passing tests and documentation checks. A GitHub Release is a separate publication step.
- Updating metadata for the same version is part of that single change, not a reason for an endless chain of extra microversions.

## Branches are not microversions

A new Git branch is **not necessary for every intermediate change, correction, or test**. Under the active `main` Ruleset, use one short-lived branch for a coherent goal and keep intermediate fixes within the same PR. Only its accepted completed result receives **one next microversion**, synchronized VERSION/CHANGELOG, and an annotated tag of the final `main` commit. See [BRANCHING](BRANCHING.en.md).

## Mandatory release tag

**Every TESSERA and individual skill release requires an annotated Git tag** pointing to the release commit. Catalog tags use `vMAJOR.MINOR.PATCH`; independent skill tags may use `<skill>/vMAJOR.MINOR.PATCH`. Releases such as `0.1.0`, `0.2.0`, and `1.0.0` must report `BLOCKED / RELEASE_NOT_TAGGED` if the tag is missing, even when documentation or builds exist. Annotations must clearly describe the real result in Russian. Never create lightweight tags, force-move existing tags, or claim GitHub publication based on a local tag alone.

Consuming projects can run `scripts/release_tag.py verify`; CI and Git hooks can independently enforce this rule. A tag check is not evidence of successful automatic activation in every agent host.

## Working microversions

- A standalone verified change increments PATCH by one.
- If a task remains unfinished after `.99`, `.100`, `.101`, and further values are allowed, with no artificial limit of 99.
- Do not invent changes merely to advance a version. Recording release metadata is part of the same release operation, not an endless chain of new versions.
- Planned new-project milestones are `0.0.99 → 0.1.0`, `0.1.99 → 0.2.0`, and `0.99.99 → 1.0.0`.
- If a task continues to `0.0.107`, a transition `0.0.107 → 0.1.0` is possible after completion and the required checks. Do not create artificial intermediate versions.
- Tests and builds are required to the extent specified by the actual project. Do not mark a release ready if mandatory checks fail.

## Human-readable messages

A commit title describes *what changed*, not which tool was run. Example in the canonical Russian style: «Добавлена проверка корректности навыка перед публикацией». A Git tag has a machine-readable name, while the tag annotation explains the change in ordinary language. Release notes contain verified facts and limitations.

## Limitation

This is TESSERA's special release workflow, **not** a claim that the workflow follows standard SemVer rules. Public packages and APIs may require different policies. Never rewrite existing projects' published history or tags.

## Independent tag protection — TD03

GitHub API observation 25 November 2026: active tag Ruleset `27932769` (release tags), include `refs/tags/v*`, empty exclusions, deletion/non_fast_forward/update rules, no bypass actors. This pattern does not cover `refs/tags/<skill>/vX.Y.Z`. Extend it before independent release. Minimal owner change: Settings → Rules → Rulesets → release tags → add `*/v*` (REST API `refs/tags/*/v*`) alongside existing `v*`; keep the existing rule, no bypass, active and all three restrictions. GitHub slash-aware fnmatch covers one-level skill names; do not claim protection of arbitrary nested namespaces. Reconcile live rules before saving. Afterwards check GET `gh api repos/Sashido01/TESSERA/rulesets/27932769` and ensure no weakening. Verify enforcement in a disposable test repository, never attempt to move existing TESSERA tags. Owner extended the Ruleset on 25 November 2026 13:22:56 +03:00; repeated API GET confirmed both includes, active, empty exclusions/bypass and all three restrictions. TD03 COMPLETE for configuration; no destructive live probes. Sources: [GitHub Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository), [REST API](https://docs.github.com/en/rest/repos/rules?apiVersion=2022-11-28).

## Independent publication — T16 candidate

`tools/publish_skill_tags.py --repo . --expected-commit <SHA>` defaults to read-only inspection of full local history and tags. `--publish` only on trusted verified main, after mandatory validate and catalog tag verification in the existing tag job. Plan uses each skill VERSION first-parent history, checks committed VERSION/SKILL.md/both changelogs and exact direct annotated catalog tag. Four historical records authorized with exact SHAs and catalog tag objects v0.0.66/.67/.69/.71 (CI 45572387469, 45579382735, 45584865396, 45589558047). New tag allowed on current verified main; unknown missing historical tag requires separate evidence-based recovery. Check all conflicts before writes; only new refs, atomic push without force, recheck remote objects. Local tags may remain after failed push; never delete automatically. Atomic push does not prevent main moving in a small race window; recheck afterwards and serialize integration. 13/13 Linux tests on disposable Git and bare remote; GitHub atomic push, Windows and actual initial four tags require CI. Tags do not establish GitHub Releases, attestation or activation. Catalog-specific plan, not universal external project publisher.

## v0.0.73 release recovery — v0.0.74 candidate

Run 45597537888: two attempts; required catalog/history/source and validate PASS, annotated catalog tag v0.0.73 7887314fad80eac721ae83daf813d15d86c431a9 points directly to cd37acd7d17797a8849073a58f01d3caf16dadb5. Independent publication FAIL (SKILL_TAG_GIT_FAILED), four refs absent. Cause not established; previous code hid operation and exit code. Do not move v0.0.73 or claim full release completion. A narrowly scoped recovery PR after all required checks is an allowed way out of deadlock when only publication failed, with exact catalog tag and validate verified. Do not merge ordinary PRs until recovery; defer Git Inspector PR #74 preserving its branch, reserve v0.0.74 for repair. No checks weakened, full main recovery CI required.

Fix: allowlisted operation/exit/category without raw stderr; verify single matching fetch/push URL. `git push --dry-run --atomic` before actual push; allow sequential mode only on explicit upstream message `the receiving end does not support --atomic push` (new tags only; compare full refs before/after every push). Stop on every other error; no automatic fallback after failed actual atomic push. Both modes without force, `--no-follow-tags` and `--no-signed`. Sequential mode can partially publish; retain successful tags and reconcile on retry; overall release PASS only with every exact ref. 19/19 Linux tests (13+6, 2.427 s), real bare remote with receive.advertiseAtomic=false, mocked rejection and partial recovery. GitHub atomic support and v0.0.73 root cause NOT_VERIFIED; live CI required. Error reference: https://git-scm.com/docs/git-push (atomic), upstream git/send-pack.c. TD02 BLOCKED until actual tags.

## v0.0.74 recovery — v0.0.75 candidate

PR #75 and run 45600249135 PASS, merge ddab826e5a17641e0f475ecc63193f412065e28e. Main run 45603880522: catalog/history/source and validate PASS; annotated v0.0.74 tag fa1672565850630db4b16fa57bf79a701f6bdc1e points directly to that commit; job 139172989317 FAIL, `SKILL_TAG_GIT_FAILED:PUSH:1:UNCLASSIFIED`. Dry-run does not reproduce the actual push rejection. GitHub API confirmed zero independent refs; root cause NOT_VERIFIED. Never move existing tags or rerun unchanged job.

Candidate selects `--publish --strategy sequential` in advance in the same restricted main tag job after full validate and exact catalog tag verification; this is a new controlled transport strategy, not automatic post-failure fallback or restriction bypass. Each push creates only one absent ref, reconciles the full snapshot before/after, and logs only the allowed tag name; stop on every rejection. New classification for atomic/remote rejection/failure and GH006 without raw stderr. Atomic remains the CLI default; fallback only after explicit unsupported atomic dry-run, retaining no automatic retry after ambiguous real push. 23/23 Linux tests (19+4, 3.761 s), exact Git blobs ac7275583dacf0a0655f5822f4e2e13ac80221be and 7f9138d9fb6fd97d5324c5eadb4074d149ae552b. GitHub protections not weakened. Live publication NOT_VERIFIED; only this narrow repair may take the next slot after required PR CI; ordinary changes await all independent refs.
