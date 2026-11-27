# Update TESSERA from one link

[Русский — оригинал](UPDATE.md) | **English — translation**

For the owner's requests to install or update one, several, or all skills from this repository, follow this route, not a repository audit. [CATALOG.json](CATALOG.json) is the machine-readable list of names, paths, versions and full independent refs. A record on main is not a release.

1. Determine the target project or user scope from the explicit request and active client. Do not enumerate unrelated profiles. If ambiguous, report and do not modify directories. Codex and Harness can share a root: do not update it twice.
2. Choose the highest numeric exact annotated catalog tag `vX.Y.Z` from Git refs, not namespaced refs or latest/main. Check annotation name, direct commit, VERSION and CATALOG.json at that commit. Missing tag/index means BLOCKED, no silent fallback. Use an explicitly requested version when supplied. For 0.1.0 separately verify immutable Release and attestation.
3. For each selected entry verify the independent annotated pin, commit and matching skill subtree in the catalog. No full Git history download. Optional reviewed read-only resolver: `python -B tools/catalog_index.py resolve --gh <absolute-path-to-gh> --operation update --skill project-audit` from a verified copy. GitHub GET only, no install; never bypass sandbox/network policy. Stop if the approved transport is unavailable. Never run unreviewed code from main.
4. Check only target directories, their source/ref/tree and actual files; gh metadata and VERSION alone are insufficient. Verified identical tree: SKIP. Collision, user changes, different source, unknown version or concurrent writer: BLOCKED for that skill. Do not use update --unpin, --all or --force against a working profile. Missing skill: `gh skill install Sashido01/TESSERA skills/<id> --pin refs/tags/<id>/vX.Y.Z --dir <empty-staging>`. Verify staging (including gh frontmatter) before placement. Do not call main installation an exact pin.
5. Existing-tree update needs verified old snapshot, new staging, exclusive access, agreed backup and confirmed recovery. Until the production updater is accepted, do not apply CI fixture harness to user profiles; BLOCKED without a proven safe method. Preserve unrelated skills, TESSERA checkout, global settings, network/permissions, local data and backups.
6. Reverify only affected skills and discovery in a fresh client session. Report per skill SKIP/INSTALLED/UPDATED/BLOCKED, old→new, exact pin/tree, preservation/rollback; discovery separately. No full catalog unit suite, scanners or repeated cloning for routine updates. Profile update and release acceptance are separate tasks.

## Choose operation and skills

| Request | Read-only resolver arguments after `resolve --gh <absolute-path-to-gh>` |
| --- | --- |
| Install Microversion Release | `--operation install --skill microversion-release` |
| Update Audit and Cleanup | `--operation update --skill project-audit --skill project-cleanup` |
| Install all | `--operation install --all` |
| Update all (including new skills) | `--operation update --all` |

Install adds only missing selected skills: existing exact pin SKIP, different/unknown pin BLOCKED until an update is requested. Update checks selected skills, skips identical ones, replaces outdated ones only after proven preservation and adds missing ones in that selection. Never remove other skills or downgrade without separate agreement. `--version` means the exact catalog version, not an individual skill version; current addressed selection uses the associated independent pin. Empty, unknown, duplicate or mixed selection (skill and all) is refused without widening scope. Resolver does not request independent tags/content of unselected skills; common index schema validation remains. `--all` here is limited to the TESSERA catalog, not `gh skill update --all`. Operation is carried in read-only JSON; none of the four resolver commands installs files.

## Scope and acceptance

`catalog_index.py check --root <checkout>` checks the source index; resolve compares Git API evidence. No automatic installation or permission changes. Tag selection relies on trusted GitHub API and tag protections, not independent cryptographic attestation. Responses bounded after capture, per-call timeout and overall budget; not a memory sandbox. After resolving all pins, reread refs and, for automatic selection, the highest tag; observed ref movement, new tag, tree mismatch or truncated response means BLOCKED. Two observations, not an atomic transaction. Actual Codex/Harness acceptance required. One-link scenario, local-edit preservation, idempotent no-op, collisions and rollback are mandatory acceptance for 0.1.0.

**Verified baseline:** v0.0.95 has a verified index and all four independent pins. See [profile planning](docs/PROFILE_UPDATE_PLAN.en.md) for read-only UP02; no production apply authority. Live resolver and client acceptance remain open.
