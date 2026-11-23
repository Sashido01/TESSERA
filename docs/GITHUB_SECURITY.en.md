# GitHub protection for TESSERA

[Русский — оригинал](GITHUB_SECURITY.md) | **English — translation**

## Verified state on 23 November 2026

Two active GitHub Rulesets have been confirmed via the GitHub API: `Protect main` (ID `27932550`) for the default branch and `release tags` (ID `27932769`) for `v*` tags.

Main requires a Pull Request with zero mandatory approvals, the GitHub Actions `validate` check, an up-to-date branch, linear history, and protections against deletion and force-push. For `v*`, updates, deletion, and force-push are restricted while creation of new tags is allowed. Both bypass lists are empty.

**Negative acceptance verified:** test Pull Request #1 with an invalid `VERSION=0.0.99` versus the existing `0.0.5` failed `validate`, and tagging did not run. [CI run](https://github.com/Sashido01/TESSERA/actions/runs/45255895372).

**Positive acceptance verified:** the corrected Pull Request #1 passed [validate](https://github.com/Sashido01/TESSERA/actions/runs/45256267316) and was squash-merged as commit `f2d961bdb0a0e768c9663a374e299d3e42ee409b`. Post-merge [GitHub Actions](https://github.com/Sashido01/TESSERA/actions/runs/45256377248) created annotated tag `v0.0.6` (tag object `1eeff57da476ef7a8930664ef6a494f586c00e79`) pointing to that exact commit.

**Still NOT_VERIFIED:** negative tests for modifying/deleting an existing published tag, administrator bypass, and unauthorized direct pushes. These risky operations were not performed on production Git history; T08 remains PARTIAL until safe acceptance can be completed.

## Implemented workflow controls

- `validate` runs with minimal `contents: read` permissions and does not persist Git credentials after checkout.
- `tag_microversion` is a separate job with `contents: write`, following validation, and only on pushes to `main`.
- Official `actions/checkout` and `actions/setup-python` are pinned to verified full commit SHAs.
- Before creating and pushing a tag, the remote `main` HEAD must equal the validated commit.
- Network failures while checking existing tags stop the operation instead of being treated as missing tags.
- Tag type, annotation message, target commit SHA, and remote tag object SHA are checked.
- `tools/check_workflow_security.py` statically checks these rules.

**Limitation:** this reduces mistakes but does not fully serialize concurrent releases. A race window remains between SHA checking and Git push; independent coordination belongs to T15.

## Active settings and verification guide

The setup procedure below is preserved for recovery and auditing. The owner has activated the Rulesets; changes are unnecessary unless specifically justified.

## Enabling branch protection

In GitHub, open `Settings → Rules → Rulesets → New ruleset → New branch ruleset` (UI labels may change).

1. Create `TESSERA main protection` targeting `main`.
2. Block deletion and forced history updates.
3. Require Pull Requests before merging. After activation, future changes should use PRs rather than direct writes.
4. Require the `validate` check and verify its trusted GitHub Actions source.
5. Avoid unrestricted administrator bypass.
6. Safely test on a separate branch or in Evaluate mode when available, then activate the ruleset.

## Tag protection

A separate Tag Ruleset for `v*` should prevent edits or deletions of published tags. Investigate `*/v*` for future independent skills.

**GitHub Actions must still be allowed to create new tags after PASS.** An unrestricted bypass that can also rewrite old tags is unacceptable. Test safe exceptions using a temporary, nonproduction prefix.

## T08 acceptance

- Rulesets are active and match `main` and protected tags.
- Invalid version or translation changes fail the required PR check.
- Unauthorized direct writes and forced history updates are rejected.
- Valid CI can create a new annotated tag but cannot overwrite existing ones.
- GitHub Actions permissions and administrator behavior are verified.
- Unavailable tests are recorded as `NOT_VERIFIED`. Do not run destructive tests on production `main`.

## Boundaries

TESSERA settings cannot automatically protect other repositories that install Microversion Release. Consuming projects require their own Git/CI rules. Published Git history remains available after current files are cleaned.
