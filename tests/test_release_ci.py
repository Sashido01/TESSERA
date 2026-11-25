"""T09.04: GitHub CI evidence from explicit API responses and pure state."""
from __future__ import annotations

import copy
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import release_ci, release_report, release_state


SHA = "a" * 40
REPO = "Sashido01/TESSERA"
RUN_ID = 12345


def fixtures():
    run = {
        "id": RUN_ID,
        "repository": {"full_name": REPO},
        "head_sha": SHA,
        "event": "push",
        "head_branch": "main",
        "path": ".github/workflows/validate.yml",
        "status": "completed",
        "conclusion": "success",
        "run_attempt": 1,
    }
    jobs = {
        "total_count": 2,
        "jobs": [
            {
                "name": name,
                "run_id": RUN_ID,
                "head_sha": SHA,
                "run_attempt": 1,
                "status": "completed",
                "conclusion": "success",
            }
            for name in release_ci.REQUIRED_JOBS
        ]
    }
    return run, jobs


class CIEvidenceTests(unittest.TestCase):
    def test_three_group_evidence_requires_source_and_original_groups(self):
        run, jobs = fixtures()
        template = dict(jobs["jobs"][0])
        jobs["jobs"].extend({**template, "name": name} for name in
                            (*release_ci.PARALLEL_JOBS, release_ci.SOURCE_JOB))
        jobs["total_count"] = len(jobs["jobs"])
        def verify():
            return release_ci.validate_ci_evidence(run, jobs, repository=REPO,
                                                   run_id=RUN_ID, commit_sha=SHA)
        self.assertEqual(verify()["ci_status"], "PASS")
        jobs["jobs"][-1]["conclusion"] = "cancelled"
        self.assertIn("CI_REQUIRED_JOB_NOT_SUCCESSFUL", verify()["problems"])
        jobs["jobs"][-1]["conclusion"] = "success"
        jobs["jobs"].pop(-2)
        jobs["total_count"] = len(jobs["jobs"])
        self.assertIn("CI_REQUIRED_JOB_MISSING", verify()["problems"])

    def test_parallel_job_evidence_requires_both(self):
        run, jobs = fixtures()
        template = dict(jobs["jobs"][0])
        jobs["jobs"].extend({**template, "name": name} for name in release_ci.PARALLEL_JOBS)
        jobs["total_count"] = len(jobs["jobs"])
        def verify():
            return release_ci.validate_ci_evidence(run, jobs, repository=REPO, run_id=RUN_ID, commit_sha=SHA)
        result = verify()
        self.assertEqual(result["ci_status"], "PASS")
        self.assertIn("history_checks", result["required_jobs"])
        jobs["jobs"][-1]["conclusion"] = "skipped"
        self.assertIn("CI_REQUIRED_JOB_NOT_SUCCESSFUL", verify()["problems"])
        jobs["jobs"].pop()
        jobs["total_count"] = len(jobs["jobs"])
        self.assertIn("CI_REQUIRED_JOB_MISSING", verify()["problems"])

    def setUp(self):
        self.run, self.jobs = fixtures()

    def verify(self):
        return release_ci.validate_ci_evidence(
            self.run, self.jobs, repository=REPO, run_id=RUN_ID, commit_sha=SHA,
        )

    def assert_problem(self, code):
        result = self.verify()
        self.assertEqual(result["ci_status"], "BLOCKED")
        self.assertIn(code, result["problems"])

    def test_valid_completed_run_and_jobs(self):
        result = self.verify()
        self.assertEqual(result["ci_status"], "PASS")
        self.assertEqual(result["release_readiness"], "NOT_VERIFIED")
        self.assertEqual(result["run_attempt"], 1)

    def test_wrong_commit_blocks(self):
        self.run["head_sha"] = "b" * 40
        self.assert_problem("CI_COMMIT_MISMATCH")

    def test_wrong_repository_blocks(self):
        self.run["repository"]["full_name"] = "other/repo"
        self.assert_problem("CI_REPOSITORY_MISMATCH")

    def test_wrong_id_blocks(self):
        self.run["id"] = RUN_ID + 1
        self.assert_problem("CI_RUN_ID_MISMATCH")

    def test_pull_request_event_blocks(self):
        self.run["event"] = "pull_request"
        self.assert_problem("CI_WRONG_EVENT_OR_BRANCH")

    def test_non_main_branch_blocks(self):
        self.run["head_branch"] = "develop"
        self.assert_problem("CI_WRONG_EVENT_OR_BRANCH")

    def test_wrong_workflow_blocks(self):
        self.run["path"] = ".github/workflows/other.yml"
        self.assert_problem("CI_WORKFLOW_MISMATCH")

    def test_workflow_path_with_main_ref_is_accepted(self):
        self.run["path"] += "@main"
        self.assertEqual(self.verify()["ci_status"], "PASS")

    def test_running_job_not_accepted(self):
        self.run["status"] = "in_progress"
        self.run["conclusion"] = None
        self.assert_problem("CI_NOT_SUCCESSFUL")

    def test_failed_run_not_accepted(self):
        self.run["conclusion"] = "failure"
        self.assert_problem("CI_NOT_SUCCESSFUL")

    def test_missing_tag_job_blocks(self):
        self.jobs["jobs"].pop()
        self.jobs["total_count"] = 1
        self.assert_problem("CI_REQUIRED_JOB_MISSING")

    def test_failed_validate_job_blocks(self):
        self.jobs["jobs"][0]["conclusion"] = "failure"
        self.assert_problem("CI_REQUIRED_JOB_NOT_SUCCESSFUL")

    def test_skipped_tag_job_blocks(self):
        self.jobs["jobs"][1]["conclusion"] = "skipped"
        self.assert_problem("CI_REQUIRED_JOB_NOT_SUCCESSFUL")

    def test_duplicate_job_name_blocks(self):
        extra = copy.deepcopy(self.jobs["jobs"][0])
        self.jobs["jobs"].append(extra)
        self.jobs["total_count"] = 3
        self.assert_problem("CI_JOB_DUPLICATE")

    def test_incomplete_page_blocks(self):
        self.jobs["total_count"] = 3
        self.assert_problem("CI_JOBS_INCOMPLETE")

    def test_jobs_from_other_attempt_block(self):
        self.jobs["jobs"][0]["run_attempt"] = 2
        self.assert_problem("CI_REQUIRED_JOB_NOT_SUCCESSFUL")

    def test_job_from_other_commit_blocks(self):
        self.jobs["jobs"][0]["head_sha"] = "b" * 40
        self.assert_problem("CI_REQUIRED_JOB_NOT_SUCCESSFUL")

    def test_wrong_job_run_id_blocks(self):
        self.jobs["jobs"][0]["run_id"] = RUN_ID + 2
        self.assert_problem("CI_REQUIRED_JOB_NOT_SUCCESSFUL")

    def test_invalid_attempt_blocks(self):
        self.run["run_attempt"] = True
        self.assert_problem("CI_ATTEMPT_INVALID")

    def test_bad_repository_argument_rejected(self):
        for name in ("--evil/repo", "owner/../repo", "owner", "owner/repo/sub", ".hidden/repo", "owner/-repo", "owner/.hidden"):
            with self.subTest(name=name), self.assertRaises(release_ci.CIEvidenceError):
                release_ci.parameters(name, RUN_ID, SHA)

    def test_bad_run_id_rejected(self):
        for value in (True, 0, -3, "123"):
            with self.subTest(value=value), self.assertRaises(release_ci.CIEvidenceError):
                release_ci.parameters(REPO, value, SHA)

    def test_bad_sha_rejected(self):
        with self.assertRaises(release_ci.CIEvidenceError):
            release_ci.parameters(REPO, RUN_ID, "HEAD")

    def test_only_explicit_fetch_makes_two_api_requests(self):
        urls = []
        def request(url):
            urls.append(url)
            return self.run if len(urls) == 1 else self.jobs
        result = release_ci.verify_github_ci(
            REPO, RUN_ID, SHA, request_json=request,
        )
        self.assertEqual(result["ci_status"], "PASS")
        self.assertEqual(len(urls), 2)
        self.assertTrue(all(x.startswith("https://api.github.com/repos/Sashido01/TESSERA/") for x in urls))

    def test_shared_transport_rejects_noncanonical_release_routes(self):
        root = "https://api.github.com/repos/owner/repo/releases/tags/"
        with mock.patch.object(release_ci.urllib.request, "build_opener") as builder:
            for tag in ("../v0.1.0", "a%252Fv0.1.0", "a%2Fb%2Fv0.1.0",
                        "a/v0.1.0", "a%2fv0.1.0", "v0.1.0?extra=1",
                        "v0.1.0#fragment", "v01.1.0", "v0.01.0"):
                with self.subTest(tag=tag), self.assertRaisesRegex(
                        release_ci.CIEvidenceError, "CI_API_URL_INVALID"):
                    release_ci.get_public_json(root + tag)
            builder.assert_not_called()

    def test_api_redirect_handler_rejects_before_dispatch(self):
        from urllib.request import Request
        handler = release_ci.NoAPIRedirect()
        request = Request("https://api.github.com/repos/owner/repo/actions/runs/1")
        for code in (301, 302, 303, 307, 308):
            for target in ("https://example.invalid/", "http://api.github.com/",
                           "https://api.github.com/repos/other/repo/actions/runs/1"):
                with self.subTest(code=code, target=target), self.assertRaisesRegex(
                        release_ci.CIEvidenceError, "CI_API_REDIRECT_INVALID"):
                    handler.redirect_request(request, None, code, "", {}, target)

    def test_bad_api_url_never_opens_network(self):
        with mock.patch.object(release_ci.urllib.request, "build_opener") as opener:
            for url in ("https://api.github.com.evil.invalid/repos/owner/repo/actions/runs/1",
                        "https://api.github.com/repos/owner/repo/actions/runs/1#fragment",
                        "https://api.github.com/repos/owner/repo/actions/runs/1?other=1",
                        "https://api.github.com/repos/../repo/actions/runs/1",
                        "http://api.github.com/repos/owner/repo/actions/runs/1"):
                with self.subTest(url=url), self.assertRaisesRegex(
                        release_ci.CIEvidenceError, "CI_API_URL_INVALID"):
                    release_ci.get_public_json(url)
            opener.assert_not_called()

    def test_api_open_uses_redirect_guard(self):
        url = "https://api.github.com/repos/owner/repo/actions/runs/1/jobs?per_page=100"
        with mock.patch.object(release_ci.urllib.request, "build_opener") as builder:
            response = builder.return_value.open.return_value.__enter__.return_value
            response.geturl.return_value = url
            response.read.return_value = b'{"jobs":[]}'
            self.assertEqual(release_ci.get_public_json(url), {"jobs": []})
            self.assertIsInstance(builder.call_args.args[0], release_ci.NoAPIRedirect)
            self.assertEqual(builder.return_value.open.call_args.kwargs["timeout"], 15)
            self.assertEqual(builder.return_value.open.call_args.args[0].full_url, url)

    def test_changed_response_url_rejected(self):
        url = "https://api.github.com/repos/owner/repo/actions/runs/1"
        with mock.patch.object(release_ci.urllib.request, "build_opener") as builder:
            response = builder.return_value.open.return_value.__enter__.return_value
            response.geturl.return_value = url + "/jobs"
            with self.assertRaisesRegex(release_ci.CIEvidenceError, "CI_API_REDIRECT_INVALID"):
                release_ci.get_public_json(url)
            response.read.assert_not_called()

    def test_api_failure_does_not_become_pass(self):
        def failed(url):
            raise release_ci.CIEvidenceError("CI_API_UNAVAILABLE")
        result = release_ci.verify_github_ci(
            REPO, RUN_ID, SHA, request_json=failed,
        )
        self.assertEqual(result["ci_status"], "BLOCKED")
        self.assertIn("CI_API_UNAVAILABLE", result["problems"])


