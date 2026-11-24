"""T12.03.01: standalone skill license and literal relative Markdown links."""
import pathlib
import posixpath
import re
import sys
import unittest
from urllib.parse import urlsplit, unquote

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_catalog_package import included_paths

SKILL = "skills/microversion-release"
LINK = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\s]+)\)")


def relative_target(source, target):
    parts = urlsplit(target)
    if parts.scheme in ("https", "http"):
        return None
    if parts.scheme or parts.netloc or parts.query:
        raise ValueError("PORTABLE_LINK_UNSUPPORTED")
    path = unquote(parts.path)
    if not path:
        return source
    if path.startswith("/") or "\\" in path or "\0" in path:
        raise ValueError("PORTABLE_LINK_INVALID")
    result = posixpath.normpath(posixpath.join(posixpath.dirname(source), path))
    if not result.startswith(SKILL + "/"):
        raise ValueError("PORTABLE_LINK_ESCAPE")
    return result


class SkillPortabilityTests(unittest.TestCase):
    def test_standalone_license(self):
        self.assertEqual((ROOT / SKILL / "LICENSE.txt").read_bytes(),
                         (ROOT / "LICENSE").read_bytes())
        header = (ROOT / SKILL / "SKILL.md").read_text(encoding="utf-8").split("\n---\n", 1)[0]
        self.assertRegex(header, r"(?m)^license: MIT$")

    def test_packaged_relative_links(self):
        packaged = {p.as_posix() for p in included_paths(ROOT)}
        self.assertIn(SKILL + "/LICENSE.txt", packaged)
        for source in sorted(packaged):
            if source.startswith(SKILL + "/") and source.endswith(".md"):
                text = (ROOT / source).read_text(encoding="utf-8")
                for target in LINK.findall(text):
                    with self.subTest(source=source, target=target):
                        resolved = relative_target(source, target)
                        if resolved is not None:
                            self.assertIn(resolved, packaged)

    def test_relative_parent_within_skill(self):
        self.assertEqual(relative_target(SKILL + "/references/INTEGRATION.md", "../LICENSE.txt"),
                         SKILL + "/LICENSE.txt")

    def test_escape_is_rejected(self):
        for path in ("../../../docs/file.md", "%2e%2e/%2e%2e/LICENSE",
                     "/absolute", "..\\outside"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                relative_target(SKILL + "/references/INTEGRATION.md", path)

    def test_optional_https_is_not_required_offline(self):
        self.assertIsNone(relative_target(SKILL + "/SKILL.md", "https://example.invalid/doc"))


if __name__ == "__main__":
    unittest.main()
