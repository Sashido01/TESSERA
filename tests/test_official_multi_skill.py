"""Offline regression tests for independent fixture tags and flat names."""
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_official_multi_skill as multi


class MultiSkillTests(unittest.TestCase):
    def test_valid_ref(self):
        self.assertEqual(multi.skill_ref("microversion-release", "0.0.100"),
                         "refs/tags/microversion-release/v0.0.100")

    def test_independent_ref_names(self):
        self.assertNotEqual(multi.skill_ref("alpha", "0.0.1"),
                            multi.skill_ref("beta", "0.0.1"))

    def test_bad_skill_names(self):
        for name in ("", "../bad", "a/b", "A", "a--b", "-a", "a.", "a" * 65):
            with self.subTest(name=name):
                with self.assertRaisesRegex(multi.InstallCheckError, "MULTI_NAME_INVALID"):
                    multi.skill_ref(name, "0.0.1")

    def test_bad_versions(self):
        for version in ("", "v1.2.3", "01.2.3", "1.2", "1.2.3-beta", "../1"):
            with self.subTest(version=version):
                with self.assertRaisesRegex(multi.InstallCheckError, "MULTI_VERSION_INVALID"):
                    multi.skill_ref("alpha", version)

    def test_duplicate_names_rejected(self):
        with self.assertRaisesRegex(multi.InstallCheckError, "MULTI_NAME_COLLISION"):
            multi.validate_names(["alpha", "beta", "alpha"])

    def test_case_alias_not_accepted(self):
        with self.assertRaisesRegex(multi.InstallCheckError, "MULTI_NAME_INVALID"):
            multi.validate_names(["alpha", "ALPHA"])

    def test_fixture_writer_keeps_other_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            multi.write_skill(root, multi.ALPHA, "0.0.1", "old")
            multi.write_skill(root, multi.BETA, "0.0.1", "other")
            before = multi.snapshot(root / multi.BETA)
            multi.write_skill(root, multi.ALPHA, "0.0.2", "new")
            self.assertEqual(multi.snapshot(root / multi.BETA), before)
            self.assertEqual((root / multi.ALPHA / "VERSION").read_text(), "0.0.2\n")


if __name__ == "__main__":
    unittest.main()
