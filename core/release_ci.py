#!/usr/bin/env python3
"""T09.04: read-only verification of completed GitHub Actions run evidence.

Only explicit calls query api.github.com; no shell, tokens, Git writes or job
execution. A passing CI run is not proof that an application was released.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any, Callable

REPOSITORY = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
EXPECTED_WORKFLOW = ".github/workflows/validate.yml"
REQUIRED_JOBS = ("validate", "Создать аннотированный тег проверенной версии")
PARALLEL_JOBS = ("catalog_checks", "history_checks")
SOURCE_JOB = "source_secret_checks"
WINDOWS_JOB = "windows_skill_checks"
JOB_PROFILES = {
    "legacy": REQUIRED_JOBS,
    "parallel": REQUIRED_JOBS + PARALLEL_JOBS,
    "source": REQUIRED_JOBS + PARALLEL_JOBS + (SOURCE_JOB,),
    "current": REQUIRED_JOBS + PARALLEL_JOBS + (SOURCE_JOB, WINDOWS_JOB),
}
CATALOG_VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z")


class CIEvidenceError(ValueError):
    """Invalid or unavailable GitHub CI evidence."""


def catalog_job_profile(version: str) -> str:
    """Select TESSERA history policy from the trusted target commit's root VERSION."""
    if not isinstance(version, str) or len(version) > 64 or not CATALOG_VERSION.fullmatch(version):
        raise CIEvidenceError("CI_CATALOG_VERSION_INVALID")
    major, minor, patch = map(int, version.split("."))
    if minor > 99:
        raise CIEvidenceError("CI_CATALOG_VERSION_INVALID")
    if (major, minor) != (0, 0) or patch >= 76:
        return "current"
    if patch >= 72:
        return "source"
    if patch >= 68:
        return "parallel"
    return "legacy"


def parameters(repository: str, run_id: int, commit_sha: str) -> None:
    if not isinstance(repository, str) or not REPOSITORY.fullmatch(repository) or ".." in repository:
        raise CIEvidenceError("CI_REPOSITORY_INVALID")
    if type(run_id) is not int or run_id < 1:
        raise CIEvidenceError("CI_RUN_ID_INVALID")
    if not isinstance(commit_sha, str) or not SHA.fullmatch(commit_sha):
        raise CIEvidenceError("CI_COMMIT_SHA_INVALID")


