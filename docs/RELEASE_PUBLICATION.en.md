# T09.05 — publication verification and evidence certificate

[Русский — оригинал](RELEASE_PUBLICATION.md) | **English — translation**

## What is being proved

A public Agent Skills catalog must distinguish a **commit with passing CI**, an **annotated Git tag**, a **GitHub Release of source code**, and **verified binary/installable artifacts**. These are separate facts. A `vX.Y.Z` Git tag does not establish a GitHub Release. A GitHub Release does not prove application delivery or operation.

As of 23 November 2026, public `Sashido01/TESSERA` has annotated tags through `v0.0.10`, but **no GitHub Releases**. Previous microversions must not be represented as published GitHub Releases.

The implementation introduces `core/release_publication.py` (read-only GitHub Release metadata verification) and `core/release_certificate.py` (deterministic unsigned evidence manifest). Neither component publishes GitHub Releases automatically.

## Two types of publication evidence

**Git tag and CI:** `TAG_AND_CI_VERIFIED` means an annotated tag object was verified on the trusted remote and a completed GitHub Actions run passed for the exact commit. It is not a GitHub Release.

**Source publication:** `SOURCE_RELEASE_PUBLISHED` can be recorded in the certificate only when an actually published GitHub Release for the same tag is also verified, neither draft nor prerelease, with a matching trusted GitHub remote and all prior checks. GitHub provides a source archive for public Releases; **this tool does not download or independently verify archive bytes**. For executable applications, a Release page still does not prove installation, binary signatures, or correct files.

## Commands

From the target Git repository root:

```bash
# No network by default: local evidence report.
python core/release_report.py --repo . --version 0.0.11

# Query a published GitHub Release and independent evidence after completed CI.
python core/release_report.py --repo . --version 0.0.11 \
  --verify-remote --verify-ci --verify-publication \
  --github-repo owner/repository --run-id 123456789 \
  --format certificate

# Human-readable output without network calls.
python core/release_report.py --repo . --version 0.0.11 --format markdown
```

These are syntax examples: substitute actual trusted repository, completed run ID, and published version for `owner/repository`, `123456789`, and `0.0.11`. No API calls, Git remote queries, or project command execution occur by default. Executing configured release commands still requires a separate `--execute-checks`. Never run untrusted Pull Request commands automatically.

## Independent GitHub Release check

Explicit `--verify-publication` performs a GET request to official `api.github.com/repos/{owner}/{repo}/releases/tags/{tag}` and checks:

- exact tag and positive release identifier;
- `draft=false`, `prerelease=false`, a valid `published_at`, and the expected GitHub Release URL;
- asset list metadata: unique names, `state=uploaded`, positive size and syntactically valid `digest` when present;
- binding between `--github-repo` and the actual trusted Git remote `origin` (or a chosen named remote) over GitHub HTTPS/SSH;
- compatibility with an annotated local tag, remote object verification, and completed CI evidence.

**Important:** GitHub's `target_commitish` is not independent commit proof; it may be a branch name rather than the target SHA. Commit proof comes from separately validated Git tag objects.

If the Release is missing or inaccessible, the API fails or returns incomplete data, the result is `PUBLICATION_QUERY_FAILED_OR_MISSING / BLOCKED`. Drafts and prereleases are not accepted as stable source publications.

## Evidence certificate

`--format certificate` outputs schema version 1 JSON containing version, commit SHA, tag object SHA, CI and Git remote results, GitHub Release metadata, and `publication_evidence_status`, `application_release_readiness`, and `signed`.

- `SOURCE_RELEASE_PUBLISHED`: source GitHub Release, completed CI, and matching remote annotated tag object all verified.
- `TAG_AND_CI_VERIFIED`: CI and remote tag verified, with no request for publication verification.
- `INCOMPLETE`: required evidence for the selected scope is missing.
- `BLOCKED`: contradictions or failed requested checks.

`evidence_sha256` is a **SHA-256 of the canonical serialization of certificate fields, excluding the checksum itself**. It checks reproducibility; **it is not a digital signature or tamper-proof attestation**. GitHub's asset digest metadata is not equivalent to independently downloading and verifying asset bytes; `asset_content_verification=NOT_PERFORMED` remains explicit.

**Always:** `application_release_readiness=NOT_VERIFIED`. Even a published source release does not establish a validated executable application release.

## Actual asset bytes — T09.06

See [RELEASE_ASSETS](RELEASE_ASSETS.en.md). An additional explicit `--verify-assets` option downloads attached files of a published Release and independently computes downloaded byte counts and SHA-256 against GitHub metadata. It is **disabled by default**, requires `--verify-publication`, and enforces size limits and trusted HTTPS hosts. `asset_content_verification=PASS` does not establish build provenance. No attached files produce `NO_RELEASE_ASSETS`, not PASS.

## Safety, limitations and future work

- No Git writes, tag creation, GitHub Release publication, artifact uploads, or automatic API requests.
- GitHub API calls require explicit flags; there is no mandatory paid API and no tokens in the certificate.
- Git remote identity is checked against the canonical `github.com/owner/repository`; local bare Git and other hosts cannot masquerade as GitHub.
- No real TESSERA GitHub Release has been created, nor is one published automatically in this stage. Positive/negative unit cases use fixture metadata.
- Future work: independent asset byte/hash validation, cryptographic signing/attestation, reproducible builds and concurrent release control.

**Status:** T09.05 implementation and unit verification; testing against a real published GitHub Release is `NOT_VERIFIED`. Overall T09 remains `PARTIAL`.
