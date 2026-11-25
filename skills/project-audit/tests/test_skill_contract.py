"""Structural acceptance only; not evaluation of agent behavior."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ContractTests(unittest.TestCase):
    def test_metadata(self):
        source = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        head = source.split("---\n", 2)[1]
        self.assertRegex(head, r"(?m)^name: project-audit$")
        self.assertRegex(head, r"(?m)^description:")
        self.assertRegex((ROOT / "VERSION").read_text().strip(), r"^\d+\.\d+\.\d+$")

    def test_translation_pairs(self):
        for file in ROOT.rglob("*.md"):
            if file.name.endswith(".en.md"):
                continue
            other = ROOT / "references/SKILL.en.md" if file == ROOT / "SKILL.md" else file.with_name(file.stem + ".en.md")
            self.assertTrue(other.is_file(), file.name)
            self.assertIn("English", file.read_text(encoding="utf-8")[:1500])
            self.assertIn("Русский", other.read_text(encoding="utf-8")[:1500])
        self.assertFalse((ROOT / "references/SKILL.en.md").read_text(encoding="utf-8").startswith("---\n"))

    def test_relative_links(self):
        for file in ROOT.rglob("*.md"):
            for target in re.findall(r"\]\(([^)]+\.md)\)", file.read_text(encoding="utf-8")):
                link = (file.parent / target).resolve()
                self.assertTrue(link.is_relative_to(ROOT))
                self.assertTrue(link.is_file(), f"{file.name}: {target}")

    def test_directions(self):
        expected = [f"A{i:02d}" for i in range(1, 31)]
        for file in ("DIRECTIONS.md", "DIRECTIONS.en.md"):
            self.assertEqual(re.findall(r"(?m)^\| (A\d\d) \|", (ROOT / "references" / file).read_text(encoding="utf-8")), expected)

    def test_acceptance(self):
        expected = [f"E{i:02d}" for i in range(1, 21)]
        for file in ("ACCEPTANCE.md", "ACCEPTANCE.en.md"):
            self.assertEqual(re.findall(r"(?m)^\| (E\d\d) \|", (ROOT / "references" / file).read_text(encoding="utf-8")), expected)

    def test_version_headings(self):
        version = (ROOT / "VERSION").read_text().strip()
        for file in ("CHANGELOG.md", "CHANGELOG.en.md"):
            self.assertRegex((ROOT / file).read_text(encoding="utf-8"), r"(?m)^## " + re.escape(version) + r"(?:\s|$)")

    def test_roadmap(self):
        for file in ("ROADMAP.md", "ROADMAP.en.md"):
            body = (ROOT / "references" / file).read_text(encoding="utf-8")
            self.assertEqual(re.findall(r"(?m)^\| (I|II|III|IV|V) \|", body), ["I", "II", "III", "IV", "V"])


if __name__ == "__main__":
    unittest.main()
