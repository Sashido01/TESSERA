"""T08.01: guard exact approved Node.js 24 action commits and locations."""
from __future__ import annotations

import importlib.util
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "tools" / "check_actions_runtime.py"
spec = importlib.util.spec_from_file_location("actions_runtime", PATH)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class Node24ActionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ci = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
        cls.signing = (ROOT / ".github" / "workflows" / "build-attested-catalog.yml").read_text(encoding="utf-8")

    def test_both_current_workflows_are_approved(self):
        self.assertEqual(checker.validate(ROOT), [])

    def test_reject_legacy_checkout_in_main_workflow(self):
        text = self.ci.replace(
            checker.PINS["actions/checkout"],
            "11d5960a326750d5838078e36cf38b85af677262",
        )
        self.assertIn("NODE24_ACTION_PIN_MISMATCH", checker.check_workflow(text, "validate.yml"))

    def test_reject_legacy_setup_python_in_signing_workflow(self):
        text = self.signing.replace(
            checker.PINS["actions/setup-python"],
            "a26af69be951a213d495a4c3e4e4022e16d87065",
        )
        self.assertIn("NODE24_ACTION_PIN_MISMATCH", checker.check_workflow(text, "build-attested-catalog.yml"))

    def test_reject_legacy_upload_artifact(self):
        text = self.signing.replace(
            checker.PINS["actions/upload-artifact"],
            "ea165f8d65b6e75b540449e92b4886f43607fa02",
        )
        self.assertIn("NODE24_ACTION_PIN_MISMATCH", checker.check_workflow(text, "build-attested-catalog.yml"))

    def test_reject_unpinned_major(self):
        text = self.ci.replace(
            "actions/checkout@" + checker.PINS["actions/checkout"],
            "actions/checkout@v7",
            1,
        )
        self.assertIn("NODE24_ACTION_NOT_SHA_PINNED", checker.check_workflow(text, "validate.yml"))

    def test_reject_extra_action(self):
        text = self.ci.replace(
            "  tag_microversion:",
            "      - uses: example/tool@1234567890123456789012345678901234567890\n"
            "  tag_microversion:",
        )
        self.assertIn("NODE24_UNEXPECTED_ACTION", checker.check_workflow(text, "validate.yml"))

    def test_reject_removed_action(self):
        line = "uses: actions/setup-python@" + checker.PINS["actions/setup-python"]
        text = self.ci.replace(line, "run: echo omitted", 1)
        self.assertIn("NODE24_ACTION_SET_CHANGED", checker.check_workflow(text, "validate.yml"))

    def test_missing_file_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            self.assertTrue(checker.validate(root))
            self.assertTrue(any("NODE24_WORKFLOW_UNAVAILABLE" in error
                                for error in checker.validate(root)))

    def test_reject_unknown_workflow_name(self):
        self.assertEqual(checker.check_workflow(self.ci, "unknown.yml"), ["NODE24_UNKNOWN_WORKFLOW"])


if __name__ == "__main__":
    unittest.main()
