import importlib.util
import itertools
import os
import subprocess
import sys
import textwrap
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools" / "check_workflow_security.py"
spec = importlib.util.spec_from_file_location("check_workflow_security", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
WORKFLOW = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")


class WorkflowSecurityTests(unittest.TestCase):
    def test_parallel_gate_requires_all_jobs(self):
        for old, new in (
                ("needs: [catalog_checks, history_checks, source_secret_checks, windows_skill_checks]", "needs: [catalog_checks, history_checks, source_secret_checks]"),
                ("if: ${{ always() }}", "if: ${{ success() }}"),
                ('test "$HISTORY_RESULT" = success', 'echo ignored'),
                ('test "$SOURCE_RESULT" = success', 'echo ignored'),
                ('test "$WINDOWS_RESULT" = success', 'echo ignored'),
                ("WINDOWS_RESULT: ${{ needs.windows_skill_checks.result }}", "WINDOWS_RESULT: success"),
                ("HISTORY_RESULT: ${{ needs.history_checks.result }}", "HISTORY_RESULT: success")):
            changed = WORKFLOW.replace(old, new)
            self.assertNotEqual(changed, WORKFLOW)
            self.assertIn("PARALLEL_REQUIRED_GATE_INVALID", module.validate_workflow(changed))

    def test_parallel_group_rejects_skipping_and_wrong_sha(self):
        for old, new in (
                ("  history_checks:\n", "  history_checks:\n    if: false\n"),
                ("  catalog_checks:\n", "  catalog_checks:\n    continue-on-error: true\n"),
                ('run: test "$(git rev-parse HEAD)" = "$CHECKED_SHA"', "run: echo skipped"),
                ("fetch-depth: 0", "fetch-depth: 1")):
            changed = WORKFLOW.replace(old, new)
            self.assertNotEqual(changed, WORKFLOW)
            self.assertIn("PARALLEL_CHECK_GROUP_UNSAFE", module.validate_workflow(changed))

    def test_parallel_history_scope_is_mandatory(self):
        changed = WORKFLOW.replace("python tools/check_gitleaks_history.py", "echo omitted")
        self.assertIn("PARALLEL_HISTORY_SCOPE_INVALID", module.validate_workflow(changed))

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux Bash gate control")
    def test_live_gate_accepts_only_four_successes(self):
        self.assertEqual(module.parallel_gate_errors(WORKFLOW.split("\n  tag_microversion:", 1)[0]), [])
        gate = WORKFLOW.split("\n  validate:\n", 1)[1].split("\n  tag_microversion:", 1)[0]
        script = textwrap.dedent(gate.split("        run: |\n", 1)[1])
        states = ("success", "failure", "cancelled", "skipped")
        for catalog, history, source, windows in itertools.product(states, repeat=4):
            with self.subTest(catalog=catalog, history=history, source=source, windows=windows):
                env = {**os.environ, "CATALOG_RESULT": catalog, "HISTORY_RESULT": history,
                       "SOURCE_RESULT": source, "WINDOWS_RESULT": windows}
                result = subprocess.run(["bash", "-c", script], env=env, capture_output=True, timeout=10)
                self.assertEqual(result.returncode == 0, catalog == history == source == windows == "success")
        for missing in ("CATALOG_RESULT", "HISTORY_RESULT", "SOURCE_RESULT", "WINDOWS_RESULT"):
            env = {**os.environ, "CATALOG_RESULT": "success", "HISTORY_RESULT": "success",
                   "SOURCE_RESULT": "success", "WINDOWS_RESULT": "success"}
            del env[missing]
            result = subprocess.run(["bash", "-c", script], env=env, capture_output=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)

    def test_windows_scope_is_mandatory(self):
        for old, new in (
                ("runs-on: windows-latest", "runs-on: ubuntu-latest"),
                ("python-version: '3.14'", "python-version: '3.13'"),
                ("python -B tools/run_skill_tests.py", "echo omitted"),
                ("  windows_skill_checks:\n", "  windows_skill_checks:\n    continue-on-error: true\n")):
            changed = WORKFLOW.replace(old, new)
            self.assertNotEqual(changed, WORKFLOW)
            self.assertIn("PARALLEL_WINDOWS_SCOPE_INVALID", module.validate_workflow(changed))

    def test_parallel_source_scope_mandatory(self):
        for script in ("check_gitleaks_review.py", "check_gitleaks_container.py",
                       "check_gitleaks_paths.py", "check_gitleaks_paths_container.py"):
            changed = WORKFLOW.replace("tools/" + script, "tools/omitted.py")
            self.assertIn("PARALLEL_SOURCE_SCOPE_INVALID", module.validate_workflow(changed))

    def test_skill_tag_publication_requires_protected_job(self):
        changed = WORKFLOW.replace("python -B tools/publish_skill_tags.py", "echo omitted")
        self.assertIn("SKILL_TAG_PUBLICATION_GATE_INVALID", module.validate_workflow(changed))
        changed = WORKFLOW.replace(" && github.repository == 'Sashido01/TESSERA'", "")
        self.assertIn("SKILL_TAG_PUBLICATION_GATE_INVALID", module.validate_workflow(changed))

    def test_skill_tag_publication_requires_explicit_recovery_strategy(self):
        changed = WORKFLOW.replace("--publish --strategy sequential", "--publish")
        self.assertIn("SKILL_TAG_PUBLICATION_GATE_INVALID", module.validate_workflow(changed))

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

    def test_missing_bytecode_isolation_rejected(self):
        modified = WORKFLOW.replace("PYTHONDONTWRITEBYTECODE: '1'", "PYTHONDONTWRITEBYTECODE: '0'")
        self.assertTrue(any("bytecode" in e for e in module.validate_workflow(modified)))

    def test_post_test_archive_smoke_is_required(self):
        modified = WORKFLOW.replace(
            "run: python tools/build_catalog_package.py --repo . --output-dir dist/post-tests --check-reproducible",
            "run: echo omitted"
        )
        self.assertTrue(any("ZIP после тестов" in e for e in module.validate_workflow(modified)))

    def test_remote_install_is_required(self):
        modified = WORKFLOW.replace("run: python tools/check_official_remote_install.py", "run: echo")
        self.assertTrue(any("удалённой проверки" in e for e in module.validate_workflow(modified)))

    def test_remote_install_cannot_use_personal_token(self):
        modified = WORKFLOW.replace("GH_TOKEN: ${{ github.token }}", "GH_TOKEN: ${{ secrets.PAT }}")
        self.assertTrue(any("read-only токеном" in e for e in module.validate_workflow(modified)))

    def test_skill_update_check_is_required(self):
        modified = WORKFLOW.replace("run: python tools/check_official_skill_update.py", "run: echo")
        self.assertTrue(any("проверки обновления" in e for e in module.validate_workflow(modified)))

    def test_multi_skill_check_is_required(self):
        modified = WORKFLOW.replace("run: python tools/check_official_multi_skill.py", "run: echo")
        self.assertTrue(any("проверки нескольких навыков" in e for e in module.validate_workflow(modified)))

    def test_nvidia_focused_check_is_required(self):
        modified = WORKFLOW.replace("run: python tools/check_nvidia_tier1.py", "run: echo")
        self.assertTrue(any("NVIDIA Tier 1" in e for e in module.validate_workflow(modified)))

    def test_nvidia_static_review_is_required(self):
        modified = WORKFLOW.replace("run: python tools/check_nvidia_static_review.py", "run: echo")
        self.assertTrue(any("статического обзора NVIDIA" in e for e in module.validate_workflow(modified)))

    def test_bandit_review_is_required(self):
        modified = WORKFLOW.replace("python tools/check_bandit_review.py", "echo")
        self.assertTrue(any("Bandit" in e for e in module.validate_workflow(modified)))

    def test_gitleaks_review_is_required(self):
        modified = WORKFLOW.replace("python tools/check_gitleaks_review.py", "echo")
        self.assertTrue(any("Gitleaks" in e for e in module.validate_workflow(modified)))

    def test_gitleaks_digest_required(self):
        modified = WORKFLOW.replace("551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb", "0" * 64)
        self.assertTrue(any("Gitleaks" in e for e in module.validate_workflow(modified)))

    def test_gitleaks_history_is_required(self):
        modified = WORKFLOW.replace("python tools/check_gitleaks_history.py", "echo")
        self.assertTrue(any("истории Gitleaks" in e for e in module.validate_workflow(modified)))

    def test_gitleaks_paths_are_required(self):
        modified = WORKFLOW.replace("python tools/check_gitleaks_paths.py", "echo")
        self.assertTrue(any("по пути" in e for e in module.validate_workflow(modified)))

    def test_skillspector_review_is_required(self):
        modified = WORKFLOW.replace("python tools/check_skillspector_review.py", "echo")
        self.assertTrue(any("SkillSpector" in e for e in module.validate_workflow(modified)))

    def test_skillspector_digest_is_required(self):
        modified = WORKFLOW.replace("e2356aa11f0d484f789543f25da6208fe2408641c8b16e7b59bc6600c5c39ffb", "0" * 64)
        self.assertTrue(any("SkillSpector" in e for e in module.validate_workflow(modified)))

    def test_dependency_review_is_required(self):
        for value in ("--locked tools/skills-ref-requirements.txt", "--root skillevaluator==1.2.0", "--root skillspector==2.13.7"):
            modified = WORKFLOW.replace("tools/check_dependency_review.py " + value, "echo omitted")
            self.assertTrue(any("аудита CVE" in e for e in module.validate_workflow(modified)))

    def test_go_review_is_required(self):
        modified = WORKFLOW.replace("run: python tools/check_go_dependency_review.py", "run: echo")
        self.assertTrue(any("аудита CVE" in e for e in module.validate_workflow(modified)))

    def test_tag_job_needs_validation(self):
        modified = WORKFLOW.replace("    needs: validate", "    needs: unknown")
        self.assertTrue(any("validate" in e for e in module.validate_workflow(modified)))


    def test_semgrep_lock_and_dependency_review_required(self):
        for value in ("11859086088d6720e5f4f303de0740a4830b065b",
                      'tools/check_dependency_review.py --root semgrep==1.182.0'):
            modified = WORKFLOW.replace(value, "omitted")
            self.assertTrue(any("Semgrep" in e for e in module.validate_workflow(modified)))


    def test_docker_preflight_required(self):
        modified = WORKFLOW.replace("run: python tools/check_docker_preflight.py", "run: echo omitted")
        self.assertTrue(any("Docker preflight" in e for e in module.validate_workflow(modified)))


    def test_gitleaks_container_required(self):
        modified = WORKFLOW.replace("run: python tools/check_gitleaks_container.py", "run: echo")
        self.assertTrue(any("контейнерной проверки Gitleaks" in e for e in module.validate_workflow(modified)))


    def test_gitleaks_history_container_required(self):
        modified = WORKFLOW.replace("run: python tools/check_gitleaks_history_container.py", "run: echo")
        self.assertTrue(any("контейнерной проверки истории Gitleaks" in e for e in module.validate_workflow(modified)))


    def test_gitleaks_paths_container_required(self):
        modified = WORKFLOW.replace("run: python tools/check_gitleaks_paths_container.py", "run: echo")
        self.assertTrue(any("контейнерной проверки правил Gitleaks по пути" in e for e in module.validate_workflow(modified)))


    def test_bandit_container_required(self):
        modified = WORKFLOW.replace("run: python tools/check_bandit_container.py", "run: echo")
        self.assertTrue(any("контейнерной проверки Bandit" in e for e in module.validate_workflow(modified)))


    def test_skillspector_container_required(self):
        modified = WORKFLOW.replace("run: python tools/check_skillspector_container.py", "run: echo")
        self.assertTrue(any("контейнерной проверки SkillSpector" in e for e in module.validate_workflow(modified)))


if __name__ == "__main__":
    unittest.main()
