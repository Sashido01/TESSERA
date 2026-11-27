"""Real disposable Git fixtures, plus hook protocol checks without a live agent."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SOURCE = Path(__file__).resolve().parents[1] / 'scripts' / 'completion_gate.py'
spec = importlib.util.spec_from_file_location('completion_gate_fixture', SOURCE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class CompletionGateTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.marker = self.root / 'once'
        self.home = self.root / 'home'
        self.home.mkdir()
        self.hooks = self.root / 'empty-hooks'
        self.hooks.mkdir()
        # Only the disposable fixture gets a clean child Git context.
        clean = {k: os.environ[k] for k in ('PATH', 'SystemRoot', 'WINDIR', 'COMSPEC',
                 'PATHEXT', 'TEMP', 'TMP', 'TMPDIR', 'APPDATA', 'LOCALAPPDATA',
                 'HOMEDRIVE', 'HOMEPATH', 'LANG', 'LC_ALL', 'LC_CTYPE', 'TZ') if k in os.environ}
        clean.update(HOME=str(self.home), USERPROFILE=str(self.home))
        env_patch = mock.patch.dict(os.environ, clean, clear=True)
        env_patch.start()
        self.addCleanup(env_patch.stop)
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'commit.gpgsign', 'false')
        self.git('config', 'tag.gpgSign', 'false')
        self.git('config', 'core.autocrlf', 'false')
        self.git('config', 'core.hooksPath', str(self.hooks))
        self.commit('0.0.99')
        self.base = self.git('rev-parse', 'HEAD')

    def git(self, *args):
        env = {k: os.environ[k] for k in gate.SYSTEM_ENV if k in os.environ}
        env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT='0',
                   GIT_ALLOW_PROTOCOL='')
        return subprocess.run(['git', '-C', str(self.repo), *args], env=env, check=True,
                              capture_output=True, text=True, timeout=15).stdout.strip()

    def commit(self, version, substantive=True, changelog=True):
        (self.repo / 'VERSION').write_text(version + '\n', encoding='utf-8')
        if changelog:
            for name in ('CHANGELOG.md', 'CHANGELOG.en.md'):
                with (self.repo / name).open('a', encoding='utf-8') as stream:
                    stream.write('## ' + version + ' — fixture\n')
        if substantive:
            (self.repo / 'content.txt').write_text(version, encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-qm', 'Fixture ' + version)

    def check(self):
        return gate.check(self.repo, self.base, bilingual=True)

    def payload(self, active=False):
        return json.dumps({'hook_event_name': 'Stop', 'cwd': str(self.repo),
                           'stop_hook_active': active}).encode()

    def test_no_change_is_not_release_readiness(self):
        result = self.check()
        self.assertEqual(result['status'], 'STRUCTURE_VERIFIED')
        self.assertEqual(result['commits_checked'], 0)
        self.assertEqual(result['release_readiness'], 'NOT_VERIFIED')

    def test_work_past_99_and_multiple_commits(self):
        self.commit('0.0.100')
        self.commit('0.0.101')
        self.assertEqual(self.check()['commits_checked'], 2)

    def test_release_annotated_required(self):
        self.commit('0.1.0')
        self.assertEqual(self.check()['status'], 'BLOCKED')
        self.git('tag', 'v0.1.0')
        self.assertEqual(self.check()['reason'], 'GATE_TAG_INVALID')
        self.git('tag', '-d', 'v0.1.0')
        self.git('tag', '-a', 'v0.1.0', '-m', 'Fixture release')
        self.assertEqual(self.check()['tags_checked'], 1)

    def test_wrong_release_target(self):
        self.commit('0.1.0')
        self.git('tag', '-a', 'v0.1.0', self.base, '-m', 'Wrong commit')
        self.assertEqual(self.check()['reason'], 'GATE_TAG_INVALID')

    def test_release_in_intermediate_commit(self):
        self.commit('0.1.0')
        self.git('tag', '-a', 'v0.1.0', '-m', 'Fixture release')
        self.commit('0.1.1')
        result = self.check()
        self.assertEqual((result['commits_checked'], result['tags_checked']), (2, 1))

    def test_skipped_or_decreased_version(self):
        self.commit('0.0.101')
        self.assertEqual(self.check()['reason'], 'GATE_TRANSITION_INVALID')
        self.assertRaises(gate.GateError, gate.transition, '0.1.1', '0.0.99')

    def test_dirty_and_untracked(self):
        (self.repo / 'content.txt').write_text('dirty', encoding='utf-8')
        self.assertEqual(self.check()['reason'], 'GATE_DIRTY')
        self.git('restore', 'content.txt')
        (self.repo / 'untracked.txt').touch()
        self.assertEqual(self.check()['reason'], 'GATE_DIRTY')

    def test_metadata_only(self):
        self.commit('0.0.100', substantive=False)
        self.assertEqual(self.check()['reason'], 'GATE_METADATA_ONLY_OR_MISSING')

    def test_missing_changelog(self):
        self.commit('0.0.100', changelog=False)
        self.assertEqual(self.check()['reason'], 'GATE_METADATA_ONLY_OR_MISSING')

    def test_predeclared_target_heading_refused(self):
        for name in ('CHANGELOG.md', 'CHANGELOG.en.md'):
            with (self.repo / name).open('a', encoding='utf-8') as stream:
                stream.write('## 0.0.100 — reserved\n')
        self.git('add', '.')
        self.git('commit', '--amend', '--no-edit', '-q')
        self.base = self.git('rev-parse', 'HEAD')
        self.commit('0.0.100', changelog=False)
        for name in ('CHANGELOG.md', 'CHANGELOG.en.md'):
            with (self.repo / name).open('a', encoding='utf-8') as stream:
                stream.write('Other text\n')
        self.git('add', '.')
        self.git('commit', '--amend', '--no-edit', '-q')
        self.assertEqual(self.check()['reason'], 'GATE_CHANGELOG_PREDECLARED')

    def test_duplicate_target_heading_refused(self):
        self.commit('0.0.100')
        with (self.repo / 'CHANGELOG.en.md').open('a', encoding='utf-8') as stream:
            stream.write('## 0.0.100 — duplicate\n')
        self.git('add', '.')
        self.git('commit', '--amend', '--no-edit', '-q')
        self.assertEqual(self.check()['reason'], 'GATE_CHANGELOG_MISSING_OR_DUPLICATE')

    def test_previous_heading_must_remain(self):
        self.commit('0.0.100')
        (self.repo / 'CHANGELOG.md').write_text('## 0.0.100 — only\n', encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '--amend', '--no-edit', '-q')
        self.assertEqual(self.check()['reason'], 'GATE_CHANGELOG_PREVIOUS_LOST')

    def test_invalid_baseline_changelog_refused(self):
        (self.repo / 'CHANGELOG.md').write_text('No baseline entry\n', encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '--amend', '--no-edit', '-q')
        self.base = self.git('rev-parse', 'HEAD')
        self.assertEqual(self.check()['reason'], 'GATE_BASELINE_CHANGELOG_INVALID')

    def test_index_flags_refused(self):
        for flag, undo in (('--assume-unchanged', '--no-assume-unchanged'),
                           ('--skip-worktree', '--no-skip-worktree')):
            self.git('update-index', flag, 'content.txt')
            self.assertEqual(self.check()['reason'], 'GATE_INDEX_FLAGS_UNSAFE')
            self.git('update-index', undo, 'content.txt')

    def test_unrelated_baseline(self):
        self.git('checkout', '--orphan', 'unrelated')
        self.commit('0.0.100')
        self.assertEqual(self.check()['reason'], 'GATE_NONLINEAR_OR_BASELINE_MISMATCH')

    def test_inherited_context_refused_before_git(self):
        with mock.patch.dict(os.environ, {'GIT_CONFIG_KEY_0': 'fixture'}), \
                mock.patch.object(gate.subprocess, 'run') as command:
            self.assertEqual(self.check()['reason'], 'GATE_GIT_CONTEXT_UNSAFE')
            command.assert_not_called()

    def test_preserve_xdg_config_location_without_git_invocation(self):
        with mock.patch.dict(os.environ, {'XDG_CONFIG_HOME': 'synthetic config root'}), \
                mock.patch.object(gate.subprocess, 'run') as command:
            inspector = gate.Inspector(self.repo)
            self.assertEqual(inspector.env['XDG_CONFIG_HOME'], 'synthetic config root')
            command.assert_not_called()

    def test_stop_one_continuation_even_if_active_false(self):
        (self.repo / 'dirty.txt').touch()
        first = gate.stop_hook(self.payload(), self.repo, self.base, self.marker, True)
        second = gate.stop_hook(self.payload(), self.repo, self.base, self.marker, True)
        self.assertEqual(first['decision'], 'block')
        self.assertIs(second['continue'], False)
        self.assertEqual(self.marker.read_bytes(), b'TESSERA continuation used\n')
        self.assertEqual(self.check()['status'], 'BLOCKED')

    def test_stop_scope_and_invalid_input_do_not_call_git(self):
        wrong = json.loads(self.payload())
        wrong['cwd'] = str(self.root)
        for raw in (b'{', b'{"cwd":"a","cwd":"b"}', json.dumps(wrong).encode(),
                    b'x' * (gate.MAX_HOOK_INPUT + 1)):
            with mock.patch.object(gate, 'check') as check:
                result = gate.stop_hook(raw, self.repo, self.base, self.marker, True)
                self.assertIs(result['continue'], False)
                check.assert_not_called()
        self.assertFalse(self.marker.exists())

    def test_active_hook_no_marker_and_pass_no_marker(self):
        self.assertIn('STRUCTURE_VERIFIED', gate.stop_hook(self.payload(), self.repo, self.base,
                                                           self.marker, True)['systemMessage'])
        (self.repo / 'dirty.txt').touch()
        self.assertIs(gate.stop_hook(self.payload(True), self.repo, self.base, self.marker, True)['continue'], False)
        self.assertFalse(self.marker.exists())

    def test_cli_exit_codes(self):
        args = [sys.executable, '-B', str(SOURCE), 'check', '--repo', str(self.repo), '--baseline', self.base]
        self.assertEqual(subprocess.run(args, capture_output=True, timeout=35).returncode, 0)
        (self.repo / 'dirty.txt').touch()
        self.assertEqual(subprocess.run(args, capture_output=True, timeout=35).returncode, 1)


if __name__ == '__main__':
    unittest.main()
