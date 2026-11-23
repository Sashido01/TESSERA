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
