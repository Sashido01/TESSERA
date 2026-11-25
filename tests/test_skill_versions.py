"""T16: independent skill versions in disposable Git repositories."""
from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from check_repository_version import check_skill_versions


class SkillVersionTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = pathlib.Path(tmp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        self.write("skills/alpha/SKILL.md", "alpha")
        self.write("skills/beta/SKILL.md", "beta")
        self.commit()
        self.versions("alpha", "0.0.1")
        self.versions("beta", "0.0.1")
        self.commit()

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True,
                              capture_output=True, text=True).stdout.strip()

    def write(self, rel, body):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")

    def versions(self, skill, version):
        self.write(f"skills/{skill}/VERSION", version + "\n")
        for name in ("CHANGELOG.md", "CHANGELOG.en.md"):
            p = self.root / f"skills/{skill}/{name}"
            old = p.read_text(encoding="utf-8") if p.exists() else ""
            self.write(f"skills/{skill}/{name}", f"## {version}\n\n" + old)

    def commit(self):
        self.git("add", ".")
        self.git("commit", "-qm", "Test change")

    def check(self):
        return check_skill_versions(self.root, self.git("rev-parse", "HEAD^"))

    def test_bootstrap_two_independent_versions(self):
        self.assertEqual(self.check(), [])

    def test_catalog_only_change(self):
        self.write("README.md", "catalog")
        self.commit()
        self.assertEqual(self.check(), [])

    def test_one_skill_change(self):
        self.write("skills/alpha/SKILL.md", "changed alpha")
        self.versions("alpha", "0.0.2")
        self.commit()
        self.assertEqual(self.check(), [])

    def test_changed_skill_without_version(self):
        self.write("skills/alpha/SKILL.md", "changed alpha")
        self.commit()
        self.assertTrue(self.check())

    def test_metadata_only_bump(self):
        self.versions("alpha", "0.0.2")
        self.commit()
        self.assertTrue(any("METADATA_ONLY" in e for e in self.check()))

    def test_version_skip(self):
        self.write("skills/alpha/SKILL.md", "changed alpha")
        self.versions("alpha", "0.0.3")
        self.commit()
        self.assertTrue(self.check())

    def test_incomplete_metadata(self):
        (self.root / "skills/alpha/CHANGELOG.en.md").unlink()
        self.commit()
        self.assertTrue(any("METADATA_MISSING" in e for e in self.check()))

    def test_new_skill_must_start_at_one(self):
        self.write("skills/gamma/SKILL.md", "gamma")
        self.versions("gamma", "0.0.2")
        self.commit()
        self.assertTrue(self.check())


if __name__ == "__main__":
    unittest.main()
