"""Keep the executable four-skill pilot consistent with reviewed published pins."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILLS = {"microversion-release", "project-audit", "repository-workflow", "project-cleanup"}
PIN = r"refs/tags/[a-z-]+/v[0-9]+\.[0-9]+\.[0-9]+"
ROW = re.compile(r"(?m)^\| ([a-z-]+) \| \x60(" + PIN +
                 r")\x60 \| \x60([0-9a-f]{40})\x60 \| \x60([0-9a-f]{40})\x60 \|$")
CASE = re.compile(r"(?m)^        '([a-z-]+)' \{ '(" + PIN + r")' \}$")


class PilotPinsTests(unittest.TestCase):
    def read(self, name):
        return (ROOT / "docs" / name).read_text(encoding="utf-8")

    def mapping(self, text):
        current = text.split("\n## ", 2)[1]
        rows = ROW.findall(current)
        self.assertEqual(len(rows), len(SKILLS))
        mapping = {skill: (pin, commit, tree) for skill, pin, commit, tree in rows}
        self.assertEqual(set(mapping), SKILLS)
        for skill, (pin, _, _) in mapping.items():
            self.assertTrue(pin.startswith("refs/tags/" + skill + "/v"))
        return mapping

    def test_bilingual_table_is_identical(self):
        self.assertEqual(self.mapping(self.read("AGENT_PILOT.md")),
                         self.mapping(self.read("AGENT_PILOT.en.md")))

    def test_executable_install_matches_table(self):
        for name in ("AGENT_PILOT.md", "AGENT_PILOT.en.md"):
            with self.subTest(name=name):
                text = self.read(name)
                mapping = self.mapping(text)
                blocks = re.findall(r"(?ms)^\x60{3}powershell\n(.*?)^\x60{3}$", text)
                relevant = [block for block in blocks if "gh skill install Sashido01/TESSERA" in block]
                self.assertEqual(len(relevant), 1)
                cases = CASE.findall(relevant[0])
                self.assertEqual(len(cases), len(SKILLS))
                self.assertEqual(dict(cases), {skill: row[0] for skill, row in mapping.items()})
                loop = re.findall(r"foreach \(\$skill in @\(([^)]+)\)\)", relevant[0])
                self.assertEqual(len(loop), 1)
                names = re.findall(r"'([a-z-]+)'", loop[0])
                self.assertEqual(len(names), len(SKILLS))
                self.assertEqual(set(names), SKILLS)
                command = re.findall(r"gh skill install Sashido01/TESSERA skills/project-cleanup --pin ("+PIN+r")",
                                     text.split("\n## ", 2)[1])
                self.assertEqual(command, [mapping["project-cleanup"][0]])
