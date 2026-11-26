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

GITLEAKS_REVIEW_EXECUTION_PASS confirms the execution contract, not absence of leaks. T12.02.02.02 is COMPLETE within declared scope: text snapshot, reachable UTF-8 blobs and five path rules. Full NVIDIA Tier 1 and T12 remain PARTIAL.

## Actual acceptance

[CI 45367459045](https://github.com/Sashido01/TESSERA/actions/runs/45367459045) PASS: 428+19 tests, 144/144 tracked UTF-8 files, 998544 bytes, zero findings, positive/negative and redaction fixtures PASS; 65.29 s. Snapshot acceptance COMPLETE; history/path-specific rules NOT_VERIFIED; T12.02.02.02 remains PARTIAL.

First CI failed because the synthetic marker used digits outside the upstream AWS rule alphabet. Corrected the marker and added a regression test; no scanner rules disabled.

## Reachable Git history (0.0.30)

A second independent check, `python tools/check_gitleaks_history.py --repo . --cli <path-to-gitleaks>`, inventories all objects reachable from local refs and HEAD using Git with replacement objects disabled, rejects shallow repositories, checks distinct blob sizes and UTF-8, then scans each nonempty blob through stdin using a bounded worker pool. It validates the exact inventory before and after, counts bytes, and verifies a synthetic marker removed in a later commit is still detected. Binary and unsupported encoding block the check; reports remain aggregate-only. This is content scanning, not filename-specific rule validation, remote-unfetched refs, commit messages, unreachable objects or archived material. [CI 45368434188](https://github.com/Sashido01/TESSERA/actions/runs/45368434188) PASS: 437+19 tests; 585/585 distinct UTF-8 blobs, 5431003 bytes, zero findings, removed-marker fixture PASS, 128.81 s. Findings advisory, execution failures block CI.

## Path-constrained rules

Upstream v8.30.1 contains five rules with explicit path predicates: PHP/Freemius, Terraform, Kubernetes YAML, NuGet config, PKCS#12 filenames. A separate review enumerates matching current paths and distinct (rule, blob) pairs from all reachable commit trees. For each candidate, scan under a canonical filename preserving the rule predicate; use exact byte coverage, only the intended rule, and a synthetic positive detection for each of the five rules. This deliberately avoids the archive-like filename bug, but does not reproduce every path-specific allowlist. No original file paths or raw findings are logged. No scan of unreachable objects or unfetched remote refs. [CI 45369335974](https://github.com/Sashido01/TESSERA/actions/runs/45369335974) PASS: 443+19 tests; 598 distinct UTF-8 blobs, 5639755 bytes, zero findings; five synthetic rule fixtures PASS; 4 current YAML files and 28 historical rule/blob pairs across 37 commits, zero findings. T12.02.02.02 COMPLETE within declared scope.

## T12.03.10 — shared launch contract (candidate)

[CVE-2026-124039](https://github.com/CVEProject/cvelistV5/blob/main/cves/2026/124xxx/CVE-2026-124039.json), published 2026-11-06: Gitleaks through 8.30.1 creates report files with insufficiently restrictive permissions. In pinned [cmd/root.go](https://github.com/gitleaks/gitleaks/blob/83d9cd684c87d95d656c1458ef04895a7f1cbd8e/cmd/root.go#L470), '-' uses stdout rather than os.Create. All three wrappers already used stdout and redact=100. A shared function now fixes those options and explicit archive depth 0 (previous upstream default), with no arbitrary report arguments. Two argument-contract tests and two changed/extra-file tests. Live fixtures compare top-level temporary directory entries; each path scan checks the sole source file and unchanged bytes. Synthetic marker stdout/stderr check remains. This is bounded side-effect evidence, not syscall monitoring, proof of no external/transient writes, or a sandbox. Output limit is checked after capture, not a hard memory cap. Archive Identify precedes the depth check; disabled traversal does not prove all archive dependencies unreachable. STATIC_MITIGATION_PRESENT; live acceptance required. Official stable Gitleaks remains 8.30.1; master 5f6ec56cfa6f8c67648d863582c7ae2f206d5c1c updates some dependencies but retains Go 1.24.11, x/crypto 0.35.0, x/sys 0.30.0 and os.Create for report files. Do not replace stable with an unverified build.

[CI 45398390191](https://github.com/Sashido01/TESSERA/actions/runs/45398390191) PASS: 518+29 tests, four regressions; 168 files (1267492 bytes), 738 blobs (8029168 bytes), 48 commits, 31 historical rule/blob pairs, zero findings; five path controls, marker redaction and unchanged top-level temporary directory PASS. T12.03.10 bounded acceptance PASS, no OS sandbox claim.

## TD04 — full history scan reliability (0.0.81 candidate)

Repeated `HISTORY_TIMEOUT`: PR #87 run 45667095081 (retry SUCCESS), PR #88 run 45672953421 (job 139412842832, first attempt FAIL before container parity). Main v0.0.80 run 45669705980: isolated scan 1359/1359 blobs, 20,537,348 bytes, 0 findings, host parity PASS, 286.87 s. Host review budget raised from 300 to 480 s (60%); retain 4 workers, 2048 blobs, 128 MiB, individual Git/scan timeouts 60/20 s and mandatory repeat inventory. Monotonic deadline checks before/after reading and scanning each blob, during aggregation and after final inventory: an overdue result is not accepted. This is a result-acceptance bound, not a guarantee of immediate termination of all subprocesses. Container deadline 540 s and job timeout 20 min unchanged; nominal host+container budgets 1020 s leave 180 s for other steps, in-job overhead and completion of already started operations. Do not reduce coverage, disable parity or accept a partial report. Five new deterministic regressions; live candidate CI required. Does not establish reliability at all future history sizes; further TD04 optimization remains separate.

## TD04 — batched Git-object reads (draft candidate)

Host review reads up to 32 objects / 4 MiB expected content in one git cat-file --batch call and checks exact headers, order, framing, size, OID, UTF-8 and end of stream. Scans remain individual, four workers, complete inventory/recheck and deadline. Container parity retains independent one-object reads. The post-capture limit is not a hard subprocess memory bound. Parser and actual batch Git prototype 10/10 Linux PASS; not the full candidate suite. New regressions cover SHA-256, reordering, corrupt headers/frames/bytes, binary/encoding, size/count and actual Git. Live CI, native Windows and full history-job measurement required; CI acceleration NOT_VERIFIED. No version assigned until the integration slot is free.

26 November 2026: repeated isolated check of the extracted batch-read and review block on Linux / Git 2.47.3 — 8/8 test methods PASS; actual disposable Git with two commits, 72 distinct blobs (70 initial, one empty, one changed), batched and single-object reads match 72/72, a synthetic scanner found a marker from the previous commit, altered final inventory rejected. This is not actual Gitleaks execution, the full suite or a scan of TESSERA repository files. Scenario added to candidate tests; full CI still required.
