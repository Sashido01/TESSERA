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
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'scripts' / 'worktree_inventory.py'
spec = importlib.util.spec_from_file_location('worktree_inventory_fixture', SOURCE)
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
A = b'a' * 40
BRANCH = b'refs/heads/main'


def row(path=b'/fixture', head=A, branch=BRANCH, extras=()):
    return b'\0'.join([b'worktree ' + path, b'HEAD ' + head,
                      b'branch ' + branch if branch else b'detached', *extras]) + b'\0\0'


def require_fixture_context():
    # Reject before creating a fixture; do not strip host Git policy and proceed.
    if any(key.upper().startswith('GIT_') and key.upper() != 'GIT_PAGER'
           for key in os.environ):
        raise RuntimeError('FIXTURE_GIT_CONTEXT_UNSAFE')


def fixture_environment():
    require_fixture_context()
    keys = ('PATH', 'SystemRoot', 'WINDIR', 'COMSPEC', 'PATHEXT',
            'TEMP', 'TMP', 'TMPDIR', 'LANG', 'LC_ALL', 'LC_CTYPE', 'TZ')
    env = {key: value for key in keys if (value := os.getenv(key)) is not None}
    env.update({'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
                'GIT_TERMINAL_PROMPT': '0'})
    return env


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

    def test_full_ref_format(self):
        for ref in (b'refs/heads/.hidden', b'refs/heads/a.lock/b',
                    b'refs/heads/a..b', b'refs/heads/a//b', b'refs/heads/a.',
                    b'refs/heads/a/', b'refs/heads/a@{b', b'refs/heads/a\\b',
                    b'refs/heads/a*b'):
            with self.subTest(ref=ref), self.assertRaises(w.InventoryError):
                w.parse(row(branch=ref))
        self.assertEqual(w.parse(row(branch=b'refs/heads/topic/v1'))[0]['branch'],
                         b'refs/heads/topic/v1')
        self.assertEqual(w.parse(row(branch=b'refs/heads/\xc3\xa9'))[0]['branch'],
                         b'refs/heads/\xc3\xa9')

    def test_mixed_or_mismatched_object_format(self):
        raw = row() + row(b'/other', head=b'a' * 64)
        with self.assertRaisesRegex(w.InventoryError, 'OBJECT_FORMAT_MIXED'):
            w.parse(raw)
        with self.assertRaisesRegex(w.InventoryError, 'OBJECT_FORMAT_MISMATCH'):
            w.compare(row(), row(), [BRANCH], [b'a' * 64])

    def test_descriptor_identity_collision(self):
        with patch.object(w, 'read_capture_record', side_effect=[
                (row(), (1, 23)), (row(), (1, 23))]):
            with self.assertRaisesRegex(w.InventoryError, 'CAPTURE_NOT_DISTINCT'):
                w.capture_pair(Path('first'), Path('second'))

    def test_fixture_refuses_context_without_mutations(self):
        case = WorktreeTests('test_actual_git_worktrees')
        for key in ('GIT_DIR', 'GIT_CONFIG_COUNT', 'GIT_CONFIG_VALUE_0'):
            with self.subTest(key=key), patch.dict(os.environ, {key: 'fixture'}), \
                    patch.object(tempfile, 'TemporaryDirectory') as temp, \
                    patch.object(subprocess, 'run') as git:
                with self.assertRaisesRegex(RuntimeError, 'FIXTURE_GIT_CONTEXT_UNSAFE'):
                    case.test_actual_git_worktrees()
                temp.assert_not_called()
                git.assert_not_called()

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

    def test_detached_head_and_branch_counts(self):
        raw = row() + row(b'/detached', branch=None)
        result = w.compare(raw, raw, [BRANCH], [A])
        self.assertEqual(result['candidate_checks'], [{'index': 1, 'matching_worktrees': 1,
            'matching_head_worktrees': 2, 'detached_head_worktrees': 1}])
        self.assertFalse(result['deletion_authorized'])
        self.assertNotIn(A.decode(), json.dumps(result))

    def test_invalid_candidate_heads(self):
        for heads in ([b'0' * 40], [b'bad'], [A, A], [None]):
            with self.subTest(heads=heads), self.assertRaises(w.InventoryError):
                w.compare(row(), row(), [BRANCH], heads)
        with self.assertRaises(w.InventoryError):
            w.compare(row(), row(), [[]])

    def test_capture_size_and_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            file = root / 'capture'
            file.write_bytes(row())
            self.assertEqual(w.read_capture(file), row())
            with self.assertRaises(w.InventoryError):
                w.read_capture(root)
            file.write_bytes(b'')
            with self.assertRaises(w.InventoryError):
                w.read_capture(file)
            with file.open('wb') as stream:
                stream.truncate(w.MAX_BYTES + 1)
            with self.assertRaises(w.InventoryError):
                w.read_capture(file)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'FIFO unavailable')
    def test_fifo_refused_without_open(self):
        with tempfile.TemporaryDirectory() as folder:
            fifo = Path(folder) / 'capture'
            os.mkfifo(fifo)
            with self.assertRaisesRegex(w.InventoryError, 'NOT_REGULAR'):
                w.read_capture(fifo)

    def test_hardlinked_captures_not_distinct(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / 'a', Path(folder) / 'b'
            a.write_bytes(row())
            try:
                os.link(a, b)
            except OSError:
                self.skipTest('hardlinks unavailable')
            result = subprocess.run([sys.executable, '-B', str(SOURCE), '--first', str(a),
                '--second', str(b)], capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 2)
            self.assertIn(b'WORKTREE_CAPTURE_NOT_DISTINCT', result.stderr)

    @unittest.skipUnless(shutil.which('git'), 'Git unavailable')
    def test_actual_git_worktrees(self):
        env = fixture_environment()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            repo, linked = root / 'repo', root / 'linked'
            repo.mkdir()
            hooks = root / 'empty-hooks'
            hooks.mkdir()
            def git(*args):
                return subprocess.run(['git', '-c', 'core.hooksPath=' + str(hooks), *args], cwd=repo,
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
