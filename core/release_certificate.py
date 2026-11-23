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
    issues = report.get("problems", [])
    if not isinstance(issues, list):
        issues = ["CERTIFICATE_INVALID_PROBLEMS"]
    if report.get("evidence_status") == "BLOCKED" or issues:
        status = "BLOCKED"
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
            "asset_content_verification": "NOT_PERFORMED",
        },
        "publication_evidence_status": status,
        "application_release_readiness": "NOT_VERIFIED",
        "signed": False,
        "problems": sorted(set(str(item) for item in issues)),
        "limitations": [
            "SHA-256 is a reproducibility checksum, not a digital signature",
            "Source release publication does not prove installation or application delivery",
            "GitHub release asset bytes and digests were not independently downloaded and checked",
        ],
    }
    encoded = json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        **evidence,
        "evidence_sha256": "sha256:" + hashlib.sha256(encoded).hexdigest(),
    }
