import hashlib
import pathlib
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import check_gitleaks_history as h
import check_gitleaks_history_container as c


class HistoryContainerTests(unittest.TestCase):
    def test_blob_identity(self):
        data = b"hello\n"
        for n, algorithm in ((40, "sha1"), (64, "sha256")):
            oid = hashlib.new(algorithm, b"blob 6\0" + data).hexdigest()
            self.assertEqual(h.blob_oid(data, n), oid)
            with mock.patch.object(h, "git", return_value=b"world\n"):
                with self.assertRaisesRegex(RuntimeError, "OID_MISMATCH"):
                    h.checked_blob(None, None, oid, len(data))

    def test_batch_limits(self):
        blobs = {f"{n:040x}": 2 for n in range(7)}
        with mock.patch.object(c, "BATCH_COUNT", 3), mock.patch.object(c, "BATCH_BYTES", 4):
            batches = list(c.batches(blobs))
        self.assertEqual([len(b) for b in batches], [2, 2, 2, 1])
        self.assertEqual(dict(x for b in batches for x in b), blobs)

    def test_batch_empty_and_invalid(self):
        self.assertEqual(list(c.batches({"a": 0})), [[("a", 0)]])
        for blobs in ({}, {"a": -1}, {"a": h.MAX_FILE + 1}):
            with self.assertRaises(RuntimeError):
                list(c.batches(blobs))

    def report(self):
        return {"digest": "d", "version": c.VERSION, "files": 2, "scanned_nonempty": 1,
                "empty": 1, "bytes_scanned": 1, "by_rule": [{"scope": "other", "rule": "test-rule", "count": 1}],
                "findings": 1, **dict.fromkeys(c.CONTROLS, "PASS")}

    def test_validate_batch(self):
        self.assertEqual(c.validate_batch(self.report(), [(0, b"x"), (0, b"")], "d"), {"test-rule": 1})

    def test_reject_bad_batch(self):
        for change in ({"files": 1}, {"digest": "e"}, {"findings": 2}, {"fixture_redaction": "FAIL"},
                       {"by_rule": [{"scope": "tests", "rule": "test-rule", "count": 1}]},
                       {"by_rule": self.report()["by_rule"] * 2}):
            with self.subTest(change=change), self.assertRaises(RuntimeError):
                c.validate_batch({**self.report(), **change}, [(0, b"x"), (0, b"")], "d")

    def test_snapshot_order_independent(self):
        self.assertEqual(h.history_snapshot({"a": 1, "b": 2}), h.history_snapshot({"b": 2, "a": 1}))
        self.assertNotEqual(h.history_snapshot({"a": 1}), h.history_snapshot({"a": 2}))


if __name__ == "__main__":
    unittest.main()
