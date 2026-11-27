#!/usr/bin/env python3
"""Read-only, bounded metadata inventory of a selected trusted project."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import sys
import time

CATEGORIES = ("protected_hint", "review_cache", "review_build",
              "review_dependency", "review_temp", "other")
PROTECTED = frozenset({"data", "userdata", "user-data", "vault", "backups",
                       "backup", "evidence", "models", "logs", "secrets",
                       "credentials", "releases", "release"})
CACHE = frozenset({"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
                   ".cache", ".parcel-cache"})
BUILD = frozenset({"build", "dist", "target", "out", ".next"})
DEPENDENCY = frozenset({"node_modules", ".venv", "venv"})
TEMP = frozenset({"tmp", ".tmp", "temp", ".temp"})
PROTECTED_SUFFIX = frozenset({".db", ".sqlite", ".sqlite3", ".pem", ".key",
                              ".pfx", ".p12", ".onnx", ".gguf", ".safetensors",
                              ".log", ".bak", ".zip"})
MAX_DETAILS = 20
MAX_PENDING_DIRS = 8192
MAX_HARDLINK_IDENTITIES = 100000


class InventoryError(ValueError):
    pass


def reparse(info):
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def entry_metadata(entry, windows):
    info = entry.stat(follow_symlinks=False)
    # Windows DirEntry.stat reports zero device, inode and link count.
    # Do not request further metadata for a known reparse point.
    if windows and not reparse(info):
        return os.stat(entry.path, follow_symlinks=False)
    return info


def ordinary_root(root):
    if '..' in Path(root).parts:
        raise InventoryError("ROOT_PARENT_TRAVERSAL")
    root = Path(os.path.abspath(root))
    if root == root.parent:
        raise InventoryError("ROOT_VOLUME_REFUSED")
    for item in (root, *root.parents):
        info = item.lstat()
        if reparse(info) or not stat.S_ISDIR(info.st_mode):
            raise InventoryError("ROOT_NOT_ORDINARY")
    return root


def category(parts):
    names = tuple(x.casefold() for x in parts)
    last = names[-1]
    if (any(n in PROTECTED or n == ".env" or n.startswith(".env.")
            or n.startswith("id_rsa") or n.startswith("id_ed25519") for n in names)
            or Path(last).suffix in PROTECTED_SUFFIX):
        return "protected_hint"
    if any(n in CACHE for n in names) or Path(last).suffix in {".pyc", ".pyo"}:
        return "review_cache"
    if any(n in DEPENDENCY for n in names):
        return "review_dependency"
    if any(n in BUILD for n in names):
        return "review_build"
    if any(n in TEMP for n in names) or last.endswith(".tmp"):
        return "review_temp"
    return "other"


def inventory(root, max_entries=200000, max_depth=64, max_seconds=30, details=False):
    if (type(max_entries) is not int or not 1 <= max_entries <= 2000000
            or type(max_depth) is not int or not 1 <= max_depth <= 128
            or type(max_seconds) is not int or not 1 <= max_seconds <= 600):
        raise InventoryError("LIMIT_INVALID")
    root = ordinary_root(root)
    base = root.lstat()
    device = base.st_dev
    started = time.monotonic()
    categories = {key: {"files": 0, "logical_bytes": 0} for key in CATEGORIES}
    skipped = {key: 0 for key in ("git_metadata", "nested_git", "links_reparse",
                                  "other_device", "special", "errors", "depth")}
    entries = dirs = count = logical = aliases = 0
    hardlinks = set()
    largest = []
    stack = [(root, (), base.st_ino)]
    limit = None
    while stack and limit is None:
        if time.monotonic() - started >= max_seconds:
            limit = "TIME_LIMIT"
            break
        folder, parts, expected_ino = stack.pop()
        try:
            current = folder.lstat()
            if (reparse(current) or not stat.S_ISDIR(current.st_mode)
                    or current.st_dev != device or current.st_ino != expected_ino):
                skipped["errors"] += 1
                continue
            if parts:
                try:
                    (folder / ".git").lstat()
                except FileNotFoundError:
                    pass
                else:
                    skipped["nested_git"] += 1
                    continue
            dirs += 1
            with os.scandir(folder) as children:
                for entry in children:
                    if entries >= max_entries:
                        limit = "ENTRY_LIMIT"
                        break
                    if time.monotonic() - started >= max_seconds:
                        limit = "TIME_LIMIT"
                        break
                    entries += 1
                    if entry.name.casefold() == ".git":
                        skipped["git_metadata"] += 1
                        continue
                    try:
                        info = entry_metadata(entry, os.name == 'nt')
                    except OSError:
                        skipped["errors"] += 1
                        continue
                    if reparse(info):
                        skipped["links_reparse"] += 1
                        continue
                    if info.st_dev != device:
                        skipped["other_device"] += 1
                        continue
                    relative = parts + (entry.name,)
                    if stat.S_ISDIR(info.st_mode):
                        if len(relative) >= max_depth:
                            skipped["depth"] += 1
                        elif len(stack) >= MAX_PENDING_DIRS:
                            limit = "PENDING_DIRECTORY_LIMIT"
                            break
                        else:
                            stack.append((Path(entry.path), relative, info.st_ino))
                        continue
                    if not stat.S_ISREG(info.st_mode):
                        skipped["special"] += 1
                        continue
                    count += 1
                    logical += info.st_size
                    key = category(relative)
                    categories[key]["files"] += 1
                    categories[key]["logical_bytes"] += info.st_size
                    if info.st_nlink > 1 and info.st_ino:
                        ident = (info.st_dev, info.st_ino)
                        if ident in hardlinks:
                            aliases += 1
                        elif len(hardlinks) >= MAX_HARDLINK_IDENTITIES:
                            limit = "HARDLINK_IDENTITY_LIMIT"
                            break
                        else:
                            hardlinks.add(ident)
                    if details and key.startswith("review_"):
                        largest.append((info.st_size, "/".join(relative), key))
                        largest.sort(reverse=True)
                        if len(largest) > MAX_DETAILS:
                            largest.pop()
        except OSError:
            skipped["errors"] += 1
    partial = limit is not None or skipped["errors"] > 0 or skipped["depth"] > 0
    result = {
        "schema_version": 1, "status": "PARTIAL" if partial else "OBSERVED",
        "scope": "SELECTED_ROOT_METADATA_WITH_EXCLUSIONS",
        "deletion_authorized": False, "snapshot_atomic": False,
        "entries_examined": entries, "directories_scanned": dirs,
        "files": count, "logical_bytes": logical,
        "observed_hardlink_aliases": aliases,
        "categories": categories, "skipped": skipped,
        "limit": limit,
        "limits": {"entries": max_entries, "depth": max_depth, "seconds": max_seconds},
        "elapsed_ms": round((time.monotonic() - started) * 1000),
        "reclaimable_bytes": None,
        "git_status": "NOT_VERIFIED",
    }
    if details:
        result["private_review_details"] = [
            {"relative_path": name, "logical_bytes": size, "category": key}
            for size, name, key in largest]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--max-entries", type=int, default=200000)
    parser.add_argument("--max-depth", type=int, default=64)
    parser.add_argument("--max-seconds", type=int, default=30)
    parser.add_argument("--details", action="store_true")
    args = parser.parse_args()
    try:
        result = inventory(args.root, args.max_entries, args.max_depth,
                           args.max_seconds, args.details)
    except (OSError, InventoryError, RuntimeError, ValueError):
        print(json.dumps({"status": "BLOCKED", "reason": "ROOT_OR_LIMIT_INVALID",
                          "deletion_authorized": False}))
        return 2
    print(json.dumps(result, sort_keys=True, ensure_ascii=True))
    return int(result["status"] == "PARTIAL")


if __name__ == "__main__":
    sys.exit(main())
