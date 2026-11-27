import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import profile_plan as p


class ProfilePlanTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = pathlib.Path(tmp.name).resolve()
        self.profile, self.stage, self.baseline = [self.root / name for name in ("profile", "stage", "baseline")]
        for directory in (self.profile, self.stage, self.baseline):
            directory.mkdir()
        self.write(self.stage, "alpha", "0.0.2")
        self.write(self.baseline, "alpha", "0.0.1")
        self.write(self.stage, "beta", "0.0.2")
        self.write(self.baseline, "beta", "0.0.1")

    def write(self, root, name, version):
        folder = root / name
        folder.mkdir()
        (folder / "VERSION").write_bytes((version + "\n").encode())
        (folder / "SKILL.md").write_bytes(b"synthetic skill\n")
        (folder / "references").mkdir()
        (folder / "references" / "guide.md").write_bytes(("guide " + version).encode())
        return folder

    def resolution(self, names=("alpha",), operation="update", all_skills=False):
        return json.dumps({"status": "RESOLVED", "repository": p.REPO, "install_authorized": False,
            "operation": operation, "selection": "ALL" if all_skills else "EXPLICIT",
            "catalog_skill_count": 2, "selected_count": len(names), "unselected_count": 2-len(names),
            "skills": [{"id": name, "version": "0.0.2", "path": "skills/" + name,
                        "ref": "refs/tags/" + name + "/v0.0.2", "tag_object": "a"*40,
                        "commit": "b"*40, "tree": "c"*40} for name in names]}).encode()

    def plan(self, names=("alpha",), operation="update", all_skills=False, baseline=True):
        return p.plan(self.profile, self.stage, self.baseline if baseline else None,
                      self.resolution(names, operation, all_skills))

    def copy(self, source, name):
        shutil.copytree(source / name, self.profile / name)

    def test_selected_install_does_not_read_other_skill(self):
        self.write(self.profile, "beta", "0.0.1")
        with mock.patch.object(p, "inventory", wraps=p.inventory) as read:
            got = self.plan(operation="install")
        self.assertEqual(got["decisions"][0]["decision"], "PLAN_INSTALL")
        self.assertEqual([x.args[0].name for x in read.call_args_list], ["alpha"])
        self.assertFalse((self.profile / "alpha").exists())
        self.assertFalse(got["apply_authorized"])
        self.assertEqual(got["source_authenticity"], "NOT_VERIFIED")

    def test_update_all_mixed_existing_and_missing(self):
        self.copy(self.baseline, "alpha")
        got = self.plan(("alpha", "beta"), all_skills=True)
        self.assertEqual([r["decision"] for r in got["decisions"]], ["PLAN_UPDATE", "PLAN_INSTALL"])
        self.assertEqual((self.profile / "alpha" / "VERSION").read_bytes(), b"0.0.1\n")
        self.assertFalse((self.profile / "beta").exists())

    def test_install_existing_old_refused(self):
        self.copy(self.baseline, "alpha")
        got = self.plan(operation="install")
        self.assertEqual(got["decisions"][0]["reason"], "EXISTING_DIFFERENT")

    def test_noop_exact_bytes(self):
        self.copy(self.stage, "alpha")
        got = self.plan()
        self.assertEqual(got["decisions"][0]["decision"], "SKIP_MATCHING_STAGE")
        self.assertEqual(self.plan(), got)

    def test_local_edit_same_size_refused(self):
        self.copy(self.baseline, "alpha")
        path = self.profile / "alpha" / "references" / "guide.md"
        path.write_bytes(b"guide 0.0.9")
        self.assertEqual(self.plan()["decisions"][0]["reason"], "LOCAL_BYTES_DIFFER")
        self.assertEqual(path.read_bytes(), b"guide 0.0.9")

    def test_extra_file_not_read(self):
        self.copy(self.baseline, "alpha")
        extra = self.profile / "alpha" / "private-extra.txt"
        extra.write_bytes(b"synthetic extra")
        with mock.patch.object(p, "read_file", wraps=p.read_file) as read:
            got = self.plan()
        self.assertEqual(got["decisions"][0]["reason"], "LOCAL_STRUCTURE_DIFFERS")
        self.assertFalse(any(x.args[0].is_relative_to(self.profile) for x in read.call_args_list))

    def test_no_baseline_and_downgrade_refused(self):
        self.copy(self.baseline, "alpha")
        self.assertEqual(self.plan(baseline=False)["decisions"][0]["reason"], "BASELINE_REQUIRED")
        for root in (self.profile, self.baseline):
            (root / "alpha" / "VERSION").write_bytes(b"0.0.3\n")
        self.assertEqual(self.plan()["decisions"][0]["reason"], "NON_ADVANCING_VERSION")

    def test_alias_refused(self):
        self.write(self.profile, "ALPHA", "0.0.1")
        self.assertEqual(self.plan()["decisions"][0]["reason"], "PROFILE_NAME_ALIAS")

    def test_hardlink_refused(self):
        self.copy(self.baseline, "alpha")
        os.link(self.profile / "alpha" / "SKILL.md", self.root / "alias")
        self.assertEqual(self.plan()["decisions"][0]["reason"], "PROFILE_SPECIAL_FILE")

    def test_symlink_refused(self):
        try:
            (self.profile / "alpha").symlink_to(self.baseline / "alpha", target_is_directory=True)
        except OSError:
            self.skipTest("symlink creation unavailable")
        self.assertEqual(self.plan()["decisions"][0]["reason"], "PROFILE_LINK_OR_IDENTITY")

    def test_overlapping_roots_and_bad_selection_refused(self):
        with self.assertRaisesRegex(p.CatalogError, "OVERLAPPING"):
            p.plan(self.stage, self.stage, self.baseline, self.resolution())
        with self.assertRaises(p.CatalogError):
            p.plan(self.profile, self.stage, self.baseline, self.resolution(("../alpha",)))
        with self.assertRaises(p.CatalogError):
            p.plan(self.profile, self.stage, self.baseline, self.resolution(("alpha", "alpha")))

    def test_stage_version_and_global_budget_refused(self):
        (self.stage / "alpha" / "VERSION").write_bytes(b"0.0.3\n")
        self.assertEqual(self.plan()["decisions"][0]["reason"], "PROFILE_STAGE_VERSION")
        with mock.patch.object(p, "MAX_TOTAL_READ", 1), self.assertRaisesRegex(p.CatalogError, "BUDGET"):
            self.plan()

    def test_persistent_stage_change_across_selection_refused(self):
        original = p.one
        def changed(*args):
            result = original(*args)
            if args[3]["id"] == "beta":
                (self.stage / "alpha" / "SKILL.md").write_bytes(b"persistent mutation")
            return result
        with mock.patch.object(p, "one", side_effect=changed):
            with self.assertRaisesRegex(p.CatalogError, "PROFILE_CHANGED"):
                self.plan(("alpha", "beta"), all_skills=True)

    def test_absence_rechecked_even_with_unchanged_root_timestamp(self):
        original, original_stat = p.one, p.metadata
        before = original_stat(self.profile)
        def changed(*args):
            result = original(*args)
            if args[3]["id"] == "beta":
                self.write(self.profile, "alpha", "0.0.1")
            return result
        def stable_root(path):
            return before if path == self.profile else original_stat(path)
        with mock.patch.object(p, "one", side_effect=changed), \
                mock.patch.object(p, "metadata", side_effect=stable_root):
            with self.assertRaisesRegex(p.CatalogError, "PROFILE_TARGET_APPEARED"):
                self.plan(("alpha", "beta"), all_skills=True)

    def test_windows_cross_method_identity_keeps_same_method_metadata(self):
        from types import SimpleNamespace
        info = (self.stage / "alpha" / "SKILL.md").stat()
        keys = ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")
        values = {key: getattr(info, key) for key in keys}
        before = SimpleNamespace(**values, st_birthtime_ns=1, st_file_attributes=0)
        after = SimpleNamespace(**{**values, "st_ctime_ns": info.st_ctime_ns + 1},
                                st_birthtime_ns=1, st_file_attributes=0)
        with mock.patch.object(p, "WINDOWS", True):
            self.assertEqual(p.cross_identity(before), p.cross_identity(after))
            self.assertNotEqual(p.identity(before), p.identity(after))
            after.st_file_attributes = p.REPARSE
            self.assertTrue(p.reparse(after))
