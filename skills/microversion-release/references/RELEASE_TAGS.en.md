# Mandatory Git tags for releases

[Русский — оригинал](RELEASE_TAGS.md) | **English — translation**

## Requirement

**Every completed release** such as `0.1.0`, `0.2.0`, and `1.0.0` must have an **annotated** Git tag with a clear Russian message, pointing to the exact release commit. If the tag is missing or incorrect, report `BLOCKED / RELEASE_NOT_TAGGED`, never `COMPLETE`.

Multi-product repositories may use namespaced tags, such as `microversion-release/v0.1.0`. Define the prefix ahead of time in project policy. Tags on working microversions `x.y.1`–`x.y.99` and `x.y.100+` follow the project's policy; tags on `x.y.0` releases are mandatory.

## Before tagging

- Identify the actual Git HEAD, repository status, and release version.
- Confirm that the real required build and checks have passed.
- Commit release files first, so the tag points to the **release commit**, not an intermediate one.
- Ensure that the name is not occupied by a different tag.
- Do not implicitly push to a remote without separate authorization.

## Safe CLI usage

From the installed skill directory, passing the target repository root explicitly:

```bash
python scripts/release_tag.py verify 0.1.0 --repo <project-root>
python scripts/release_tag.py create 0.1.0 --repo <project-root> --message "Релиз 0.1.0 — исправлен запуск приложения"
python scripts/release_tag.py verify 0.1.0 --repo <project-root>
```

For a monorepo:

```bash
python scripts/release_tag.py create 0.1.0 --repo <project-root> --prefix microversion-release/ --message "Релиз навыка 0.1.0 — проверено обновление версий"
```

`create` produces **only a local annotated Git tag**; it does not commit, run tests, or access the network. Reruns are idempotent only when the existing annotated tag already resolves to the current HEAD. Invalid existing tags are never force-overwritten.

## Publishing to GitHub or other remotes

If the release is declared **published**, a local tag alone is not enough: confirm an authorized push of the correct tag and its target commit on the remote. A GitHub Release, archive, and build files are distinct outcomes and must be reported separately.

## Failures

- `RELEASE_NOT_TAGGED`: missing tag, lightweight tag, tag targeting the wrong commit, or empty annotation.
- No write permission: report `BLOCKED` without workarounds.
- Existing conflicting tag: stop and investigate; never force-update it.
- Concurrent agents: coordinate release operations before tagging.

**Limitation:** a verified Git tag does not replace actual build and application testing.


To bind to previously completed checks, pass `--expected-head <full-SHA>` to `create` and `verify`. A mismatch with HEAD blocks the operation. Even without the option, `create` captures the current SHA before writing and passes it explicitly to Git; verification inspects the immutable annotated tag object, its direct target commit and internal tag name. Rechecking HEAD and the ref detects observed changes. If a conflict occurs after creation, leave the tag unchanged, report BLOCKED, and investigate with explicit authorization. This is not an atomic concurrent-writer lock, proof of passing tests, or complete race protection.

A normal Git environment without external repository, namespace, object-store or configuration redirection through the listed environment variables is required. The CLI blocks rather than silently ignores these settings. Invocation from a Git hook or custom environment may require a separately reviewed adapter. The installed Git, PATH, selected repository configuration (including signing programs and hooks), and filesystem must be trusted; this is not a sandbox.

The Git child receives only a fixed set of process, path, local identity and signing-context variables. All other variables (including tokens and arbitrary application variables) are excluded; the parent environment stays unchanged. Configurations requiring additional variables may fail with BLOCKED and need a separately reviewed integration. This is not isolation from files, local signing helpers or the network.
