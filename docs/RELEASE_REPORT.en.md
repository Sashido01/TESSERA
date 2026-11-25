# T09.03 — remote Git tags and evidence-based reports

[Русский — оригинал](RELEASE_REPORT.md) | **English — translation**

## Purpose

Release Core now contains three independent components:

- [T09.01](RELEASE_CORE.en.md): `core/release_inspect.py` validates a local annotated tag, the version stored in an exact commit, and its SHA.
- [T09.02](RELEASE_PREFLIGHT.en.md): `core/release_preflight.py` validates VERSION, CHANGELOG, and a build/test plan. Commands execute only with explicit authorization.
- **T09.03**: `core/release_remote.py` compares the annotated Git tag **object SHA** on a remote to the local object; `core/release_report.py` emits JSON or Markdown from actual observations.

These components are independent of Codex, Harness, Claude Code, and Hermes. A Git tag **does not** establish that an application has been published.

## Commands

```bash
# Only local Git and a planned preflight; no network or test execution
python core/release_report.py --repo . --version 0.0.9

# Explicit remote verification against a previously trusted Git remote
python core/release_report.py --repo . --version 0.0.9 --verify-remote --remote origin

# Human-readable report, with no remote query
python core/release_report.py --repo . --version 0.0.9 --format markdown

# Trusted projects only: explicitly run approved release-checks.json commands
python core/release_report.py --repo . --version 0.0.9 --execute-checks

# Historical release: verify a full commit SHA without rerunning old tests
python core/release_report.py --repo . --version 0.0.8 --commit <full-commit-sha> --verify-remote
```

Replace `<...>` placeholders with actual local values, without publishing private paths. A local Git repository is required. Network access happens **only** when `--verify-remote` is selected. Build/test commands execute **only** with `--execute-checks` and must be reviewed and authorized for the trusted project. Both options can be combined; never run untrusted Pull Request commands automatically.

## What remote proof means

The verifier asks the named remote for the exact `refs/tags/<version>` via `git ls-remote --refs --tags`. Annotated tags are compared using the **tag object SHA**, not merely the commit SHA they point to. The local version and exact target commit SHA must also be valid.

- `PASS`: the remote reported the same annotated tag object at the time of the request.
- `REMOTE_TAG_MISSING`: the exact ref was absent.
- `REMOTE_TAG_OBJECT_MISMATCH`: the ref points to a different tag object, potentially pointing to the same commit.
- `REMOTE_QUERY_FAILED` / `REMOTE_QUERY_TIMEOUT`: transport verification failed, not proof that a tag is absent.
- `LOCAL_TAG_INVALID`: local verification failed; no remote query was made.

The named **trusted Git remote** can be GitHub or another Git server. The tool cannot independently establish server identity outside its existing transport and trust configuration; it does not create a GitHub Release or verify an installable package.

## Report contract

JSON includes `local_tag_status`, `preflight_status`, `checks_status`, `remote_tag_status`, `stage`, `evidence_status`, `release_readiness`, `problems`, and the exact commit SHA.

- `evidence_status=PASS`: **all requested checks** passed; checks not requested remain `NOT_CHECKED` or `NOT_RUN`.
- `evidence_status=BLOCKED`: at least one requested verification failed.
- `release_readiness=NOT_VERIFIED`: always, including when local checks and the remote tag pass.
- `remote_publication=TAG_REF_VERIFIED`: only the remote Git ref was verified, not a published application.
- `github_release=NOT_CHECKED`: no GitHub Release verification.
- Historical commits use `preflight_status=NOT_CHECKED_HISTORICAL`. Running historical checks against current HEAD is forbidden.

Exit 0 means `evidence_status=PASS`; exit 1 means BLOCKED. Neither exit code represents a final application release decision.

## Completed GitHub Actions verification — T09.04

See [Release CI](RELEASE_CI.en.md). After an entire workflow finishes, add explicit `--verify-ci --github-repo owner/repository --run-id 123456789` options. The verifier checks commit SHA, repository name, push to main, expected workflow, and both required jobs. Reports include `ci_status` and verified run identifiers. **Without `--verify-ci`, there is no API request.** Even `CI_VERIFIED` and `CI_AND_REMOTE_TAG_VERIFIED` do not imply a published product: `release_readiness=NOT_VERIFIED`.

