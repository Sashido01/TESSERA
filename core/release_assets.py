#!/usr/bin/env python3
"""T09.06: bounded byte-by-byte SHA-256 verification of PUBLIC GitHub Release assets.

Only explicit --verify-assets may initiate downloads. Nothing is saved to disk.
The digest source is GitHub's asset metadata, not a separate signed attestation.
"""
from __future__ import annotations

import hashlib
import re
import urllib.error
import urllib.parse
import urllib.request
from contextlib import closing
from typing import Any, Callable, ContextManager

try:
    from .release_publication import valid_repository, valid_tag
except ImportError:
    from release_publication import valid_repository, valid_tag

NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
TRUSTED_HOSTS = frozenset({"github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"})
CHUNK = 65536
DEFAULT_MAX_ASSET_BYTES = 64 * 1024 * 1024
HARD_MAX_ASSET_BYTES = 512 * 1024 * 1024
MAX_ASSETS = 20


class AssetVerificationError(ValueError):
    """Unsafe or invalid asset request."""


def check_url(url: str, *, initial: bool) -> None:
    if not isinstance(url, str) or len(url) > 4096:
        raise AssetVerificationError("ASSET_URL_INVALID")
    try:
        parsed = urllib.parse.urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise AssetVerificationError("ASSET_URL_INVALID") from exc
    if (parsed.scheme != "https" or parsed.hostname not in TRUSTED_HOSTS
            or port not in (None, 443) or parsed.username or parsed.password
            or parsed.fragment):
        raise AssetVerificationError("ASSET_URL_UNTRUSTED")
    if initial and (parsed.hostname != "github.com" or parsed.query):
        raise AssetVerificationError("ASSET_URL_UNTRUSTED")


def exact_download_url(repository: str, tag: str, name: str, url: str) -> None:
    valid_repository(repository)
    valid_tag(tag)
    if not isinstance(name, str) or NAME.fullmatch(name) is None:
        raise AssetVerificationError("ASSET_NAME_INVALID")
    check_url(url, initial=True)
    parsed = urllib.parse.urlsplit(url)
    expected = f"/{repository}/releases/download/{tag}/{name}"
    if urllib.parse.unquote(parsed.path) != expected:
        raise AssetVerificationError("ASSET_URL_MISMATCH")


class RestrictRedirects(urllib.request.HTTPRedirectHandler):
    """Disallow non-HTTPS or unexpected redirect domains."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(newurl, initial=False)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def open_asset_stream(url: str) -> ContextManager[Any]:
    """Open streaming download from official GitHub/CDN without credentials."""
    check_url(url, initial=True)
    opener = urllib.request.build_opener(RestrictRedirects())
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/octet-stream", "User-Agent": "TESSERA-asset-byte-verifier"},
        method="GET",
    )
    response = opener.open(req, timeout=20)
    try:
        check_url(response.geturl(), initial=False)
        if response.status != 200:
            raise AssetVerificationError("ASSET_HTTP_STATUS_INVALID")
    except Exception:
        response.close()
        raise
    return response


def verify_asset_stream(
    repository: str, tag: str, asset: dict[str, Any],
    *,
    maximum_bytes: int = DEFAULT_MAX_ASSET_BYTES,
    stream_factory: Callable[[str], ContextManager[Any]] = open_asset_stream,
) -> dict[str, Any]:
    """Fail closed on missing trusted metadata, incorrect size or SHA-256."""
    if type(maximum_bytes) is not int or not 1 <= maximum_bytes <= HARD_MAX_ASSET_BYTES:
        raise AssetVerificationError("ASSET_LIMIT_INVALID")
    if not isinstance(asset, dict):
        raise AssetVerificationError("ASSET_METADATA_INVALID")
    name, size, digest = (asset.get(x) for x in ("name", "size", "reported_digest"))
    url = asset.get("browser_download_url")
    exact_download_url(repository, tag, name, url)
    if type(size) is not int or size <= 0 or size > maximum_bytes:
        raise AssetVerificationError("ASSET_SIZE_INVALID_OR_EXCEEDS_LIMIT")
    if not isinstance(digest, str) or DIGEST.fullmatch(digest) is None:
        raise AssetVerificationError("ASSET_DIGEST_REQUIRED")
    hashed = hashlib.sha256()
    count = 0
    try:
        with closing(stream_factory(url)) as stream:
            while True:
                chunk = stream.read(CHUNK)
                if not chunk:
                    break
                if not isinstance(chunk, bytes) or not chunk:
                    raise AssetVerificationError("ASSET_STREAM_INVALID")
                count += len(chunk)
                if count > size or count > maximum_bytes:
                    raise AssetVerificationError("ASSET_DOWNLOAD_TOO_LARGE")
                hashed.update(chunk)
    except AssetVerificationError:
        raise
    except (OSError, TimeoutError, urllib.error.URLError) as exc:
        raise AssetVerificationError("ASSET_DOWNLOAD_FAILED") from exc
    actual_digest = "sha256:" + hashed.hexdigest()
    if count != size:
        raise AssetVerificationError("ASSET_SIZE_MISMATCH")
    if actual_digest != digest:
        raise AssetVerificationError("ASSET_SHA256_MISMATCH")
    return {
        "name": name,
        "bytes_verified": count,
        "sha256": actual_digest,
        "sha256_source": "github_release_metadata",
        "status": "PASS",
    }


def verify_release_assets(
    repository: str, tag: str, assets: list[dict[str, Any]],
    *,
    maximum_bytes: int = DEFAULT_MAX_ASSET_BYTES,
    stream_factory: Callable[[str], ContextManager[Any]] = open_asset_stream,
) -> dict[str, Any]:
    valid_repository(repository)
    valid_tag(tag)
    result: dict[str, Any] = {
        "asset_content_verification": "NOT_PERFORMED",
        "verified_assets": [],
        "problems": [],
    }
    if not isinstance(assets, list) or len(assets) > MAX_ASSETS:
        result["problems"] = ["ASSET_LIST_INVALID"]
        result["asset_content_verification"] = "BLOCKED"
        return result
    if not assets:
        result["asset_content_verification"] = "NO_RELEASE_ASSETS"
        return result

    names: set[str] = set()
    for asset in assets:
        name = asset.get("name") if isinstance(asset, dict) else None
        if not isinstance(name, str) or NAME.fullmatch(name) is None:
            result["problems"].append("ASSET_NAME_INVALID")
            break
        if name in names:
            result["problems"].append("ASSET_DUPLICATE_NAME")
            break
        names.add(name)
        try:
            proof = verify_asset_stream(
                repository, tag, asset, maximum_bytes=maximum_bytes,
                stream_factory=stream_factory,
            )
        except AssetVerificationError as exc:
            result["problems"].append(str(exc))
            break
        result["verified_assets"].append(proof)
    result["asset_content_verification"] = "BLOCKED" if result["problems"] else "PASS"
    return result
