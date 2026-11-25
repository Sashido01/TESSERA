#!/usr/bin/env python3
"""Verify the pinned SkillSpector wheel without importing or extracting it."""
from __future__ import annotations

import argparse
import base64
import configparser
import csv
from email.parser import BytesParser
from email.policy import default
import hashlib
import io
import json
from pathlib import Path
import re
import stat
import subprocess
import sys
import zipfile

SOURCE = 'c323ad4c43e3c8f2de051572cc25b2711d11e648'
WHEEL_SHA256 = 'e2356aa11f0d484f789543f25da6208fe2408641c8b16e7b59bc6600c5c39ffb'
WHEEL_SIZE = 1342092
WHEEL_NAME = 'skillspector-2.13.7-py3-none-any.whl'
DIST = 'skillspector-2.13.7.dist-info/'
RECORD = DIST + 'RECORD'
REQUIRED = {DIST + x for x in ('METADATA', 'WHEEL', 'entry_points.txt', 'RECORD')}
LICENSES = {DIST + prefix + name for prefix in ('', 'licenses/')
            for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md')}
MAX_ENTRY = 8 * 1024 * 1024
MAX_TOTAL = 16 * 1024 * 1024
MAX_ENTRIES = 512
PATH = re.compile(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\Z')


class WheelError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise WheelError(code)


def git_blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def safe_name(name):
    return PATH.fullmatch(name) is not None and all(x not in ('.', '..') for x in name.split('/'))


def source_manifest(source):
    # Source is the separately pinned, trusted upstream checkout. Read Git objects,
    # not checked-out files (which may have platform newline transformations).
    run = subprocess.run(['git', '--no-replace-objects', '-C', str(source), 'ls-tree',
                          '-r', '-z', SOURCE, '--', 'src/skillspector', 'LICENSE',
                          'THIRD_PARTY_NOTICES.md'], stdin=subprocess.DEVNULL,
                         capture_output=True, timeout=20, check=False)
    require(run.returncode == 0 and len(run.stdout) <= 1024 * 1024, 'WHEEL_SOURCE_TREE')
    entries = {}
    for row in run.stdout.split(b'\0')[:-1]:
        header, path = row.decode('ascii').split('\t', 1)
        mode, kind, oid = header.split()
        require(mode == '100644' and kind == 'blob' and re.fullmatch('[0-9a-f]{40}', oid),
                'WHEEL_SOURCE_ENTRY')
        if path.startswith('src/skillspector/'):
            name = path[4:]
        else:
            require(path in ('LICENSE', 'THIRD_PARTY_NOTICES.md'), 'WHEEL_SOURCE_ENTRY')
            name = path
        require(safe_name(name) and name not in entries, 'WHEEL_SOURCE_ENTRY')
        entries[name] = oid
    require(run.stdout.endswith(b'\0') and len(entries) == 171 and
            sum(name.startswith('skillspector/') for name in entries) == 169 and
            {'LICENSE', 'THIRD_PARTY_NOTICES.md'} <= set(entries), 'WHEEL_SOURCE_COUNT')
    return entries


def inspect(raw, source):
    package = {name for name in source if name.startswith('skillspector/')}
    files = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        require(0 < len(infos) <= MAX_ENTRIES, 'WHEEL_ENTRY_LIMIT')
        total = 0
        seen = set()
        for info in infos:
            name = info.filename
            mode = stat.S_IFMT(info.external_attr >> 16)
            require(safe_name(name) and name.casefold() not in seen and not info.is_dir()
                    and mode in (0, stat.S_IFREG) and not (info.flag_bits & 1)
                    and info.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED),
                    'WHEEL_ENTRY_INVALID')
            seen.add(name.casefold())
            require(name in package | REQUIRED | LICENSES, 'WHEEL_ENTRY_UNEXPECTED')
            total += info.file_size
            require(info.file_size <= MAX_ENTRY and total <= MAX_TOTAL, 'WHEEL_SIZE_LIMIT')
            data = archive.read(info)
            require(len(data) == info.file_size, 'WHEEL_ENTRY_SIZE')
            files[name] = data
    require(package | REQUIRED <= set(files), 'WHEEL_ENTRY_MISSING')
    for name in package:
        require(git_blob(files[name]) == source[name], 'WHEEL_SOURCE_MISMATCH')
    for name in LICENSES & set(files):
        require(git_blob(files[name]) == source[name.rsplit('/', 1)[-1]], 'WHEEL_LICENSE_MISMATCH')
    records = {}
    for row in csv.reader(io.StringIO(files[RECORD].decode('utf-8'), newline=''), strict=True):
        require(len(row) == 3 and row[0] not in records, 'WHEEL_RECORD_INVALID')
        records[row[0]] = row[1:]
    require(set(records) == set(files) and records[RECORD] == ['', ''], 'WHEEL_RECORD_COVERAGE')
    for name, data in files.items():
        if name != RECORD:
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode('ascii').rstrip('=')
            require(records[name] == ['sha256=' + digest, str(len(data))], 'WHEEL_RECORD_MISMATCH')
    metadata = BytesParser(policy=default).parsebytes(files[DIST + 'METADATA'])
    require(metadata.get_all('Name') == ['skillspector'] and metadata.get_all('Version') == ['2.13.7'],
            'WHEEL_METADATA')
    wheel = BytesParser(policy=default).parsebytes(files[DIST + 'WHEEL'])
    require(wheel.get_all('Root-Is-Purelib') == ['true'] and wheel.get_all('Tag') == ['py3-none-any'],
            'WHEEL_FORMAT')
    entry = configparser.ConfigParser(interpolation=None, strict=True)
    entry.read_string(files[DIST + 'entry_points.txt'].decode('utf-8'))
    require(not entry.defaults() and entry.sections() == ['console_scripts'] and
            dict(entry['console_scripts']) == {'skillspector': 'skillspector.cli_entry:app'},
            'WHEEL_ENTRYPOINT')
    return {'package_files': len(package), 'wheel_files': len(files), 'record_files': len(records),
            'source_blob_match': 'PASS', 'record': 'PASS', 'execution': 'NOT_RUN'}


def verify(path, source):
    require(path.name == WHEEL_NAME and path.is_file() and not path.is_symlink(), 'WHEEL_PATH')
    with path.open('rb') as stream:
        raw = stream.read(WHEEL_SIZE + 1)
    require(len(raw) == WHEEL_SIZE and hashlib.sha256(raw).hexdigest() == WHEEL_SHA256, 'WHEEL_PIN')
    return {**inspect(raw, source_manifest(source)), 'sha256': WHEEL_SHA256, 'source_commit': SOURCE}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel', required=True, type=Path)
    parser.add_argument('--source', required=True, type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.wheel, args.source)
    except (WheelError, OSError, ValueError, KeyError, UnicodeError, zipfile.BadZipFile,
            RuntimeError, csv.Error, configparser.Error, subprocess.SubprocessError) as exc:
        print('BLOCKED: ' + (str(exc) if isinstance(exc, WheelError) else 'WHEEL_INVALID'), file=sys.stderr)
        return 1
    print('SKILLSPECTOR_WHEEL_PROVENANCE_PASS: ' + json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
