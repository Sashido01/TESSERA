# Branches and Pull Requests in TESSERA

[Русский — оригинал](BRANCHING.md) | **English — translation**

## One coherent goal, one verifiable delivery

**A new branch is not required for every commit, fix, or agent step.** Active server-side Rulesets protect `main` and release tags, so changes must reach protected `main` through a Pull Request with required CI. GitHub protects the **target branch and tags**; it does not require a unique branch for every microversion.

Normal workflow: one short-lived working branch for **one coherent goal**, multiple intermediate commits and corrections **in the same branch**, and one Pull Request when ready. After successful checks, Squash and merge, followed by the annotated tag for the accepted `main` commit. The working branch can then be deleted; existing `main` history and published tags must never be rewritten.

## Microversions without unnecessary branches

- Assign the release microversion to a **completed, independently validated result**, not to an intermediate test run, failed CI, documentation tweak, or pre-merge fix.
- Intermediate commits within one unfinished goal do not require their own release tags. The **final Squash commit** validated by CI must contain a consistent `VERSION`, both Russian and English CHANGELOG entries, and the complete approved change.
- Fix CI failures in the same working branch and the same PR. Do not create another branch or increment the version just to fix an unmerged change.
- Two truly **independent completed goals** may require two successive microversions and releases. Do not combine unrelated work just to reduce PR count.
- A release exists only after the verified `main` commit receives its matching immutable annotated tag.

## Why not a permanent develop branch

With the current Squash and merge policy, a long-lived `develop` would require additional reconciliation with `main` after every merge. Careless resets could rewrite history. Short-lived branches per goal are simpler for now. Concurrent agents need separate coordination rather than an implicit `push --force`.

## Security

Never bypass protected `main`, disable Rulesets for convenience, force-push published tags, or claim working commits as releases. PR checks must not run untrusted build commands with elevated permissions. Automated tag publication after Squash merge verifies the current `main` SHA and rejects tag rewriting.

**Note:** a working branch is a mechanism for complying with server-side protections, not a product version. See [VERSIONING](VERSIONING.en.md) for version rules and [GITHUB_SECURITY](GITHUB_SECURITY.en.md) for access restrictions.