class EvidenceStageTests(unittest.TestCase):
    def classify(self, **kwargs):
        d = dict(
            problems=[], local_tag_status="PASS", remote_tag_status="NOT_CHECKED",
            checks_status="NOT_RUN", ci_status="NOT_CHECKED",
        )
        d.update(kwargs)
        return release_state.evidence_stage(**d)

    def test_ci_and_remote_are_verifiable_but_not_released(self):
        self.assertEqual(
            self.classify(ci_status="PASS", remote_tag_status="PASS"),
            "CI_AND_REMOTE_TAG_VERIFIED",
        )

    def test_ci_only(self):
        self.assertEqual(self.classify(ci_status="PASS"), "CI_VERIFIED")

    def test_any_failure_blocks(self):
        self.assertEqual(self.classify(ci_status="BLOCKED"), "BLOCKED")
        self.assertEqual(self.classify(problems=["CI_COMMIT_MISMATCH"]), "BLOCKED")
        self.assertEqual(self.classify(local_tag_status="BLOCKED"), "BLOCKED")


class ReportCIIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = pathlib.Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "CI Test")
        self.git("config", "user.email", "ci@example.invalid")
        (self.repo / "VERSION").write_text("0.0.10\n", encoding="utf-8")
        (self.repo / "CHANGELOG.md").write_text("## 0.0.10 — Введена проверка\n", encoding="utf-8")
        (self.repo / "CHANGELOG.en.md").write_text("## 0.0.10 — CI check\n", encoding="utf-8")
        cfg = {
            "schema_version": 1, "version_file": "VERSION",
            "release_notes": ["CHANGELOG.md", "CHANGELOG.en.md"],
            "build": {"not_applicable_reason": "This fixture does not produce a build."},
            "tests": [{"id": "unit", "argv": [sys.executable, "-c", "pass"], "cwd": ".", "timeout_seconds": 10}],
        }
        (self.repo / "release-checks.json").write_text(
            json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
        )
        self.git("add", ".")
        self.git("commit", "-qm", "Добавлена версия для проверки CI")
        self.sha = self.git("rev-parse", "HEAD")
        self.git("tag", "-a", "v0.0.10", "-m", "Релиз 0.0.10 — проверка CI")

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.repo), *args],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    def test_default_report_does_not_call_github(self):
        with mock.patch.object(release_report, "verify_github_ci", side_effect=AssertionError("unexpected call")):
            result = release_report.build_report(self.repo, "0.0.10")
        self.assertEqual(result["ci_status"], "NOT_CHECKED")
        self.assertEqual(result["release_readiness"], "NOT_VERIFIED")

    def test_verified_ci_uses_exact_inspected_commit(self):
        def check(repo, run_id, sha):
            self.assertEqual(sha, self.sha)
            self.assertEqual(repo, REPO)
            self.assertEqual(run_id, RUN_ID)
            return {"ci_status": "PASS", "problems": [], "observed_commit_sha": sha, "run_attempt": 1}
        with mock.patch.object(release_report, "verify_github_ci", side_effect=check) as called:
            result = release_report.build_report(
                self.repo, "0.0.10", verify_ci=True, github_repo=REPO, run_id=RUN_ID,
            )
        called.assert_called_once()
        self.assertEqual(result["ci_status"], "PASS")
        self.assertEqual(result["stage"], "CI_VERIFIED")
        self.assertEqual(result["release_readiness"], "NOT_VERIFIED")

    def test_failing_ci_blocks_release_evidence(self):
        payload = {"ci_status": "BLOCKED", "problems": ["CI_COMMIT_MISMATCH"]}
        with mock.patch.object(release_report, "verify_github_ci", return_value=payload):
            result = release_report.build_report(
                self.repo, "0.0.10", verify_ci=True, github_repo=REPO, run_id=RUN_ID,
            )
        self.assertEqual(result["evidence_status"], "BLOCKED")
        self.assertIn("CI_COMMIT_MISMATCH", result["problems"])

    def test_missing_ci_arguments_rejected(self):
        with self.assertRaisesRegex(release_report.InspectionError, "CI_REQUIRES"):
            release_report.build_report(self.repo, "0.0.10", verify_ci=True)

    def test_report_contains_ci_status(self):
        result = release_report.build_report(self.repo, "0.0.10")
        self.assertIn("Завершённый CI: NOT_CHECKED", release_report.markdown(result))


if __name__ == "__main__":
    unittest.main()
