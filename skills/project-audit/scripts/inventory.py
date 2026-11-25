#!/usr/bin/env python3
"""Bounded, metadata-only inventory of an explicitly selected project tree.

Not a sandbox or a content integrity check. Use a trusted, stable snapshot.
No source execution, Git invocation, content reads, or filesystem writes.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

DEFAULT_EXCLUDED = frozenset({'.git', '.venv', 'venv', 'node_modules', '__pycache__', '.tox', '.mypy_cache', '.pytest_cache'})
MAX_ENTRIES = 50_000
MAX_DEPTH = 64
MARKERS = frozenset({'pyproject.toml', 'requirements.txt', 'Cargo.toml', 'Cargo.lock', 'package.json', 'package-lock.json', 'go.mod', 'go.sum', 'pom.xml', 'build.gradle', 'CMakeLists.txt', 'Makefile', 'README.md', 'AGENTS.md', 'VERSION'})


class InventoryError(ValueError):
    pass


def is_redirect(info: os.stat_result) -> bool:
    # A Windows junction is a reparse point even if not a POSIX symlink.
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))


def directory_stat(path: str | Path) -> os.stat_result:
    # Windows DirEntry.stat() returns zero for device and inode. Use fresh,
    # non-following metadata for directories on every platform instead.
    return os.stat(path, follow_symlinks=False)


def inventory(root: Path, *, max_entries: int = 10_000, max_depth: int = 32) -> dict:
    if not 1 <= max_entries <= MAX_ENTRIES or not 0 <= max_depth <= MAX_DEPTH:
        raise InventoryError('INVENTORY_LIMIT_INVALID')
    # Do not silently dereference a redirected root or an ancestor.
    root = Path(os.path.abspath(root))
    try:
        for ancestor in reversed((root, *root.parents)):
            info = ancestor.lstat()
            if is_redirect(info) or not stat.S_ISDIR(info.st_mode):
                raise InventoryError('INVENTORY_ROOT_INVALID')
    except OSError:
        raise InventoryError('INVENTORY_ROOT_UNAVAILABLE') from None
    records: list[dict] = []
    gaps: list[dict] = []
    extensions: Counter[str] = Counter()
    markers: list[str] = []
    directory_paths: list[str] = []
    files = directories = bytes_total = examined = 0
    stopped = False
    root_info = root.lstat()
    if is_redirect(root_info) or not stat.S_ISDIR(root_info.st_mode):
        raise InventoryError('INVENTORY_ROOT_INVALID')
    stack = [(root, '', 0, root_info)]

    while stack and not stopped:
        directory, relative, depth, expected = stack.pop()
        try:
            current = directory.lstat()
            if (is_redirect(current) or not stat.S_ISDIR(current.st_mode)
                    or (current.st_dev, current.st_ino) != (expected.st_dev, expected.st_ino)):
                gaps.append({'path': relative or '.', 'reason': 'DIRECTORY_CHANGED'})
                continue
            # Bound enumeration before sorting; do not load arbitrarily large directories.
            entries = []
            remaining = max_entries - examined
            with os.scandir(directory) as iterator:
                for entry in iterator:
                    if len(entries) >= remaining:
                        stopped = True
                        break
                    entries.append(entry)
            if stopped:
                # Do not return arbitrary filesystem-order subsets of a directory.
                gaps.append({'path': relative or '.', 'reason': 'ENTRY_LIMIT'})
                break
            children = []
            for entry in sorted(entries, key=lambda item: item.name):
                examined += 1
                rel = f'{relative}/{entry.name}' if relative else entry.name
                try:
                    info = entry.stat(follow_symlinks=False)
                except OSError:
                    gaps.append({'path': rel, 'reason': 'STAT_UNAVAILABLE'})
                    continue
                if is_redirect(info):
                    gaps.append({'path': rel, 'reason': 'REDIRECTION_NOT_FOLLOWED'})
                elif stat.S_ISDIR(info.st_mode):
                    try:
                        fresh = directory_stat(entry.path)
                    except OSError:
                        gaps.append({'path': rel, 'reason': 'STAT_UNAVAILABLE'})
                        continue
                    if is_redirect(fresh):
                        gaps.append({'path': rel, 'reason': 'REDIRECTION_NOT_FOLLOWED'})
                        continue
                    if not stat.S_ISDIR(fresh.st_mode):
                        gaps.append({'path': rel, 'reason': 'DIRECTORY_CHANGED'})
                        continue
                    directories += 1
                    directory_paths.append(rel)
                    if fresh.st_dev != root_info.st_dev:
                        gaps.append({'path': rel, 'reason': 'DEVICE_BOUNDARY'})
                    elif info.st_ino and (info.st_dev, info.st_ino) != (fresh.st_dev, fresh.st_ino):
                        gaps.append({'path': rel, 'reason': 'DIRECTORY_CHANGED'})
                    elif entry.name.casefold() in DEFAULT_EXCLUDED:
                        gaps.append({'path': rel, 'reason': 'DEFAULT_EXCLUSION'})
                    elif depth >= max_depth:
                        gaps.append({'path': rel, 'reason': 'DEPTH_LIMIT'})
                    else:
                        children.append((Path(entry.path), rel, depth + 1, fresh))
                elif stat.S_ISREG(info.st_mode):
                    files += 1
                    bytes_total += info.st_size
                    extensions[Path(entry.name).suffix.casefold() or '(none)'] += 1
                    if entry.name in MARKERS:
                        markers.append(rel)
                    records.append({'path': rel, 'kind': 'file', 'bytes': info.st_size,
                                    'mtime_ns': info.st_mtime_ns})
                else:
                    gaps.append({'path': rel, 'reason': 'SPECIAL_FILE_NOT_READ'})
            stack.extend(reversed(children))
            # This detects some races, not arbitrary file or directory substitution.
            after = directory.lstat()
            if (after.st_dev, after.st_ino, after.st_mtime_ns) != (current.st_dev, current.st_ino, current.st_mtime_ns):
                gaps.append({'path': relative or '.', 'reason': 'DIRECTORY_CHANGED'})
        except OSError:
            gaps.append({'path': relative or '.', 'reason': 'DIRECTORY_UNAVAILABLE'})
    records.sort(key=lambda row: row['path'])
    gaps.sort(key=lambda row: (row['path'], row['reason']))
    excluded = sum(row['reason'] == 'DEFAULT_EXCLUSION' for row in gaps)
    unresolved = len(gaps) - excluded
    payload = {'files': records, 'directories': sorted(directory_paths),
               'gaps': gaps, 'excluded_names': sorted(DEFAULT_EXCLUDED),
               'max_entries': max_entries, 'max_depth': max_depth}
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=True, sort_keys=True,
                                      separators=(',', ':')).encode('ascii')).hexdigest()
    return {'schema_version': 1, 'status': 'PARTIAL' if unresolved else 'SCOPED_COMPLETE',
            'scope': 'METADATA_ONLY', 'examined_entries': examined,
            'regular_files': files, 'observed_directories': directories,
            'regular_file_bytes': bytes_total, 'extensions': dict(sorted(extensions.items())),
            'markers': sorted(markers), 'excluded_subtrees': excluded,
            'unresolved_gaps': unresolved, 'pending_directories': len(stack) + int(stopped),
            'content_integrity': 'NOT_VERIFIED', 'metadata_sha256': digest, **payload}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--max-entries', type=int, default=10_000)
    parser.add_argument('--max-depth', type=int, default=32)
    args = parser.parse_args()
    try:
        result = inventory(args.root, max_entries=args.max_entries, max_depth=args.max_depth)
    except (InventoryError, OSError) as exc:
        print(str(exc) if isinstance(exc, InventoryError) else 'INVENTORY_IO_FAILED', file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2))
    return int(result['status'] == 'PARTIAL')


if __name__ == '__main__':
    sys.exit(main())
