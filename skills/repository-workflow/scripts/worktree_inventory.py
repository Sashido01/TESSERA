#!/usr/bin/env python3
"""Compare two explicit Git worktree porcelain -z captures without invoking Git."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import stat
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
    # Git check-ref-format restrictions for a full refs/heads/... name.
    require(not any(c in value for c in (b'..', b'@{', b'~', b'^', b':',
                                         b'?', b'*', b'[', b'\\')) and
            not value.endswith(b'.') and
            all(part and not part.startswith(b'.') and not part.endswith(b'.lock')
                for part in value.split(b'/')), 'WORKTREE_BRANCH_INVALID')
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
        rows.append({'bare': bare, 'detached': detached, 'branch': branch, 'head': attrs.get(b'HEAD'),
                     'unborn': not bare and set(attrs[b'HEAD']) == {48},
                     'locked': b'locked' in attrs, 'prunable': b'prunable' in attrs})
    require(len({len(row['head']) for row in rows if row['head'] is not None}) <= 1,
            'WORKTREE_OBJECT_FORMAT_MIXED')
    return rows


def compare(first, second, candidates=(), candidate_heads=()):
    require(isinstance(candidates, (tuple, list)) and len(candidates) <= MAX_CANDIDATES,
            'WORKTREE_CANDIDATE_LIMIT')
    for ref in candidates:
        branch_ref(ref)
        require(ref.isascii(), 'WORKTREE_CANDIDATE_ASCII_REQUIRED')
    require(len(set(candidates)) == len(candidates), 'WORKTREE_CANDIDATE_LIMIT')
    require(isinstance(candidate_heads, (tuple, list)) and
            len(candidate_heads) in (0, len(candidates)), 'WORKTREE_HEAD_COUNT')
    for head in candidate_heads:
        require(isinstance(head, bytes) and OID.fullmatch(head) and set(head) != {48},
                'WORKTREE_CANDIDATE_HEAD_INVALID')
    parse(first)
    b = parse(second)
    result = {'schema_version': 1, 'deletion_authorized': False,
              'snapshot_authenticity': 'NOT_VERIFIED', 'local_occupancy_now': 'NOT_VERIFIED'}
    if first != second:
        return {**result, 'status': 'STALE', 'candidate_checks': []}
    widths = {len(row['head']) for row in b if row['head'] is not None}
    if widths:
        require(all(len(head) in widths for head in candidate_heads),
                'WORKTREE_CANDIDATE_OBJECT_FORMAT_MISMATCH')
    checks = []
    for i, ref in enumerate(candidates):
        item = {'index': i + 1, 'matching_worktrees': sum(row['branch'] == ref for row in b)}
        if candidate_heads:
            head = candidate_heads[i]
            item['matching_head_worktrees'] = sum(row['head'] == head for row in b)
            item['detached_head_worktrees'] = sum(row['detached'] and row['head'] == head for row in b)
        checks.append(item)
    return {**result, 'status': 'OBSERVED', 'worktrees': len(b),
            'counts': {key: sum(row[key] for row in b)
                       for key in ('bare', 'detached', 'unborn', 'locked', 'prunable')},
            'candidate_checks': checks}


def ordinary(info):
    return stat.S_ISREG(info.st_mode) and not (
        getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0))


def identity(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def read_capture_record(path):
    # Trusted ordinary captures only. Refuse special files before open, recheck
    # the opened descriptor, and use nonblocking/no-follow flags where available.
    before = path.lstat()
    require(ordinary(before), 'WORKTREE_CAPTURE_NOT_REGULAR')
    require(0 < before.st_size <= MAX_BYTES, 'WORKTREE_INPUT_LIMIT')
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        require(ordinary(opened) and identity(opened) == identity(before), 'WORKTREE_CAPTURE_CHANGED')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read(MAX_BYTES + 1)
        require(len(raw) == before.st_size and identity(os.fstat(fd)) == identity(before)
                and identity(path.lstat()) == identity(before), 'WORKTREE_CAPTURE_CHANGED')
        require(opened.st_ino != 0, 'WORKTREE_CAPTURE_IDENTITY_UNKNOWN')
        return raw, (opened.st_dev, opened.st_ino)
    finally:
        os.close(fd)


def read_capture(path):
    return read_capture_record(path)[0]


def capture_pair(first, second):
    # Reject aliases using identities of the descriptors actually read, not
    # only a pathname samefile precheck. Still not atomic or race-proof.
    a, identity_a = read_capture_record(first)
    b, identity_b = read_capture_record(second)
    require(identity_a != identity_b, 'WORKTREE_CAPTURE_NOT_DISTINCT')
    return a, b


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--first', type=Path, required=True)
    parser.add_argument('--second', type=Path, required=True)
    parser.add_argument('--branch', action='append', default=[])
    parser.add_argument('--head', action='append', default=[])
    args = parser.parse_args()
    try:
        first, second = capture_pair(args.first, args.second)
        result = compare(first, second,
                         [x.encode('ascii') for x in args.branch],
                         [x.encode('ascii') for x in args.head])
    except (InventoryError, OSError, UnicodeError, ValueError, RuntimeError) as exc:
        print(str(exc) if isinstance(exc, InventoryError) else 'WORKTREE_INPUT_INVALID', file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return int(result['status'] == 'STALE')


if __name__ == '__main__':
    sys.exit(main())
