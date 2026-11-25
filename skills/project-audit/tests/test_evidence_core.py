from pathlib import Path
import copy
import json
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import evidence_core as m

DIGEST = 'a' * 64


def record(name='E1', **changes):
    return {'id': name, 'snapshot_id': 'S1', 'fingerprint': DIGEST, 'scope': 'unit',
            'kind': 'CHECK', 'result': 'PASS', 'source': 'fixture-result',
            'observed_at': '2026-11-25T10:00:00Z', 'limitations': [], **changes}


def register(*rows, fingerprint=DIGEST, refs=None):
    return {'schema_version': 1, 'snapshot': {'id': 'S1', 'fingerprint': fingerprint, 'as_of': '2026-11-25T11:00:00Z'},
            'evidence': list(rows), 'criteria': [{'id': 'C1', 'scope': 'unit', 'evidence_ids': [x['id'] for x in rows] if refs is None else refs}]}


class EvidenceTests(unittest.TestCase):
    def result(self, *rows, **kwargs):
        return m.evaluate(register(*rows, **kwargs))

    def test_pass_is_not_complete(self):
        r = self.result(record())
        self.assertEqual(r['criteria'][0]['state'], 'PASS_RECORDED')
        self.assertEqual(r['implementation_status'], 'NOT_VERIFIED')
        self.assertEqual(r['source_authenticity'], 'NOT_VERIFIED')

    def test_failure_preserved(self):
        self.assertEqual(self.result(record(result='FAIL'))['criteria'][0]['state'], 'FAIL_RECORDED')

    def test_conflict_preserved(self):
        r = self.result(record(), record('E2', result='FAIL'))['criteria'][0]
        self.assertEqual((r['state'], r['pass'], r['fail']), ('CONFLICTING', ['E1'], ['E2']))

    def test_other_snapshot_and_digest_stale(self):
        r = self.result(record(snapshot_id='S0'), record('E2', fingerprint='b' * 64))['criteria'][0]
        self.assertEqual((r['state'], r['stale']), ('STALE', ['E1', 'E2']))

    def test_null_fingerprint_not_bound(self):
        for kwargs, row in (({'fingerprint': None}, record()), ({}, record(fingerprint=None))):
            self.assertEqual(self.result(row, **kwargs)['criteria'][0]['state'], 'NOT_VERIFIED')

    def test_scope_mismatch(self):
        r = self.result(record(scope='integration'))['criteria'][0]
        self.assertEqual((r['state'], r['scope_mismatch']), ('NOT_VERIFIED', ['E1']))

    def test_owner_inference_and_observation_not_check(self):
        r = self.result(record(kind='OWNER_REPORT'), record('E2', kind='INFERENCE'), record('E3', kind='OBSERVATION'))['criteria'][0]
        self.assertEqual((r['state'], len(r['indirect'])), ('NOT_VERIFIED', 3))

    def test_not_run_and_empty(self):
        self.assertEqual(self.result(record(result='NOT_RUN'))['criteria'][0]['state'], 'NOT_VERIFIED')
        self.assertEqual(self.result()['criteria'][0]['state'], 'NOT_VERIFIED')

    def test_duplicate_ids_and_bad_references(self):
        for data in (register(record(), record()), register(record(), refs=['unknown']), register(record(), refs=['E1','E1'])):
            with self.assertRaises(m.EvidenceError): m.evaluate(data)

    def test_duplicate_criteria(self):
        data = register(record()); data['criteria'].append(copy.deepcopy(data['criteria'][0]))
        with self.assertRaisesRegex(m.EvidenceError, 'DUPLICATE_CRITERION'): m.evaluate(data)

    def test_future_and_invalid_time(self):
        for value in ('2026-11-25T12:00:00Z', '2026-02-30T10:00:00Z', '2026-11-25'):
            with self.assertRaises(m.EvidenceError): self.result(record(observed_at=value))

    def test_invalid_fingerprint_and_schema(self):
        for value in ('bad', 1, {}):
            with self.assertRaises(m.EvidenceError): self.result(record(fingerprint=value))
        data = register(record()); data['schema_version'] = True
        with self.assertRaises(m.EvidenceError): m.evaluate(data)

    def test_scope_and_private_text_not_emitted(self):
        r = self.result(record(source='private-locator', limitations=['private detail']))
        self.assertNotIn('private', json.dumps(r))

    def test_canonical_digest_and_counts(self):
        d = register(record()); d['criteria'].append({'id':'C2','scope':'other','evidence_ids':[]})
        r = m.evaluate(d)
        self.assertEqual(r['criteria_total'], sum(r['counts'].values()))
        self.assertEqual(r, m.evaluate(dict(reversed(list(d.items())))))

    def test_cli_duplicate_key_and_valid_register(self):
        runner = Path(m.__file__)
        with tempfile.TemporaryDirectory() as t:
            path = Path(t) / 'input.json'
            path.write_text('{"schema_version":1,"schema_version":1}', encoding='utf-8')
            args = [sys.executable, '-B', str(runner), '--register', str(path)]
            proc = subprocess.run(args, capture_output=True, text=True, timeout=10)
            self.assertEqual(proc.returncode, 2); self.assertIn('EVIDENCE_DUPLICATE_KEY', proc.stderr)
            path.write_text(json.dumps(register(record())), encoding='utf-8')
            proc = subprocess.run(args, capture_output=True, text=True, timeout=10)
            self.assertEqual(proc.returncode, 0); self.assertEqual(json.loads(proc.stdout)['status'], 'REGISTER_VALIDATED')


if __name__ == '__main__':
    unittest.main()
