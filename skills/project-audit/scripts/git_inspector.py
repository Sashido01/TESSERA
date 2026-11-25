#!/usr/bin/env python3
"""Local Git metadata observation; only for a trusted, stable repository."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

OID = re.compile(rb'(?:[0-9a-f]{40}|[0-9a-f]{64})\Z')
MAX_OUTPUT = 4 * 1024 * 1024
TIMEOUT = 15

class InspectError(ValueError):
    pass


def executable():
    for entry in os.environ.get('PATH', '').split(os.pathsep):
        if not Path(entry).is_absolute():
            continue
        found = shutil.which('git', path=entry)
        if found and Path(found).is_absolute():
            return str(Path(found).resolve(strict=True))
    raise InspectError('GIT_NOT_AVAILABLE')


def query(root, exe, *args):
    # Do not let inherited GIT_DIR, GIT_WORK_TREE, config injections or
    # alternate object directories change the selected repository.
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith('GIT_')}
    env.update(GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0',
               GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_NO_LAZY_FETCH='1')
    try:
        result = subprocess.run([exe, '--no-replace-objects', '--no-optional-locks',
                                 '-C', str(root), '-c', 'core.fsmonitor=false',
                                 '-c', 'core.untrackedCache=false', *args],
                                env=env, stdin=subprocess.DEVNULL, capture_output=True,
                                shell=False, timeout=TIMEOUT, check=False)
    except subprocess.TimeoutExpired:
        raise InspectError('GIT_TIMEOUT') from None
    except OSError:
        raise InspectError('GIT_EXECUTION_FAILED') from None
    # Post-capture check; not a hard memory limit.
    if len(result.stdout) + len(result.stderr) > MAX_OUTPUT:
        raise InspectError('GIT_OUTPUT_LIMIT')
    if result.returncode:
        raise InspectError('GIT_QUERY_FAILED')
    return result.stdout


def parse_status(raw):
    if raw and not raw.endswith(b'\0'):
        raise InspectError('GIT_STATUS_INVALID')
    oid = branch = None
    kinds = Counter()
    for record in raw.split(b'\0')[:-1]:
        if record.startswith(b'# branch.oid '):
            if oid is not None:
                raise InspectError('GIT_STATUS_INVALID')
            oid = record[len(b'# branch.oid '):]
        elif record.startswith(b'# branch.head '):
            if branch is not None:
                raise InspectError('GIT_STATUS_INVALID')
            branch = record[len(b'# branch.head '):]
        elif record.startswith(b'# '):
            # Unknown headers are allowed by the porcelain v2 specification.
            continue
        elif record.startswith(b'1 '):
            kinds['tracked_changed'] += 1
        elif record.startswith(b'u '):
            kinds['unmerged'] += 1
        elif record.startswith(b'? '):
            kinds['untracked'] += 1
        else:
            raise InspectError('GIT_STATUS_INVALID')
    if not branch or oid is None or (oid != b'(initial)' and not OID.fullmatch(oid)):
        raise InspectError('GIT_STATUS_INVALID')
    return {'head': None if oid == b'(initial)' else oid.decode('ascii'),
            'head_state': 'UNBORN' if oid == b'(initial)' else ('DETACHED' if branch == b'(detached)' else 'ATTACHED'),
            'worktree_clean': not bool(kinds), 'changes': dict(sorted(kinds.items())),
            'status_sha256': hashlib.sha256(raw).hexdigest()}


def observe(root: Path):
    root = root.resolve(strict=True)
    exe = executable()
    top = query(root, exe, 'rev-parse', '--show-toplevel')
    if Path(os.fsdecode(top.rstrip(b'\n'))).resolve() != root:
        raise InspectError('GIT_ROOT_REQUIRED')
    def status():
        return query(root, exe, 'status', '--porcelain=v2', '-z', '--branch',
                     '--untracked-files=all', '--ignore-submodules=all', '--no-renames')
    first = status()
    data = parse_status(first)
    refs = query(root, exe, 'for-each-ref', '--format=%(objecttype) %(objectname) %(refname)', 'refs/heads', 'refs/tags')
    counts = Counter()
    for line in refs.splitlines():
        fields = line.split(b' ', 2)
        if len(fields) != 3 or not OID.fullmatch(fields[1]):
            raise InspectError('GIT_REFS_INVALID')
        kind, _, name = fields
        if name.startswith(b'refs/heads/'):
            counts['local_branches'] += 1
        elif name.startswith(b'refs/tags/'):
            counts['annotated_tags' if kind == b'tag' else 'other_tags'] += 1
        else:
            raise InspectError('GIT_REFS_INVALID')
    # Remote names only, never URLs or network requests.
    remotes = query(root, exe, 'remote').splitlines()
    second = status()
    refs_again = query(root, exe, 'for-each-ref', '--format=%(objecttype) %(objectname) %(refname)', 'refs/heads', 'refs/tags')
    remote_again = query(root, exe, 'remote').splitlines()
    stable = first == second and refs == refs_again and remotes == remote_again
    return {'schema_version': 1, 'status': 'OBSERVED' if stable else 'STALE', **data,
            'refs': {k: counts[k] for k in ('local_branches', 'annotated_tags', 'other_tags')},
            'refs_sha256': hashlib.sha256(refs).hexdigest(), 'remote_count': len(remotes), 'snapshot_stable_observations': stable,
            'content_integrity': 'NOT_VERIFIED', 'remote_state': 'NOT_CHECKED',
            'submodule_worktrees': 'NOT_CHECKED'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    args = parser.parse_args()
    try:
        data = observe(args.root)
    except (InspectError, OSError) as exc:
        print(str(exc) if isinstance(exc, InspectError) else 'GIT_ROOT_UNAVAILABLE', file=sys.stderr)
        return 2
    print(json.dumps(data, sort_keys=True, indent=2))
    return int(data['status'] == 'STALE')

if __name__ == '__main__':
    sys.exit(main())
