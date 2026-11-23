# GitHub protection for TESSERA

[Русский — оригинал](GITHUB_SECURITY.md) | **English — translation**

## Verified state

On 23 November 2026, `main.protected=false` and repository Rulesets were empty. **Server-side protection was not enabled.** A passing CI run alone does not prohibit direct writes to the main branch.

The connected GitHub actions here can read settings and write repository files but cannot create Rulesets. The settings below must be applied separately by a repository administrator. T08 cannot be considered complete until those rules are active and tested.

## Implemented workflow controls

- `validate` runs with minimal `contents: read` permissions and does not persist Git credentials after checkout.
- `tag_microversion` is a separate job with `contents: write`, following validation, and only on pushes to `main`.
- Official `actions/checkout` and `actions/setup-python` are pinned to verified full commit SHAs.
- Before creating and pushing a tag, the remote `main` HEAD must equal the validated commit.
- Network failures while checking existing tags stop the operation instead of being treated as missing tags.
- Tag type, annotation message, target commit SHA, and remote tag object SHA are checked.
- `tools/check_workflow_security.py` statically checks these rules.

**Limitation:** this reduces mistakes but does not fully serialize concurrent releases. A race window remains between SHA checking and Git push; independent coordination belongs to T15.

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
