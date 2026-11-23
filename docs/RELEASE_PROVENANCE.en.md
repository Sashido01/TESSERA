# T09.07 — verify artifact provenance with signed GitHub attestations

[Русский — оригинал](RELEASE_PROVENANCE.md) | **English — translation**

## Purpose

TESSERA uses the **official GitHub CLI** and **GitHub artifact attestations (Sigstore / SLSA provenance)** instead of implementing custom cryptography. `core/release_provenance.py` verifies a cryptographically signed provenance claim for an exact artifact and binds it to the expected source commit, Git tag, repository, and approved signing workflow.

Verification is explicit and only applicable after a project actually publishes a GitHub Release with an attached asset **and generates an attestation for that artifact**. A Git tag, passing tests, or reported asset digest alone is insufficient. TESSERA had no GitHub Releases when T09.07 was prepared; no live signed project artifact is confirmed.

## Trust model and checked evidence

Verification has two separate stages:

1. A **local artifact file** obtained by the user from the exact GitHub Release is opened. Its name, byte count, and independently computed SHA-256 are matched against the verified release asset metadata. The default limit is 64 MiB and the hard maximum is 512 MiB; bytes are read in bounded chunks. Symlinks or mismatched names, sizes, and digests are rejected.
2. `gh attestation verify` runs against **the same file**, constrained by exact `--repo`, `--source-digest` (full source commit SHA), `--source-ref refs/tags/<version>`, `--signer-workflow`, and predicate `https://slsa.dev/provenance/v1`. Self-hosted runner attestations are excluded with `--deny-self-hosted-runners`. The official CLI validates certificates and cryptographic signatures against GitHub/Sigstore trust. TESSERA also checks the signed subject SHA-256 against the local artifact.

**A specific signing workflow is mandatory:** its full identity must be `owner/repository/.github/workflows/build.yml` within the same trusted repository. Generic passing jobs and arbitrary signer workflows are not accepted. Actual signing requires a separately designed build workflow triggered from the verified tag and protected from unreviewed Pull Request modifications.

**Trust limitation:** a valid attestation proves that the claim was signed under the expected GitHub Actions identity. It does not independently prove that software is safe, a build fully reproducible, or every descriptive field of the `predicate` true. Workflow execution may influence those fields.

## Usage

The official `gh` with `gh attestation verify` must be installed and public GitHub attestation access must be available. Run in a trusted local environment; TESSERA does not silently install the CLI or save tokens.

```bash
# Default: local-only, no attestation network requests
python core/release_report.py --repo . --version 0.0.13

# After a real Release, a downloaded artifact, and a trusted signing workflow exist:
python core/release_report.py --repo . --version 0.0.13 \
  --verify-publication --verify-provenance \
  --github-repo owner/repository \
  --artifact-file <local-asset-file> \
  --signer-workflow owner/repository/.github/workflows/build.yml \
  --format certificate
```

This is **syntax guidance**, not a claim that TESSERA currently has such a `build.yml` or signed artifact. The file basename must match exactly one attached GitHub Release asset. To verify the remote tag and completed CI as well, explicitly add `--verify-remote --verify-ci --run-id <completed-run-id>`.

## Explicit failure cases

- `PROVENANCE_REQUIRES_PUBLICATION_VERIFICATION`: no verified source publication requested.
- `PROVENANCE_REQUIRES_FILE_AND_SIGNER`: artifact or trusted signer was omitted.
- `PROVENANCE_RELEASE_ASSET_MISSING`: no unique attached asset matches.
- `PROVENANCE_FILE_DIGEST_MISMATCH`, `PROVENANCE_FILE_SIZE_MISMATCH`, `PROVENANCE_FILE_MISMATCH`: wrong file or bytes.
- `PROVENANCE_VERIFIER_UNAVAILABLE`, `PROVENANCE_VERIFIER_TIMEOUT`, `PROVENANCE_SIGNATURE_VERIFICATION_FAILED`, `PROVENANCE_VERIFIER_OUTPUT_INVALID`: missing verifier, timeout, rejected signature, or malformed verification evidence.
- `PROVENANCE_ARTIFACT_CHANGED_DURING_VERIFICATION`: artifact changed while verification was running.

The final report intentionally omits CLI error details, secrets, local absolute file paths, and full signed claim contents.

## Evidence report and certificate

`core/release_report.py` adds `provenance_status`, `local_artifact_integrity`, `provenance_signer_workflow`, `provenance_source_commit`, `provenance_source_ref`, and `provenance_verified_asset`, without exposing local paths.

`core/release_certificate.py` still reports `signed=false`: **the final evidence certificate itself remains unsigned**. Separate `attestation_signature_verified=true` applies only to the cryptographically verified GitHub attestation. `SOURCE_ASSET_ATTESTATION_VERIFIED` requires a published GitHub Release, matching remote tag, successful completed CI, correct local bytes, and valid provenance signature. Even then, `application_release_readiness=NOT_VERIFIED`.

With no real signed TESSERA assets, this end-to-end status has not been observed in production. Unit tests simulate the official CLI's outcomes; they **do not substitute for real certificates**.

## Remaining work for full T09

1. Design a trusted build workflow that produces an artifact from a fixed release tag; pin actions to SHAs and minimize privileges.
2. Enable real GitHub artifact attestation only after a genuine build exists. The signing job needs `id-token: write`, `attestations: write`, and `contents: read`.
3. Verify the full real chain: tag → build → attestation → asset publication → download → independent gh verification. Do not publish a fake release for testing.
4. Add safe concurrent release coordination and independently prove application readiness. T09 stays PARTIAL.

References: [GitHub artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations), [official gh attestation verify](https://cli.github.com/manual/gh_attestation_verify).
