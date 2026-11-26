#!/usr/bin/env python3
"""Compare two explicit Git worktree porcelain -z captures without invoking Git."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

MAX_BYTES = 2 * 1024 * 1024
MAX_ROWS = 2000
MAX_CANDIDATES = 100
OID = re.compile(rb'(?:[0-9a-f]{40}|[0-9a-f]{64})\Z')


class InventoryError(ValueError):
    pass


def require(ok, code):
    if not ok:
        raise InventoryError(code)


def branch_ref(value):
    require(isinstance(value, bytes) and value.startswith(b'refs/heads/') and
            len(value) > len(b'refs/heads/') and not any(c <= 32 or c == 127 for c in value),
            'WORKTREE_BRANCH_INVALID')
    return value


def parse(raw):
    require(isinstance(raw, bytes) and 0 < len(raw) <= MAX_BYTES, 'WORKTREE_INPUT_LIMIT')
    require(raw.endswith(b'\0\0'), 'WORKTREE_FRAME_INVALID')
    groups = raw[:-2].split(b'\0\0')
    require(0 < len(groups) <= MAX_ROWS, 'WORKTREE_ROW_LIMIT')
    paths = set()
    rows = []
    for group in groups:
        lines = group.split(b'\0')
        require(2 <= len(lines) <= 6 and lines[0].startswith(b'worktree '), 'WORKTREE_FRAME_INVALID')
        path = lines[0][9:]
        require(path and path not in paths, 'WORKTREE_PATH_INVALID')
        paths.add(path)
        attrs = {}
        for line in lines[1:]:
            key, sep, value = line.partition(b' ')
            require(key in {b'HEAD', b'branch', b'bare', b'detached', b'locked', b'prunable'}
                    and key not in attrs, 'WORKTREE_ATTRIBUTE_INVALID')
            if key == b'HEAD':
                require(sep and OID.fullmatch(value), 'WORKTREE_HEAD_INVALID')
            elif key == b'branch':
                require(sep, 'WORKTREE_BRANCH_INVALID')
                branch_ref(value)
            elif key in {b'bare', b'detached'}:
                require(not sep, 'WORKTREE_ATTRIBUTE_INVALID')
            attrs[key] = value
        bare = b'bare' in attrs
        detached = b'detached' in attrs
        branch = attrs.get(b'branch')
        if bare:
            require(b'HEAD' not in attrs and not detached and branch is None, 'WORKTREE_STATE_INVALID')
        else:
            require(b'HEAD' in attrs and detached != (branch is not None), 'WORKTREE_STATE_INVALID')
        rows.append({'bare': bare, 'detached': detached, 'branch': branch,
                     'unborn': not bare and set(attrs[b'HEAD']) == {48},
                     'locked': b'locked' in attrs, 'prunable': b'prunable' in attrs})
    return rows


def compare(first, second, candidates=()):
    require(len(candidates) <= MAX_CANDIDATES and len(set(candidates)) == len(candidates),
            'WORKTREE_CANDIDATE_LIMIT')
    for ref in candidates:
        branch_ref(ref)
        require(ref.isascii(), 'WORKTREE_CANDIDATE_ASCII_REQUIRED')
    a, b = parse(first), parse(second)
    result = {'schema_version': 1, 'deletion_authorized': False,
              'snapshot_authenticity': 'NOT_VERIFIED', 'local_occupancy_now': 'NOT_VERIFIED'}
    if first != second:
        return {**result, 'status': 'STALE', 'candidate_checks': []}
    return {**result, 'status': 'OBSERVED', 'worktrees': len(b),
            'counts': {key: sum(row[key] for row in b)
                       for key in ('bare', 'detached', 'unborn', 'locked', 'prunable')},
            'candidate_checks': [{'index': i, 'matching_worktrees': sum(row['branch'] == ref for row in b)}
                                 for i, ref in enumerate(candidates, 1)]}


def read_capture(path):
    with path.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    require(len(raw) <= MAX_BYTES, 'WORKTREE_INPUT_LIMIT')
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--first', type=Path, required=True)
    parser.add_argument('--second', type=Path, required=True)
    parser.add_argument('--branch', action='append', default=[])
    args = parser.parse_args()
    try:
        require(args.first.resolve(strict=True) != args.second.resolve(strict=True), 'WORKTREE_CAPTURE_NOT_DISTINCT')
        result = compare(read_capture(args.first), read_capture(args.second),
                         [x.encode('ascii') for x in args.branch])
    except (InventoryError, OSError, UnicodeError, ValueError, RuntimeError) as exc:
        print(str(exc) if isinstance(exc, InventoryError) else 'WORKTREE_INPUT_INVALID', file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return int(result['status'] == 'STALE')


if __name__ == '__main__':
    sys.exit(main())
