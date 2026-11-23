#!/usr/bin/env python3
"""T09.07: optional GitHub Sigstore/SLSA provenance via official GitHub CLI.

Runs trusted installed gh attestation verify; does not sign or publish.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import subprocess
from typing import Any, Callable

try:
    from .release_publication import valid_repository, valid_tag
    from .release_assets import HARD_MAX_ASSET_BYTES, NAME, DIGEST, CHUNK
except ImportError:
    from release_publication import valid_repository, valid_tag
    from release_assets import HARD_MAX_ASSET_BYTES, NAME, DIGEST, CHUNK

SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
WORKFLOW = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\.ya?ml\Z")
PREDICATE = "https://slsa.dev/provenance/v1"
MAX_CLI_OUTPUT = 2 * 1024 * 1024


class ProvenanceError(ValueError):
    """Safe, machine-readable reason for failed provenance verification."""


def safe_signer_workflow(repo: str, signer: str) -> None:
    """Only a specific workflow belonging to the exact trusted GitHub repo."""
    valid_repository(repo)
    root = repo + "/.github/workflows/"
    if not isinstance(signer, str) or not signer.startswith(root):
        raise ProvenanceError("PROVENANCE_SIGNER_MISMATCH")
    if WORKFLOW.fullmatch(signer[len(root):]) is None:
        raise ProvenanceError("PROVENANCE_SIGNER_INVALID")


def local_file_evidence(
    file: pathlib.Path,
    *,
    metadata: dict[str, Any],
    limit: int,
) -> dict[str, Any]:
    """Independently hash local bytes against published GitHub asset metadata."""
    if type(limit) is not int or not 1 <= limit <= HARD_MAX_ASSET_BYTES:
        raise ProvenanceError("PROVENANCE_LIMIT_INVALID")
    if not isinstance(metadata, dict):
        raise ProvenanceError("PROVENANCE_METADATA_INVALID")
    name, size, digest = (
        metadata.get("name"), metadata.get("size"), metadata.get("reported_digest")
    )
    if not isinstance(name, str) or NAME.fullmatch(name) is None:
        raise ProvenanceError("PROVENANCE_ASSET_NAME_INVALID")
    if type(size) is not int or not 1 <= size <= limit:
        raise ProvenanceError("PROVENANCE_ASSET_SIZE_INVALID")
    if not isinstance(digest, str) or DIGEST.fullmatch(digest) is None:
        raise ProvenanceError("PROVENANCE_EXPECTED_DIGEST_MISSING")
    try:
        if file.is_symlink() or not file.is_file() or file.name != name:
            raise ProvenanceError("PROVENANCE_FILE_MISMATCH")
        if file.stat().st_size != size:
            raise ProvenanceError("PROVENANCE_FILE_SIZE_MISMATCH")
        hashed = hashlib.sha256()
        count = 0
        with file.open("rb") as stream:
            while True:
                part = stream.read(CHUNK)
                if not part:
                    break
                count += len(part)
                if count > size or count > limit:
                    raise ProvenanceError("PROVENANCE_FILE_TOO_LARGE")
                hashed.update(part)
        if count != size:
            raise ProvenanceError("PROVENANCE_FILE_SIZE_MISMATCH")
        observed = "sha256:" + hashed.hexdigest()
        if observed != digest:
            raise ProvenanceError("PROVENANCE_FILE_DIGEST_MISMATCH")
    except OSError as exc:
        raise ProvenanceError("PROVENANCE_FILE_UNREADABLE") from exc
    return {"name": name, "bytes_verified": count, "sha256": observed}


def verify_gh_json(data: str, *, expected_digest: str) -> bool:
    """Check successful CLI output still contains the expected signed subject."""
    if not isinstance(data, str) or len(data.encode("utf-8")) > MAX_CLI_OUTPUT:
        return False
    try:
        records = json.loads(data)
    except (ValueError, UnicodeError):
        return False
    if not isinstance(records, list) or not records:
        return False
    for record in records:
        if not isinstance(record, dict):
            continue
        result = record.get("verificationResult")
        if not isinstance(result, dict):
            continue
        signature = result.get("signature")
        statement = result.get("statement")
        if not isinstance(signature, dict) or not signature.get("certificate"):
            continue
        if not isinstance(statement, dict) or statement.get("predicateType") != PREDICATE:
            continue
        subjects = statement.get("subject")
        if not isinstance(subjects, list):
            continue
        if any(
            isinstance(subject, dict)
            and isinstance(subject.get("digest"), dict)
            and subject["digest"].get("sha256") == expected_digest.removeprefix("sha256:")
            for subject in subjects
        ):
            return True
    return False


def verify_release_provenance(
    *,
    repository: str,
    tag: str,
    source_commit: str,
    signer_workflow: str,
    artifact_file: pathlib.Path,
    asset_metadata: dict[str, Any],
    max_bytes: int = 64 * 1024 * 1024,
    timeout_seconds: int = 60,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    """Fail closed. The CLI verifies the Sigstore attestation and identities.

    Runner injection is only for unit tests, not a public policy bypass.
    """
    valid_repository(repository)
    valid_tag(tag)
    safe_signer_workflow(repository, signer_workflow)
    if not isinstance(source_commit, str) or SHA.fullmatch(source_commit) is None:
        raise ProvenanceError("PROVENANCE_SOURCE_SHA_INVALID")
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 120:
        raise ProvenanceError("PROVENANCE_TIMEOUT_INVALID")
    file = pathlib.Path(artifact_file)
    byte_proof = local_file_evidence(file, metadata=asset_metadata, limit=max_bytes)
    result: dict[str, Any] = {
        "schema_version": 1,
        "provenance_status": "BLOCKED",
        "artifact_provenance": "NOT_VERIFIED",
        "local_artifact_integrity": "PASS",
        "asset_name": byte_proof["name"],
        "asset_sha256": byte_proof["sha256"],
        "bytes_verified": byte_proof["bytes_verified"],
        "source_commit_sha": source_commit,
        "source_ref": "refs/tags/" + tag,
        "signer_workflow": signer_workflow,
        "verifier": "gh attestation verify",
        "signed_attestation": False,
        "application_release_readiness": "NOT_VERIFIED",
        "problems": [],
    }
    argv = [
        "gh", "attestation", "verify", str(file),
        "--repo", repository,
        "--source-digest", source_commit,
        "--source-ref", "refs/tags/" + tag,
        "--signer-workflow", signer_workflow,
        "--predicate-type", PREDICATE,
        "--deny-self-hosted-runners",
        "--format", "json",
    ]
    env = os.environ.copy()
    env["GH_PROMPT_DISABLED"] = "1"
    env["GH_HOST"] = "github.com"
    try:
        completed = runner(
            argv, text=True, encoding="utf-8", capture_output=True,
            stdin=subprocess.DEVNULL, timeout=timeout_seconds, check=False, env=env,
        )
    except subprocess.TimeoutExpired:
        result["problems"].append("PROVENANCE_VERIFIER_TIMEOUT")
        return result
    except (OSError, UnicodeError):
        result["problems"].append("PROVENANCE_VERIFIER_UNAVAILABLE")
        return result
    if completed.returncode != 0:
        result["problems"].append("PROVENANCE_SIGNATURE_VERIFICATION_FAILED")
        return result
    if not verify_gh_json(completed.stdout, expected_digest=byte_proof["sha256"]):
        result["problems"].append("PROVENANCE_VERIFIER_OUTPUT_INVALID")
        return result
    try:
        current = local_file_evidence(file, metadata=asset_metadata, limit=max_bytes)
    except ProvenanceError:
        result["problems"].append("PROVENANCE_ARTIFACT_CHANGED_DURING_VERIFICATION")
        return result
    if current != byte_proof:
        result["problems"].append("PROVENANCE_ARTIFACT_CHANGED_DURING_VERIFICATION")
        return result
    result["provenance_status"] = "PASS"
    result["artifact_provenance"] = "GITHUB_ATTESTATION_VERIFIED"
    result["signed_attestation"] = True
    return result
