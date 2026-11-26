"""Synthetic graph fixtures; no project or network access."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'scripts' / 'delta_plan.py'
spec = importlib.util.spec_from_file_location('delta_plan_fixture', SOURCE)
delta = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delta)
A, B = 'a' * 64, 'b' * 64


def fixture():
    previous = {'scope': 'demo', 'context_sha256': A, 'coverage_declared_complete': True,
                'nodes': [{'id': name, 'fingerprint': A, 'depends_on': refs}
                          for name, refs in [('input', []), ('test', ['input']),
                                             ('report', ['test']), ('unrelated', [])]]}
    return {'schema_version': 1, 'previous': previous, 'current': copy.deepcopy(previous)}


def affected(result):
    return {x['id'] for x in result['recheck_required']}


class DeltaTests(unittest.TestCase):
    def test_unchanged_does_not_authorize_reuse(self):
        result = delta.plan(fixture())
        self.assertEqual(result['recheck_required'], [])
        self.assertEqual(len(result['unchanged_declared_inputs']), 4)
        self.assertEqual(result['evidence_reuse'], 'NOT_AUTHORIZED')
        self.assertEqual(result['audit_status'], 'NOT_VERIFIED')

    def test_transitive_invalidation(self):
        data = fixture()
        data['current']['nodes'][0]['fingerprint'] = B
        self.assertEqual(affected(delta.plan(data)), {'input', 'test', 'report'})

    def test_unknown_previous_and_current(self):
        for side in ('previous', 'current'):
            data = fixture()
            data[side]['nodes'][0]['fingerprint'] = None
            self.assertEqual(affected(delta.plan(data)), {'input', 'test', 'report'})

    def test_global_context_or_coverage(self):
        for key, value in [('context_sha256', B), ('context_sha256', None),
                           ('scope', 'other'), ('coverage_declared_complete', False)]:
            with self.subTest(key=key, value=value):
                data = fixture()
                data['current'][key] = value
                result = delta.plan(data)
                self.assertEqual(result['mode'], 'FULL_RECHECK')
                self.assertEqual(len(affected(result)), 4)

    def test_removed_node(self):
        data = fixture()
        data['current']['nodes'].pop()
        result = delta.plan(data)
        self.assertEqual(result['removed_nodes'], ['unrelated'])
        self.assertEqual(len(affected(result)), 3)

    def test_added_node(self):
        data = fixture()
        data['current']['nodes'].append({'id': 'new', 'fingerprint': A, 'depends_on': []})
        self.assertEqual(len(affected(delta.plan(data))), 5)

    def test_topology_change(self):
        data = fixture()
        data['current']['nodes'][3]['depends_on'] = ['input']
        self.assertEqual(len(affected(delta.plan(data))), 4)

    def test_order_independent(self):
        data = fixture()
        before = delta.plan(data)
        data['current']['nodes'].reverse()
        self.assertEqual(delta.plan(data), before)

    def test_bad_edges_and_cycles(self):
        for refs, code in [(['missing'], 'UNKNOWN_DEPENDENCY'), (['input'], 'EDGE'),
                           (['test', 'test'], 'EDGE'), (['report'], 'CYCLE')]:
            with self.subTest(code=code):
                data = fixture()
                data['current']['nodes'][0]['depends_on'] = refs
                with self.assertRaisesRegex(delta.DeltaError, code):
                    delta.plan(data)

    def test_bad_schema_and_digest(self):
        data = fixture()
        data['schema_version'] = True
        with self.assertRaisesRegex(delta.DeltaError, 'SCHEMA_VERSION'):
            delta.plan(data)
        data = fixture()
        data['current']['nodes'][0]['fingerprint'] = 'invalid'
        with self.assertRaisesRegex(delta.DeltaError, 'DIGEST'):
            delta.plan(data)

    def test_duplicate_node(self):
        data = fixture()
        data['current']['nodes'].append(data['current']['nodes'][0])
        with self.assertRaisesRegex(delta.DeltaError, 'DUPLICATE_NODE'):
            delta.plan(data)

    def test_long_chain(self):
        data = fixture()
        nodes = [{'id': f'n{i}', 'fingerprint': A,
                  'depends_on': [f'n{i-1}'] if i else []} for i in range(1500)]
        data['previous']['nodes'] = nodes
        data['current']['nodes'] = copy.deepcopy(nodes)
        data['current']['nodes'][0]['fingerprint'] = B
        self.assertEqual(len(affected(delta.plan(data))), 1500)

    def test_limits(self):
        data = fixture()
        data['current']['nodes'] = [None] * (delta.MAX_NODES + 1)
        with self.assertRaisesRegex(delta.DeltaError, 'NODE_LIMIT'):
            delta.plan(data)
        data = fixture()
        data['current']['nodes'][0]['depends_on'] = ['x'] * (delta.MAX_EDGES + 1)
        with self.assertRaisesRegex(delta.DeltaError, 'EDGE_LIMIT'):
            delta.plan(data)

    def test_cli_duplicate_json_key_and_valid_input(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'manifest.json'
            for raw, code in [('{"schema_version":1,"schema_version":1}', 2),
                              (json.dumps(fixture()), 0)]:
                source.write_text(raw, encoding='utf-8')
                result = subprocess.run([sys.executable, '-B', str(SOURCE), '--manifest', str(source)],
                                        capture_output=True, text=True, timeout=15, check=False)
                self.assertEqual(result.returncode, code)
                self.assertEqual(source.read_text(encoding='utf-8'), raw)
                if code == 0:
                    self.assertEqual(json.loads(result.stdout)['status'], 'PLAN_ONLY')
                else:
                    self.assertEqual(result.stderr.strip(), 'DELTA_DUPLICATE_KEY')


if __name__ == '__main__':
    unittest.main()
