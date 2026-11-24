"""Offline regression tests for T10.02 remote pin acceptance."""
from __future__ import annotations
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_official_remote_install as remote

TREE = "a" * 40
SKILL = b"---\nname: microversion-release\ndescription: Test\n---\n\nBody\n"
FILES = {"SKILL.md": SKILL, "references/INTEGRATION.md": b"Exact reference\n"}


def installed_skill(pin: str) -> bytes:
    return ("---\nname: microversion-release\nmetadata:\n"
            f"  github-repo: {remote.URL}\n"
            f"  github-path: {remote.SKILL_PATH}\n"
            f"  github-ref: {pin}\n  github-pinned: {pin}\n"
            f"  github-tree-sha: {TREE}\n---\nBody\n").encode()


class RemoteInstallTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.repo = pathlib.Path(temp.name)
        self.target = self.repo / "skills" / remote.SKILL
        self.target.mkdir(parents=True)
        (self.target / "references").mkdir()
        (self.target / "references" / "INTEGRATION.md").write_bytes(FILES["references/INTEGRATION.md"])
        (self.target / "SKILL.md").write_bytes(installed_skill(remote.REF))

    def verify(self):
        remote.verify_install(self.target, FILES, TREE, remote.REF)

    def test_exact_install(self):
        self.verify()

    def test_wrong_pin(self):
        (self.target / "SKILL.md").write_bytes(installed_skill(remote.COMMIT))
        with self.assertRaisesRegex(remote.InstallCheckError, "REMOTE_METADATA_MISMATCH"):
            self.verify()

    def test_wrong_tree(self):
        (self.target / "SKILL.md").write_bytes(installed_skill(remote.REF).replace(TREE.encode(), b"b" * 40))
        with self.assertRaisesRegex(remote.InstallCheckError, "REMOTE_METADATA_MISMATCH"):
            self.verify()

    def test_duplicate_metadata(self):
        header = installed_skill(remote.REF).replace(b"  github-ref:", b"  github-ref: duplicate\n  github-ref:")
        (self.target / "SKILL.md").write_bytes(header)
        with self.assertRaisesRegex(remote.InstallCheckError, "REMOTE_METADATA_MISSING_OR_DUPLICATE"):
            self.verify()

    def test_changed_body(self):
        (self.target / "SKILL.md").write_bytes(installed_skill(remote.REF).replace(b"Body\n", b"Changed\n"))
        with self.assertRaisesRegex(remote.InstallCheckError, "REMOTE_SKILL_BODY_MISMATCH"):
            self.verify()

    def test_changed_reference(self):
        (self.target / "references" / "INTEGRATION.md").write_bytes(b"Changed")
        with self.assertRaisesRegex(remote.InstallCheckError, "REMOTE_FILE_BYTES_MISMATCH"):
            self.verify()

    def test_extra_file(self):
        (self.target / "extra").write_bytes(b"extra")
        with self.assertRaisesRegex(remote.InstallCheckError, "REMOTE_FILE_INVENTORY_MISMATCH"):
            self.verify()

    def test_missing_file(self):
        (self.target / "references" / "INTEGRATION.md").unlink()
        with self.assertRaisesRegex(remote.InstallCheckError, "REMOTE_FILE_INVENTORY_MISMATCH"):
            self.verify()

    def test_missing_token_stops_before_cli(self):
        with self.assertRaisesRegex(remote.InstallCheckError, "REMOTE_READ_TOKEN_REQUIRED"):
            remote.accept(self.repo, pathlib.Path(sys.executable), "")

    def test_listing_must_confirm_full_pin(self):
        data = [{"skillName": remote.SKILL, "sourceURL": remote.URL,
                 "version": remote.COMMIT, "pinned": True, "path": str(self.target)}]
        remote.check_listing(json.dumps(data), remote.COMMIT, self.target)
        data[0]["pinned"] = False
        with self.assertRaisesRegex(remote.InstallCheckError, "REMOTE_LIST_METADATA_MISMATCH"):
            remote.check_listing(json.dumps(data), remote.COMMIT, self.target)

    def test_complete_offline_contract(self):
        calls = []
        def fake(argv, **kwargs):
            args = argv[1:]
            calls.append(args)
            self.assertEqual(kwargs["env"]["GH_TOKEN"], "synthetic-test-token")
            self.assertNotIn("GITHUB_TOKEN", kwargs["env"])
            self.assertNotIn("--force", args)
            self.assertNotIn("--unpin", args)
            self.assertNotEqual(kwargs["cwd"], str(self.repo))
            if args == ["version"]:
                return subprocess.CompletedProcess(argv, 0, "gh version 2.105.0 (test)\n", "")
            dest = pathlib.Path(args[args.index("--dir") + 1])
            target = dest / remote.SKILL
            if args[:2] == ["skill", "install"]:
                pin = args[args.index("--pin") + 1]
                if target.exists():
                    return subprocess.CompletedProcess(argv, 1, "", "skills already installed")
                (target / "references").mkdir(parents=True)
                (target / "SKILL.md").write_bytes(installed_skill(pin))
                (target / "references" / "INTEGRATION.md").write_bytes(FILES["references/INTEGRATION.md"])
                return subprocess.CompletedProcess(argv, 0, "", "")
            pin = remote.REF if dest.name == "tag" else remote.COMMIT
            if args[:2] == ["skill", "list"]:
                rows = [{"skillName": remote.SKILL, "sourceURL": remote.URL,
                         "version": pin.removeprefix("refs/tags/"), "pinned": True, "path": str(target)}]
                return subprocess.CompletedProcess(argv, 0, json.dumps(rows), "")
            if args[:2] == ["skill", "update"]:
                self.assertIn("--dry-run", args)
                return subprocess.CompletedProcess(argv, 0, "", f"{remote.SKILL} is pinned to {pin} (skipped)")
            self.fail("unexpected invocation")
        result = remote.accept(self.repo, pathlib.Path(sys.executable), "synthetic-test-token",
                               runner=fake, baseline=lambda *_: (TREE, FILES))
        self.assertEqual(result["tag_install"], "PASS")
        self.assertEqual(result["sha_install"], "PASS")
        self.assertEqual(len(calls), 9)
        self.assertEqual(result["client_activation"], "NOT_VERIFIED")


if __name__ == "__main__":
    unittest.main()
