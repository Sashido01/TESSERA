# T12.01 — NVIDIA SkillEvaluator focused Tier 1

[Русский — оригинал](NVIDIA_TIER1.md) | **English — translation**

## Decision and scope

As of 24 November 2026, reviewed the official [v1.2.0 release](https://github.com/NVIDIA/SkillEvaluator/releases/tag/v1.2.0), source commit `5625c2534bf266f810aea489ffbe69da0bb2645e`, Apache-2.0 license. Only the base wheel, no extras. Release metadata records SHA-256 `cd367d655b567bb6015aa79b0229d1f268ad4fa0429619f896f5dccef8e6948a`. The 19 direct/transitive dependencies for Linux x86_64 CPython 3.13 are pinned to wheel versions and hashes from the [commit's uv.lock](https://github.com/NVIDIA/SkillEvaluator/blob/5625c2534bf266f810aea489ffbe69da0bb2645e/uv.lock). Separate venv, pip --require-hashes --only-binary=:all and pip check. This is neither cryptographic signature verification of NVIDIA's release nor a complete dependency licensing/vulnerability audit.

The official [Tier 1 reference](https://docs.nvidia.com/skills/skillevaluator/tier1-reference) distinguishes static and LLM stages. Generic validate may enable other tiers by default and is forbidden. Only the focused command `skillevaluator tier1 PATH --no-llm --checks schema,quality --min-score 70 -r json -o REPORT_DIR` is permitted. Isolated HOME and environment; no provider keys or GitHub token passed; PIP_NO_INDEX and UV_OFFLINE during evaluation. This is not an OS network sandbox; downloading pinned wheels in CI requires network access. Never execute skill contents, LLM stages, Tier 2/3. Never install [all], [llm], [tier2], [tier3].

## Acceptance

`tools/check_nvidia_tier1.py` checks exact version, copied catalog, completion of both validators, JSON, disabled LLM, consistent exit code and verdict, score from 0 to 100. A separate malformed synthetic skill must fail schema. Report contents and local paths are not published: only check identifiers, severity and score. Original sources must remain unchanged.

**Initial policy is advisory:** a valid report with a quality/schema FAIL does not make the skill PASS. CI blocks missing execution, incomplete/inconsistent reports or a missed negative test. Findings require review rather than automatic suppression. Evaluate English-language quality heuristics separately against the Russian original.

**T12.01 result (24 November 2026): selected checks PASS.** [CI 45358283596](https://github.com/Sashido01/TESSERA/actions/runs/45358283596) confirmed `NVIDIA_TIER1_FOCUSED_EXECUTION_PASS`: official wheel and 19 dependencies installed with hashes, pip check PASS, schema PASSED, quality PASSED, score 75.0/100 at threshold 70, 18 findings (7 medium, 11 low), negative fixture PASS, LLM DISABLED. 393 catalog tests and 19 skill tests PASS. First CI 45358033088 failed because the expected validator display name differed from its actual machine identifier `QUALITY`; corrected and verified in the second run. Findings were not suppressed. Full security and language-specific false positives remain unassessed. T12.01 COMPLETE within schema/quality scope. Overall T12 PARTIAL: security, PII, license, code-integrity, unicode, lint, dependency and harness-check are untested; full Tier 1, client-agent compatibility, false positives, complete cost and dependency license audit remain NOT_VERIFIED. No paid AI APIs. CI resource costs are not necessarily zero.

Next isolated stage: [T12.02.01 — static checks and profiles](NVIDIA_STATIC_REVIEW.en.md).

## T12.03.13 — integrated static run (candidate)

Explicit 11 check groups and 13 validator rows including dependency. Pinned SkillEvaluator 1.2.0, SkillSpector 2.13.7, Bandit 1.9.4, Gitleaks 8.30.1; version and Gitleaks binary SHA checks, absolute scanner overrides, private PATH Gitleaks adapter with fixed detect contract and --redact=100, --max-archive-depth 0. No LLM or raw CI reports; temporary copy and content checks. Managed fallback check limited to known directories; PIP_NO_INDEX/UV_OFFLINE are not network isolation. Semgrep NOT_RUN (not installed), future dependency manifests block until a separate pinned contract. Policy verdict distinct from execution; all rows do not constitute certification. Seven offline regressions, live CI required; live synthetic redaction control of integrated adapter and full sandbox remain open.

## T12.03.13 — PR result

[CI 45403712350](https://github.com/Sashido01/TESSERA/actions/runs/45403712350) PASS: 543+29 tests, 13 rows, execution PASS, policy FAIL (Security Scan 1 HIGH, 19 MEDIUM), the other 12 PASSED; SkillSpector 53/100, 0 suppressions. Semgrep NOT_RUN, certification NOT_VERIFIED. Merged into main; main and tag acceptance separate.

## T12.03.14 — live Gitleaks adapter control (candidate)

The real pinned binary is invoked through the same private shim with the exact upstream argument contract in a separate temporary directory with a synthetic TOML rule. Clean file: exit 0, empty JSON; nonfunctional synthetic marker: exit 10, one finding of the expected rule and file, Secret=REDACTED, marker absent from stdout and stderr. Fixture/config bytes and fixture directory entries are checked. Five offline regressions. Do not emit the marker or raw report; live CI acceptance required. This is a shim control with a custom rule, not proof of upstream allowlist/detector completeness, network isolation, or NVIDIA certification. T12 PARTIAL.

## T12.03.14 — PR result

[CI 45405865725](https://github.com/Sashido01/TESSERA/actions/runs/45405865725) PASS: 548+29=577 tests; real shim clean/detection/stdout-stderr redaction/fixture entries PASS. Overall policy FAIL, 1 HIGH and 19 MEDIUM in Security Scan; Semgrep NOT_RUN. v0.0.45 main CI 45405654421 and annotated tag verified; v0.0.46 merged into main, its own acceptance separate.

## T12.03.15 — aggregate HIGH finding attribution (candidate)

[Pinned upstream](https://github.com/NVIDIA/SkillEvaluator/blob/5625c2534bf266f810aea489ffbe69da0bb2645e/src/skillevaluator/validators/security.py#L5693-L5703) adds a separate HIGH finding with category SECURITY and check_name skillspector_risk_score when effective_score > 50 and there are no individual CRITICAL/HIGH findings. The JSON reporter preserves structured check_name through Finding.to_dict(). Thus the integrated report's 1 HIGH alongside direct SkillSpector's 0 HIGH and 53/100 is consistent with the aggregate gate, but the previous integrated report did not publish the exact identifier. New high_attribution counts only the exact category/check_name combination for HIGH in Security Scan; all other HIGH findings count as other_high. No findings, severity, policy verdict, thresholds or scanner execution are changed. Messages, paths and arbitrary identifiers are not emitted. Three regressions; live CI must confirm actual counts. T12 PARTIAL; Semgrep and network sandbox remain open.

## T12.03.15 — PR result

[CI 45418208676](https://github.com/Sashido01/TESSERA/actions/runs/45418208676) PASS: 551+29 tests, aggregate_risk_gate=1, other_high=0, MEDIUM=19, policy FAIL. v0.0.46 main CI 45417975016 and annotated tag verified; v0.0.47 merged into main, its acceptance separate.

## T12.03.16 — Semgrep in Tier 1 (candidate)

Use NVIDIA upstream lock 5625c2534bf266f810aea489ffbe69da0bb2645e, blob 11859086088d6720e5f4f303de0740a4830b065b (66 pinned package rows, 915 SHA-256 lines), separate venv, wheel-only, require-hashes, pip check, OSV and license metadata of the actual environment. Semgrep 1.182.0, six local NVIDIA rules (blob 3ef2067b69ef50f09b39c933771f751bc227b3db), exact version, explicit override and REQUIRE_SEMGREP=1. Clean and positive Python fixtures are scanned but never executed; check exit, no errors, scanned path, exact ID and preservation. The Tier 1 report must record the exact Semgrep version in Code Risk Analysis; absence/incompleteness blocks execution. Five regressions. Metrics and version check disabled, no registry/Pro/LLM; not an OS network sandbox, native OCaml binary audit or certification. Upstream excludes tests/test in integrated analysis; independent Bandit/Gitleaks/SkillSpector remain. Live CI required, T12 PARTIAL.

## T12.03.16 — PR result

[CI 45419767513](https://github.com/Sashido01/TESSERA/actions/runs/45419767513) PASS: 556+29=585 tests, Semgrep 1.182.0 EXECUTED, clean/detection/coverage/fixture PASS, Code Risk Analysis PASSED. 67 Python distributions, OSV 8 IDs in 3 packages (mcp 1.29.0:5, opentelemetry-api 1.37.0:2, wcmatch 8.5.2:1), 3 UNKNOWN license metadata, native binaries NOT_SCANNED. Separate open risks; policy FAIL 19 MEDIUM + aggregate HIGH unchanged. v0.0.47 main CI and annotated tag verified; v0.0.48 merged into main, its acceptance separate.

## T12.03.17 — skill Git helper hardening (candidate)

Based on the 19 MEDIUM review (PR 48, comment 7135272307): production AST4 corresponds to actual Git invocation; each call limited to 60 s, absolute executable from absolute PATH entries, closed stdin, shell=False, fixed errors without raw diagnostics, post-capture limit of 1,048,576 characters. Six regressions; memory/pipe risk, trusted PATH/config, Windows and races remain limitations. AST4 may remain as an expected subprocess finding; no suppressions. CI required, T12 PARTIAL.

## T12.03.17 — PR result

[CI 45421559705](https://github.com/Sashido01/TESSERA/actions/runs/45421559705) PASS: 556+35=591 tests, all six new regressions. SkillSpector 53/100, 19 MEDIUM, 0 suppressions, coverage 100% of inspected files, Code Risk Analysis PASSED; policy FAIL unchanged. v0.0.48 main CI 45421312225 and annotated tag verified; v0.0.49 merged into main, its acceptance separate.

## T12.03.18 — static test imports (candidate)

Three test modules replace fixed-file importlib loading with ordinary imports from scripts in the current trusted checkout: reject conflicting sys.modules cache, temporarily prepend the directory to sys.path, restore after import, verify __file__ against the expected source. Three module-origin checks; existing scenarios retained. This simplifies test code, not a sandbox; checkout and Python import hooks must remain trusted. No changes to scanners, thresholds, suppressions, production skill code or permissions. CI must confirm regressions and actual AST3 counts; score reduction is not promised. T12 PARTIAL.

## T12.03.18 — PR result

[CI 45423325658](https://github.com/Sashido01/TESSERA/actions/runs/45423325658) PASS: 556+38=594 tests, AST3 6→0, SkillSpector 53→36/100, MEDIUM 19→13, aggregate HIGH 1→0, 0 suppressions, coverage 100% of inspected files. Integrated static policy PASS, not security certification. v0.0.49 main CI 45423143946 and annotated tag verified; v0.0.50 merged into main, its acceptance separate.

## T12.03.19 — Russian terminology clarity (candidate)

22 editorial substitutions in six skill files: ordinary phrases instead of mixed hyphenated tokens. Preliminary review of 17 files; independent ASCII Latin + Cyrillic/Greek token count in modified files 22→0. Five Russian documents and two release_tag.py exception messages; English translation retains its existing meaning, executable commands, error codes, access policy and algorithms unchanged. Not a full Unicode audit or proof of AE4 removal; live CI required. No rules disabled or suppressions used. AST4 and LP3 remain subject to review; T12 PARTIAL.

## T12.03.19 — PR result

[CI 45425640926](https://github.com/Sashido01/TESSERA/actions/runs/45425640926) PASS, 556+38=594 tests, AE4 6→0, MEDIUM 13→7 (AST4 6, LP3 1), SkillSpector 36→22/100, 0 suppressions, integrated policy PASS. v0.0.50 main CI 45425408841 and annotated tag verified; v0.0.51 merged into main, its acceptance separate.

## T12.03.20 — Linux namespace preflight (candidate)

Required synthetic control, separate from scanners: positive parent connection to IPv4 loopback listener, negative inside separate network namespace, distinct net namespace inodes, PID=1, exact soft/hard rlimits CPU 10 s, AS 1 GiB, FSIZE 16 MiB, NOFILE 256, CORE 0; closed stdin/inherited FDs, minimal environment, output to temporary files, timeout and PID namespace termination (descendant created separate setsid session, did not write marker). Prototype actually passed in separate Linux x86_64 container UID=0, util-linux 2.41.5, not GitHub Runner. Five offline regressions. CI blocks on failure, no sudo/fallback. Test limits are not scanner profiles; filesystem isolation, AF_UNIX, aggregate cgroup budget, real scanner workloads and Windows NOT_VERIFIED. Not a sandbox, T12 PARTIAL. Semgrep 8 OSV IDs remain open.

First PR CI 45427345462: 561+38=599 tests PASS, required preflight FAIL on Ubuntu 26.04. Root cause undetermined (overly generic error code). Within the same candidate, add bounded numeric user/net/pid namespace policy indicators and fixed unshare/prlimit error codes without publishing stderr, one more offline regression (six total). No fallback, control requirements and runner permissions unchanged. Repeat CI required.

Second PR CI 45427736161: 562+38=600 tests PASS, NAMESPACE_UNSHARE_PERMISSION_DENIED; kernel/unprivileged_userns_clone=1, apparmor_restrict_unprivileged_userns=1, user/net/pid max=55883. AppArmor likely, exact audit denial unavailable. Instead of changing host policy, select an explicit Docker synthetic preflight on the trusted disposable runner: Python 3.13.18 slim trixie linux/amd64 image pinned to manifest SHA-256 48d884813cf44e927cf64c5529dd630dd3b18338c6dc727991eef9b71e934a20; source https://hub.docker.com/layers/library/python/3.13.18-slim-trixie/images/sha256-48d884813cf44e927cf64c5529dd630dd3b18338c6dc727991eef9b71e934a20 . Image has published advisories, not a verified supply chain; synthetic only, no repository, secrets or mount/socket. Nonroot, no caps, no-new-privileges, seccomp, network none, read-only root, tmpfs, cgroup memory/swap/CPU/PID. Check actual values inside container and host sentinel; cleanup required. Four new offline tests. Original unshare retained as diagnostic tool, no automatic fallback. Docker daemon is a trusted root-equivalent host boundary, unavailable inside container; do not transfer to user machines without a separate threat model. Resource exhaustion, timeout descendants and actual scanner execution NOT_VERIFIED. CI required, T12 PARTIAL.

## T12.03.21 — containerized Gitleaks (candidate)

T12.03.20: [CI 45428224320](https://github.com/Sashido01/TESSERA/actions/runs/45428224320) PASS, 566+38=604 tests, Docker synthetic preflight PASS. v0.0.52 merged into main, tag separate. New mandatory control compares host and container for tracked UTF-8 stdin scope: identical snapshot fingerprint, TSG1 digest, exact file/byte counts, findings by rule, clean/negative/redaction controls. One nonroot container with pinned image and SHA256 binary, minimal helper modules and binary in separate read-only bind, no repo/.git/socket mounts, network disabled, 2 CPU/512 MiB/64 PID, log-driver none, 300s timeout and rm --force. Nine offline regressions; actual new code and Docker workload require CI. Host scan retained, history/path checks not isolated, image not certified, retained report limit not hard disk quota, cleanup timeout/daemon failures unproven. T12 PARTIAL.

## T12.03.21 — PR result

[CI 45432568241](https://github.com/Sashido01/TESSERA/actions/runs/45432568241) PASS: 575+38=613 tests; Docker Gitleaks 177 files, 1,404,601 bytes, 0 findings, host parity/frame digest/redaction/source preservation PASS. Host history: 864 blobs, 10,663,788 bytes, 0 findings. Integrated Tier 1 policy PASS; v0.0.52 main CI 45432307038 and annotated tag verified. v0.0.53 merged into main, its acceptance separate.

## T12.03.22 — containerized history scanning (candidate)

Reusable Gitleaks transport, separate required reachable UTF-8 blob check: host inventory, Git blob OID SHA-1/SHA-256 validation, inventory fingerprint, TSG1 batches <=256 objects and <=16 MiB each, unchanged aggregate cap 128 MiB/2048 blobs. Overall deadline 540s, each scan up to 300s; exact coverage/findings parity with host, synthetic previous-content and existing live Git fixture on host. No .git/OID/path passed to container; only bytes and other category. Seven new offline regressions. CI required; performance and complete Docker workload NOT_VERIFIED, path-specific/integrated scans remain on host. Git SHA-1 is not proof of cryptographic collision resistance. T12 PARTIAL.

## T12.03.22 — PR result

[CI 45434506035](https://github.com/Sashido01/TESSERA/actions/runs/45434506035) PASS: 582+38=620 tests; Docker history 878 blobs, 10,952,864 bytes, 4 batches, 316.56s, 0 findings; identity, digest, host parity, previous-content PASS. CI 795s against 1200s limit. v0.0.53 main CI and tag verified; v0.0.54 merged into main, tag separate.

## T12.03.23 — containerized path check (candidate)

Separate TSP1 transport mode: 10 fixed categories (2 scopes x 5 existing rules), up to 256 targets/16 MiB per batch, aggregate cap 4096 targets/192 MiB, 180s deadline. Empty batch permitted only for TSP1 to execute five control fixtures. No real paths/OIDs/.git passed; fixed canonical names, existing scan_rule, strict ten report rows and snapshot parity with host, repeated source check. Nine new offline regressions (8 + workflow guard). Existing checks retained; integrated Gitleaks remains host. Real execution and limits require CI. T12 PARTIAL.
