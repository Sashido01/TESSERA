#!/usr/bin/env python3
"""Plan rechecks from two declared audit graphs; never reuse evidence automatically."""
from __future__ import annotations

import argparse
from collections import deque
import json
from pathlib import Path
import re
import sys

ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\Z')
SHA = re.compile(r'[0-9a-f]{64}\Z')
MAX_BYTES = 2 * 1024 * 1024
MAX_NODES = 2000
MAX_EDGES = 20000


class DeltaError(ValueError):
    pass


def require(ok, code):
    if not ok:
        raise DeltaError(code)


def fields(value, keys):
    require(isinstance(value, dict) and set(value) == set(keys), 'DELTA_SCHEMA')


def ident(value):
    require(isinstance(value, str) and ID.fullmatch(value), 'DELTA_ID')
    return value


def digest(value):
    require(value is None or isinstance(value, str) and SHA.fullmatch(value), 'DELTA_DIGEST')
    return value


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'DELTA_DUPLICATE_KEY')
        result[key] = value
    return result


def graph(value):
    fields(value, ('scope', 'context_sha256', 'coverage_declared_complete', 'nodes'))
    ident(value['scope'])
    digest(value['context_sha256'])
    require(type(value['coverage_declared_complete']) is bool, 'DELTA_COVERAGE')
    rows = value['nodes']
    require(isinstance(rows, list) and 0 < len(rows) <= MAX_NODES, 'DELTA_NODE_LIMIT')
    nodes = {}
    edges = 0
    for row in rows:
        fields(row, ('id', 'fingerprint', 'depends_on'))
        key = ident(row['id'])
        require(key not in nodes, 'DELTA_DUPLICATE_NODE')
        refs = row['depends_on']
        require(isinstance(refs, list) and len(refs) <= MAX_EDGES - edges, 'DELTA_EDGE_LIMIT')
        refs = [ident(x) for x in refs]
        require(len(set(refs)) == len(refs) and key not in refs, 'DELTA_EDGE')
        edges += len(refs)
        nodes[key] = (digest(row['fingerprint']), frozenset(refs))
    reverse = {key: [] for key in nodes}
    pending = {}
    for key, (_, refs) in nodes.items():
        require(refs <= nodes.keys(), 'DELTA_UNKNOWN_DEPENDENCY')
        pending[key] = len(refs)
        for dependency in refs:
            reverse[dependency].append(key)
    queue = deque(key for key, count in pending.items() if not count)
    visited = 0
    while queue:
        visited += 1
        for dependent in reverse[queue.popleft()]:
            pending[dependent] -= 1
            if not pending[dependent]:
                queue.append(dependent)
    require(visited == len(nodes), 'DELTA_CYCLE')
    return nodes, reverse


def plan(data):
    fields(data, ('schema_version', 'previous', 'current'))
    require(type(data['schema_version']) is int and data['schema_version'] == 1, 'DELTA_SCHEMA_VERSION')
    previous, current = data['previous'], data['current']
    old, _ = graph(previous)
    new, reverse = graph(current)
    global_reasons = []
    if previous['scope'] != current['scope']:
        global_reasons.append('SCOPE_CHANGED')
    if not previous['coverage_declared_complete'] or not current['coverage_declared_complete']:
        global_reasons.append('INCOMPLETE_DECLARED_COVERAGE')
    if (previous['context_sha256'] is None or current['context_sha256'] is None
            or previous['context_sha256'] != current['context_sha256']):
        global_reasons.append('CONTEXT_CHANGED_OR_UNKNOWN')
    if old.keys() != new.keys() or any(old[k][1] != new[k][1] for k in old.keys() & new.keys()):
        global_reasons.append('GRAPH_CHANGED')
    reasons = {}
    if global_reasons:
        reasons = {key: 'FULL_RECHECK_REQUIRED' for key in new}
    else:
        for key, (value, _) in new.items():
            prior = old[key][0]
            if value is None or prior is None:
                reasons[key] = 'UNKNOWN_FINGERPRINT'
            elif value != prior:
                reasons[key] = 'FINGERPRINT_CHANGED'
        queue = deque(reasons)
        while queue:
            for dependent in reverse[queue.popleft()]:
                if dependent not in reasons:
                    reasons[dependent] = 'DEPENDENCY_CHANGED_OR_UNKNOWN'
                    queue.append(dependent)
    return {
        'schema_version': 1,
        'status': 'PLAN_ONLY',
        'mode': 'FULL_RECHECK' if global_reasons else 'DECLARED_DELTA',
        'global_reasons': global_reasons,
        'nodes_total': len(new),
        'recheck_required': [{'id': key, 'reason': reasons[key]} for key in sorted(reasons)],
        'unchanged_declared_inputs': sorted(new.keys() - reasons.keys()),
        'removed_nodes': sorted(old.keys() - new.keys()),
        'coverage_authenticity': 'NOT_VERIFIED',
        'fingerprint_authenticity': 'NOT_VERIFIED',
        'evidence_reuse': 'NOT_AUTHORIZED',
        'audit_status': 'NOT_VERIFIED',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    args = parser.parse_args()
    try:
        with args.manifest.open('rb') as source:
            raw = source.read(MAX_BYTES + 1)
        require(len(raw) <= MAX_BYTES, 'DELTA_INPUT_LIMIT')
        result = plan(json.loads(raw, object_pairs_hook=unique_pairs))
    except (DeltaError, OSError, UnicodeError, ValueError, RecursionError) as exc:
        print(str(exc) if isinstance(exc, DeltaError) else 'DELTA_INPUT_INVALID', file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
