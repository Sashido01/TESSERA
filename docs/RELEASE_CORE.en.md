# Release Core — Git evidence inspector (T09.01)

[Русский — оригинал](RELEASE_CORE.md) | **English — translation**

## Purpose

`core/release_inspect.py` is the first independent part of TESSERA's Release Core. It **only reads** an existing Git repository and prints structured JSON without modifying files, commits, tags, or accessing the network. It is independent of Codex, Harness, Claude, Hermes, and other agent hosts.

## What is actually checked

- The Git repository root and the exact full SHA of the requested commit.
- The `VERSION` file **inside the target commit**, rather than the current working copy (historical releases can be checked).
- Existence of the version tag, optionally with a namespace prefix.
- An actual annotated `tag` object rather than a lightweight ref.
- Nonempty annotation and tag target matching the exact requested commit.
- Current worktree cleanliness is reported as a separate fact; it does not prove release readiness.

## CLI

From the TESSERA root:

```bash
python core/release_inspect.py --repo <project-root> --version 0.1.0
python core/release_inspect.py --repo <project-root> --version 0.1.0 --commit <full-commit-sha>
python core/release_inspect.py --repo <project-root> --version 0.1.0 --prefix microversion-release/
```

`--commit` accepts only a full SHA; HEAD is used otherwise. JSON fields include `inspection_status`, `release_readiness`, `expected_commit_sha`, `version_in_commit`, `tag_annotated`, `tag_target_commit_sha`, and `problems`.

Exit 0 means `inspection_status=PASS`; exit 1 means `BLOCKED` or an inaccessible Git repository. **PASS only demonstrates version/tag consistency.** The `release_readiness` field intentionally remains `NOT_VERIFIED` until independent build/test verification exists.

## Failure codes

- `RELEASE_NOT_TAGGED`: missing tag.
- `TAG_NOT_ANNOTATED` / `TAG_ANNOTATION_MISSING`: lightweight tag or empty annotation.
- `TAG_WRONG_COMMIT`: tag refers to another commit.
- `VERSION_MISSING_IN_COMMIT` / `VERSION_MISMATCH`: missing or differing recorded version.
- `TAG_TARGET_NOT_COMMIT`: tag does not resolve to a commit.

## Next Release Core component — T09.02

The separate [Release Preflight](RELEASE_PREFLIGHT.en.md) checks the version, CHANGELOG entries, and a trusted plan of required builds/tests. `--plan` executes nothing, while `--execute` runs the declared commands only with explicit authorization. This is a **separate component**; this tag inspector stays fully read-only. Passing preflight does not mean a tag exists or an application was published.

## Remote tag verification

A separate [T09.03](RELEASE_REPORT.en.md) stage checks whether the **same annotated tag object** exists on a trusted Git remote and emits an evidence-based report. The T09.01 local inspector remains intentionally offline and read-only.

## What is not implemented

- No build/test execution or validation of test evidence.
- No parsing of target changelogs, signed releases, or packaging manifests.
- No remote pushing, remote tag validation, or GitHub Release checks.
- No final RELEASED decision or concurrency serialization.
- The target project must store its version in `VERSION`; alternative version sources require future adapters.

This is **T09 PARTIAL**, not a complete release system. Future preflight, build, tag, remote, and report operations will build on independent verification, not agent claims.

## Testing

```bash
python -m unittest discover -s tests -v
```

Tests create temporary Git repositories and never modify unrelated projects.

## T12.03.11 — fixed-object local inspection (candidate)

Shared read-only Git helper for inspect/preflight/report rejects inherited Git context, forwards an explicit environment allowlist without identity/signing/auth, uses --no-replace-objects, --no-optional-locks, disables fsmonitor, prohibits interactive prompting and requests no lazy fetch. 30 seconds per invocation, closed stdin, fixed error codes without raw stderr. Trusted Git/PATH, configuration and filesystem remain prerequisites; not a hard memory quota, network sandbox or proof of no side effects. Tag inspection reads a fixed SHA, requires a direct commit and matching embedded tag name, rechecks the ref and current HEAD; historical mode requires exact commit SHA, not tag object SHA. JSON schema v1 retained. Eight new regressions; live CI required. ABA/TOCTOU after inspection, remote subprocess and user preflight commands remain separate concerns. T15 remains open.

## T12.03.12 — remote inspection (candidate)

Only a configured named remote with one effective fetch URL; absolute local path/file, HTTPS and SSH, no HTTP/git/ext, password or HTTPS userinfo. GIT_ALLOW_PROTOCOL permits file:https:ssh, fixed upload-pack, no HTTP redirects, closed stdin and minimal environment; SSH_AUTH_SOCK allowed for explicit remote operation. Trusted Git config, credential helpers, SSH config, HOME/PATH and server remain prerequisites. No network sandbox or descendant termination guarantee; rechecks do not eliminate ABA/TOCTOU. Recheck local evidence and URL after query; report compares commit and object SHA. GitHub publication uses the same URL contract. Ten regressions; CI required. Actual authenticated HTTPS/SSH NOT_VERIFIED.
