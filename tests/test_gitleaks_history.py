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
            return [(A, 1, b"x")]

        def scan(*args):
            calls["scan"] += 1
            advance("scan")
            return {}, b"", b""

        with mock.patch.object(h.time, "monotonic", side_effect=lambda: clock[0]), \
                mock.patch.object(h, "inventory", side_effect=inventory), \
                mock.patch.object(h, "checked_blob_batch", side_effect=blob), \
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

    def blob_frame(self, content, oid_length=40):
        oid = h.blob_oid(content, oid_length)
        return (oid, len(content)), f"{oid} blob {len(content)}\n".encode() + content + b"\n"

    def test_batch_empty_and_multiline_objects(self):
        a, raw_a = self.blob_frame(b"")
        b, raw_b = self.blob_frame(b"first\nsecond\n")
        self.assertEqual(h.parse_blob_batch(raw_a + raw_b, [a, b]),
                         [(a[0], a[1], b""), (b[0], b[1], b"first\nsecond\n")])

    def test_batch_sha256_identity(self):
        row, raw = self.blob_frame(b"fixture", 64)
        self.assertEqual(h.parse_blob_batch(raw, [row]), [(row[0], row[1], b"fixture")])

    def test_batch_malformed_or_truncated_rejected(self):
        row, raw = self.blob_frame(b"abc")
        for data, code in ((raw.replace(b"blob", b"tree", 1), "HEADER"),
                           (raw[:-1], "FRAME"), (raw + b"extra", "TRAILING"),
                           (raw.replace(b"abc\n", b"xyz\n"), "OID")):
            with self.subTest(code=code), self.assertRaisesRegex(h.InstallCheckError, code):
                h.parse_blob_batch(data, [row])

    def test_batch_duplicate_or_reordered_rejected(self):
        a, raw_a = self.blob_frame(b"abc")
        b, raw_b = self.blob_frame(b"xyz")
        with self.assertRaisesRegex(h.InstallCheckError, "INPUT"):
            h.parse_blob_batch(raw_a + raw_a, [a, a])
        with self.assertRaisesRegex(h.InstallCheckError, "HEADER"):
            h.parse_blob_batch(raw_b + raw_a, [a, b])

    def test_batch_binary_and_invalid_encoding_rejected(self):
        for content, code in ((b"a\0", "BINARY"), (b"\xff", "ENCODING")):
            row, raw = self.blob_frame(content)
            with self.subTest(code=code), self.assertRaisesRegex(h.InstallCheckError, code):
                h.parse_blob_batch(raw, [row])

    def test_batch_chunk_count_and_byte_bound(self):
        sizes = {f"{i:040x}": h.MAX_FILE for i in range(5)}
        self.assertEqual([len(b) for b in h.history_batches(sizes)], [2, 2, 1])
        empty = {f"{i:040x}": 0 for i in range(65)}
        self.assertEqual([len(b) for b in h.history_batches(empty)], [32, 32, 1])
        with self.assertRaisesRegex(h.InstallCheckError, "INPUT"):
            list(h.history_batches({A: h.MAX_FILE + 1}))

    def test_invalid_batch_refused_before_git(self):
        for batch in ([(A, 1), (A, 1)], [(A, h.MAX_FILE + 1)],
                      [(f"{i:040x}", h.MAX_FILE) for i in range(3)]):
            with self.subTest(batch_size=len(batch)), mock.patch.object(h, "git") as git:
                with self.assertRaisesRegex(h.InstallCheckError, "INPUT"):
                    h.checked_blob_batch(None, {}, batch)
                git.assert_not_called()

    def test_batch_real_git_matches_single_object_reads(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            env = h.fixture_env(root)
            h.git(root, env, "init", "-q")
            blobs = {}
            for content in (b"", b"abc\n", b"first\nsecond\n"):
                oid = h.git(root, env, "hash-object", "-w", "--stdin", data=content).strip().decode("ascii")
                blobs[oid] = len(content)
            batch = next(h.history_batches(blobs))
            actual = h.checked_blob_batch(root, env, batch)
            self.assertEqual(actual, [(oid, size, h.checked_blob(root, env, oid, size))
                                      for oid, size in batch])

    def test_unexpected_object(self):
        with self.assertRaisesRegex(h.InstallCheckError, "INVALID"):
            h.blob_metadata(f"{B} blob 1\n".encode(), {A})


if __name__ == "__main__":
    unittest.main()
