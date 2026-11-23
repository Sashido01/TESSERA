# T10.01 — isolated installation with official GitHub CLI

[Русский — оригинал](GH_SKILL_INSTALL.md) | **English — translation**

## Scope

T10 uses the official [`gh skill install`](https://cli.github.com/manual/gh_skill_install), not a third-party skill manager. The interface is in preview and may change.

T10.01 checks **local installation** via `gh skill install <source> microversion-release --from-local --dir <destination>`, discovery with `gh skill list --dir`, unchanged source files and a defensive no-overwrite guard. All test destinations are temporary. No real user profile, agent installation, or GitHub Release is modified.

Actual installation **from a remote Git tag or commit SHA** is not yet verified and belongs to T10.02. Seeing installed files does not prove that Codex, Harness, Claude Code, or Hermes loaded or activated the skill (T03/T05).

## Official CLI safety risk

Review of the **official GitHub CLI `v2.105.0`** source at commit `e1219499a578b69e3437adaa31cd60614e23c802` identifies two distinct constraints:

1. `--from-local` and `--pin` are **mutually exclusive**. A local copy cannot be claimed as version-pinned to a Git tag or source commit.
2. The local `InstallLocal` implementation writes files using `os.WriteFile` without checking whether the same-named skill directory/files already exist. Repeating `gh skill install --from-local --dir ...` may therefore overwrite user-edited files even **without `--force`**. Never perform this direct operation in a preexisting user skill directory without backup, review and explicit consent.

Official `gh skill install` has **no `--dry-run` flag**. This differs from `gh skill publish --dry-run` (format validation) and `gh skill update --dry-run` (non-mutating update check).

## Safe CI acceptance

- Reuse the official GitHub CLI `2.105.0` from T11.02, an SHA-256-verified Linux AMD64 archive (digest `79e7ab5db738c48777b696e374f8b428f0647debfb424f44d2f426370407fe2f`). CI checks the digest **before** running the executable.
- `tools/check_official_local_install.py` snapshots the checked `skills/` files into a temporary folder and compares SHA-256 content fingerprints before and after.
- Run the real `gh skill install` **only** against a brand-new temporary target with isolated HOME/GH_CONFIG_DIR, no inherited GitHub tokens, remotes, or user Git config.
- Verify installed `microversion-release/SKILL.md`, preserved Markdown body and `references/INTEGRATION.md`, and injected source metadata in the installed skill frontmatter.
- Require the real `gh skill list --dir` to discover the installed skill.
- Exercise incompatible `--from-local --pin` only with a different empty temporary destination: require an explicit rejection and no files created.
- The `safe_destination` guard must reject preexisting targets **before calling the official installer**. No destructive overwrite test against actual user data is permitted.

## Manual use

For existing projects until full T10 acceptance, use the [minimal offline installer](../skills/microversion-release/references/INTEGRATION.en.md): it performs DRY-RUN by default and copies with explicit `--apply` only if the target does not already exist.

Official local installation should target **a new empty skill directory only**, after reviewing the skill contents. Future remote installation syntax:

~~~text
gh skill install Sashido01/TESSERA microversion-release --pin vX.Y.Z --dir <new-empty-skills-dir>
~~~

This is a **planned T10.02 command**, not evidence of a successful pinned remote installation. `--pin` is valid in the **remote GitHub mode**, not alongside `--from-local`. Avoid `--force` on any existing installation.

## Acceptance and limitations

T10.01 is COMPLETE only after a real GitHub Actions run confirms the official CLI binary, successful local install and list, rejected `--pin` conflict and unchanged original source. Overall T10 remains PARTIAL until actual pinned remote install, update safety and installed agent behavior are verified. The real signed ZIP remains a separate open issue (T09.10).
