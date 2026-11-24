# T12.02.02.02 — Gitleaks text snapshot review

[Русский — оригинал](GITLEAKS_REVIEW.md) | **English — translation**

Uses official [Gitleaks v8.30.1](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1), MIT. Linux amd64 archive is SHA-256 pinned using official GitHub Release metadata. Only the executable is extracted. No Gitleaks GitHub Action, paid services, AI APIs, Tier 2/3 or NVIDIA automatic installers.

## Scope and safeguards

- Snapshot of all Git-tracked working tree files (checkout in CI). Each nonempty UTF-8 file is supplied separately through stdin; empty files are counted separately. Symlinks, invalid paths, binary/non-UTF-8 files and exceeded limits block the check. Git history, untracked files, binary and nested archives are not scanned.
- [Upstream issue #2316](https://github.com/gitleaks/gitleaks/issues/2316) reports skipping text files with archive-like names. stdin does not pass filenames; the exact number of bytes read is verified for each file. Filename-dependent rules need separate investigation; built-in configuration and its content allowlists are used.
- Dedicated temporary directory without repository configuration or inherited keys; --ignore-gitleaks-allow, --redact=100, distinct exit code 10 for findings. No user baselines, exclusions or suppressions.
- JSON and stderr are captured in memory, not printed or published as artifacts. Verify version, exit codes, scanned byte count, absence of partial scans, valid JSON, redaction of Secret, snapshot immutability, positive and negative synthetic cases. Final report contains only aggregates by rule IDs and tests/other groups.
- The synthetic marker is not a real key and is constructed only in memory. Verify detection even with gitleaks:allow and absence of the marker in captured output. This does not prove detection of all secrets or protection of arbitrary report fields; environment isolation is not a network sandbox.
- Findings are advisory until manual review; execution failure or incomplete coverage blocks CI. NO_FINDINGS applies only to the declared scope and built-in rules.

## Execution and acceptance

`python tools/check_gitleaks_review.py --repo . --cli <path-to-gitleaks>`

GITLEAKS_REVIEW_EXECUTION_PASS confirms the execution contract, not absence of leaks. T12.02.02.02 is PARTIAL: snapshot scan execution COMPLETE; history and path-dependent rules remain unverified. Full NVIDIA Tier 1 and T12 remain PARTIAL.

## Actual acceptance

[CI 45367459045](https://github.com/Sashido01/TESSERA/actions/runs/45367459045) PASS: 428+19 tests, 144/144 tracked UTF-8 files, 998544 bytes, zero findings, positive/negative and redaction fixtures PASS; 65.29 s. Snapshot acceptance COMPLETE; history/path-specific rules NOT_VERIFIED; T12.02.02.02 remains PARTIAL.

First CI failed because the synthetic marker used digits outside the upstream AWS rule alphabet. Corrected the marker and added a regression test; no scanner rules disabled.
