"""Synthetic records and actual disposable Git; no production repository access."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'scripts' / 'worktree_inventory.py'
spec = importlib.util.spec_from_file_location('worktree_inventory_fixture', SOURCE)
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
A = b'a' * 40
BRANCH = b'refs/heads/main'


def row(path=b'/fixture', head=A, branch=BRANCH, extras=()):
    return b'\0'.join([b'worktree ' + path, b'HEAD ' + head,
                      b'branch ' + branch if branch else b'detached', *extras]) + b'\0\0'


class WorktreeTests(unittest.TestCase):
    def test_matching_and_absent_candidates(self):
        raw = row() + row(b'/other', branch=b'refs/heads/other')
        result = w.compare(raw, raw, [BRANCH, b'refs/heads/missing'])
        self.assertEqual(result['candidate_checks'], [{'index': 1, 'matching_worktrees': 1},
                                                       {'index': 2, 'matching_worktrees': 0}])
        self.assertFalse(result['deletion_authorized'])
        self.assertEqual(result['local_occupancy_now'], 'NOT_VERIFIED')
        self.assertNotIn('/fixture', json.dumps(result))
        self.assertNotIn('refs/heads/', json.dumps(result))

    def test_opaque_paths_and_reasons(self):
        raw = row(b'/odd\n\xff', branch=None, extras=(b'locked first\nsecond', b'prunable reason'))
        self.assertEqual(w.compare(raw, raw)['counts']['locked'], 1)
        self.assertEqual(w.compare(raw, raw)['counts']['prunable'], 1)
        self.assertNotIn('second', json.dumps(w.compare(raw, raw)))

    def test_bare_and_unborn(self):
        raw = b'worktree /bare\0bare\0\0' + row(head=b'0' * 40)
        counts = w.compare(raw, raw)['counts']
        self.assertEqual((counts['bare'], counts['unborn']), (1, 1))

    def test_sha256(self):
        raw = row(head=b'a' * 64)
        self.assertEqual(w.compare(raw, raw)['status'], 'OBSERVED')

    def test_stale_including_changed_reason(self):
        a = row(extras=(b'locked reason1',))
        b = row(extras=(b'locked reason2',))
        result = w.compare(a, b, [BRANCH])
        self.assertEqual(result['status'], 'STALE')
        self.assertEqual(result['candidate_checks'], [])

    def test_unknown_duplicate_and_invalid_attributes(self):
        for extra in (b'unknown', b'HEAD ' + A, b'detached', b'bare', b'locked\0locked'):
            with self.subTest(extra=extra), self.assertRaises(w.InventoryError):
                w.parse(row(extras=(extra,)))

    def test_truncated_or_duplicate_records(self):
        for raw in (row()[:-1], row() + row(), b'worktree /fixture\0\0', b''):
            with self.subTest(raw=raw), self.assertRaises(w.InventoryError):
                w.parse(raw)

    def test_bad_oid_and_branch(self):
        for raw in (row(head=b'no'), row(branch=b'refs/tags/v1'), row(branch=b'refs/heads/a b')):
            with self.subTest(raw=raw), self.assertRaises(w.InventoryError):
                w.parse(raw)

    def test_duplicate_branch_not_collapsed(self):
        raw = row() + row(b'/other')
        self.assertEqual(w.compare(raw, raw, [BRANCH])['candidate_checks'][0]['matching_worktrees'], 2)

    def test_candidate_limits_and_encoding(self):
        for refs in ([BRANCH, BRANCH], [b'refs/heads/\xff'], [b'refs/tags/v1']):
            with self.subTest(refs=refs), self.assertRaises(w.InventoryError):
                w.compare(row(), row(), refs)

    def test_cli_distinct_captures_and_stale(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / 'a', Path(folder) / 'b'
            a.write_bytes(row()); b.write_bytes(row())
            args = [sys.executable, '-B', str(SOURCE), '--first', str(a), '--second']
            for path, code in ((a, 2), (b, 0)):
                result = subprocess.run(args + [str(path)], capture_output=True, timeout=15)
                self.assertEqual(result.returncode, code)
            b.write_bytes(row(branch=None))
            self.assertEqual(subprocess.run(args + [str(b)], capture_output=True, timeout=15).returncode, 1)

    @unittest.skipUnless(shutil.which('git'), 'Git unavailable')
    def test_actual_git_worktrees(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            repo, linked = root / 'repo', root / 'linked'
            repo.mkdir()
            env = {k: v for k, v in os.environ.items() if not k.upper().startswith('GIT_')}
            env.update({'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
                        'GIT_TERMINAL_PROMPT': '0'})
            def git(*args):
                return subprocess.run(['git', '-c', 'core.hooksPath=' + os.devnull, *args], cwd=repo,
                                      env=env, capture_output=True, check=True, timeout=20).stdout
            git('init', '-q', '-b', 'main')
            unborn = git('worktree', 'list', '--porcelain', '-z')
            self.assertEqual(w.compare(unborn, unborn)['counts']['unborn'], 1)
            git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                'commit', '--allow-empty', '-qm', 'init')
            git('worktree', 'add', '-q', '--detach', str(linked))
            git('worktree', 'lock', '--reason', 'test\nreason', str(linked))
            first = git('worktree', 'list', '--porcelain', '-z')
            second = git('worktree', 'list', '--porcelain', '-z')
            result = w.compare(first, second, [BRANCH])
            self.assertEqual(result['worktrees'], 2)
            self.assertEqual(result['counts']['detached'], 1)
            self.assertEqual(result['counts']['locked'], 1)
            self.assertEqual(result['candidate_checks'][0]['matching_worktrees'], 1)


if __name__ == '__main__':
    unittest.main()
