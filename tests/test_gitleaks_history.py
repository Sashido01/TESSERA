"""Offline object inventory validation; real history fixture runs in CI."""
import pathlib
import sys
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_gitleaks_history as h

A = "a" * 40
B = "b" * 40


class HistoryTests(unittest.TestCase):
    def test_blob_and_commit(self):
        self.assertEqual(h.blob_metadata(f"{A} blob 5\n{B} commit 10\n".encode(), {A, B}), {A: 5})

    def test_empty_blob(self):
        self.assertEqual(h.blob_metadata(f"{A} blob 0\n".encode(), {A}), {A: 0})

    def test_missing_object(self):
        with self.assertRaisesRegex(h.InstallCheckError, "MISSING"):
            h.blob_metadata(f"{A} missing\n".encode(), {A})

    def test_wrong_count(self):
        with self.assertRaisesRegex(h.InstallCheckError, "COUNT"):
            h.blob_metadata(f"{A} blob 5\n".encode(), {A, B})

    def test_duplicate(self):
        with self.assertRaisesRegex(h.InstallCheckError, "INVALID"):
            h.blob_metadata(f"{A} blob 5\n{A} blob 5\n".encode(), {A, B})

    def test_oversize(self):
        with self.assertRaisesRegex(h.InstallCheckError, "LIMIT"):
            h.blob_metadata(f"{A} blob {h.MAX_FILE + 1}\n".encode(), {A})

    def test_no_blobs(self):
        with self.assertRaisesRegex(h.InstallCheckError, "COVERAGE"):
            h.blob_metadata(f"{A} tree 1\n".encode(), {A})

    def review_with_clock(self, advance_at=None):
        clock = [0.0]
        calls = {"inventory": 0, "blob": 0, "scan": 0}

        def advance(stage):
            if advance_at == stage:
                clock[0] = float(h.MAX_SECONDS)

        def inventory(*args):
            calls["inventory"] += 1
            advance("inventory" if calls["inventory"] == 1 else "final_inventory")
            return {A: 1}

        def blob(*args):
            calls["blob"] += 1
            advance("blob")
            return b"x"

        def scan(*args):
            calls["scan"] += 1
            advance("scan")
            return {}, b"", b""

        with mock.patch.object(h.time, "monotonic", side_effect=lambda: clock[0]), \
                mock.patch.object(h, "inventory", side_effect=inventory), \
                mock.patch.object(h, "checked_blob", side_effect=blob), \
                mock.patch.object(h, "scan", side_effect=scan):
            if advance_at:
                with self.assertRaisesRegex(h.InstallCheckError, "HISTORY_TIMEOUT"):
                    h.review(None, None, None, {})
                return calls
            result = h.review(None, None, None, {})
            self.assertEqual(result["distinct_blobs"], 1)
            self.assertEqual(result["bytes_scanned"], 1)
            self.assertEqual(result["findings"], 0)
            return calls

    def test_history_deadline_before_blob(self):
        self.assertEqual(self.review_with_clock("inventory"),
                         {"inventory": 1, "blob": 0, "scan": 0})

    def test_history_deadline_after_blob(self):
        self.assertEqual(self.review_with_clock("blob"),
                         {"inventory": 1, "blob": 1, "scan": 0})

    def test_history_deadline_after_last_scan(self):
        self.assertEqual(self.review_with_clock("scan"),
                         {"inventory": 1, "blob": 1, "scan": 1})

    def test_history_deadline_after_final_inventory(self):
        self.assertEqual(self.review_with_clock("final_inventory"),
                         {"inventory": 2, "blob": 1, "scan": 1})

    def test_history_full_coverage_within_deadline(self):
        self.assertEqual(self.review_with_clock(),
                         {"inventory": 2, "blob": 1, "scan": 1})

    def test_unexpected_object(self):
        with self.assertRaisesRegex(h.InstallCheckError, "INVALID"):
            h.blob_metadata(f"{B} blob 1\n".encode(), {A})


if __name__ == "__main__":
    unittest.main()
