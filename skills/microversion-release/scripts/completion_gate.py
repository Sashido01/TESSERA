#!/usr/bin/env python3
"""Read-only structural completion gate for an explicitly selected Git project."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

OID = re.compile(r'(?:[0-9a-f]{40}|[0-9a-f]{64})\Z')
VERSION = re.compile(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z')
MAX_COMMITS = 32
MAX_OUTPUT = 2 * 1024 * 1024
MAX_HOOK_INPUT = 256 * 1024
SYSTEM_ENV = ('PATH', 'HOME', 'USERPROFILE', 'HOMEDRIVE', 'HOMEPATH', 'SystemRoot',
              'WINDIR', 'COMSPEC', 'PATHEXT', 'TEMP', 'TMP', 'TMPDIR', 'APPDATA',
              'LOCALAPPDATA', 'LANG', 'LC_ALL', 'LC_CTYPE', 'TZ')


class GateError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise GateError(code)


def version_parts(value):
    require(isinstance(value, str) and len(value) <= 64 and VERSION.fullmatch(value),
            'GATE_VERSION_INVALID')
    parts = tuple(map(int, value.split('.')))
    require(parts[1] <= 99, 'GATE_VERSION_INVALID')
    return parts


def transition(previous, current):
    major, minor, patch = version_parts(previous)
    actual = version_parts(current)
    if actual == (major, minor, patch + 1):
        return 'WORK'
    release = (major, minor + 1, 0) if minor < 99 else (major + 1, 0, 0)
    require(patch >= 99 and actual == release, 'GATE_TRANSITION_INVALID')
    return 'RELEASE'


def entry_count(body, version):
    """Count exact structural version headings, not semantic changelog quality."""
    return len(re.findall(r'(?m)^## ' + re.escape(version) + r'(?:[ \t]|\r?$)', body))


def release_version(value):
    major, minor, patch = version_parts(value)
    return patch == 0 and (major != 0 or minor != 0)


class Inspector:
    def __init__(self, repo):
        # Unlike a test fixture, never strip inherited Git policy and proceed.
        require(not any(k.upper().startswith('GIT_') and k.upper() != 'GIT_PAGER'
                        for k in os.environ), 'GATE_GIT_CONTEXT_UNSAFE')
        self.repo = repo.resolve(strict=True)
        self.env = {k: os.environ[k] for k in SYSTEM_ENV if k in os.environ}
        self.env.update(GIT_NO_LAZY_FETCH='1', GIT_TERMINAL_PROMPT='0', GIT_ALLOW_PROTOCOL='')
        self.executable = None
        for item in self.env.get('PATH', '').split(os.pathsep):
            directory = Path(item)
            if not directory.is_absolute():
                continue
            candidate = directory / ('git.exe' if os.name == 'nt' else 'git')
            if candidate.is_file() and os.access(candidate, os.X_OK):
                self.executable = candidate.resolve(strict=True)
                break
        require(self.executable is not None, 'GATE_GIT_UNAVAILABLE')
        self.deadline = time.monotonic() + 30

    def git(self, *args):
        remaining = self.deadline - time.monotonic()
        require(remaining > 0, 'GATE_TIMEOUT')
        try:
            result = subprocess.run([str(self.executable), '--no-replace-objects', '--no-optional-locks',
                                     '-c', 'core.fsmonitor=false', '-c', 'core.untrackedCache=false',
                                     '-C', str(self.repo), *args], env=self.env, stdin=subprocess.DEVNULL,
                                    capture_output=True, timeout=min(remaining, 5), check=False)
        except subprocess.TimeoutExpired as exc:
            raise GateError('GATE_TIMEOUT') from exc
        require(time.monotonic() < self.deadline, 'GATE_TIMEOUT')
        require(result.returncode == 0, 'GATE_GIT_FAILED')
        require(len(result.stdout) + len(result.stderr) <= MAX_OUTPUT, 'GATE_OUTPUT_LIMIT')
        return result.stdout.decode('utf-8', errors='strict')

    def head(self):
        value = self.git('rev-parse', '--verify', 'HEAD^{commit}').strip()
        require(OID.fullmatch(value), 'GATE_HEAD_INVALID')
        return value

    def clean(self):
        # Git status alone can hide assume-unchanged and skip-worktree paths.
        flags = self.git('ls-files', '-v', '-z').split('\0')
        require(all(row.startswith('H ') for row in flags if row), 'GATE_INDEX_FLAGS_UNSAFE')
        require(not self.git('status', '--porcelain=v1', '-z', '--untracked-files=all',
                             '--ignore-submodules=none'), 'GATE_DIRTY')

    def file(self, commit, name):
        record = self.git('ls-tree', '-z', commit, '--', name)
        require(re.fullmatch(r'100(?:644|755) blob [0-9a-f]{40,64}\t' + re.escape(name) + r'\x00', record),
                'GATE_METADATA_INVALID')
        return self.git('show', commit + ':' + name)

    def version(self, commit):
        value = self.file(commit, 'VERSION').strip()
        version_parts(value)
        return value

    def tag(self, commit, version):
        ref = 'refs/tags/v' + version
        oid = self.git('rev-parse', '--verify', ref).strip()
        require(OID.fullmatch(oid) and self.git('cat-file', '-t', oid).strip() == 'tag',
                'GATE_TAG_INVALID')
        header, sep, body = self.git('cat-file', '-p', oid).partition('\n\n')
        require(sep and body.strip() and header.splitlines()[:3] ==
                ['object ' + commit, 'type commit', 'tag v' + version], 'GATE_TAG_INVALID')
        return ref, oid

    def check(self, baseline, bilingual=False):
        require(isinstance(baseline, str) and OID.fullmatch(baseline), 'GATE_BASELINE_INVALID')
        require(Path(self.git('rev-parse', '--show-toplevel').strip()).resolve() == self.repo,
                'GATE_ROOT_MISMATCH')
        self.clean()
        head = self.head()
        require(self.git('rev-parse', '--verify', baseline + '^{commit}').strip() == baseline,
                'GATE_BASELINE_INVALID')
        previous, version = baseline, self.version(baseline)
        rows = self.git('rev-list', '--parents', '--reverse', '--max-count=' + str(MAX_COMMITS + 1),
                        baseline + '..' + head).splitlines()
        require(len(rows) <= MAX_COMMITS, 'GATE_COMMIT_LIMIT')
        changelogs = ['CHANGELOG.md'] + (['CHANGELOG.en.md'] if bilingual else [])
        metadata = {'VERSION', *changelogs}
        all_metadata = {'VERSION', 'CHANGELOG.md', 'CHANGELOG.en.md'}
        previous_logs = {name: self.file(baseline, name) for name in changelogs}
        for body in previous_logs.values():
            require(entry_count(body, version) == 1, 'GATE_BASELINE_CHANGELOG_INVALID')
        tags = [self.tag(baseline, version)] if release_version(version) else []
        for row in rows:
            parts = row.split()
            require(len(parts) == 2 and OID.fullmatch(parts[0]) and parts[1] == previous,
                    'GATE_NONLINEAR_OR_BASELINE_MISMATCH')
            commit = parts[0]
            current = self.version(commit)
            kind = transition(version, current)
            changed = set(self.git('diff-tree', '--no-commit-id', '--name-only', '-r', '-z',
                                   '--no-renames', previous, commit).split('\0')) - {''}
            require(metadata <= changed and bool(changed - all_metadata), 'GATE_METADATA_ONLY_OR_MISSING')
            for name in changelogs:
                body = self.file(commit, name)
                require(entry_count(previous_logs[name], current) == 0,
                        'GATE_CHANGELOG_PREDECLARED')
                require(entry_count(body, current) == 1, 'GATE_CHANGELOG_MISSING_OR_DUPLICATE')
                require(entry_count(body, version) == 1, 'GATE_CHANGELOG_PREVIOUS_LOST')
                previous_logs[name] = body
            if kind == 'RELEASE':
                tags.append(self.tag(commit, current))
            previous, version = commit, current
        require(previous == head, 'GATE_BASELINE_MISMATCH')
        self.clean()
        require(self.head() == head, 'GATE_STALE')
        for ref, oid in tags:
            require(self.git('rev-parse', '--verify', ref).strip() == oid, 'GATE_STALE')
        return {'status': 'STRUCTURE_VERIFIED', 'commit': head, 'baseline': baseline,
                'version': version, 'commits_checked': len(rows), 'tags_checked': len(tags),
                'tag_objects': [{'ref': ref, 'oid': oid} for ref, oid in tags],
                'test_execution': 'NOT_RUN', 'release_readiness': 'NOT_VERIFIED'}


def check(repo, baseline, bilingual=False):
    try:
        return Inspector(repo).check(baseline, bilingual)
    except (GateError, OSError, UnicodeError, ValueError, RuntimeError) as exc:
        return {'status': 'BLOCKED', 'reason': str(exc) if isinstance(exc, GateError) else 'GATE_RUNTIME_FAILED',
                'test_execution': 'NOT_RUN', 'release_readiness': 'NOT_VERIFIED'}


def unique_pairs(pairs):
    data = {}
    for key, value in pairs:
        require(key not in data, 'GATE_HOOK_DUPLICATE_KEY')
        data[key] = value
    return data


def stop_hook(raw, repo, baseline, marker, bilingual=False):
    """One continuation per owner-selected run marker; no automatic deletion."""
    reason = 'GATE_HOOK_INPUT_INVALID'
    try:
        require(len(raw) <= MAX_HOOK_INPUT, reason)
        payload = json.loads(raw, object_pairs_hook=unique_pairs)
        require(isinstance(payload, dict) and payload.get('hook_event_name') == 'Stop'
                and type(payload.get('stop_hook_active')) is bool, reason)
        cwd = payload.get('cwd')
        require(isinstance(cwd, str) and os.path.isabs(cwd) and
                os.path.normcase(os.path.normpath(cwd)) == os.path.normcase(str(repo.resolve(strict=True))),
                'GATE_HOOK_SCOPE_MISMATCH')
        result = check(repo, baseline, bilingual)
        if result['status'] == 'STRUCTURE_VERIFIED':
            return {'systemMessage': 'TESSERA STRUCTURE_VERIFIED; tests and release readiness require independent verification.'}
        reason = result['reason']
        if not payload['stop_hook_active']:
            require(marker.is_absolute() and marker.parent.is_dir() and
                    not marker.parent.resolve().is_relative_to(repo.resolve()), 'GATE_MARKER_INVALID')
            # Exclusive create, no existing marker is read, rewritten or deleted.
            with marker.open('xb') as stream:
                stream.write(b'TESSERA continuation used\n')
            return {'decision': 'block', 'reason': 'TESSERA BLOCKED: ' + reason +
                    '. Correct only authorized changes; never bypass policy. If blocked report BLOCKED.'}
    except FileExistsError:
        pass
    except (GateError, OSError, UnicodeError, ValueError, RuntimeError):
        reason = 'GATE_HOOK_INPUT_OR_MARKER_FAILED'
    return {'continue': False, 'stopReason': 'TESSERA BLOCKED: ' + reason +
            '; independent acceptance required.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('check', 'stop'))
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--bilingual', action='store_true')
    parser.add_argument('--marker', type=Path)
    args = parser.parse_args()
    if args.mode == 'stop':
        if args.marker is None:
            print(json.dumps({'continue': False, 'stopReason': 'TESSERA BLOCKED: GATE_MARKER_REQUIRED'}))
            return 0
        result = stop_hook(sys.stdin.buffer.read(MAX_HOOK_INPUT + 1), args.repo, args.baseline,
                           args.marker, args.bilingual)
        print(json.dumps(result, sort_keys=True))
        return 0
    result = check(args.repo, args.baseline, args.bilingual)
    print(json.dumps(result, sort_keys=True))
    return int(result['status'] != 'STRUCTURE_VERIFIED')


if __name__ == '__main__':
    sys.exit(main())
