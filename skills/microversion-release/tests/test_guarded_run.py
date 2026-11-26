"""Owner-side wrapper integration with actual child processes and Git fixtures."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SOURCE = Path(__file__).resolve().parents[1] / 'scripts' / 'guarded_run.py'
AGENT = '''import pathlib, subprocess, sys
root = pathlib.Path.cwd()
mode = sys.argv[1]
if mode == 'fail':
    sys.exit(7)
if mode == 'noop':
    sys.exit(0)
(root / 'code.txt').write_text('new content', encoding='utf-8')
if mode == 'dirty':
    sys.exit(0)
version = '0.1.0' if mode in ('release', 'missing-tag') else '0.0.100'
(root / 'VERSION').write_text(version + '\\n', encoding='utf-8')
with (root / 'CHANGELOG.md').open('a', encoding='utf-8') as stream:
    stream.write('## ' + version + ' — fixture\\n')
subprocess.run(['git', 'add', '.'], check=True)
subprocess.run(['git', 'commit', '-qm', 'Fixture change'], check=True)
if mode == 'release':
    subprocess.run(['git', '-c', 'tag.gpgSign=false', 'tag', '-a', 'v0.1.0', '-m',
                    'Fixture release'], check=True)
'''
TEST = '''import pathlib, sys
mode = sys.argv[1]
if mode == 'fail':
    sys.exit(9)
if mode == 'mutate':
    pathlib.Path('code.txt').write_text('changed by test', encoding='utf-8')
'''


class GuardedRunTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        home = self.root / 'home'
        home.mkdir()
        hooks = self.root / 'empty-hooks'
        hooks.mkdir()
        env = {k: os.environ[k] for k in ('PATH', 'SystemRoot', 'WINDIR', 'COMSPEC',
                 'PATHEXT', 'TEMP', 'TMP', 'TMPDIR', 'APPDATA', 'LOCALAPPDATA',
                 'HOMEDRIVE', 'HOMEPATH', 'LANG', 'LC_ALL', 'LC_CTYPE', 'TZ') if k in os.environ}
        env.update(HOME=str(home), USERPROFILE=str(home))
        patch = mock.patch.dict(os.environ, env, clear=True)
        patch.start()
        self.addCleanup(patch.stop)
        self.git('init', '-q', '-b', 'main')
        for key, value in (('user.name', 'Fixture'), ('user.email', 'fixture@example.invalid'),
                           ('commit.gpgsign', 'false'), ('core.autocrlf', 'false'),
                           ('core.hooksPath', str(hooks))):
            self.git('config', key, value)
        (self.repo / 'VERSION').write_text('0.0.99\n', encoding='utf-8')
        (self.repo / 'CHANGELOG.md').write_text('## 0.0.99 — fixture\n', encoding='utf-8')
        (self.repo / 'code.txt').write_text('old content', encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-qm', 'Fixture baseline')
        self.base = self.git('rev-parse', 'HEAD')
        self.agent = self.root / 'agent.py'
        self.tests = self.root / 'tests.py'
        self.agent.write_text(AGENT, encoding='utf-8')
        self.tests.write_text(TEST, encoding='utf-8')

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True,
                              capture_output=True, text=True, timeout=15).stdout.strip()

    def invoke(self, agent='valid', test='valid', execute=True, extra=(), target='0.0.100'):
        python = str(Path(sys.executable).resolve())
        args = [python, '-B', str(SOURCE), '--repo', str(self.repo), '--baseline', self.base,
                '--expected-version', target, '--agent-exe', python, '--agent-arg=-B', '--agent-arg', str(self.agent),
                '--agent-arg', agent, '--test-exe', python, '--test-arg=-B', '--test-arg',
                str(self.tests), '--test-arg', test, *extra]
        if execute:
            args.append('--execute')
        result = subprocess.run(args, capture_output=True, timeout=75)
        return result.returncode, json.loads(result.stdout)

    def test_plan_never_runs_commands(self):
        code, result = self.invoke(execute=False)
        self.assertEqual((code, result['status']), (0, 'PLAN_ONLY'))
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.base)
        self.assertIsNone(result['agent_exit_code'])

    def test_successful_process_and_tests(self):
        code, result = self.invoke()
        self.assertEqual((code, result['status']), (0, 'ACCEPTANCE_CHECKS_PASSED'))
        self.assertEqual(result['structure']['version'], '0.0.100')
        self.assertEqual(result['structure']['commit'], self.git('rev-parse', 'HEAD'))
        self.assertEqual(result['release_readiness'], 'NOT_VERIFIED')

    def test_fake_success_dirty_tree_blocks(self):
        code, result = self.invoke(agent='dirty')
        self.assertEqual((code, result['reason']), (1, 'RUN_STRUCTURE_FAILED'))
        self.assertIsNone(result['test_exit_code'])

    def test_noop_blocks_by_default(self):
        code, result = self.invoke(agent='noop')
        self.assertEqual((code, result['reason']), (1, 'RUN_NO_CHANGE'))

    def test_read_only_explicitly_allowed(self):
        code, result = self.invoke(agent='noop', extra=('--allow-no-change',), target='0.0.99')
        self.assertEqual((code, result['status']), (0, 'ACCEPTANCE_CHECKS_PASSED'))
        self.assertEqual(result['structure']['commits_checked'], 0)

    def test_target_version_mismatch_blocks_before_tests(self):
        code, result = self.invoke(target='0.1.0')
        self.assertEqual((code, result['reason']), (1, 'RUN_TARGET_VERSION_MISMATCH'))
        self.assertEqual(result['expected_version'], '0.1.0')
        self.assertEqual(result['structure']['version'], '0.0.100')
        self.assertIsNone(result['test_exit_code'])

    def test_exact_release_target_with_tag(self):
        code, result = self.invoke(agent='release', target='0.1.0')
        self.assertEqual((code, result['status']), (0, 'ACCEPTANCE_CHECKS_PASSED'))
        self.assertEqual(result['structure']['version'], '0.1.0')
        self.assertEqual(result['structure']['tags_checked'], 1)
        self.assertEqual(result['release_readiness'], 'NOT_VERIFIED')

    def test_exact_release_target_without_tag(self):
        code, result = self.invoke(agent='missing-tag', target='0.1.0')
        self.assertEqual((code, result['reason']), (1, 'RUN_STRUCTURE_FAILED'))
        self.assertIsNone(result['test_exit_code'])

    def test_invalid_or_old_target_refused_before_agent(self):
        for target, reason in [('v0.1.0', 'GATE_VERSION_INVALID'),
                               ('0.0.98', 'RUN_TARGET_VERSION_BEHIND_BASELINE'),
                               ('0.0.99', 'RUN_TARGET_VERSION_REQUIRES_CHANGE')]:
            with self.subTest(target=target):
                code, result = self.invoke(target=target)
                self.assertEqual((code, result['reason']), (1, reason))
                self.assertIsNone(result['agent_exit_code'])
                self.assertEqual(self.git('rev-parse', 'HEAD'), self.base)

    def test_agent_failure_blocks(self):
        code, result = self.invoke(agent='fail')
        self.assertEqual((code, result['reason']), (1, 'RUN_AGENT_FAILED'))
        self.assertEqual(result['agent_exit_code'], 7)
        self.assertIsNone(result['test_exit_code'])

    def test_test_failure_blocks(self):
        code, result = self.invoke(test='fail')
        self.assertEqual((code, result['reason']), (1, 'RUN_TEST_FAILED'))
        self.assertEqual(result['test_exit_code'], 9)

    def test_test_changes_state_blocked(self):
        code, result = self.invoke(test='mutate')
        self.assertEqual((code, result['reason']), (1, 'RUN_POST_TEST_STATE_CHANGED'))

    def test_initial_dirty_tree_blocks_before_agent(self):
        (self.repo / 'untracked.txt').touch()
        code, result = self.invoke()
        self.assertEqual((code, result['reason']), (1, 'RUN_INITIAL_BASELINE_INVALID'))
        self.assertIsNone(result['agent_exit_code'])

    def test_relative_executable_refused(self):
        code, result = self.invoke(extra=('--agent-exe', 'python'))
        self.assertEqual((code, result['reason']), (1, 'RUN_EXECUTABLE_NOT_ABSOLUTE'))


if __name__ == '__main__':
    unittest.main()
