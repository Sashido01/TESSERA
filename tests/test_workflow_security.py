import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools" / "check_workflow_security.py"
spec = importlib.util.spec_from_file_location("check_workflow_security", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
WORKFLOW = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")


class WorkflowSecurityTests(unittest.TestCase):
    def test_current_workflow(self):
        self.assertEqual(module.validate_workflow(WORKFLOW), [])

    def test_unpinned_action_is_rejected(self):
        modified = WORKFLOW.replace("actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1", "actions/checkout@v4")
        self.assertTrue(any("SHA" in e for e in module.validate_workflow(modified)))

    def test_unsafe_pr_trigger_is_rejected(self):
        modified = WORKFLOW.replace("  pull_request:", "  pull_request_target:")
        self.assertTrue(any("pull_request_target" in e for e in module.validate_workflow(modified)))

    def test_missing_remote_head_guard_is_rejected(self):
        modified = WORKFLOW.replace('remote_head="$(git ls-remote --heads origin refs/heads/main',
                                    'other="$(git ls-remote --heads origin refs/heads/main')
        self.assertTrue(any("main" in e for e in module.validate_workflow(modified)))

    def test_read_only_validation_is_required(self):
        modified = WORKFLOW.replace("persist-credentials: false", "persist-credentials: true")
        self.assertTrue(any("credentials" in e for e in module.validate_workflow(modified)))

    def test_tag_job_needs_validation(self):
        modified = WORKFLOW.replace("    needs: validate", "    needs: unknown")
        self.assertTrue(any("validate" in e for e in module.validate_workflow(modified)))


if __name__ == "__main__":
    unittest.main()
