"""Batch application, resume and preflight failures in disposable roots."""
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import profile_batch_apply as a
from profile_journal import append, scan
from profile_move import move_verified
from profile_transaction_fixture import fingerprint
from catalog_index import CatalogError, REPO


@unittest.skipUnless(os.name == "nt" or sys.platform == "linux", "unsupported platform")
class BatchApplyTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = pathlib.Path(temp.name).resolve()
        self.profile, self.stage, self.backup, self.log = [root / n for n in ("profile", "stage", "backup", "log")]
        for p in (self.profile, self.stage, self.backup, self.log):
            p.mkdir()
        self.records, self.skipped, self.pins = [], [], []
        for name in ("alpha", "beta", "gamma"):
            new = self.make(self.stage, name, "0.0.2")
            old = (None, None)
            if name == "alpha":
                old = self.make(self.profile, name, "0.0.1")
            if name == "gamma":
                shutil.copytree(self.stage / name, self.profile / name)
                self.skipped.append({"id": name, "version": new[0], "sha256": new[1]})
            else:
                self.records.append({"schema_version": 1, "repository": REPO, "id": name,
                    "operation": "update" if old[0] else "install", "phase": "PREPARED",
                    "old_version": old[0], "old_sha256": old[1],
                    "new_version": new[0], "new_sha256": new[1]})
                for k in a.LOGS:
                    (self.log / name / k).mkdir(parents=True)
            self.pins.append({"id": name, "version": new[0], "stage_sha256": new[1],
                              "raw_sha256": "a"*64, "tree": "b"*40,
                              "commit": "c"*40, "tag_object": "d"*40,
                              "ref": "refs/tags/" + name + "/v" + new[0]})
        self.plan = {"status": "BATCH_PREFLIGHT_OBSERVED", "apply_authorized": False,
                     "operation": "update", "selection": "ALL", "selected_count": 3,
                     "records": self.records, "skipped": self.skipped, "pins": self.pins}
        other = self.profile / "other"
        other.mkdir()
        (other / "marker").write_bytes(b"untouched")

    def make(self, root, name, ver):
        p = root / name
        p.mkdir()
        (p / "VERSION").write_bytes((ver + "\n").encode())
        (p / "SKILL.md").write_bytes(ver.encode())
        return fingerprint(p)

    def execute(self):
        return a.execute(self.profile, self.stage, self.backup, self.log, self.plan)

    def check_initial(self):
        self.assertFalse((self.log / a.RECEIPT).exists())
        self.assertFalse((self.profile / "beta").exists())
        self.assertEqual((self.profile / "alpha" / "VERSION").read_bytes(), b"0.0.1\n")

    def test_mixed_batch_and_repeat(self):
        result = self.execute()
        self.assertEqual(result["completed"], ["alpha", "beta"])
        self.assertEqual(result["skipped"], ["gamma"])
        self.assertFalse(result["atomic_batch"])
        self.assertEqual((self.backup / "alpha" / "VERSION").read_bytes(), b"0.0.1\n")
        self.assertEqual((self.profile / "other" / "marker").read_bytes(), b"untouched")
        with mock.patch.object(a, "advance") as advance:
            self.execute()
            advance.assert_not_called()

    def test_later_conflict_blocks_every_write(self):
        (self.stage / "beta" / "SKILL.md").write_bytes(b"changed")
        with self.assertRaisesRegex(CatalogError, "BATCH_LAYOUT"):
            self.execute()
        self.check_initial()

    def test_skip_changed_blocks_every_write(self):
        (self.profile / "gamma" / "SKILL.md").write_bytes(b"changed")
        with self.assertRaisesRegex(CatalogError, "BATCH_SKIPPED_CHANGED"):
            self.execute()
        self.check_initial()

    def test_resume_after_second_skill_interrupted(self):
        real = a.advance
        def fail(*args):
            record = args[-1]
            if record["id"] == "beta":
                append(args[3], record)
                move_verified(self.stage, self.profile, "beta",
                              (record["new_version"], record["new_sha256"]))
                raise OSError("fixture interruption")
            return real(*args)
        with mock.patch.object(a, "advance", side_effect=fail):
            with self.assertRaises(OSError):
                self.execute()
        self.assertEqual(scan(self.log / "alpha" / "forward")[-1]["phase"], "VERIFIED")
        with mock.patch.object(a, "advance", wraps=real) as resume:
            self.execute()
            self.assertEqual([x.args[-1]["id"] for x in resume.call_args_list], ["beta"])

    def test_receipt_mismatch_blocks(self):
        self.execute()
        self.plan["pins"][0]["commit"] = "e"*40
        with self.assertRaisesRegex(CatalogError, "BATCH_RECEIPT_MISMATCH"):
            self.execute()

    def test_existing_journal_without_receipt_blocks(self):
        append(self.log / "alpha" / "forward", self.records[0])
        with self.assertRaisesRegex(CatalogError, "BATCH_MISSING_RECEIPT"):
            self.execute()
        self.check_initial()

    def test_out_of_order_history_blocks(self):
        _, raw = a.manifest(self.plan)
        a.write_receipt(self.log / a.RECEIPT, raw)
        append(self.log / "beta" / "forward", self.records[1])
        with self.assertRaisesRegex(CatalogError, "BATCH_ORDER"):
            self.execute()
        self.assertFalse((self.profile / "beta").exists())

    def test_receipt_partial_blocks(self):
        (self.log / a.RECEIPT).write_bytes(b"{")
        with self.assertRaisesRegex(CatalogError, "BATCH_RECEIPT_MISMATCH"):
            self.execute()
        self.assertEqual((self.log / a.RECEIPT).read_bytes(), b"{")

    def test_duplicate_record_blocks(self):
        self.records.append(dict(self.records[0]))
        with self.assertRaisesRegex(CatalogError, "BATCH_NAME"):
            self.execute()
        self.check_initial()

    def test_wrong_pin_blocks(self):
        self.plan["pins"][0]["stage_sha256"] = "e"*64
        with self.assertRaisesRegex(CatalogError, "BATCH_PIN"):
            self.execute()
        self.check_initial()


if __name__ == "__main__":
    unittest.main()
