"""Cancellation preserves the old and new copies in isolated fixtures."""
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import profile_cancel as c
from profile_journal import append, scan
from profile_move import move_verified
from profile_transaction_fixture import fingerprint
from catalog_index import CatalogError, REPO


@unittest.skipUnless(os.name == "nt" or sys.platform == "linux", "unsupported platform")
class CancelTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = pathlib.Path(temp.name).resolve()
        self.roots = [root / n for n in ("profile", "stage", "backup", "forward", "cancel")]
        self.profile, self.stage, self.backup, self.forward, self.log = self.roots
        for path in self.roots:
            path.mkdir()
        self.other = self.profile / "other"
        self.other.mkdir()
        (self.other / "marker").write_bytes(b"untouched")

    def prepare(self, operation):
        for root, version in ((self.stage, "0.0.2"), (self.profile, "0.0.1")):
            if root == self.profile and operation == "install":
                continue
            path = root / "alpha"
            path.mkdir()
            (path / "VERSION").write_bytes((version + "\n").encode())
            (path / "SKILL.md").write_bytes(version.encode())
        self.old = fingerprint(self.profile / "alpha") if operation == "update" else (None, None)
        self.new = fingerprint(self.stage / "alpha")
        self.record = {"schema_version": 1, "repository": REPO, "id": "alpha",
                       "operation": operation, "phase": "PREPARED",
                       "old_version": self.old[0], "old_sha256": self.old[1],
                       "new_version": self.new[0], "new_sha256": self.new[1]}
        append(self.forward, self.record)

    def cancel(self):
        return c.cancel(*self.roots)

    def check_result(self, install=False):
        if install:
            self.assertFalse((self.profile / "alpha").exists())
        else:
            self.assertEqual(fingerprint(self.profile / "alpha"), self.old)
        self.assertEqual(fingerprint(self.stage / "alpha"), self.new)
        self.assertFalse((self.backup / "alpha").exists())
        self.assertEqual((self.other / "marker").read_bytes(), b"untouched")
        self.assertEqual([x["phase"] for x in scan(self.log)], ["PREPARED", "VERIFIED"])

    def test_cancel_before_update(self):
        self.prepare("update")
        original = scan(self.forward)
        result = self.cancel()
        self.assertEqual(result["status"], "CANCELLED_OBSERVED")
        self.assertFalse(result["apply_authorized"])
        self.assertEqual(scan(self.forward), original)
        self.check_result()

    def test_cancel_after_old_move_before_journal(self):
        self.prepare("update")
        move_verified(self.profile, self.backup, "alpha", self.old)
        self.cancel()
        self.check_result()

    def test_cancel_after_old_move_recorded(self):
        self.prepare("update")
        move_verified(self.profile, self.backup, "alpha", self.old)
        append(self.forward, {**self.record, "phase": "OLD_MOVED"})
        original = scan(self.forward)
        self.cancel()
        self.assertEqual(scan(self.forward), original)
        self.check_result()

    def test_cancel_first_install(self):
        self.prepare("install")
        move_verified(self.stage, self.profile, "alpha", self.new)
        append(self.forward, {**self.record, "phase": "NEW_MOVED"})
        append(self.forward, {**self.record, "phase": "VERIFIED"})
        self.cancel()
        self.check_result(install=True)

    def test_cancel_before_first_install(self):
        self.prepare("install")
        self.cancel()
        self.check_result(install=True)

    def test_resume_after_cancel_move(self):
        self.prepare("update")
        move_verified(self.profile, self.backup, "alpha", self.old)
        append(self.forward, {**self.record, "phase": "OLD_MOVED"})
        def interrupted(*args):
            move_verified(*args)
            raise OSError("fixture interruption")
        with mock.patch.object(c, "move_verified", side_effect=interrupted):
            with self.assertRaises(OSError):
                self.cancel()
        self.assertEqual(scan(self.log)[-1]["phase"], "PREPARED")
        self.cancel()
        self.check_result()
        with mock.patch.object(c, "move_verified") as move:
            self.cancel()
            move.assert_not_called()

    def test_completed_update_requires_rollback(self):
        self.prepare("update")
        move_verified(self.profile, self.backup, "alpha", self.old)
        append(self.forward, {**self.record, "phase": "OLD_MOVED"})
        move_verified(self.stage, self.profile, "alpha", self.new)
        with self.assertRaisesRegex(CatalogError, "CANCEL_FORWARD_LAYOUT"):
            self.cancel()
        self.assertEqual(fingerprint(self.profile / "alpha"), self.new)
        self.assertEqual(fingerprint(self.backup / "alpha"), self.old)

    def test_changed_stage_blocks(self):
        self.prepare("update")
        move_verified(self.profile, self.backup, "alpha", self.old)
        (self.stage / "alpha" / "SKILL.md").write_bytes(b"owner edit")
        with self.assertRaisesRegex(CatalogError, "CANCEL_FORWARD_LAYOUT"):
            self.cancel()
        self.assertEqual(fingerprint(self.backup / "alpha"), self.old)
        self.assertEqual(scan(self.log), [])

    def test_wrong_cancel_history_blocks(self):
        self.prepare("install")
        append(self.log, {**self.record, "operation": "cancel-install", "new_sha256": "c"*64})
        with self.assertRaisesRegex(CatalogError, "CANCEL_JOURNAL_MISMATCH"):
            self.cancel()
        self.assertEqual(fingerprint(self.stage / "alpha"), self.new)


if __name__ == "__main__":
    unittest.main()
