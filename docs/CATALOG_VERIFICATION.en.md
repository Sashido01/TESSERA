# T09.09 — independent offline catalog ZIP verification

[Русский — оригинал](CATALOG_VERIFICATION.md) | **English — translation** ([this file](CATALOG_VERIFICATION.en.md))

## Purpose

`tools/verify_catalog_package.py` verifies the actual bytes of an already obtained TESSERA source ZIP. It requires no network, credentials, GitHub CLI, extraction, or execution of archive contents. The `--version` and `--source-commit` arguments must come from independent evidence, never solely from the untrusted manifest.

~~~bash
python tools/verify_catalog_package.py \
  --archive TESSERA-catalog-v0.0.15.zip \
  --version 0.0.15 \
  --source-commit <full-release-commit-SHA>
~~~

This is an example for an existing file, not proof of an actual signing run or GitHub Release. First independently establish the exact remote tag and commit.

## Validation

- A regular ZIP file, not a symlink, up to 64 MiB.
- All entries must be under the exact `TESSERA-X.Y.Z/` prefix. Traversal, absolute paths, backslashes, duplicates, symlinks, directories, encryption, and compression are rejected.
- Up to 2048 entries, 4 MiB per file, and 1 MiB for the manifest, with no extraction to disk.
- `MANIFEST.json` must have the supported schema, exact version, and externally supplied full commit SHA. The member set must match the manifest exactly.
- Every file's actual size and SHA-256 must match. LICENSE, both README files, VERSION, and at least one `skills/<name>/SKILL.md` are mandatory.
- A passing result contains the ZIP SHA-256 and file count, with `status=PASS`, `attestation=NOT_VERIFIED`, and `publication=NOT_VERIFIED`.

Any failure produces `BLOCKED` and exit status 1. No absolute user path, file content, or secret appears in output. These checks prove **internal consistency against a manifest**, not author identity: an attacker can modify both the archive and the manifest.

## Separate provenance proof

Authenticity requires independent validation of the annotated `vX.Y.Z` tag, exact commit SHA, and `gh attestation verify` with strict `--repo`, `--source-ref`, `--source-digest`, `--signer-workflow`, and denial of self-hosted runners. The existing `core/release_provenance.py` binds signatures to **published GitHub Release assets** and their metadata. A temporary GitHub Actions Artifact is a separate distribution channel, not yet integrated into this contract.

**Never** infer SIGNED, PUBLISHED, RELEASED, or downstream application readiness from `status=PASS` alone. Live Codex/Harness/Claude/Hermes integration is outside the scope of this verifier.

**CLI security:** use `gh 2.102.0+` for actual `gh attestation verify` and `gh run download`. Older versions had published signer/ref verification flaws and symlink download issues. See [RELEASE_PROVENANCE](RELEASE_PROVENANCE.en.md).

## Acceptance boundaries

A positive fixture uses the actual packager. Negative cases include byte tampering, wrong SHA/version, corrupted ZIP, missing manifest, duplicates, traversal, absolute paths, symlinks, and compression. T09 remains PARTIAL pending a live signed build, independent verification, and the remaining Release Core requirements.

## Update tools in the source ZIP (0.0.97 candidate)

Starting at 0.0.97 the ZIP contract requires CATALOG.json, both UPDATE and profile-plan documents, and the three read-only UP01/UP02 tools. Verification rejects missing/extra files and inconsistent catalog versions even with a recomputed manifest. Older ZIPs retain their legacy contract. The ZIP remains a runtime subset: skill tests are excluded, so it is not a raw Git tree or staging for skill_tree.py. Use verifier code from an independently trusted checkout, never execute code from an unverified ZIP. Attestation, live resolver, gh metadata, apply and rollback remain separate open tasks.

## Verify gh staging metadata (0.0.98 candidate)

0.0.97 main 4f0e5ec0175e42bf67afceef3360497d1261d140, CI 46062411446 SUCCESS, annotated tag object 726389b4f834b243413ab84ef36d9379bbd1684d.

UP02.02: read-only gh_stage binds supplied raw Git tree to installed staging and checks the exact five github-* metadata fields, original frontmatter fields, body, other file bytes, modes and stage fingerprint. Narrow YAML subset (plain/simple quoted scalars and >- without complex constructs); unsupported forms BLOCKED. Actual gh serialization, lockfile, live refs, apply authorization, atomicity and rollback NOT_VERIFIED. From 0.0.98 the tool is required in ZIP; 0.0.97 remains compatible. Ten fixture tests and package gate; native/full CI pending.
