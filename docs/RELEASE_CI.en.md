# T09.04 — independent verification of completed GitHub Actions runs

[Русский — оригинал](RELEASE_CI.md) | **English — translation**

## Purpose

The new `core/release_ci.py` component validates **actual GitHub Actions REST API data** rather than accepting an agent's statements about tests as evidence. It is designed for an **already completed** workflow run. The `core/release_state.py` component reduces observed evidence into a limited stage without claiming that an application is ready or published.

Integration with [Release Report](RELEASE_REPORT.en.md) is enabled **only by the explicit** `--verify-ci` flag. Otherwise, reporting remains local. The request also requires a trusted GitHub repository, a completed workflow run ID, and a local repository holding the exact expected commit.

## Example commands

After the entire GitHub Actions run has finished:

```bash
python core/release_report.py --repo . --version 0.0.10 \
  --verify-ci --github-repo owner/repository --run-id 123456789

# Optionally verify the remote annotated tag as well
python core/release_report.py --repo . --version 0.0.10 \
  --verify-remote --verify-ci --github-repo owner/repository --run-id 123456789
```

These are **syntax examples**, not claims about any particular workflow run. Replace the repository and run ID with values from a trusted completed run. A real local annotated `v0.0.10` tag is required. Never publish a local user's path in the repository documentation.

## What is checked against GitHub

Using the official REST endpoints `GET /repos/{owner}/{repo}/actions/runs/{run_id}` and `GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs?per_page=100`, the verifier checks:

1. Exact workflow run ID, repository name, and full target commit SHA.
2. `event=push`, `head_branch=main`, and expected workflow file `.github/workflows/validate.yml`.
3. Workflow `status=completed` and `conclusion=success`.
4. Actual `run_attempt` matching every required job.
5. Successful completion of every job in the preselected profile, not merely jobs present in the API response.
6. Job list completeness: `total_count` must equal the number of returned jobs. If more than a single API window (100) is needed, the verification is blocked rather than silently skipping jobs.

Missing or skipped jobs, mismatching SHAs, wrong workflow, incomplete runs, different attempts, API errors, and network failures produce `ci_status=BLOCKED`.

## What the result means

The report now includes `ci_status`, `ci_run_id`, `ci_repository`, `ci_observed_commit_sha`, and `ci_run_attempt`. The pure `core/release_state.py` reducer emits `CI_VERIFIED` or `CI_AND_REMOTE_TAG_VERIFIED` only when the requested checks succeed.

**Important limitation:** `release_readiness` always remains `NOT_VERIFIED` throughout T09.04. A passing workflow proves the recorded GitHub jobs succeeded, not that the tests were sufficient, artifacts are authentic, software was delivered, a GitHub Release exists, or security issues are absent.

## Why this cannot verify its own running job

A workflow cannot reliably require its own `completed/success` state **before it has finished**. That would create a circular dependency.

The existing `tag_microversion` job therefore continues to verify its local/remote annotated tag after push. T09.04 checks a **completed** workflow separately, when requested by an operator or independent external controller. Automating subsequent verification and storing immutable evidence is separate future work.

## Security and limitations

- GitHub requests occur only with `--verify-ci`, use HTTPS, and target a fixed `api.github.com` host. Arbitrary external API URLs are rejected.
- No Git writes, `git push`, token handling, project commands, automatic tests, or release publication are performed.
- Requests have a 15-second timeout and a 2 MiB response cap. Network exception text, tokens, and response headers are not written to reports.
- Public GitHub Actions data is accessible without a mandatory token within GitHub API rate limits. Private repositories are not supported by this unauthenticated implementation.
- `--github-repo` explicitly selects the trusted repository; it is not independently matched to the local `origin`.
- Evidence relies on the GitHub REST API and HTTPS, not cryptographic artifact attestation.
- Network scenarios use controlled HTTP mocks in unit tests; a real completed GitHub workflow must be independently tested.

## Follow-up T09.05

[Release Publication](RELEASE_PUBLICATION.en.md) treats completed CI as one independent fact. It does not attempt to check GitHub Release publication in an ongoing workflow, avoiding circular dependencies. Source publication verification is a separate explicit operation after CI has finished.

## Checks and status

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s skills/microversion-release/tests -v
```

**T09.04 COMPLETE** refers to implemented CI evidence checks, report states, and tests. **Overall T09 remains PARTIAL:** final `RELEASED` determination, software publication evidence, and safe parallel-release coordination are not implemented.

## Fixed required-job profile — candidate

Default current requires 6 jobs: validate, tag, catalog_checks, history_checks, source_secret_checks, windows_skill_checks. Historical TESSERA policy is selected from the root VERSION of the exact inspected commit (not skill VERSION or API job list): before 0.0.68 legacy; 0.0.68–71 parallel; 0.0.72–75 source; from 0.0.76 and later MINOR/MAJOR current. Boundaries checked against actual historical tag workflows. Missing trusted VERSION blocks; other repositories use current. A newer mandatory job in an older profile blocks the result. Direct API verifier defaults to current. Never downgrade the profile when jobs are missing. Report includes ci_job_profile and ci_required_jobs. Isolated algorithm model 8/8 Linux; full candidate CI required.
