"""Forward transaction integration in isolated ordinary directories."""
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import profile_advance as a
from profile_cancel import cancel
from profile_rollback import restore
from profile_journal import append, scan
from profile_move import move_verified
from profile_transaction_fixture import fingerprint
from catalog_index import CatalogError, REPO


@unittest.skipUnless(os.name == "nt" or sys.platform == "linux", "unsupported platform")
class AdvanceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = pathlib.Path(temp.name).resolve()
        self.roots = [root / n for n in ("profile", "stage", "backup", "forward", "rollback", "cancel")]
        self.profile, self.stage, self.backup, self.forward, self.rollback, self.cancel = self.roots
        for path in self.roots:
            path.mkdir()
        self.other = self.profile / "other"
        self.other.mkdir()
        (self.other / "marker").write_bytes(b"untouched")

    def prepare(self, operation="update"):
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

    def advance(self):
        return a.advance(*self.roots, self.record)

    def verify_final(self, install=False):
        self.assertEqual(fingerprint(self.profile / "alpha"), self.new)
        self.assertFalse((self.stage / "alpha").exists())
        if install:
            self.assertFalse((self.backup / "alpha").exists())
        else:
            self.assertEqual(fingerprint(self.backup / "alpha"), self.old)
        self.assertEqual(scan(self.forward)[-1]["phase"], "VERIFIED")
        self.assertEqual((self.other / "marker").read_bytes(), b"untouched")

    def test_update_and_idempotent_resume(self):
        self.prepare()
        result = self.advance()
        self.assertEqual(result["status"], "UPDATED_OBSERVED")
        self.assertFalse(result["apply_authorized"])
        self.verify_final()
        with mock.patch.object(a, "move_verified") as move:
            self.advance()
            move.assert_not_called()

    def test_install(self):
        self.prepare("install")
        self.assertEqual(self.advance()["status"], "INSTALLED_OBSERVED")
        self.verify_final(install=True)

    def test_resume_after_old_move(self):
        self.prepare()
        append(self.forward, self.record)
        move_verified(self.profile, self.backup, "alpha", self.old)
        self.advance()
        self.verify_final()

    def test_resume_after_new_move(self):
        self.prepare()
        append(self.forward, self.record)
        move_verified(self.profile, self.backup, "alpha", self.old)
        append(self.forward, {**self.record, "phase": "OLD_MOVED"})
        move_verified(self.stage, self.profile, "alpha", self.new)
        self.advance()
        self.verify_final()

    def test_resume_install_after_move(self):
        self.prepare("install")
        append(self.forward, self.record)
        move_verified(self.stage, self.profile, "alpha", self.new)
        self.advance()
        self.verify_final(install=True)

    def test_modified_profile_blocks_before_journal(self):
        self.prepare()
        p = self.profile / "alpha" / "SKILL.md"
        p.write_bytes(b"owner edit")
        with self.assertRaisesRegex(CatalogError, "ADVANCE_INITIAL_LAYOUT"):
            self.advance()
        self.assertEqual(p.read_bytes(), b"owner edit")
        self.assertEqual(scan(self.forward), [])

    def test_wrong_expected_digest_blocks_resume(self):
        self.prepare()
        append(self.forward, self.record)
        self.record["new_sha256"] = "c"*64
        with self.assertRaisesRegex(CatalogError, "ADVANCE_JOURNAL_MISMATCH"):
            self.advance()
        self.assertEqual(fingerprint(self.profile / "alpha"), self.old)

    def test_cancelled_operation_cannot_resume(self):
        self.prepare()
        append(self.forward, self.record)
        cancel(self.profile, self.stage, self.backup, self.forward, self.cancel)
        with self.assertRaisesRegex(CatalogError, "ADVANCE_REVERSE_STARTED"):
            self.advance()
        self.assertEqual(fingerprint(self.profile / "alpha"), self.old)

    def test_rolled_back_operation_cannot_resume(self):
        self.prepare()
        self.advance()
        restore(self.profile, self.stage, self.backup, self.forward, self.rollback)
        with self.assertRaisesRegex(CatalogError, "ADVANCE_REVERSE_STARTED"):
            self.advance()
        self.assertEqual(fingerprint(self.profile / "alpha"), self.old)

    def test_corrupt_reverse_log_blocks(self):
        self.prepare()
        (self.cancel / "00-prepared.json").write_bytes(b"{")
        with self.assertRaises(ValueError):
            self.advance()
        self.assertEqual(scan(self.forward), [])
        self.assertEqual(fingerprint(self.profile / "alpha"), self.old)


if __name__ == "__main__":
    unittest.main()
