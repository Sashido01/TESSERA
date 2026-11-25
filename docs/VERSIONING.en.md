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