class NoAPIRedirect(urllib.request.HTTPRedirectHandler):
    """Never contact a redirect target when verifying public CI evidence."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CIEvidenceError("CI_API_REDIRECT_INVALID")


def get_public_json(url: str) -> dict[str, Any]:
    """Get exact public CI or Release API URLs; reject redirects before dispatch."""
    if not isinstance(url, str) or len(url) > 4096:
        raise CIEvidenceError("CI_API_URL_INVALID")
    # The publication verifier shares this transport and URL-quotes its tag.
    # Accept exactly its canonical single-namespace form, not arbitrary escapes.
    match = re.fullmatch(
        r"https://api\.github\.com/repos/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/"
        r"(?:actions/runs/[1-9][0-9]*(?:/jobs\?per_page=100)?"
        r"|releases/tags/(?:[a-z0-9]+(?:-[a-z0-9]+)*%2F)?"
        r"v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*))",
        url,
    )
    if match is None or not REPOSITORY.fullmatch(match.group(1)) or ".." in match.group(1):
        raise CIEvidenceError("CI_API_URL_INVALID")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "TESSERA-release-ci-inspector",
        },
        method="GET",
    )
    try:
        opener = urllib.request.build_opener(NoAPIRedirect())
        with opener.open(request, timeout=15) as response:
            if response.geturl() != url:
                raise CIEvidenceError("CI_API_REDIRECT_INVALID")
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise CIEvidenceError("CI_API_UNAVAILABLE") from exc
    if len(body) > MAX_RESPONSE_BYTES:
        raise CIEvidenceError("CI_API_RESPONSE_TOO_LARGE")
    try:
        value = json.loads(body)
    except (UnicodeError, ValueError) as exc:
        raise CIEvidenceError("CI_API_JSON_INVALID") from exc
    if not isinstance(value, dict):
        raise CIEvidenceError("CI_API_RESPONSE_INVALID")
    return value


def validate_ci_evidence(
    run: dict[str, Any],
    jobs_data: dict[str, Any],
    *,
    repository: str,
    run_id: int,
    commit_sha: str,
    job_profile: str = "current",
) -> dict[str, Any]:
    """Validate a complete, exact-commit run against independently chosen policy."""
    parameters(repository, run_id, commit_sha)
    if not isinstance(job_profile, str) or job_profile not in JOB_PROFILES:
        raise CIEvidenceError("CI_JOB_PROFILE_INVALID")
    problems: list[str] = []
    if not isinstance(run, dict) or not isinstance(jobs_data, dict):
        raise CIEvidenceError("CI_DATA_INVALID")
    if run.get("id") != run_id:
        problems.append("CI_RUN_ID_MISMATCH")
    if not isinstance(run.get("repository"), dict) or run["repository"].get("full_name") != repository:
        problems.append("CI_REPOSITORY_MISMATCH")
    if run.get("head_sha") != commit_sha:
        problems.append("CI_COMMIT_MISMATCH")
    if run.get("event") != "push" or run.get("head_branch") != "main":
        problems.append("CI_WRONG_EVENT_OR_BRANCH")
    path = run.get("path")
    if not isinstance(path, str) or path.split("@", 1)[0] != EXPECTED_WORKFLOW:
        problems.append("CI_WORKFLOW_MISMATCH")
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        problems.append("CI_NOT_SUCCESSFUL")
    attempt = run.get("run_attempt")
    if type(attempt) is not int or attempt < 1:
        problems.append("CI_ATTEMPT_INVALID")

    jobs = jobs_data.get("jobs")
    total = jobs_data.get("total_count")
    if not isinstance(jobs, list) or type(total) is not int or total < 0 or total != len(jobs):
        problems.append("CI_JOBS_INCOMPLETE")
        jobs = []
    if len(jobs) > 100:
        problems.append("CI_JOBS_INCOMPLETE")
        jobs = []
    # Never infer the required checks from jobs present in the API response.
    required_jobs = JOB_PROFILES[job_profile]
    known_jobs = set(JOB_PROFILES["current"])
    relevant: dict[str, dict[str, Any]] = {}
    for item in jobs:
        if not isinstance(item, dict):
            problems.append("CI_JOB_INVALID")
            continue
        name = item.get("name")
        if not isinstance(name, str):
            problems.append("CI_JOB_INVALID")
            continue
        if name in known_jobs and name not in required_jobs:
            problems.append("CI_JOB_PROFILE_MISMATCH")
        if name not in required_jobs:
            continue
        if name in relevant:
            problems.append("CI_JOB_DUPLICATE")
        else:
            relevant[name] = item
    for name in required_jobs:
        item = relevant.get(name)
        if item is None:
            problems.append("CI_REQUIRED_JOB_MISSING")
        elif (
            item.get("run_id") != run_id
            or item.get("head_sha") != commit_sha
            or item.get("run_attempt") != attempt
            or item.get("status") != "completed"
            or item.get("conclusion") != "success"
        ):
            problems.append("CI_REQUIRED_JOB_NOT_SUCCESSFUL")

    return {
        "schema_version": 1,
        "repository": repository,
        "run_id": run_id,
        "expected_commit_sha": commit_sha,
        "observed_commit_sha": run.get("head_sha"),
        "run_attempt": attempt if type(attempt) is int else None,
        "job_profile": job_profile,
        "required_jobs": list(required_jobs),
        "ci_status": "PASS" if not problems else "BLOCKED",
        "release_readiness": "NOT_VERIFIED",
        "problems": list(dict.fromkeys(problems)),
    }


def verify_github_ci(
    repository: str,
    run_id: int,
    commit_sha: str,
    *,
    request_json: Callable[[str], dict[str, Any]] = get_public_json,
    job_profile: str = "current",
) -> dict[str, Any]:
    """Explicit API query, bound to the user's selected trusted owner/repo."""
    parameters(repository, run_id, commit_sha)
    if not isinstance(job_profile, str) or job_profile not in JOB_PROFILES:
        raise CIEvidenceError("CI_JOB_PROFILE_INVALID")
    root = "https://api.github.com/repos/" + repository + "/actions/runs/" + str(run_id)
    try:
        run = request_json(root)
        jobs_data = request_json(root + "/jobs?per_page=100")
    except CIEvidenceError as exc:
        return {
            "schema_version": 1,
            "repository": repository,
            "run_id": run_id,
            "expected_commit_sha": commit_sha,
            "ci_status": "BLOCKED",
            "release_readiness": "NOT_VERIFIED",
            "problems": [str(exc)],
        }
    return validate_ci_evidence(
        run, jobs_data, repository=repository, run_id=run_id, commit_sha=commit_sha,
        job_profile=job_profile,
    )
