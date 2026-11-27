"""Synthetic captures and a disposable Git fixture; no real project changes."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import cleanup_plan as p

SHA = b"a" * 40


def head(path, mode=b"100644", oid=SHA):
    return mode + (b" commit " if mode == b"160000" else b" blob ") + oid + b"\t" + path + b"\0"


def index(path, mode=b"100644", stage=b"0", oid=SHA):
    return mode + b" " + oid + b" " + stage + b"\t" + path + b"\0"


def capture(heads=b"", indexes=b"", ignored=b"", untracked=b"", sha=SHA):
    return dict(zip(p.NAMES, (sha + b"\n", heads, indexes, ignored, untracked), strict=True))


def fixture_env():
    if any(k.upper().startswith("GIT_") and k.upper() != "GIT_PAGER" for k in os.environ):
        raise RuntimeError("FIXTURE_GIT_CONTEXT_UNSAFE")
    keys = ("PATH", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP", "TMPDIR",
            "LANG", "LC_ALL", "LC_CTYPE", "TZ")
    env = {k: v for k in keys if (v := os.getenv(k)) is not None}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0")
    return env


class PlanTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.parent = Path(tmp.name).resolve()
        self.root = self.parent / "project"
        (self.root / ".git").mkdir(parents=True)

    def file(self, name, data=b"abc"):
        f = self.root / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data)
        return f

    def check(self, c, scopes=(b"build",), details=True):
        return p.plan(self.root, c, dict(c), scopes, details)

    def snapshots(self, c):
        folders = (self.parent / "first", self.parent / "second")
        for folder in folders:
            folder.mkdir()
            for name in p.NAMES:
                (folder / name).write_bytes(c[name])
        return folders

    def test_exact_candidates_not_tracked_or_untracked(self):
        for name in ("build/old.tmp", "build/new.tmp", "build/keep.tmp", "build/review.tmp",
                     "build/model.gguf", "dist/other.tmp"):
            self.file(name)
        c = capture(head(b"build/old.tmp"), index(b"build/new.tmp"),
                    b"build/old.tmp\0build/new.tmp\0build/review.tmp\0build/model.gguf\0dist/other.tmp\0",
                    b"build/keep.tmp\0")
        result = self.check(c)
        self.assertEqual(result["status"], "OBSERVED")
        self.assertEqual(result["counts"], {"outside_scope": 1, "protected_or_unknown": 1,
            "tracked_overlap": 2, "untracked_overlap": 0, "metadata_unverified": 0, "review": 1})
        self.assertEqual(result["private_review"][0]["relative_path"], "build/review.tmp")
        self.assertEqual(result["review_logical_bytes"], 3)
        self.assertFalse(result["deletion_authorized"])
        self.assertEqual(result["capture_authenticity"], "NOT_VERIFIED")
        self.assertIsNone(result["reclaimable_bytes"])

    def test_tracked_prefix_in_both_directions_and_gitlink(self):
        self.file("build/tracked/child")
        self.file("build/collision")
        self.file("build/submodule/x")
        c = capture(head(b"build/tracked") + head(b"build/submodule", b"160000"),
                    index(b"build/collision/child"),
                    b"build/tracked/child\0build/collision\0build/submodule/x\0")
        self.assertEqual(self.check(c)["counts"]["tracked_overlap"], 3)

    def test_untracked_prefix_preserved(self):
        self.file("build/folder/file")
        result = self.check(capture(ignored=b"build/folder/file\0", untracked=b"build/folder\0"))
        self.assertEqual(result["counts"]["untracked_overlap"], 1)

    def test_case_and_unicode_ancestor_aliases_block(self):
        for a, b in ((b"build/Foo/a", b"build/foo/b"),
                     ("build/café/a".encode(), "build/cafe\u0301/b".encode())):
            with self.subTest(a=a), self.assertRaisesRegex(p.PlanError, "PATH_ALIAS_COLLISION"):
                self.check(capture(head(a), ignored=b + b"\0"))

    def test_unicode_paths_and_compatibility_protection(self):
        f = self.file("build/тест.tmp")
        result = self.check(capture(ignored="build/тест.tmp\0".encode()))
        self.assertEqual(result["private_review"][0]["relative_path"], "build/тест.tmp")
        self.assertEqual(f.read_bytes(), b"abc")
        f = self.file("build/ｓｅｃｒｅｔｓ/thing")
        result = self.check(capture(ignored="build/ｓｅｃｒｅｔｓ/thing\0".encode()))
        self.assertEqual(result["counts"]["protected_or_unknown"], 1)
        self.assertEqual(result["private_review"], [])

    def test_nonportable_path_rejected(self):
        for raw in (b"/abs", b"build/../a", b"build//a", b"build/NUL.txt", b"build/x.",
                    b"build/x ", b"build/a:b", b"build/FILE~1", b"build/a\\b", b"build/.git/x",
                    b"build/line\nname", b"build/\xff", b"build/a/"):
            with self.subTest(raw=raw), self.assertRaises(p.PlanError):
                self.check(capture(ignored=raw + b"\0"))

    def test_malformed_and_duplicate_records(self):
        for c in (capture(ignored=b"build/a"), capture(ignored=b"\0"),
                  capture(ignored=b"build/a\0build/a\0"), capture(heads=b"bad\0"),
                  capture(indexes=index(b"build/a", stage=b"2")),
                  capture(heads=head(b"build/a", oid=b"b" * 64)),
                  capture(ignored=b"build/a\0", untracked=b"build/a\0"),
                  capture(sha=b"0" * 40), capture(heads=head(b"build/a", mode=b"040000")),
                  capture(heads=head(b"build/a") + head(b"build/a/b"))):
            with self.subTest(c=c), self.assertRaises(p.PlanError):
                self.check(c)
        with patch.object(p, "MAX_FRAME", 4), self.assertRaises(p.PlanError):
            p.rows(b"12345\0")

    def test_stale_capture_no_candidates(self):
        first = capture(ignored=b"build/a\0")
        second = capture(ignored=b"build/b\0")
        result = p.plan(self.root, first, second, [b"build"], True)
        self.assertEqual(result["status"], "STALE")
        self.assertNotIn("private_review", result)
        self.assertFalse(result["deletion_authorized"])

    def test_scope_and_exact_spelling(self):
        self.file("build/a")
        c = capture(ignored=b"build/a\0")
        for scopes in ((b"build", b"build/sub"), (b"build", b"build"), (b"data",), (b".",), ()):
            with self.subTest(scopes=scopes), self.assertRaises(p.PlanError):
                self.check(c, scopes)
        self.assertEqual(self.check(c, (b"BUILD",))["counts"]["outside_scope"], 1)

    def test_metadata_nested_and_missing(self):
        self.file("build/nested/.git", b"fixture")
        self.file("build/nested/a")
        result = self.check(capture(ignored=b"build/nested/a\0build/missing\0"))
        self.assertEqual(result["counts"]["metadata_unverified"], 2)
        self.assertEqual(result["counts"]["review"], 0)

    def test_link_and_hardlink_rejected(self):
        f = self.file("build/target")
        try:
            os.link(f, f.with_name("alias"))
            (f.parent / "link").symlink_to(f)
        except (OSError, NotImplementedError):
            self.skipTest("link capability unavailable")
        result = self.check(capture(ignored=b"build/target\0build/alias\0build/link\0"))
        self.assertEqual(result["counts"]["metadata_unverified"], 3)

    def test_metadata_no_content_read_default_privacy(self):
        f = self.file("build/private.tmp")
        c = capture(ignored=b"build/private.tmp\0")
        with patch("builtins.open", side_effect=AssertionError("content")), \
                patch.object(Path, "open", side_effect=AssertionError("content")), \
                patch.object(p.os, "open", side_effect=AssertionError("content")):
            result = self.check(c, details=False)
        self.assertEqual(result["counts"]["review"], 1)
        self.assertNotIn("private.tmp", json.dumps(result))
        self.assertNotIn("private_review", result)
        self.assertEqual(f.read_bytes(), b"abc")

    def test_bounded_output_and_partial_no_details(self):
        self.file("build/a", b"1"); self.file("build/b", b"222")
        c = capture(ignored=b"build/a\0build/b\0")
        with patch.object(p, "MAX_DETAILS", 1):
            result = self.check(c)
        self.assertFalse(result["private_details_complete"])
        self.assertEqual(len(result["private_review"]), 1)
        self.assertEqual(result["private_review"][0]["relative_path"], "build/b")
        with patch.object(p, "MAX_REVIEW", 1):
            result = self.check(c)
        self.assertEqual(result["status"], "PARTIAL")
        self.assertNotIn("private_review", result)

    def test_empty_capture_and_sha256(self):
        c = capture(sha=b"a" * 64)
        self.assertEqual(self.check(c)["counts"]["review"], 0)
        self.assertEqual(self.check(c)["ignored_observed"], 0)

    def test_capture_cli_and_same_directory(self):
        self.file("build/a")
        first, second = self.snapshots(capture(ignored=b"build/a\0"))
        self.assertEqual(p.read_pair(self.root, first, second)[0]["ignored.z"], b"build/a\0")
        with self.assertRaisesRegex(p.PlanError, "CAPTURE_NOT_DISTINCT"):
            p.read_pair(self.root, first, first)
        with self.assertRaisesRegex(p.PlanError, "CAPTURE_SCOPE_OVERLAP"):
            p.read_pair(self.root, self.root, second)
        command = [sys.executable, "-B", str(SCRIPTS / "cleanup_plan.py"), "--root", str(self.root),
                   "--first", str(first), "--second", str(second), "--scope", "build"]
        result = subprocess.run(command, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["counts"]["review"], 1)
        (second / "ignored.z").write_bytes(b"")
        self.assertEqual(subprocess.run(command, capture_output=True, timeout=15).returncode, 1)
        (second / "ignored.z").write_bytes(b"bad")
        (first / "ignored.z").write_bytes(b"bad")
        result = subprocess.run(command, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["reason"], "CAPTURE_FRAME_INVALID")

    @staticmethod
    def adjusted(info, **changes):
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns",
                  "st_mode", "st_nlink", "st_birthtime_ns", "st_file_attributes")
        data = {field: getattr(info, field) for field in fields if hasattr(info, field)}
        data.update(changes)
        return SimpleNamespace(**data)

    def test_windows_cross_method_ctime_difference(self):
        f = self.file("build/a")
        original = os.fstat

        def descriptor_stat(fd):
            info = original(fd)
            return self.adjusted(info, st_ctime_ns=info.st_ctime_ns + 100)

        with patch.object(p, "WINDOWS", True), patch.object(p.os, "fstat", side_effect=descriptor_stat):
            self.assertEqual(p.read_record(f)[0], b"abc")

    def test_windows_same_method_ctime_change_refused(self):
        f = self.file("build/a")
        original = os.fstat
        calls = 0

        def descriptor_stat(fd):
            nonlocal calls
            calls += 1
            info = original(fd)
            return self.adjusted(info, st_ctime_ns=info.st_ctime_ns + calls * 100)

        with patch.object(p, "WINDOWS", True), patch.object(p.os, "fstat", side_effect=descriptor_stat):
            with self.assertRaisesRegex(p.PlanError, "CAPTURE_CHANGED"):
                p.read_record(f)

    def test_windows_cross_method_mtime_or_identity_change_refused(self):
        f = self.file("build/a")
        original = os.fstat
        for field in ("st_mtime_ns", "st_ino", "st_nlink"):
            def descriptor_stat(fd):
                info = original(fd)
                return self.adjusted(info, **{field: getattr(info, field) + 1})

            with self.subTest(field=field), patch.object(p, "WINDOWS", True), \
                    patch.object(p.os, "fstat", side_effect=descriptor_stat):
                with self.assertRaisesRegex(p.PlanError, "CAPTURE_CHANGED"):
                    p.read_record(f)

    def test_hardlinked_capture_rejected(self):
        f = self.file("build/a")
        try:
            os.link(f, f.with_name("alias"))
        except OSError:
            self.skipTest("hardlink unavailable")
        with self.assertRaisesRegex(p.PlanError, "CAPTURE_NOT_ORDINARY"):
            p.read_record(f)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO unavailable")
    def test_special_capture_rejected(self):
        f = self.root / "pipe"
        os.mkfifo(f)
        with self.assertRaisesRegex(p.PlanError, "CAPTURE_NOT_ORDINARY"):
            p.read_record(f)


class GitFixtureTests(unittest.TestCase):
    def test_unsafe_git_context_refused(self):
        with patch.dict(os.environ, {"GIT_CONFIG_COUNT": "1"}):
            with self.assertRaisesRegex(RuntimeError, "FIXTURE_GIT_CONTEXT_UNSAFE"):
                fixture_env()

    @unittest.skipUnless(shutil.which("git"), "Git unavailable")
    def test_actual_git_staged_deletion_and_ignored_file(self):
        env = fixture_env()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve() / "repo"
            root.mkdir()
            hooks = root.parent / "hooks"
            hooks.mkdir()

            def git(*args):
                return subprocess.run(["git", "-c", "core.hooksPath=" + str(hooks), *args], cwd=root,
                    env=env, stdin=subprocess.DEVNULL, capture_output=True, check=True, timeout=15).stdout

            git("init", "-q", "-b", "main")
            (root / "build").mkdir()
            (root / ".gitignore").write_text("build/\n", encoding="utf-8")
            old = root / "build" / "tracked.tmp"
            old.write_bytes(b"old")
            git("add", ".gitignore")
            git("add", "-f", "build/tracked.tmp")
            git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")
            git("rm", "--cached", "build/tracked.tmp")
            review = root / "build" / "review.tmp"
            review.write_bytes(b"review")
            (root / "untracked.txt").write_bytes(b"work")

            def snapshot():
                return dict(zip(p.NAMES, (git("rev-parse", "--verify", "HEAD"),
                    git("ls-tree", "-r", "-z", "HEAD"), git("ls-files", "--stage", "-z"),
                    git("ls-files", "--others", "--ignored", "--exclude-standard", "-z"),
                    git("ls-files", "--others", "--exclude-standard", "-z")), strict=True))

            first = snapshot(); second = snapshot()
            result = p.plan(root, first, second, [b"build"], True)
            self.assertEqual(result["counts"]["tracked_overlap"], 1)
            self.assertEqual(result["counts"]["review"], 1)
            self.assertEqual(result["private_review"][0]["relative_path"], "build/review.tmp")
            self.assertEqual(result["review_logical_bytes"], 6)
            self.assertEqual(old.read_bytes(), b"old")
            self.assertEqual(review.read_bytes(), b"review")
            self.assertEqual(first, snapshot())


if __name__ == "__main__":
    unittest.main()
