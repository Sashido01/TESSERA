# T09.06 — independent GitHub Release asset byte verification

[Русский — оригинал](RELEASE_ASSETS.md) | **English — translation**

## Purpose

`core/release_assets.py` downloads an asset of an actually published **public** GitHub Release **only after explicit authorization** and stream-verifies its byte length and SHA-256 against GitHub REST API metadata. Results are independent of any AI agent's assertions. No files are written to disk and no Git tags are modified.

**Important:** both the `size` and `digest` metadata and the asset itself come from GitHub. Matching downloaded bytes to those fields proves transfer integrity relative to the fetched metadata; it **does not provide an independent developer signature, source provenance, reproducible build proof, or malware assurance**.

## Usage

```bash
# Local Git and plan only; no network/download
python core/release_report.py --repo . --version 0.0.12

# Published release metadata only; no asset download
python core/release_report.py --repo . --version 0.0.12 \
  --verify-publication --github-repo owner/repository

# Actual bytes check; requires a published Release with attached assets
python core/release_report.py --repo . --version 0.0.12 \
  --verify-publication --verify-assets --github-repo owner/repository \
  --format certificate

# Larger asset, if justified: explicit size cap in bytes
python core/release_report.py --repo . --version 0.0.12 \
  --verify-publication --verify-assets --github-repo owner/repository \
  --max-asset-bytes 134217728
```

`owner/repository`, versions, and paths are examples, not any owner's local configuration. Review the trusted Git remote and selected publication first. `--verify-assets` requires `--verify-publication`. For complete tag/CI evidence, additionally request `--verify-remote` and `--verify-ci --run-id <id>` **after** GitHub Actions has completed.

## Verified conditions

1. A published, non-draft, non-prerelease Release must exist; the selected Git remote must match the explicit GitHub repository.
2. Asset URLs must match `https://github.com/{owner}/{repo}/releases/download/{tag}/{filename}` with checked components. HTTPS redirects are allowed only to known GitHub CDN hosts: `github.com`, `release-assets.githubusercontent.com`, `objects.githubusercontent.com`. Unknown hosts, HTTP, embedded credentials, or a mismatched tag are blocked.
3. Each asset requires `state=uploaded`, a positive size, and `digest=sha256:<64 hex>`. Missing GitHub digests cause BLOCKED, not a guessed hash.
4. Bytes are streamed in 64 KiB chunks; only the hash state and one small chunk reside in memory. The actual byte count, size cap, and final SHA-256 are verified.
5. The default per-asset limit is 64 MiB, hard maximum 512 MiB; at most 20 assets are verified per run. Processing stops at the first failure.
6. Network errors, corruption, truncated/oversized bodies, and SHA mismatches result in `asset_content_verification=BLOCKED`.

A Release with no attached assets returns **`NO_RELEASE_ASSETS`**, not PASS. GitHub-generated source archives are not attached release assets and are not verified by this component.

## Evidence certificate

The report and `--format certificate` now include `publication_asset_content_verification`, `verified_assets` with actual byte counts and SHA-256 values, `artifact_provenance=NOT_VERIFIED`, and `application_release_readiness=NOT_VERIFIED`.

Only after at least one asset passes byte verification, the corresponding public GitHub Release is verified, the annotated tag object matches on remote, and a completed CI run has passed may the certificate state be **`SOURCE_ASSETS_BYTES_VERIFIED`**. This means **downloaded bytes match GitHub metadata**, not that the software is installed or proven safe. The module never asserts an application-level `RELEASED` state.

`evidence_sha256` is a checksum of the **JSON certificate itself**, unsigned and not tamperproof.

## Tests and remaining limits

Tests cover matching and corrupted bytes, truncated/oversized responses, missing digests, unsafe URLs/redirects, size caps, duplicate names, missing assets, and unverified publication. Tests use local byte streams; they need **no paid infrastructure, external downloads, or modifications to published tags**.

When this stage was prepared, TESSERA had no actually published GitHub Release with attached files. Therefore **live end-to-end asset downloading on TESSERA remains NOT_VERIFIED**. Overall T09 remains PARTIAL: independent artifact provenance attestation, safe concurrent releases, and proof of executable software behavior are still missing.

Asset metadata reference: [official GitHub REST API docs](https://docs.github.com/en/rest/releases/assets).
