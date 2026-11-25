from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import publish_skill_tags as m


class SkillTagsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / 'repo'
        self.root.mkdir()
        self.remote = self.root.parent / 'remote.git'
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'tag.gpgSign', 'false')
        subprocess.run(['git', 'init', '--bare', '-q', str(self.remote)], check=True)
        self.git('remote', 'add', 'origin', str(self.remote))
        self.first = self.commit('0.0.1', '0.0.1')
        self.second = self.commit('0.0.2', '0.0.2')
        self.backfill = {'audit/v0.0.1': (self.first, self.git('rev-parse', 'v0.0.1'))}
        self.git('push', '-q', 'origin', 'main', '--tags')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], stderr=subprocess.PIPE).decode().strip()

    def commit(self, root_version, skill_version):
        (self.root / 'VERSION').write_text(root_version + '\n')
        d = self.root / 'skills' / 'audit'
        d.mkdir(parents=True, exist_ok=True)
        (d / 'SKILL.md').write_text('# Audit\n')
        (d / 'VERSION').write_text(skill_version + '\n')
        for name in ('CHANGELOG.md', 'CHANGELOG.en.md'):
            (d / name).write_text(f'## {skill_version} — Fixture\n', encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-qm', root_version)
        self.git('tag', '-a', 'v' + root_version, '-m', 'Fixture')
        return self.git('rev-parse', 'HEAD')

    def test_plan_read_only_and_exact(self):
        before = self.git('show-ref')
        rows = m.plan(self.root, self.second, backfill=self.backfill)
        self.assertEqual([(r['name'], r['commit']) for r in rows], [('audit/v0.0.1', self.first), ('audit/v0.0.2', self.second)])
        self.assertEqual(before, self.git('show-ref'))
        self.assertTrue(all(r['creation_allowed'] for r in rows))

    def test_publish_atomic_and_idempotent(self):
        rows = m.publish(self.root, self.second, backfill=self.backfill)
        refs = m.remote_refs(self.root)
        for r in rows:
            self.assertEqual(refs['refs/tags/' + r['name']], r['local_object'])
            m.verify_tag(self.root, r['name'], r['commit'], r['local_object'])
        self.assertEqual(rows, m.publish(self.root, self.second, backfill=self.backfill))
        self.assertEqual(refs, m.remote_refs(self.root))

    def test_missing_historical_authorization(self):
        with self.assertRaisesRegex(m.TagError, 'HISTORICAL_RECOVERY_REQUIRED'):
            m.publish(self.root, self.second, backfill={})
        self.assertIsNone(m.local_object(self.root, 'audit/v0.0.2'))

    def test_wrong_backfill_receipt(self):
        with self.assertRaisesRegex(m.TagError, 'BACKFILL_MISMATCH'):
            m.plan(self.root, self.second, backfill={'audit/v0.0.1': (self.first, 'a' * 40)})

    def test_backfill_missing(self):
        with self.assertRaisesRegex(m.TagError, 'BACKFILL_MISSING'):
            m.plan(self.root, self.second, backfill={**self.backfill, 'other/v0.0.1': (self.first, 'a' * 40)})

    def test_conflicting_local_tag_rejected_before_writes(self):
        self.git('tag', '-a', 'audit/v0.0.2', self.first, '-m', 'Wrong target')
        with self.assertRaisesRegex(m.TagError, 'TARGET_OR_MESSAGE_INVALID'):
            m.publish(self.root, self.second, backfill=self.backfill)
        self.assertIsNone(m.local_object(self.root, 'audit/v0.0.1'))

    def test_lightweight_rejected(self):
        self.git('tag', 'audit/v0.0.1', self.first)
        with self.assertRaisesRegex(m.TagError, 'NOT_ANNOTATED'):
            m.plan(self.root, self.second, backfill=self.backfill)

    def test_remote_tag_conflict_rejected(self):
        self.git('tag', '-a', 'audit/v0.0.1', self.first, '-m', 'Remote')
        self.git('push', '-q', 'origin', 'refs/tags/audit/v0.0.1')
        self.git('tag', '-d', 'audit/v0.0.1')
        with self.assertRaisesRegex(m.TagError, 'REMOTE_MISMATCH'):
            m.publish(self.root, self.second, backfill=self.backfill)
        self.assertIsNone(m.local_object(self.root, 'audit/v0.0.2'))

    def test_missing_catalog_tag_rejected(self):
        self.git('tag', '-d', 'v0.0.1')
        with self.assertRaisesRegex(m.TagError, 'OBJECT_INVALID'):
            m.plan(self.root, self.second, backfill=self.backfill)

    def test_dirty_and_wrong_head(self):
        with self.assertRaisesRegex(m.TagError, 'HEAD_MISMATCH'):
            m.plan(self.root, self.first, backfill=self.backfill)
        (self.root / 'untracked').write_text('x')
        with self.assertRaisesRegex(m.TagError, 'DIRTY'):
            m.plan(self.root, self.second, backfill=self.backfill)

    def test_remote_main_changed(self):
        self.git('push', '-q', '--force', 'origin', self.first + ':refs/heads/main')
        with self.assertRaisesRegex(m.TagError, 'REMOTE_MAIN_CHANGED'):
            m.publish(self.root, self.second, backfill=self.backfill)

    def test_current_unchanged_skill_uses_historical_target(self):
        m.publish(self.root, self.second, backfill=self.backfill)
        third = self.commit('0.0.3', '0.0.2')
        self.git('push', '-q', 'origin', 'main', '--tags')
        rows = m.publish(self.root, third, backfill=self.backfill)
        self.assertEqual(rows[-1]['commit'], self.second)

    def test_remote_race_before_push(self):
        refs = m.remote_refs(self.root)
        with patch.object(m, 'remote_refs', side_effect=[refs, {**refs, 'refs/heads/main': self.first}]):
            with self.assertRaisesRegex(m.TagError, 'REMOTE_CHANGED'):
                m.publish(self.root, self.second, backfill=self.backfill)
        self.assertNotIn('refs/tags/audit/v0.0.1', m.remote_refs(self.root))


if __name__ == '__main__':
    unittest.main()
