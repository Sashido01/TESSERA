#!/usr/bin/env python3
"""Проверка скачанного исходного ZIP каталога TESSERA без распаковки и сети.

Сравнивает байты с MANIFEST.json и переданными извне версией и commit SHA.
Не подтверждает подпись, происхождение GitHub или публикацию.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import stat
import sys
import zipfile

from catalog_index import CatalogError
from catalog_package_policy import requires_update_files, check_update_catalog

VERSION_RE = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z")
SHA_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
DIGEST_RE = re.compile(r"[0-9a-f]{64}\Z")
ROOT_FILES = {"LICENSE", "README.md", "README.en.md", "VERSION"}
MAX_ARCHIVE = 64 * 1024 * 1024
MAX_MEMBER = 4 * 1024 * 1024
MAX_MANIFEST = 1024 * 1024
MAX_ENTRIES = 2048


class VerificationError(ValueError):
    """Безопасный код отказа, без вывода пользовательских путей."""


def _member_bytes(archive: zipfile.ZipFile, entry: zipfile.ZipInfo, limit: int) -> bytes:
    if entry.file_size > limit:
        raise VerificationError("CATALOG_MEMBER_TOO_LARGE")
    data = bytearray()
    with archive.open(entry, "r") as stream:
        while chunk := stream.read(64 * 1024):
            data.extend(chunk)
            if len(data) > limit:
                raise VerificationError("CATALOG_MEMBER_TOO_LARGE")
    if len(data) != entry.file_size:
        raise VerificationError("CATALOG_MEMBER_SIZE_MISMATCH")
    return bytes(data)


def _valid_name(name: str, prefix: str) -> bool:
    if not isinstance(name, str) or not name.startswith(prefix):
        return False
    relative = name[len(prefix):]
    return (
        bool(relative)
        and "\\" not in relative
        and not relative.startswith("/")
        and all(part not in ("", ".", "..") for part in relative.split("/"))
        and not any(ord(char) < 32 for char in relative)
    )


def verify(archive_path: pathlib.Path, *, version: str, source_commit: str) -> dict[str, object]:
    if not isinstance(version, str) or VERSION_RE.fullmatch(version) is None:
        raise VerificationError("CATALOG_VERSION_INVALID")
    if not isinstance(source_commit, str) or SHA_RE.fullmatch(source_commit) is None:
        raise VerificationError("CATALOG_SOURCE_SHA_INVALID")
    path = pathlib.Path(archive_path)
    try:
        if path.is_symlink() or not path.is_file():
            raise VerificationError("CATALOG_FILE_INVALID")
        size = path.stat().st_size
        if not 1 <= size <= MAX_ARCHIVE:
            raise VerificationError("CATALOG_ARCHIVE_SIZE_INVALID")
        prefix = f"TESSERA-{version}/"
        manifest_name = prefix + "MANIFEST.json"
        with zipfile.ZipFile(path, "r", allowZip64=False) as zf:
            entries = zf.infolist()
            if not 1 <= len(entries) <= MAX_ENTRIES:
                raise VerificationError("CATALOG_ENTRY_COUNT_INVALID")
            indexed: dict[str, zipfile.ZipInfo] = {}
            for entry in entries:
                if (not _valid_name(entry.filename, prefix)
                        or entry.filename in indexed
                        or entry.is_dir()
                        or entry.compress_type != zipfile.ZIP_STORED
                        or entry.flag_bits & 1
                        or entry.create_system != 3
                        or stat.S_IFMT(entry.external_attr >> 16) != stat.S_IFREG):
                    raise VerificationError("CATALOG_ENTRY_UNSAFE")
                if not 0 <= entry.file_size <= MAX_MEMBER:
                    raise VerificationError("CATALOG_MEMBER_TOO_LARGE")
                indexed[entry.filename] = entry
            if manifest_name not in indexed:
                raise VerificationError("CATALOG_MANIFEST_MISSING")
            if indexed[manifest_name].file_size > MAX_MANIFEST:
                raise VerificationError("CATALOG_MANIFEST_TOO_LARGE")
            try:
                manifest = json.loads(_member_bytes(zf, indexed[manifest_name], MAX_MANIFEST))
            except (ValueError, UnicodeError):
                raise VerificationError("CATALOG_MANIFEST_INVALID") from None
            if (not isinstance(manifest, dict)
                    or set(manifest) != {"schema_version", "artifact_kind",
                                        "catalog_version", "source_commit_sha", "files"}
                    or type(manifest["schema_version"]) is not int
                    or manifest["schema_version"] != 1
                    or manifest["artifact_kind"] != "TESSERA_AGENT_SKILLS_CATALOG_SOURCE"
                    or manifest["catalog_version"] != version
                    or manifest["source_commit_sha"] != source_commit
                    or not isinstance(manifest["files"], list)):
                raise VerificationError("CATALOG_MANIFEST_MISMATCH")
            records = manifest["files"]
            if not records or len(records) != len(indexed) - 1:
                raise VerificationError("CATALOG_FILE_SET_MISMATCH")
            names: list[str] = []
            version_metadata: dict[str, dict[str, bytes]] = {}
            total = 0
            index_bytes = None
            for record in records:
                if not isinstance(record, dict) or set(record) != {"path", "bytes", "sha256"}:
                    raise VerificationError("CATALOG_MANIFEST_RECORD_INVALID")
                name = record["path"]
                declared_size = record["bytes"]
                digest = record["sha256"]
                if (not isinstance(name, str) or not _valid_name(prefix + name, prefix)
                        or type(declared_size) is not int
                        or not 0 <= declared_size <= MAX_MEMBER
                        or not isinstance(digest, str) or DIGEST_RE.fullmatch(digest) is None):
                    raise VerificationError("CATALOG_MANIFEST_RECORD_INVALID")
                member = indexed.get(prefix + name)
                if member is None or member.file_size != declared_size:
                    raise VerificationError("CATALOG_FILE_SET_MISMATCH")
                data = _member_bytes(zf, member, MAX_MEMBER)
                total += len(data)
                if total > MAX_ARCHIVE:
                    raise VerificationError("CATALOG_TOTAL_SIZE_INVALID")
                if hashlib.sha256(data).hexdigest() != digest:
                    raise VerificationError("CATALOG_CONTENT_DIGEST_MISMATCH")
                if name == "CATALOG.json":
                    index_bytes = data
                if name == "VERSION" and data.decode("utf-8", errors="replace").strip() != version:
                    raise VerificationError("CATALOG_VERSION_MISMATCH")
                match = re.fullmatch(r"skills/([a-z0-9]+(?:-[a-z0-9]+)*)/(VERSION|CHANGELOG\.md|CHANGELOG\.en\.md)", name)
                if match:
                    version_metadata.setdefault(match[1], {})[match[2]] = data
                names.append(name)
            if names != sorted(set(names)) or set(indexed) != {manifest_name} | {prefix + n for n in names}:
                raise VerificationError("CATALOG_FILE_SET_MISMATCH")
            if not ROOT_FILES.issubset(set(names)) or not any(
                re.fullmatch(r"skills/[a-z0-9]+(?:-[a-z0-9]+)*/SKILL\.md", n) for n in names
            ):
                raise VerificationError("CATALOG_REQUIRED_FILES_MISSING")
            skill_versions = {}
            for skill, metadata in version_metadata.items():
                if (set(metadata) != {"VERSION", "CHANGELOG.md", "CHANGELOG.en.md"}
                        or f"skills/{skill}/SKILL.md" not in names):
                    raise VerificationError("CATALOG_SKILL_VERSION_METADATA_INCOMPLETE")
                try:
                    skill_version = metadata["VERSION"].decode("utf-8").strip()
                    if not VERSION_RE.fullmatch(skill_version) or int(skill_version.split(".")[1]) > 99:
                        raise VerificationError("CATALOG_SKILL_VERSION_INVALID")
                    skill_versions[skill] = skill_version
                    for key in ("CHANGELOG.md", "CHANGELOG.en.md"):
                        if not re.search(r"(?m)^## " + re.escape(skill_version) + r"(?:\s|$)",
                                         metadata[key].decode("utf-8")):
                            raise VerificationError("CATALOG_SKILL_CHANGELOG_INVALID")
                except UnicodeError:
                    raise VerificationError("CATALOG_SKILL_VERSION_ENCODING_INVALID") from None
            if requires_update_files(version):
                try:
                    check_update_catalog(names, index_bytes, skill_versions, version)
                except (CatalogError, ValueError, UnicodeError) as exc:
                    raise VerificationError("CATALOG_UPDATE_CONTRACT_INVALID") from exc
        sha = hashlib.sha256()
        with path.open("rb") as stream:
            while chunk := stream.read(64 * 1024):
                sha.update(chunk)
    except (OSError, zipfile.BadZipFile, RuntimeError, EOFError) as exc:
        raise VerificationError("CATALOG_ARCHIVE_UNREADABLE") from exc
    return {
        "status": "PASS",
        "catalog_version": version,
        "source_commit_sha_claim": source_commit,
        "file_count": len(names),
        "archive_bytes": size,
        "archive_sha256": sha.hexdigest(),
        "integrity": "PASS",
        "attestation": "NOT_VERIFIED",
        "publication": "NOT_VERIFIED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=pathlib.Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    try:
        result = verify(args.archive, version=args.version, source_commit=args.source_commit)
    except VerificationError as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
