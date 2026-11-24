"""Offline regression tests of the staged re-pin acceptance helper."""
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_official_skill_update as update


class SwapTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = pathlib.Path(temp.name)
        self.target, self.staged, self.backup = (
            self.root / name for name in ("old", "staged", "backup")
        )
        for root, text in ((self.target, "old"), (self.staged, "new")):
            root.mkdir()
            (root / "SKILL.md").write_text(text, encoding="utf-8")
            (root / "scripts").mkdir()
            (root / "scripts" / "helper.py").write_text(text, encoding="utf-8")
        self.old = update.snapshot(self.target)
        self.new = update.snapshot(self.staged)

    def swap(self, **kwargs):
        update.guarded_swap(self.target, self.staged, self.backup,
                            self.old, self.new, **kwargs)

    def test_success_retains_backup(self):
        self.swap()
        self.assertEqual(update.snapshot(self.target), self.new)
        self.assertEqual(update.snapshot(self.backup), self.old)
        self.assertFalse(self.staged.exists())

    def test_rollback_injected_failure(self):
        with self.assertRaisesRegex(update.InstallCheckError, "UPDATE_INJECTED_FAILURE"):
            self.swap(inject_failure=True)
        self.assertEqual(update.snapshot(self.target), self.old)
        self.assertEqual(update.snapshot(self.staged), self.new)
        self.assertFalse(self.backup.exists())

    def test_extra_hidden_file_refused_without_change(self):
        marker = self.target / ".local"
        marker.write_text("keep", encoding="utf-8")
        before = update.snapshot(self.target)
        with self.assertRaisesRegex(update.InstallCheckError, "UPDATE_LOCAL_CHANGES"):
            self.swap()
        self.assertEqual(update.snapshot(self.target), before)
        self.assertFalse(self.backup.exists())

    def test_modified_file_refused(self):
        (self.target / "SKILL.md").write_text("user edit", encoding="utf-8")
        with self.assertRaisesRegex(update.InstallCheckError, "UPDATE_LOCAL_CHANGES"):
            self.swap()

    def test_missing_file_refused(self):
        (self.target / "scripts" / "helper.py").unlink()
        with self.assertRaisesRegex(update.InstallCheckError, "UPDATE_LOCAL_CHANGES"):
            self.swap()

    def test_empty_local_directory_refused(self):
        (self.target / "owner").mkdir()
        with self.assertRaisesRegex(update.InstallCheckError, "UPDATE_LOCAL_CHANGES"):
            self.swap()

    def test_changed_stage_refused(self):
        (self.staged / "SKILL.md").write_text("tampered", encoding="utf-8")
        with self.assertRaisesRegex(update.InstallCheckError, "UPDATE_STAGED_CHANGES"):
            self.swap()
        self.assertEqual(update.snapshot(self.target), self.old)

    def test_existing_backup_refused(self):
        self.backup.mkdir()
        with self.assertRaisesRegex(update.InstallCheckError, "UPDATE_BACKUP_EXISTS"):
            self.swap()

    def test_restore_keeps_newer_backup(self):
        self.swap()
        later = self.root / "newer"
        update.guarded_swap(self.target, self.backup, later, self.new, self.old)
        self.assertEqual(update.snapshot(self.target), self.old)
        self.assertEqual(update.snapshot(later), self.new)

    def test_nested_backup_refused(self):
        with self.assertRaisesRegex(update.InstallCheckError, "UPDATE_NESTED_PATH"):
            update.guarded_swap(self.target, self.staged, self.target / "backup",
                                self.old, self.new)

    def test_alias_refused(self):
        with self.assertRaisesRegex(update.InstallCheckError, "UPDATE_PATH_ALIAS"):
            update.guarded_swap(self.target, self.target, self.backup,
                                self.old, self.old)

    def test_symlink_refused(self):
        alias = self.target / "alias"
        try:
            alias.symlink_to(self.staged / "SKILL.md")
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaisesRegex(update.InstallCheckError, "UPDATE_NONREGULAR_OR_LINK"):
            update.snapshot(self.target)


if __name__ == "__main__":
    unittest.main()
