"""UP02.03: recovery observations on disposable same-volume fixtures."""
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import profile_plan as p
import profile_recovery as r


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = pathlib.Path(temp.name).resolve()
        self.profile, self.stage, self.backup = [root / n for n in ("profile", "stage", "backup")]
        for folder in (self.profile, self.stage, self.backup):
            folder.mkdir()
        self.old = self.profile / "alpha"
        self.new = self.stage / "alpha"
        self.saved = self.backup / "alpha"
        for path, version in ((self.old, "0.0.1"), (self.new, "0.0.2")):
            path.mkdir()
            (path / "VERSION").write_bytes((version + "\n").encode())
            (path / "SKILL.md").write_bytes(b"fixture\n")
        def fingerprint(path):
            budget = p.Budget()
            return p.snapshot(path, p.inventory(path, budget), budget)[1]
        self.record = {"schema_version": 1, "repository": p.REPO, "id": "alpha",
                       "operation": "update", "phase": "PREPARED",
                       "old_version": "0.0.1", "new_version": "0.0.2",
                       "old_sha256": fingerprint(self.old), "new_sha256": fingerprint(self.new)}

    def inspect(self):
        return r.inspect(self.profile, self.stage, self.backup, json.dumps(self.record).encode())

    def test_prepared(self):
        got = self.inspect()
        self.assertEqual(got["state"], "NOT_STARTED")
        self.assertFalse(got["apply_authorized"])
        self.assertTrue(self.old.exists() and self.new.exists() and not self.saved.exists())

    def test_interrupted_after_first_rename(self):
        self.old.rename(self.saved)
        self.assertEqual(self.inspect()["state"], "OLD_IN_BACKUP")
        self.record["phase"] = "OLD_MOVED"
        self.assertEqual(self.inspect()["state"], "OLD_IN_BACKUP")
        self.assertTrue(self.saved.exists() and self.new.exists() and not self.old.exists())

    def test_interrupted_after_second_rename(self):
        self.old.rename(self.saved)
        self.record["phase"] = "OLD_MOVED"
        self.new.rename(self.old)
        self.assertEqual(self.inspect()["state"], "NEW_PRESENT_OLD_RETAINED")
        for phase in ("NEW_MOVED", "VERIFIED"):
            self.record["phase"] = phase
            self.assertEqual(self.inspect()["state"], "NEW_PRESENT_OLD_RETAINED")

    def test_two_steps_ahead_blocked(self):
        self.old.rename(self.saved)
        self.new.rename(self.old)
        self.assertEqual(self.inspect()["status"], "BLOCKED")

    def test_local_edit_blocked(self):
        (self.old / "SKILL.md").write_bytes(b"owner edit")
        self.assertEqual(self.inspect()["layout"]["profile"], "OTHER")
        self.assertEqual(self.inspect()["status"], "BLOCKED")

    def test_missing_stage_blocked(self):
        self.new.rename(self.stage / "unselected")
        self.assertEqual(self.inspect()["status"], "BLOCKED")
        self.assertTrue((self.stage / "unselected").exists())

    def test_install_states(self):
        self.old.rename(self.profile / "unselected")
        self.record.update(operation="install", old_version=None, old_sha256=None)
        self.assertEqual(self.inspect()["state"], "NOT_STARTED")
        self.new.rename(self.old)
        self.assertEqual(self.inspect()["state"], "NEW_PRESENT")
        self.assertTrue((self.profile / "unselected").exists())

    def test_wrong_journal_fields_refused(self):
        self.record["id"] = "../alpha"
        with self.assertRaises(p.CatalogError):
            self.inspect()

    def test_invalid_phase_refused(self):
        self.record["phase"] = "UNKNOWN"
        with self.assertRaises(p.CatalogError):
            self.inspect()

    def test_unrelated_skill_not_read(self):
        extra = self.profile / "unselected"
        extra.mkdir()
        (extra / "marker").write_bytes(b"unrelated")
        self.assertEqual(self.inspect()["state"], "NOT_STARTED")
        self.assertEqual((extra / "marker").read_bytes(), b"unrelated")


if __name__ == "__main__":
    unittest.main()
