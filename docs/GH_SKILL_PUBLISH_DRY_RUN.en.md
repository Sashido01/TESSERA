# T11.02 — real gh skill publish --dry-run validation

[Русский — оригинал](GH_SKILL_PUBLISH_DRY_RUN.md) | **English — translation**

## What is being verified

The official [GitHub CLI command](https://cli.github.com/manual/gh_skill_publish) `gh skill publish --dry-run` validates Agent Skills format and, unlike `gh skill publish`, does not create a GitHub Release. The command is in preview and may change.

Every TESSERA PR and push to `main` executes the **real** `gh 2.105.0` binary in a temporary isolated skill tree. Both a positive case and a malformed-name negative case are mandatory. CI fails on an unknown result, execution error, changed file, or unexpected Git remote.

## Immutable binary

- Source: official [GitHub CLI 2.105.0](https://github.com/cli/cli/releases/tag/v2.105.0), Linux AMD64 asset `gh_2.105.0_linux_amd64.tar.gz`.
- Archive SHA-256 independently read from official GitHub Release metadata: `79e7ab5db738c48777b696e374f8b428f0647debfb424f44d2f426370407fe2f`.
- CI downloads the archive over HTTPS and checks the SHA-256 **before extraction and execution**. No global installation occurs. The binary location is passed explicitly and its reported version is checked.
- `tools/run_publish_dry_run.py` uses the Python standard library, Git, and temporary storage.

## Isolation and security

The script copies only `skills/` into a temporary directory. The temporary Git repository has no remote, inherited GitHub tokens, publishing permissions, or user Git configuration. It uses `GH_PROMPT_DISABLED=1`, a separate `GH_CONFIG_DIR`, array-based subprocess calls (no shell), and bounded timeouts.

Validation steps:

1. Reject unexpected skill names and symlinks, then fingerprint the complete original skill tree.
2. Create a temporary snapshot and independently verify its file-byte fingerprint.
3. Require the real `gh skill publish --dry-run` to succeed without changing the snapshot.
4. Change the name field of the **temporary** first SKILL.md to a mismatched name. Require the real CLI to reject it without rewriting the altered test file.
5. Verify that no remote was added and the original project's skill tree remains unchanged.

Public output includes only an evidence status, CLI version and safe error codes, never raw subprocess stderr, tokens or private absolute paths.

## Evidence boundaries

With **no remote**, the CLI does **not** perform its additional live GitHub checks for repository topics, server-side security settings or published releases. The result therefore proves **real local publish-format validation** but not full remote publication readiness or activation in installed agent clients.

The script never invokes non-dry-run `gh skill publish`, `--tag` without `--dry-run`, or `--fix`. It does not create any GitHub Release. Remaining independent work: T09.10 (signed ZIP), T10 (GitHub CLI installation), and T03/T05 (actual agent hosts).

## Acceptance

Local isolated T11.02 dry-run can be marked COMPLETE only after a real GitHub Actions CI job downloads and hash-verifies the CLI and executes both positive/negative scenarios. Overall T11 remains PARTIAL for full public release readiness and client compatibility.
