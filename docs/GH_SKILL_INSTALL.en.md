# T10.01 — isolated installation with official GitHub CLI

[Русский — оригинал](GH_SKILL_INSTALL.md) | **English — translation**

## Scope

T10 uses the official [`gh skill install`](https://cli.github.com/manual/gh_skill_install), not a third-party skill manager. The interface is in preview and may change.

T10.01 checks **local installation** via `gh skill install <source> microversion-release --from-local --dir <destination>`, discovery with `gh skill list --dir`, unchanged source files and a defensive no-overwrite guard. All test destinations are temporary. No real user profile, agent installation, or GitHub Release is modified.

Actual installation **from a remote Git tag or commit SHA** is tested separately in T10.02 below. Seeing installed files does not prove that Codex, Harness, Claude Code, or Hermes loaded or activated the skill (T03/T05).

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

Use the fully qualified `refs/tags/vX.Y.Z` to avoid short-ref ambiguity. `--pin` is valid in the **remote GitHub mode**, not alongside `--from-local`. Avoid `--force` on any existing installation.

## Acceptance and limitations

T10.01 is COMPLETE only after a real GitHub Actions run confirms the official CLI binary, successful local install and list, rejected `--pin` conflict and unchanged original source. Overall T10 remains PARTIAL until actual pinned remote install, update safety and installed agent behavior are verified. The signed v0.0.21 ZIP was independently verified in T09.10; that does not prove client installation.

## T10.02 — pinned remote installation

Official `gh 2.105.0` resolves a short ref as a branch first, then a tag, then a commit SHA. TESSERA's fixed acceptance baseline therefore uses the **fully qualified** `refs/tags/v0.0.22` and separately commit `34923e27e669da0092440a0bbfb00b2dfdd98a37`. Expected annotated tag object: `b9967ac3aa1abac7fdb8e7abceb8c6a3f79da66c`. Source: [resolveExplicitRef / resolveTagRef in official CLI v2.105.0](https://github.com/cli/cli/blob/v2.105.0/internal/skills/discovery/discovery.go).

`tools/check_official_remote_install.py` tests both pins using the **actual** official CLI. Two separate fresh temporary directories; isolated HOME and GH_CONFIG_DIR; only the short-lived read-only CI token (`github.token`, no PAT or user token). Git verification does not receive this token. The expected file inventory and bytes come from the independently identified annotated tag's Git tree. For SKILL.md, compare Markdown body and github-repo, github-path, github-ref, github-pinned, github-tree-sha metadata; full semantic equivalence of YAML frontmatter is not claimed. `gh skill list --dir --json` checks pinned status, source and version. `gh skill update --dry-run` must skip both pinned skills without mutation; reinstalling into a disposable existing target without --force must be refused without changing files. No skill content is executed.

**Live T10.02 acceptance (24 November 2026): COMPLETE.** [GitHub Actions 45351217500](https://github.com/Sashido01/TESSERA/actions/runs/45351217500) SUCCESS, official gh 2.105.0 reported `GH_SKILL_REMOTE_PIN_PASS`: tag_install, sha_install, pinned_update_dry_run, duplicate_install_refusal — PASS. Expected skill Git tree `4ed1f6095092b51cfd80d12f68865eecc6f86398` matched both installs' metadata; supplementary file inventory and bytes, SKILL.md Markdown body and pin verified. 362 catalog and 19 skill tests passed. This proves installation with a CI token on Linux, not activation within an agent.

Acceptance requires a real CI run with `GH_SKILL_REMOTE_PIN_PASS`; mocked tests do not establish remote installation. Actual updates with --unpin, multi-skill name conflicts/independent tags, client activation and unauthenticated API remain NOT_VERIFIED. Do not promise automatic updates to the latest Git tag: per CLI source, an unpinned install first selects the latest GitHub Release and otherwise the default branch. Never use --force in existing profiles.

Example separate installation after passing CI (fresh empty directory; review the skill first):

~~~text
gh skill install Sashido01/TESSERA microversion-release --pin refs/tags/v0.0.22 --dir <new-empty-skills-dir>
~~~

## T10.03.01 — actual update and guarded re-pin

Reviewed [official gh 2.105.0 update.go](https://github.com/cli/cli/blob/v2.105.0/pkg/cmd/skills/update/update.go). `--unpin` allows update discovery without retaining the pin, but does not select a specific replacement tag. The CLI resolves the latest GitHub Release, falling back to the default branch when no release exists. Successful updates replace directory contents; local edits and extra files can disappear. Some restore errors are ignored in upstream rollback code, so recovery under all failures is not guaranteed.

`tools/check_official_skill_update.py` uses disposable CI directories, a read-only token and fixed annotated tags v0.0.5 and v0.0.23 with distinct Git trees. Native update expectations come from the exact remote main SHA checked before/after the operation. A real `update --unpin --dry-run` is followed by `--unpin --all` against synthetic local edits only. Removal of the synthetic edits confirms a risk, not a feature. The actual updated tree, absence of pin and file inventory are checked.

The guarded exact re-pin scenario never uses `--force` or directly updates a live skill. It independently installs both versions, snapshots all entries (including hidden/extra files, mode, size and SHA-256), refuses local edits or staged mutations, renames the old copy to backup and the new copy into the target on the same filesystem. It checks injected failure after moving the old copy, original byte restoration and explicit rollback after success while retaining the newer copy. Symlinks, hardlinks, nested/aliased paths and existing backups are rejected. The helper retains the backup on rollback failure; the CI harness uses disposable data.

This is **an acceptance harness, not a production user-profile updater**. Exclusive directory access is required; crash recovery, concurrent writers, parent path substitution, Windows and live agent clients are not verified. Never silently merge local edits or apply this scenario to existing profiles. T10.03.02 separately covers multi-skill collisions and independent tags without publishing fictitious skills in TESSERA. T10.03.01 acceptance requires an actual CI `GH_SKILL_UPDATE_PASS`.

