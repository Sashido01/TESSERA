"""Rollback of a completed update, including interrupted reverse moves."""
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import profile_rollback as r
from profile_journal import append, scan
from profile_transaction_fixture import fingerprint
from profile_move import move_verified
from catalog_index import REPO, CatalogError


@unittest.skipUnless(os.name == "nt" or sys.platform == "linux", "unsupported platform")
class RollbackTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = pathlib.Path(temp.name).resolve()
        self.roots = [root / n for n in ("profile", "stage", "backup", "forward", "rollback")]
        self.profile, self.stage, self.backup, self.forward, self.rollback = self.roots
        for path in self.roots:
            path.mkdir()
        for root, version in ((self.profile, "0.0.1"), (self.stage, "0.0.2")):
            path = root / "alpha"
            path.mkdir()
            (path / "VERSION").write_bytes((version + "\n").encode())
            (path / "SKILL.md").write_bytes(version.encode())
        self.old = fingerprint(self.profile / "alpha")
        self.new = fingerprint(self.stage / "alpha")
        self.record = {"schema_version": 1, "repository": REPO, "id": "alpha",
                       "operation": "update", "phase": "PREPARED",
                       "old_version": self.old[0], "old_sha256": self.old[1],
                       "new_version": self.new[0], "new_sha256": self.new[1]}
        append(self.forward, self.record)
        move_verified(self.profile, self.backup, "alpha", self.old)
        append(self.forward, {**self.record, "phase": "OLD_MOVED"})
        move_verified(self.stage, self.profile, "alpha", self.new)
        self.other = self.profile / "other"
        self.other.mkdir()
        (self.other / "marker").write_bytes(b"untouched")

    def complete_forward(self):
        for phase in ("NEW_MOVED", "VERIFIED"):
            append(self.forward, {**self.record, "phase": phase})

    def restore(self):
        return r.restore(*self.roots)

    def check_restored(self):
        self.assertEqual(fingerprint(self.profile / "alpha"), self.old)
        self.assertEqual(fingerprint(self.stage / "alpha"), self.new)
        self.assertFalse((self.backup / "alpha").exists())
        self.assertEqual((self.other / "marker").read_bytes(), b"untouched")
        self.assertEqual(scan(self.rollback)[-1]["phase"], "VERIFIED")

    def test_completed_update(self):
        self.complete_forward()
        before = scan(self.forward)
        result = self.restore()
        self.assertEqual(result["status"], "RESTORED_OBSERVED")
        self.assertFalse(result["apply_authorized"])
        self.assertEqual(scan(self.forward), before)
        self.check_restored()

    def test_forward_journal_lag(self):
        self.restore()
        self.check_restored()
        self.assertEqual(scan(self.forward)[-1]["phase"], "OLD_MOVED")

    def test_resume_after_first_move(self):
        def interrupt(*args):
            move_verified(*args)
            raise OSError("fixture interruption")
        with mock.patch.object(r, "move_verified", side_effect=interrupt):
            with self.assertRaises(OSError):
                self.restore()
        self.assertEqual(scan(self.rollback)[-1]["phase"], "PREPARED")
        self.restore()
        self.check_restored()

    def test_resume_after_second_move(self):
        def interrupt(*args):
            result = move_verified(*args)
            if args[0] == self.backup:
                raise OSError("fixture interruption")
            return result
        with mock.patch.object(r, "move_verified", side_effect=interrupt):
            with self.assertRaises(OSError):
                self.restore()
        self.assertEqual(scan(self.rollback)[-1]["phase"], "OLD_MOVED")
        self.restore()
        self.check_restored()

    def test_resume_after_complete_does_not_move(self):
        self.restore()
        with mock.patch.object(r, "move_verified") as move:
            self.restore()
            move.assert_not_called()
        self.check_restored()

    def test_local_edit_blocks(self):
        path = self.profile / "alpha" / "SKILL.md"
        path.write_bytes(b"owner edit")
        with self.assertRaisesRegex(CatalogError, "ROLLBACK_FORWARD_LAYOUT"):
            self.restore()
        self.assertEqual(path.read_bytes(), b"owner edit")
        self.assertEqual(scan(self.rollback), [])

    def test_stage_collision_blocks(self):
        path = self.stage / "alpha"
        path.mkdir()
        (path / "SKILL.md").write_bytes(b"collision")
        (path / "VERSION").write_bytes(b"0.0.9\n")
        with self.assertRaisesRegex(CatalogError, "ROLLBACK_FORWARD_LAYOUT"):
            self.restore()
        self.assertEqual((path / "SKILL.md").read_bytes(), b"collision")
        self.assertEqual(fingerprint(self.profile / "alpha"), self.new)

    def test_backup_edit_blocks(self):
        (self.backup / "alpha" / "SKILL.md").write_bytes(b"changed")
        with self.assertRaisesRegex(CatalogError, "ROLLBACK_FORWARD_LAYOUT"):
            self.restore()
        self.assertEqual(fingerprint(self.profile / "alpha"), self.new)

    def test_wrong_rollback_journal_blocks(self):
        record = {**self.record, "operation": "rollback",
                  "old_version": self.new[0], "new_version": self.old[0],
                  "old_sha256": self.new[1], "new_sha256": "c"*64}
        append(self.rollback, record)
        with self.assertRaisesRegex(CatalogError, "ROLLBACK_JOURNAL_MISMATCH"):
            self.restore()
        self.assertEqual(fingerprint(self.profile / "alpha"), self.new)


if __name__ == "__main__":
    unittest.main()