## Separate publication verification — T09.05

See [Release Publication](RELEASE_PUBLICATION.en.md). `--verify-publication` requires a trusted `--github-repo`, checks the Git remote identity, and queries a genuinely **published** GitHub Release. `--format certificate` produces an unsigned evidence certificate with a reproducible SHA-256 of its own fields. `SOURCE_RELEASE_PUBLISHED` requires independently verified remote tag, completed CI, and GitHub Release metadata. Application `release_readiness` nevertheless remains `NOT_VERIFIED`.

## Actual asset bytes — T09.06

[RELEASE_ASSETS](RELEASE_ASSETS.en.md) introduces explicit `--verify-assets` after successful `--verify-publication`. Reports include `publication_asset_content_verification`, `verified_assets`, and `artifact_provenance=NOT_VERIFIED`. Certificate status `SOURCE_ASSETS_BYTES_VERIFIED` additionally requires a completed CI, matching remote tag, published Release, and actual matching downloaded bytes. The certificate's own checksum is not a signature.

## Artifact provenance attestation — T09.07

See [RELEASE_PROVENANCE](RELEASE_PROVENANCE.en.md). Explicit `--verify-provenance` requires `--verify-publication`, a real local `--artifact-file`, and a trusted `--signer-workflow`. The module first verifies file bytes against GitHub Release metadata, then invokes official `gh attestation verify` constrained by exact source commit SHA, `refs/tags/<version>`, and signer identity. No local path is included in the report. `provenance_status=PASS` proves the verified signed claim, not application readiness.

## Security and acceptance

- No Git fetch, push, tag creation, or tag updates.
- Queries use a configured remote with noninteractive credentials and a bounded timeout; `protocol.ext` is disabled.
- The exact ref name and SHA format are validated; transport failures are not confused with missing tags. Credentials and stderr are excluded from reports.
- TESSERA's CI runs the report **after** an annotated tag is confirmed in its dedicated GitHub Actions job. Pull Request validation does not require the future tag.
- Remote tests use temporary local bare Git repositories, never TESSERA's published history.

**Limits:** T09 remains PARTIAL. Independent external CI proof, concurrency serialization, artifact signatures, and a final `RELEASED` controller are not implemented. The T09.02 build-plan check does not prove the adequacy of a project's test suite.

## Independent skill — T16 candidate

`--skill <skill-name>` selects `skills/<skill-name>/VERSION` and annotated tag `<skill-name>/vX.Y.Z`. For current HEAD supply a separate trusted `--config` whose version_file and both release_notes refer to that skill's VERSION and CHANGELOG. Root plan is rejected. Historical reports do not execute checks. `--skill` and `--prefix` are mutually exclusive; legacy `--prefix` reads the root VERSION. Remote checks the exact tag object. Plans and tests do not prove publication or activation. Live CI and independent tags remain open.

### Local Microversion Release plan

`python core/release_preflight.py --repo . --skill microversion-release --version 0.0.1 --config release-checks-microversion-release.json --plan` checks the plan without execution. Use `--execute` only on an authorized trusted clean checkout. Uses the shared runner for one skill; zero ordinary successful tests fails. No separate binary build; catalog ZIP, publication and activation remain separate. This plan still requires CI; adding it does not establish a namespaced tag.

### Bounded skill test execution — TD12

Shared runner `python tools/run_skill_tests.py` and selection `--skill microversion-release` use a separate process per skill with a default 120-second limit (`--timeout` 1–900 s). A timeout fails the result; independent skills continue. Local Linux checks: 13/13 (10 existing, three new), 21.170 s. This bounds the immediate test process, not a sandbox or a guarantee of descendant termination; output volume is unbounded. Trusted checkout, outer preflight and CI timeouts remain required. Windows and full candidate CI are unverified. TD12 PARTIAL.
