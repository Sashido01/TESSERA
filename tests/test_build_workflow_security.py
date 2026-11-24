"""T09.08: negative checks for the opt-in signing workflow."""
from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_build_workflow_security as sec


class BuildWorkflowSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = sec.WORKFLOW.read_text(encoding="utf-8")

    def test_current_workflow(self):
        self.assertEqual(sec.validate(self.original), [])

    def test_unpinned_attest_action(self):
        bad = self.original.replace(
            "actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6", "actions/attest@v4"
        )
        self.assertIn("ATTEST_UNPINNED_OR_DUPLICATE_ACTION", sec.validate(bad))

    def test_unpinned_artifact_action(self):
        bad = self.original.replace(
            "actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9",
            "actions/upload-artifact@v4"
        )
        self.assertIn("ATTEST_UNPINNED_OR_DUPLICATE_ACTION", sec.validate(bad))

    def test_pr_trigger_rejected(self):
        bad = self.original.replace("  workflow_dispatch:", "  workflow_dispatch:\n  pull_request:")
        self.assertIn("ATTEST_UNSAFE_TRIGGER", sec.validate(bad))

    def test_write_contents_rejected(self):
        bad = self.original.replace("      contents: read", "      contents: write")
        self.assertIn("ATTEST_WRITE_ACCESS_INVALID", sec.validate(bad))

    def test_missing_tag_guard_rejected(self):
        bad = self.original.replace("github.ref_type == 'tag'", "github.ref_type == 'branch'")
        self.assertIn("ATTEST_REQUIRED_CONTROL_MISSING", sec.validate(bad))

    def test_missing_exact_github_ref_rejected(self):
        bad = self.original.replace('if [[ "${GITHUB_REF}" != "refs/tags/${tag}" ]]', "if false")
        self.assertIn("ATTEST_REQUIRED_CONTROL_MISSING", sec.validate(bad))

    def test_missing_main_ancestry_rejected(self):
        bad = self.original.replace("git merge-base --is-ancestor HEAD origin/main", "true")
        self.assertIn("ATTEST_REQUIRED_CONTROL_MISSING", sec.validate(bad))

    def test_missing_require_tag_rejected(self):
        bad = self.original.replace("--require-tag --check-reproducible", "--check-reproducible")
        self.assertIn("ATTEST_REQUIRED_CONTROL_MISSING", sec.validate(bad))

    def test_unsanitized_artifact_upload_rejected(self):
        bad = self.original.replace("if-no-files-found: error", "if-no-files-found: warn")
        self.assertIn("ATTEST_REQUIRED_CONTROL_MISSING", sec.validate(bad))

    def test_forbidden_release_creation_rejected(self):
        bad = self.original + "\n# gh release create\n"
        self.assertIn("ATTEST_FORBIDDEN_OPERATION", sec.validate(bad))

    def test_unexpected_action_rejected(self):
        bad = self.original.replace(
            "actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6",
            "someone/unknown@1234567890123456789012345678901234567890",
        )
        self.assertIn("ATTEST_UNEXPECTED_ACTION", sec.validate(bad))

    def test_missing_no_bytecode_guard_rejected(self):
        bad = self.original.replace("PYTHONDONTWRITEBYTECODE: '1'", "PYTHONDONTWRITEBYTECODE: '0'")
        self.assertIn("ATTEST_PYCACHE_ISOLATION_MISSING", sec.validate(bad))

    def test_concurrency_not_canceled(self):
        bad = self.original.replace("cancel-in-progress: false", "cancel-in-progress: true")
        self.assertIn("ATTEST_CONCURRENCY_UNSAFE", sec.validate(bad))


if __name__ == "__main__":
    unittest.main()
