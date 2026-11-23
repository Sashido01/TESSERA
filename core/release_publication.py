#!/usr/bin/env python3
"""T09.05: inspect PUBLIC GitHub Release metadata without publishing anything.

A source-code GitHub Release is distinct from a Git tag and a downloadable,
verified application artifact. All requests are explicit and read-only.
"""
from __future__ import annotations

import datetime as dt
import pathlib
import re
import subprocess
import urllib.error
import urllib.parse
from typing import Any, Callable

try:
    from .release_ci import CIEvidenceError, REPOSITORY, get_public_json
    from .release_inspect import InspectionError, tag_name
except ImportError:
    from release_ci import CIEvidenceError, REPOSITORY, get_public_json
    from release_inspect import InspectionError, tag_name

TAG_PATTERN = re.compile(r"(?:[a-z0-9]+(?:-[a-z0-9]+)*/)?v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\Z")
SHA256 = re.compile(r"sha256:[0-9a-f]{64}\Z")


class PublicationError(InspectionError):
    """Invalid publication request or evidence."""


def valid_repository(repository: str) -> None:
    if not isinstance(repository, str) or REPOSITORY.fullmatch(repository) is None or ".." in repository:
        raise PublicationError("PUBLICATION_REPOSITORY_INVALID")



def verify_github_remote_identity(root: pathlib.Path, remote: str, repository: str) -> str:
    """Bind chosen Git remote to the explicit GitHub owner/repository."""
    valid_repository(repository)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", remote):
        return "BLOCKED"
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "remote", "get-url", remote],
            text=True, encoding="utf-8", capture_output=True, check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "BLOCKED"
    if result.returncode != 0:
        return "BLOCKED"
    address = result.stdout.strip()
    if address.startswith("git@github.com:"):
        path = address.removeprefix("git@github.com:")
    else:
        parts = urllib.parse.urlsplit(address)
        if (parts.scheme not in ("https", "ssh")
                or parts.hostname != "github.com"
                or parts.port is not None
                or parts.query or parts.fragment
                or (parts.scheme == "ssh" and parts.username != "git")
                or (parts.scheme == "https" and (parts.username or parts.password))):
            return "BLOCKED"
        path = parts.path.lstrip("/")
    path = path.removesuffix(".git")
    return "PASS" if path.casefold() == repository.casefold() else "BLOCKED"


def valid_tag(tag: str) -> None:
    if not isinstance(tag, str) or TAG_PATTERN.fullmatch(tag) is None:
        raise PublicationError("PUBLICATION_TAG_INVALID")


def published_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        timestamp = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return timestamp.tzinfo is not None
    except ValueError:
        return False


def validate_release(
    release: dict[str, Any],
    *,
    repository: str,
    tag: str,
) -> dict[str, Any]:
    """Validate public GitHub release metadata; never assert artifact bytes verified."""
    valid_repository(repository)
    valid_tag(tag)
    if not isinstance(release, dict):
        raise PublicationError("PUBLICATION_RESPONSE_INVALID")

    problems: list[str] = []
    ident = release.get("id")
    if type(ident) is not int or ident <= 0:
        problems.append("PUBLICATION_ID_INVALID")
    if release.get("tag_name") != tag:
        problems.append("PUBLICATION_TAG_MISMATCH")
    if release.get("draft") is not False:
        problems.append("PUBLICATION_DRAFT_OR_UNKNOWN")
    if type(release.get("prerelease")) is not bool:
        problems.append("PUBLICATION_PRERELEASE_UNKNOWN")
    elif release["prerelease"]:
        problems.append("PUBLICATION_IS_PRERELEASE")
    if not published_date(release.get("published_at")):
        problems.append("PUBLICATION_DATE_INVALID")
    actual_url = release.get("html_url")
    expected_url = "https://github.com/" + repository + "/releases/tag/" + urllib.parse.quote(tag, safe="/")
    if not isinstance(actual_url, str) or actual_url.rstrip("/") != expected_url:
        problems.append("PUBLICATION_URL_MISMATCH")

    assets = release.get("assets")
    if not isinstance(assets, list):
        problems.append("PUBLICATION_ASSETS_INVALID")
        assets = []
    if len(assets) > 100:
        problems.append("PUBLICATION_ASSETS_TOO_MANY")
        assets = []
    summaries = []
    names: set[str] = set()
    for asset in assets:
        if not isinstance(asset, dict):
            problems.append("PUBLICATION_ASSET_INVALID")
            continue
        name, state, size, digest = (asset.get(k) for k in ("name", "state", "size", "digest"))
        if not isinstance(name, str) or not name or "/" in name or "\\" in name or name in names:
            problems.append("PUBLICATION_ASSET_NAME_INVALID")
            continue
        names.add(name)
        if state != "uploaded" or type(size) is not int or size <= 0:
            problems.append("PUBLICATION_ASSET_NOT_READY")
            continue
        if digest is not None and (not isinstance(digest, str) or SHA256.fullmatch(digest) is None):
            problems.append("PUBLICATION_ASSET_DIGEST_INVALID")
            continue
        summaries.append({"name": name, "size": size, "reported_digest": digest, "browser_download_url": asset.get("browser_download_url")})

    if problems:
        status = "BLOCKED"
    else:
        status = "SOURCE_RELEASE_PUBLISHED"
    return {
        "schema_version": 1,
        "repository": repository,
        "tag": tag,
        "release_id": ident if type(ident) is int else None,
        "release_url": expected_url if status == "SOURCE_RELEASE_PUBLISHED" else None,
        "published_at": release.get("published_at") if published_date(release.get("published_at")) else None,
        "asset_metadata": summaries,
        "asset_content_verification": "NOT_PERFORMED",
        "publication_status": status,
        "release_readiness": "NOT_VERIFIED",
        "problems": list(dict.fromkeys(problems)),
    }


def verify_github_publication(
    repository: str,
    tag: str,
    *,
    request_json: Callable[[str], dict[str, Any]] = get_public_json,
) -> dict[str, Any]:
    valid_repository(repository)
    valid_tag(tag)
    endpoint = (
        "https://api.github.com/repos/" + repository +
        "/releases/tags/" + urllib.parse.quote(tag, safe="")
    )
    try:
        data = request_json(endpoint)
    except (PublicationError, CIEvidenceError, urllib.error.URLError, OSError):
        return {
            "schema_version": 1,
            "repository": repository,
            "tag": tag,
            "publication_status": "BLOCKED",
            "release_readiness": "NOT_VERIFIED",
            "release_url": None,
            "asset_metadata": [],
            "problems": ["PUBLICATION_QUERY_FAILED_OR_MISSING"],
        }
    return validate_release(data, repository=repository, tag=tag)
