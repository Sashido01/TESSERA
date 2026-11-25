#!/usr/bin/env python3
"""Validate a supplied evidence register; never infer actual project completion."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys

ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\Z')
SHA = re.compile(r'[0-9a-f]{64}\Z')
UTC = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z')
KINDS = frozenset({'CHECK', 'OBSERVATION', 'OWNER_REPORT', 'INFERENCE'})
RESULTS = frozenset({'PASS', 'FAIL', 'NOT_RUN', 'UNKNOWN'})
MAX_BYTES = 2 * 1024 * 1024
MAX_ROWS = 2000


class EvidenceError(ValueError):
    pass


def require(ok, code):
    if not ok:
        raise EvidenceError(code)


def fields(value, expected):
    require(isinstance(value, dict) and set(value) == set(expected), 'EVIDENCE_SCHEMA_INVALID')


def ident(value):
    require(isinstance(value, str) and ID.fullmatch(value), 'EVIDENCE_ID_INVALID')
    return value


def fingerprint(value):
    require(value is None or isinstance(value, str) and SHA.fullmatch(value), 'EVIDENCE_FINGERPRINT_INVALID')
    return value


def utc(value):
    require(isinstance(value, str) and UTC.fullmatch(value), 'EVIDENCE_TIME_INVALID')
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise EvidenceError('EVIDENCE_TIME_INVALID') from None


def bounded_text(value):
    require(isinstance(value, str) and 0 < len(value.strip()) <= 512 and
            not any(ord(c) < 32 or 0xd800 <= ord(c) <= 0xdfff for c in value), 'EVIDENCE_TEXT_INVALID')
    return value


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'EVIDENCE_DUPLICATE_KEY')
        result[key] = value
    return result


def evaluate(data):
    fields(data, ('schema_version', 'snapshot', 'evidence', 'criteria'))
    require(type(data['schema_version']) is int and data['schema_version'] == 1, 'EVIDENCE_SCHEMA_VERSION')
    current = data['snapshot']
    fields(current, ('id', 'fingerprint', 'as_of'))
    sid = ident(current['id'])
    digest = fingerprint(current['fingerprint'])
    as_of = utc(current['as_of'])
    records = {}
    rows = data['evidence']
    require(isinstance(rows, list) and len(rows) <= MAX_ROWS, 'EVIDENCE_SIZE')
    for row in rows:
        fields(row, ('id', 'snapshot_id', 'fingerprint', 'scope', 'kind', 'result', 'source', 'observed_at', 'limitations'))
        name = ident(row['id'])
        require(name not in records, 'EVIDENCE_DUPLICATE_ID')
        ident(row['snapshot_id']); fingerprint(row['fingerprint']); ident(row['scope'])
        require(isinstance(row['kind'], str) and row['kind'] in KINDS and
                isinstance(row['result'], str) and row['result'] in RESULTS, 'EVIDENCE_ENUM_INVALID')
        bounded_text(row['source'])
        require(utc(row['observed_at']) <= as_of, 'EVIDENCE_FUTURE_OBSERVATION')
        limits = row['limitations']
        require(isinstance(limits, list) and len(limits) <= 32, 'EVIDENCE_LIMITATIONS_INVALID')
        for item in limits:
            bounded_text(item)
        records[name] = row
    criteria = data['criteria']
    require(isinstance(criteria, list) and 0 < len(criteria) <= MAX_ROWS, 'EVIDENCE_SIZE')
    seen = set()
    output = []
    for item in criteria:
        fields(item, ('id', 'scope', 'evidence_ids'))
        name = ident(item['id']); scope = ident(item['scope'])
        require(name not in seen, 'EVIDENCE_DUPLICATE_CRITERION')
        seen.add(name)
        refs = item['evidence_ids']
        require(isinstance(refs, list) and len(refs) <= 100, 'EVIDENCE_REFERENCES_INVALID')
        refs = [ident(x) for x in refs]
        require(len(set(refs)) == len(refs) and all(x in records for x in refs), 'EVIDENCE_REFERENCES_INVALID')
        classified = {k: [] for k in ('pass', 'fail', 'stale', 'unbound', 'scope_mismatch', 'indirect', 'not_run')}
        for key in sorted(refs):
            row = records[key]
            if row['scope'] != scope:
                bucket = 'scope_mismatch'
            elif row['snapshot_id'] != sid or (digest is not None and row['fingerprint'] is not None and row['fingerprint'] != digest):
                bucket = 'stale'
            elif digest is None or row['fingerprint'] is None:
                bucket = 'unbound'
            elif row['kind'] != 'CHECK':
                bucket = 'indirect'
            elif row['result'] == 'PASS':
                bucket = 'pass'
            elif row['result'] == 'FAIL':
                bucket = 'fail'
            else:
                bucket = 'not_run'
            classified[bucket].append(key)
        if classified['pass'] and classified['fail']:
            state = 'CONFLICTING'
        elif classified['fail']:
            state = 'FAIL_RECORDED'
        elif classified['pass']:
            state = 'PASS_RECORDED'
        elif classified['stale']:
            state = 'STALE'
        else:
            state = 'NOT_VERIFIED'
        output.append({'id': name, 'scope': scope, 'state': state, **classified})
    output.sort(key=lambda x: x['id'])
    counts = Counter(x['state'] for x in output)
    canonical = json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('ascii')
    return {'schema_version': 1, 'status': 'REGISTER_VALIDATED', 'snapshot_id': sid,
            'register_sha256': hashlib.sha256(canonical).hexdigest(),
            'criteria_total': len(output), 'counts': dict(sorted(counts.items())), 'criteria': output,
            'source_authenticity': 'NOT_VERIFIED', 'content_integrity': 'NOT_VERIFIED',
            'implementation_status': 'NOT_VERIFIED'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--register', required=True, type=Path)
    args = parser.parse_args()
    try:
        with args.register.open('rb') as source:
            raw = source.read(MAX_BYTES + 1)
        require(len(raw) <= MAX_BYTES, 'EVIDENCE_SIZE')
        result = evaluate(json.loads(raw, object_pairs_hook=unique_pairs))
    except (EvidenceError, OSError, UnicodeError, ValueError, RecursionError) as exc:
        print(str(exc) if isinstance(exc, EvidenceError) else 'EVIDENCE_INPUT_INVALID', file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
