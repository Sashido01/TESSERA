#!/usr/bin/env python3
"""T09.05: deterministic, unsigned evidence manifest (not an attestation)."""
from __future__ import annotations

import hashlib
import json
from typing import Any


def make_certificate(report: dict[str, Any]) -> dict[str, Any]:
    """Create a stable digest over factual fields, without claiming signature."""
    publication = report.get("publication_status", "NOT_CHECKED")
    remote = report.get("remote_tag_status", "NOT_CHECKED")
    ci = report.get("ci_status", "NOT_CHECKED")
    asset_status = report.get("publication_asset_content_verification", "NOT_PERFORMED")
    provenance_status = report.get("provenance_status", "NOT_CHECKED")
    local_integrity = report.get("local_artifact_integrity", "NOT_CHECKED")
    issues = report.get("problems", [])
    if not isinstance(issues, list):
        issues = ["CERTIFICATE_INVALID_PROBLEMS"]
    if (report.get("evidence_status") == "BLOCKED" or issues
            or asset_status == "BLOCKED" or provenance_status == "BLOCKED"):
        status = "BLOCKED"
    elif (publication == "SOURCE_RELEASE_PUBLISHED" and remote == "PASS"
          and ci == "PASS" and provenance_status == "PASS"
          and local_integrity == "PASS"):
        status = "SOURCE_ASSET_ATTESTATION_VERIFIED"
    elif (publication == "SOURCE_RELEASE_PUBLISHED" and remote == "PASS"
          and ci == "PASS" and asset_status == "PASS"):
        status = "SOURCE_ASSETS_BYTES_VERIFIED"
    elif publication == "SOURCE_RELEASE_PUBLISHED" and remote == "PASS" and ci == "PASS":
        status = "SOURCE_RELEASE_PUBLISHED"
    elif publication not in ("NOT_CHECKED",):
        status = "INCOMPLETE"
    elif remote == "PASS" and ci == "PASS":
        status = "TAG_AND_CI_VERIFIED"
    else:
        status = "INCOMPLETE"

    evidence: dict[str, Any] = {
        "schema_version": 1,
        "subject": {
            "version": report.get("requested_version"),
            "tag": report.get("requested_tag"),
            "commit_sha": report.get("target_commit_sha"),
            "tag_object_sha": report.get("local_tag_object_sha"),
        },
        "checks": {
            "local_tag": report.get("local_tag_status"),
            "remote_tag": remote,
            "ci": ci,
            "ci_run_id": report.get("ci_run_id"),
            "ci_run_attempt": report.get("ci_run_attempt"),
            "release_metadata": publication,
            "release_id": report.get("publication_release_id"),
            "release_url": report.get("publication_url"),
            "asset_content_verification": asset_status,
            "verified_assets": report.get("verified_assets", []),
            "artifact_provenance": report.get("artifact_provenance", "NOT_VERIFIED"),
            "provenance_status": provenance_status,
            "provenance_signer_workflow": report.get("provenance_signer_workflow"),
            "provenance_source_commit": report.get("provenance_source_commit"),
            "provenance_source_ref": report.get("provenance_source_ref"),
            "provenance_verified_asset": report.get("provenance_verified_asset"),
            "local_artifact_integrity": local_integrity,
            "attestation_signature_verified": provenance_status == "PASS",
        },
        "publication_evidence_status": status,
        "application_release_readiness": "NOT_VERIFIED",
        "signed": False,
        "problems": sorted(set(str(item) for item in issues)),
        "limitations": [
            "SHA-256 is a reproducibility checksum, not a digital signature",
            "Source release publication does not prove installation or application delivery",
            "Matching bytes to GitHub metadata is not a build attestation",
            "A verified workflow attestation does not prove build reproducibility or software safety",
        ],
    }
    encoded = json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        **evidence,
        "evidence_sha256": "sha256:" + hashlib.sha256(encoded).hexdigest(),
    }
