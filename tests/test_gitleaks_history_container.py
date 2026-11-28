import hashlib
import io
import threading
import pathlib
import sys
import tempfile
import time
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

    def test_read_subchunks_preserve_exact_records(self):
        blobs = {h.blob_oid(f"fixture {i}".encode(), 40): f"fixture {i}".encode()
                 for i in range(65)}
        batch = sorted((oid, len(data)) for oid, data in blobs.items())
        def reader(repo, env, chunk):
            return [(oid, size, blobs[oid]) for oid, size in chunk]
        with mock.patch.object(c, "checked_blob_batch", side_effect=reader) as read:
            self.assertEqual(c.records_for_batch(None, {}, batch, time.monotonic() + 10),
                             [(0, blobs[oid]) for oid, _ in batch])
            self.assertEqual([len(x.args[2]) for x in read.call_args_list], [32, 32, 1])

    def test_read_invalid_refused_before_git(self):
        a, b = "a" * 40, "b" * 40
        for batch in ([], [(a, 1), (a, 1)], [(b, 1), (a, 1)],
                      [(a, -1)], [(a, h.MAX_FILE + 1)], [(a, True)],
                      [(a, 1), ("invalid", 1)]):
            with self.subTest(batch=batch), mock.patch.object(c, "checked_blob_batch") as read:
                with self.assertRaises(RuntimeError):
                    c.records_for_batch(None, {}, batch, time.monotonic() + 10)
                read.assert_not_called()

    def test_read_incomplete_or_reordered_rejected(self):
        batch = [("a" * 40, 1), ("b" * 40, 1)]
        for rows in ([], [(batch[0][0], 1, b"x")],
                     [(batch[1][0], 1, b"y"), (batch[0][0], 1, b"x")],
                     [(batch[0][0], 1, b"wrong"), (batch[1][0], 1, b"y")]):
            with self.subTest(rows=rows), mock.patch.object(c, "checked_blob_batch", return_value=rows):
                with self.assertRaisesRegex(RuntimeError, "READ_COVERAGE"):
                    c.records_for_batch(None, {}, batch, time.monotonic() + 10)

    def test_read_deadline_refused(self):
        batch = [("a" * 40, 1)]
        with mock.patch.object(c, "checked_blob_batch") as read:
            with self.assertRaisesRegex(RuntimeError, "DEADLINE"):
                c.records_for_batch(None, {}, batch, 0)
            read.assert_not_called()
        with mock.patch.object(c.time, "monotonic", side_effect=[1, 3]), \
                mock.patch.object(c, "checked_blob_batch", return_value=[("a" * 40, 1, b"x")]):
            with self.assertRaisesRegex(RuntimeError, "DEADLINE"):
                c.records_for_batch(None, {}, batch, 2)

    def test_read_actual_git_preserves_blob_boundaries(self):
        import os
        if any(k.upper().startswith("GIT_") and k.upper() != "GIT_PAGER" for k in os.environ):
            raise RuntimeError("FIXTURE_GIT_CONTEXT_UNSAFE")
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            env = h.fixture_env(root)
            h.git(root, env, "init", "-q")
            blobs = {}
            for data in [b"", b"first\nsecond\n", *[f"entry {i}\n".encode() for i in range(65)]]:
                oid = h.git(root, env, "hash-object", "-w", "--stdin", data=data).strip().decode("ascii")
                blobs[oid] = len(data)
            batch = sorted(blobs.items())
            expected = [(0, h.checked_blob(root, env, oid, size)) for oid, size in batch]
            self.assertEqual(c.records_for_batch(root, env, batch, time.monotonic() + 30), expected)

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

    def test_worker_selection_requires_cpu_quota_and_memory(self):
        for quota, memory, cpus, expected in (
                ("max 100000", 3000000, 4, 2),
                ("400000 100000", 3000000, 4, 2),
                ("200000 100000", 3000000, 4, 1),
                ("max 100000", 1000000, 4, 1),
                ("max 100000", 3000000, 2, 1),
                ("bad", 3000000, 4, 1)):
            def opened(path, *args, **kwargs):
                return io.StringIO(quota if path.name == "cpu.max" else f"MemAvailable: {memory} kB\n")
            with self.subTest(quota=quota, memory=memory, cpus=cpus), \
                    mock.patch.object(c.os, "sched_getaffinity", create=True, return_value=set(range(cpus))), \
                    mock.patch.object(c.pathlib.Path, "open", opened):
                self.assertEqual(c.container_workers(), expected)

    def test_parallel_windows_keep_order_and_cover_all_batches(self):
        blobs = {f"{i:040x}": 1 for i in range(5)}
        barrier = threading.Barrier(2)
        def read(repo, env, batch, deadline):
            return [(0, bytes([int(batch[0][0], 16)]))]
        def execute(records):
            index = records[0][1][0]
            if index < 4:
                barrier.wait(timeout=5)
            return {"test": index}
        with mock.patch.object(c, "BATCH_COUNT", 1), \
                mock.patch.object(c, "records_for_batch", side_effect=read):
            got = list(c.scan_batches(None, {}, blobs, time.monotonic()+15, execute, 2))
        self.assertEqual([b[0][0] for b, _ in got], sorted(blobs))
        self.assertEqual([r["test"] for _, r in got], list(range(5)))

    def test_failed_window_never_reads_or_submits_next(self):
        blobs = {f"{i:040x}": 1 for i in range(5)}
        called = []
        def read(repo, env, batch, deadline):
            called.append(batch[0][0])
            return [(0, b"x")]
        with mock.patch.object(c, "BATCH_COUNT", 1), \
                mock.patch.object(c, "records_for_batch", side_effect=read):
            with self.assertRaisesRegex(RuntimeError, "fixture"):
                list(c.scan_batches(None, {}, blobs, time.monotonic()+10,
                                    mock.Mock(side_effect=RuntimeError("fixture")), 2))
        self.assertEqual(called, sorted(blobs)[:2])

    def test_expired_deadline_and_bad_workers_do_not_read(self):
        for deadline, workers in ((0, 2), (time.monotonic()+10, 3)):
            with mock.patch.object(c, "records_for_batch") as read:
                with self.assertRaises(RuntimeError):
                    list(c.scan_batches(None, {}, {"a"*40: 1}, deadline, None, workers))
                read.assert_not_called()

    def test_snapshot_order_independent(self):
        self.assertEqual(h.history_snapshot({"a": 1, "b": 2}), h.history_snapshot({"b": 2, "a": 1}))
        self.assertNotEqual(h.history_snapshot({"a": 1}), h.history_snapshot({"a": 2}))


if __name__ == "__main__":
    unittest.main()
