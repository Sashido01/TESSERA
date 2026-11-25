#!/usr/bin/env python3
"""Plan independent skill tags, or explicitly publish from trusted verified main."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

SHA = re.compile(r'[0-9a-f]{40}\Z')
VERSION = re.compile(r'(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z')
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
# Reviewed historical backfill: name, exact first-parent commit, catalog tag object.
BACKFILL = {
    'microversion-release/v0.0.1': ('a550e0e638ca51a8a9b034773930da7ba5c25796', '70ff367c08de917b2374ee75cfc76707bab8c50c'),
    'project-audit/v0.0.1': ('9700c0f0a2dab9180cbb442538541242dcb5d5d7', 'd4697fa65ca77a687d8dea66e80a71089303b961'),
    'repository-workflow/v0.0.1': ('7fd8f698f818cbfabd7986d7c5e536d711f158b7', 'fec4f7059312009388c1322b42a31a558f2cc981'),
    'project-audit/v0.0.2': ('0983994f1fb21b79b8592351d6308c4acdc1ce13', '5979332e6eb1f107c61f2dd3c4684335df95c3d6'),
}


class TagError(ValueError):
    pass


def require(ok, code):
    if not ok:
        raise TagError(code)


def git(root, *args, missing=False):
    try:
        result = subprocess.run(['git', '--no-replace-objects', '-C', str(root), *args],
                                stdin=subprocess.DEVNULL, capture_output=True, check=False, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        raise TagError('SKILL_TAG_GIT_UNAVAILABLE') from None
    require(len(result.stdout) <= 8 * 1024 * 1024, 'SKILL_TAG_OUTPUT_LIMIT')
    if result.returncode:
        if missing and result.returncode == 1:
            return None
        raise TagError('SKILL_TAG_GIT_FAILED')
    return result.stdout.decode('utf-8', errors='strict').rstrip('\n')


def read_file(root, sha, path):
    entry = git(root, 'ls-tree', sha, '--', path)
    require(re.fullmatch(r'100(?:644|755) blob [0-9a-f]{40}\t' + re.escape(path), entry) is not None,
            'SKILL_TAG_FILE_INVALID')
    return git(root, 'show', f'{sha}:{path}')


def local_object(root, name):
    ref = 'refs/tags/' + name
    if git(root, 'show-ref', '--verify', '--quiet', ref, missing=True) is None:
        return None
    return git(root, 'show-ref', '--verify', '--hash', ref)


def verify_tag(root, name, target, obj):
    require(obj and SHA.fullmatch(obj), 'SKILL_TAG_OBJECT_INVALID')
    require(git(root, 'cat-file', '-t', obj) == 'tag', 'SKILL_TAG_NOT_ANNOTATED')
    header, sep, message = git(root, 'cat-file', '-p', obj).partition('\n\n')
    lines = header.splitlines()
    require(sep and message.strip() and lines[:3] == [f'object {target}', 'type commit', f'tag {name}'],
            'SKILL_TAG_TARGET_OR_MESSAGE_INVALID')


def remote_refs(root):
    data = {}
    for line in git(root, 'ls-remote', '--refs', 'origin', 'refs/heads/main', 'refs/tags/*').splitlines():
        obj, sep, ref = line.partition('\t')
        require(sep and SHA.fullmatch(obj) and ref not in data and
                (ref == 'refs/heads/main' or ref.startswith('refs/tags/')), 'SKILL_TAG_REMOTE_INVALID')
        data[ref] = obj
    return data


def plan(root, expected, *, backfill=BACKFILL):
    require(SHA.fullmatch(expected) and git(root, 'rev-parse', 'HEAD') == expected, 'SKILL_TAG_HEAD_MISMATCH')
    require(not git(root, 'status', '--porcelain=v1', '--untracked-files=all'), 'SKILL_TAG_DIRTY')
    require(git(root, 'rev-parse', '--is-shallow-repository') == 'false', 'SKILL_TAG_SHALLOW')
    skills = git(root, 'ls-tree', '--name-only', expected + ':skills').splitlines()
    require(0 < len(skills) <= 100 and all(SLUG.fullmatch(x) for x in skills), 'SKILL_TAG_SKILL_INVALID')
    rows = []
    seen = set()
    for skill in skills:
        path = f'skills/{skill}/'
        history = git(root, 'log', '--first-parent', '--format=%H', expected, '--', path + 'VERSION').splitlines()
        require(0 < len(history) <= 10000, 'SKILL_TAG_HISTORY_INVALID')
        require(read_file(root, expected, path + 'VERSION').strip() == read_file(root, history[0], path + 'VERSION').strip(),
                'SKILL_TAG_HISTORY_MISMATCH')
        for sha in reversed(history):
            require(SHA.fullmatch(sha), 'SKILL_TAG_HISTORY_INVALID')
            version = read_file(root, sha, path + 'VERSION').strip()
            require(VERSION.fullmatch(version), 'SKILL_TAG_VERSION_INVALID')
            read_file(root, sha, path + 'SKILL.md')
            for file in ('CHANGELOG.md', 'CHANGELOG.en.md'):
                require(re.search(r'(?m)^## ' + re.escape(version) + r'(?:\s|$)', read_file(root, sha, path + file)),
                        'SKILL_TAG_NOTES_MISSING')
            name = f'{skill}/v{version}'
            require(name not in seen, 'SKILL_TAG_DUPLICATE_VERSION')
            seen.add(name)
            catalog = read_file(root, sha, 'VERSION').strip()
            require(VERSION.fullmatch(catalog), 'SKILL_TAG_CATALOG_VERSION_INVALID')
            catalog_name = 'v' + catalog
            catalog_obj = local_object(root, catalog_name)
            verify_tag(root, catalog_name, sha, catalog_obj)
            obj = local_object(root, name)
            if obj:
                verify_tag(root, name, sha, obj)
            if name in backfill:
                require(backfill[name] == (sha, catalog_obj), 'SKILL_TAG_BACKFILL_MISMATCH')
            rows.append({'name': name, 'commit': sha, 'catalog': catalog_name,
                         'catalog_object': catalog_obj, 'local_object': obj,
                         'creation_allowed': sha == expected or name in backfill})
    require(set(backfill) <= seen, 'SKILL_TAG_BACKFILL_MISSING')
    return rows


def publish(root, expected, *, backfill=BACKFILL):
    rows = plan(root, expected, backfill=backfill)
    refs = remote_refs(root)
    require(refs.get('refs/heads/main') == expected, 'SKILL_TAG_REMOTE_MAIN_CHANGED')
    pending = []
    for row in rows:
        ref = 'refs/tags/' + row['name']
        require(refs.get('refs/tags/' + row['catalog']) == row['catalog_object'], 'SKILL_TAG_CATALOG_REMOTE_MISMATCH')
        if ref in refs:
            require(row['local_object'] == refs[ref], 'SKILL_TAG_REMOTE_MISMATCH')
        else:
            require(row['creation_allowed'], 'SKILL_TAG_HISTORICAL_RECOVERY_REQUIRED')
            pending.append(row)
    # All conflicts checked before any mutation. Local tags may remain after failed push.
    for row in pending:
        if not row['local_object']:
            git(root, '-c', 'user.name=github-actions[bot]', '-c', 'user.email=41898282+github-actions[bot]@users.noreply.github.com',
                'tag', '--no-sign', '-a', row['name'], row['commit'], '-m', f"Версия навыка {row['name']} — проверенный каталог {row['catalog']}")
        row['local_object'] = local_object(root, row['name'])
        verify_tag(root, row['name'], row['commit'], row['local_object'])
    require(remote_refs(root) == refs and git(root, 'rev-parse', 'HEAD') == expected, 'SKILL_TAG_REMOTE_CHANGED')
    if pending:
        git(root, 'push', '--atomic', 'origin', *['refs/tags/' + row['name'] for row in pending])
    after = remote_refs(root)
    require(after.get('refs/heads/main') == expected, 'SKILL_TAG_REMOTE_MAIN_CHANGED')
    for row in rows:
        require(after.get('refs/tags/' + row['name']) == row['local_object'] and
                after.get('refs/tags/' + row['catalog']) == row['catalog_object'], 'SKILL_TAG_REMOTE_MISMATCH')
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--expected-commit', required=True)
    parser.add_argument('--publish', action='store_true', help='Explicitly publish from trusted, verified main to origin')
    args = parser.parse_args()
    try:
        rows = (publish if args.publish else plan)(args.repo.resolve(), args.expected_commit)
    except (TagError, OSError, UnicodeError) as exc:
        print(str(exc) if isinstance(exc, TagError) else 'SKILL_TAG_INPUT_INVALID', file=sys.stderr)
        return 1
    print(json.dumps({'status': 'TAG_REFS_VERIFIED' if args.publish else 'PLAN_ONLY', 'tags': rows}, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
