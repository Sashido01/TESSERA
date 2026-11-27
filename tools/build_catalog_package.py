#!/usr/bin/env python3
"""Детерминированный исходный ZIP-пакет каталога Agent Skills TESSERA.

Сборка не меняет Git и не публикует Release. --require-tag требует
аннотированный тег текущей версии, направленный на точный HEAD.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import zipfile

from catalog_index import CatalogError
from catalog_package_policy import UPDATE_FILES, requires_update_files, check_update_catalog

VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z")
SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
SKILL = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
ROOT_FILES = ("LICENSE", "README.md", "README.en.md", "VERSION")
TIME = (1980, 1, 1, 0, 0, 0)


class PackageError(ValueError):
    """Отказ безопасной сборки с коротким машинным кодом."""


def git(root: pathlib.Path, *args: str) -> str:
    try:
        run = subprocess.run(
            ["git", "-C", str(root), *args],
            text=True, capture_output=True, check=False, timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PackageError("PACKAGE_GIT_UNAVAILABLE") from exc
    if run.returncode:
        raise PackageError("PACKAGE_GIT_FAILED")
    return run.stdout.strip()


def inspect_source(root: pathlib.Path, *, require_tag: bool) -> tuple[str, str]:
    root = root.resolve(strict=True)
    actual = pathlib.Path(git(root, "rev-parse", "--show-toplevel")).resolve()
    if root != actual:
        raise PackageError("PACKAGE_NOT_GIT_ROOT")
    if git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise PackageError("PACKAGE_DIRTY_WORKTREE")
    version_path = root / "VERSION"
    try:
        version = version_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise PackageError("PACKAGE_VERSION_MISSING") from exc
    if not VERSION.fullmatch(version):
        raise PackageError("PACKAGE_VERSION_INVALID")
    commit = git(root, "rev-parse", "HEAD")
    if not SHA.fullmatch(commit):
        raise PackageError("PACKAGE_COMMIT_INVALID")
    if require_tag:
        tag = "v" + version
        if git(root, "cat-file", "-t", "refs/tags/" + tag) != "tag":
            raise PackageError("PACKAGE_ANNOTATED_TAG_REQUIRED")
        if git(root, "rev-list", "-n", "1", "refs/tags/" + tag) != commit:
            raise PackageError("PACKAGE_TAG_COMMIT_MISMATCH")
    return version, commit


def included_paths(root: pathlib.Path) -> list[pathlib.Path]:
    """Только runtime-код и публичные описания навыков, не тесты/состояние."""
    root = root.resolve(strict=True)
    skills = root / "skills"
    if skills.is_symlink() or not skills.is_dir():
        raise PackageError("PACKAGE_SKILLS_DIRECTORY_MISSING")
    result = [pathlib.Path(name) for name in ROOT_FILES]
    count = 0
    for child in sorted(skills.iterdir(), key=lambda p: p.name):
        if child.is_symlink() or not child.is_dir() or not SKILL.fullmatch(child.name):
            raise PackageError("PACKAGE_SKILL_DIRECTORY_INVALID")
        count += 1
        if count > 100:
            raise PackageError("PACKAGE_TOO_MANY_SKILLS")
        rel = pathlib.Path("skills") / child.name
        result.append(rel / "SKILL.md")
        for name in ("README.md", "README.en.md", "LICENSE.txt"):
            if (child / name).exists():
                result.append(rel / name)
        metadata = ("VERSION", "CHANGELOG.md", "CHANGELOG.en.md")
        if any((child / name).exists() or (child / name).is_symlink() for name in metadata):
            if any(not (child / name).is_file() or (child / name).is_symlink() for name in metadata):
                raise PackageError("PACKAGE_SKILL_VERSION_METADATA_INCOMPLETE")
            result.extend(rel / name for name in metadata)
        for dirname, suffix in (("references", ".md"), ("scripts", ".py")):
            directory = child / dirname
            if directory.exists():
                if directory.is_symlink() or not directory.is_dir():
                    raise PackageError("PACKAGE_RUNTIME_DIRECTORY_INVALID")
                for f in sorted(directory.iterdir(), key=lambda p: p.name):
                    if f.is_symlink() or not f.is_file() or f.suffix != suffix:
                        raise PackageError("PACKAGE_RUNTIME_FILE_INVALID")
                    result.append(rel / dirname / f.name)
    if not count:
        raise PackageError("PACKAGE_NO_SKILLS")
    return sorted(result, key=lambda p: p.as_posix())


def file_bytes(root: pathlib.Path, relative: pathlib.Path) -> bytes:
    root = root.resolve(strict=True)
    if any(part in (".", "..") for part in relative.parts) or relative.is_absolute():
        raise PackageError("PACKAGE_UNSAFE_PATH")
    path = root / relative
    try:
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
            raise PackageError("PACKAGE_INVALID_FILE")
        data = path.read_bytes()
    except OSError as exc:
        raise PackageError("PACKAGE_FILE_UNREADABLE") from exc
    if len(data) > 4 * 1024 * 1024:
        raise PackageError("PACKAGE_FILE_TOO_LARGE")
    return data


def package_bytes(root: pathlib.Path, version: str, commit_sha: str) -> bytes:
    """Чистое детерминированное содержимое ZIP при одинаковых исходных байтах."""
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise PackageError("PACKAGE_VERSION_INVALID")
    if not isinstance(commit_sha, str) or not SHA.fullmatch(commit_sha):
        raise PackageError("PACKAGE_COMMIT_INVALID")
    files = {}
    for relative in included_paths(root):
        files[relative.as_posix()] = file_bytes(root, relative)
    if files["VERSION"].decode("utf-8").strip() != version:
        raise PackageError("PACKAGE_VERSION_MISMATCH")
    if requires_update_files(version):
        for name in sorted(UPDATE_FILES):
            files[name] = file_bytes(root, pathlib.Path(name))
        try:
            check_update_catalog(files, files["CATALOG.json"], {
                name.split("/")[1]: data.decode("utf-8").strip()
                for name, data in files.items() if re.fullmatch(r"skills/[^/]+/VERSION", name)
            })
        except (CatalogError, ValueError, UnicodeError) as exc:
            raise PackageError("PACKAGE_UPDATE_CATALOG_INVALID") from exc
    for name, data in files.items():
        if re.fullmatch(r"skills/[a-z0-9]+(?:-[a-z0-9]+)*/VERSION", name):
            skill_version = data.decode("utf-8").strip()
            if not VERSION.fullmatch(skill_version) or int(skill_version.split(".")[1]) > 99:
                raise PackageError("PACKAGE_SKILL_VERSION_INVALID")
            prefix = name[:-len("VERSION")]
            for changelog in ("CHANGELOG.md", "CHANGELOG.en.md"):
                if not re.search(r"(?m)^## " + re.escape(skill_version) + r"(?:\s|$)",
                                 files[prefix + changelog].decode("utf-8")):
                    raise PackageError("PACKAGE_SKILL_CHANGELOG_INVALID")
    manifest = {
        "schema_version": 1,
        "artifact_kind": "TESSERA_AGENT_SKILLS_CATALOG_SOURCE",
        "catalog_version": version,
        "source_commit_sha": commit_sha,
        "files": [
            {"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in sorted(files.items())
        ],
    }
    files["MANIFEST.json"] = (
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    import io
    output = io.BytesIO()
    with zipfile.ZipFile(output, mode="w", compression=zipfile.ZIP_STORED, allowZip64=False) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo("TESSERA-" + version + "/" + name, date_time=TIME)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return output.getvalue()


def build(
    root: pathlib.Path, output_dir: pathlib.Path,
    *, require_tag: bool = False, check_reproducible: bool = False,
) -> dict[str, object]:
    version, sha = inspect_source(root, require_tag=require_tag)
    blob = package_bytes(root, version, sha)
    if check_reproducible and blob != package_bytes(root, version, sha):
        raise PackageError("PACKAGE_NOT_DETERMINISTIC")
    if len(blob) > 64 * 1024 * 1024:
        raise PackageError("PACKAGE_ARCHIVE_TOO_LARGE")
    target = output_dir / ("TESSERA-catalog-v" + version + ".zip")
    if target.exists():
        raise PackageError("PACKAGE_OUTPUT_EXISTS")
    if output_dir.is_symlink():
        raise PackageError("PACKAGE_OUTPUT_SYMLINK")
    output_dir.mkdir(parents=True, exist_ok=True)
    target.write_bytes(blob)
    return {
        "schema_version": 1,
        "version": version,
        "source_commit_sha": sha,
        "archive_name": target.name,
        "archive_bytes": len(blob),
        "archive_sha256": hashlib.sha256(blob).hexdigest(),
        "annotated_tag_checked": require_tag,
        "reproducibility_checked": check_reproducible,
        "publication": "NOT_PERFORMED",
        "attestation": "NOT_PERFORMED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=pathlib.Path, default=pathlib.Path("dist"))
    parser.add_argument("--require-tag", action="store_true")
    parser.add_argument("--check-reproducible", action="store_true")
    args = parser.parse_args()
    try:
        result = build(args.repo, args.output_dir, require_tag=args.require_tag,
                       check_reproducible=args.check_reproducible)
    except (PackageError, OSError, UnicodeError) as exc:
        print("BLOCKED: " + (str(exc) if isinstance(exc, PackageError) else "PACKAGE_IO_FAILED"), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
