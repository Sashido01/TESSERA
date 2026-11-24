# TESSERA changelog

[Русский — основной язык](CHANGELOG.md) | **English — translation**

This file tracks changes to the **shared catalog**. Individual skills may maintain their own version histories.

## 0.0.65 — Universal skill test runner

- Separate-process unittest discovery for all skills; reject suites with no ordinary successful tests. Validation CI, signing and preflight share the runner. Ten regression scenarios; full CI required.
- Five-stage Project Audit evolution approved; T12 remains PARTIAL.

## 0.0.64 — Integrated SkillSpector Docker (T12.03.32)

- Static-only NVIDIA adapter, report validation and receipts, five regressions. CI required; T12 PARTIAL.

## 0.0.63 — Standalone SkillSpector Docker (T12.03.31)

- Isolated static SkillSpector, 74 distribution pins, host/container parity, eight regressions. CI required; T12 PARTIAL.

## 0.0.62 — Safe Bandit coordinates (T12.03.30)

- Bounded finding locations, host/container parity, six regressions. CI required; T12 PARTIAL.

## 0.0.61 — Scanner configuration SHA-256 (T12.03.29)

- Pin exact Semgrep and Bandit configuration SHA-256 instead of SHA-1; retain Git blob provenance. Two regression tests, no suppression. CI required; T12 PARTIAL.

## 0.0.60 — Integrated Bandit Docker (T12.03.28)

- Restricted NVIDIA adapter, INI, coverage and report verification, six regressions. CI required; T12 PARTIAL.

## 0.0.59 — Standalone Bandit Docker (T12.03.27)

- Minimal pinned runtime, read-only snapshot, host parity, four regressions. CI required; T12 PARTIAL.

## 0.0.58 — Integrated Gitleaks Docker (T12.03.26)

- Isolated NVIDIA adapter, skill snapshot, restricted TOML and report, eight regressions. CI required; T12 PARTIAL.

## 0.0.57 — Bounded Gitleaks concurrency (T12.03.25)

- Two TSG1 workers, unchanged limits, full coverage, three regression tests. CI required; T12 PARTIAL.

## 0.0.56 — Semgrep license evidence (T12.03.24)

- Three pinned upstream LICENSE texts, existing wheel/RECORD verification, two regression tests. CI required; T12 PARTIAL.

## 0.0.55 — Containerized path check (T12.03.23)

- TSP1, five rules, ten categories, host parity and nine regressions. CI required, T12 PARTIAL.

## 0.0.54 — Containerized history scanning (T12.03.22)

- Batched blob transport, OID checks and host parity; seven regressions. CI required, T12 PARTIAL.

## 0.0.53 — Isolated Gitleaks (T12.03.21)

- Tracked UTF-8 host/container parity, TSG1, pinned binary, nine regressions. CI required, T12 PARTIAL.

## 0.0.52 — Linux namespace preflight (T12.03.20)

- Required synthetic network, PID, rlimits and timeout preflight; five offline regressions. Local unshare PASS, GitHub unshare BLOCKED; explicit required Docker synthetic preflight, CI required; not a complete sandbox.

## 0.0.51 — Clarified Russian skill terminology (T12.03.19)

- 22 editorial substitutions in six files, meaning and algorithms retained, independent mixed-token count 22→0; CI required, no suppressions.

## 0.0.50 — Simplified skill test imports (T12.03.18)

- Ordinary imports of three checkout modules, origin and conflicting cache checks, three regressions. CI required; no threshold or suppression changes.

## 0.0.49 — Hardened skill Git helper (T12.03.17)

- Absolute executable, timeout, closed stdin, safe diagnostics and post-capture output limit; six regressions. CI required; trusted configuration and environment limitations remain.

## 0.0.48 — Pinned Semgrep in NVIDIA Tier 1 (T12.03.16)

- Upstream lock, local rules, live controls and required scanner report, OSV/licenses; five regressions. CI required, sandbox and certification open.

## 0.0.47 — Tier 1 aggregate HIGH finding attribution (T12.03.15)

- Separate aggregate_risk_gate and other_high counts, original severity and policy unchanged; three regressions. Live CI acceptance required.

## 0.0.46 — Live Tier 1 Gitleaks redaction control (T12.03.14)

- Real shim clean and synthetic finding controls, stdout/stderr redaction and fixture preservation; five regressions. CI required; upstream completeness and sandbox not verified.

## 0.0.45 — Integrated static NVIDIA Tier 1 (T12.03.13)

- Explicit complete check-group lineup, pinned scanners and bounded Gitleaks adapter, aggregate-only reports, seven regressions. CI required; Semgrep and certification not verified.

## 0.0.44 — Hardened remote Release Core inspection (T12.03.12)

- One named remote, transport scope, fixed upload-pack, minimal environment and consistent evidence. Ten regressions; CI required, live network acceptance separate.

## 0.0.43 — Hardened Release Core local inspection (T12.03.11)

- Fixed tag object and direct commit, rechecks, minimal environment, no Git replace objects, timeout. Eight regressions; CI required. Remote and concurrency locking remain separate.

## 0.0.42 — Shared Gitleaks safe launch contract (T12.03.10)

- Fixed stdout/redact and archive-depth options; bounded temporary-file invariants, four regressions. CI required; not an OS sandbox.

## 0.0.41 — Minimum tool scope and Go audit evidence (T12.03.09)

- Explicit skill access boundaries without preapproved tools, independent Git/CI verification; actual v0.0.40 evidence and OSV/Govulncheck ID comparison. No LP3 suppression; CI required.

## 0.0.40 — Go binary review using Govulncheck (T12.03.08)

- Candidate: pinned source, isolated CI build, extract and binary mode, explicit distinction between fallback and extracted symbols, scanner OSV self-audit and before/after SHA-256, eight offline regressions and two upstream local-database controls; live acceptance required. Call reachability not proven.

## 0.0.39 — Bind tag to the exact verified commit (T12.03.07)

- Candidate: explicit target SHA, immutable object verification, direct commit and tag name, `--expected-head`, ref recheck; seven regressions, including rejection of inherited Git context/config overrides and child environment minimization. CI required; concurrent locking is not implemented.

## 0.0.38 — Installed license content verification (T12.03.06)

- Candidate: bounded license record checks for two exact Python versions, RECORD SHA-256 and size, upstream comparison; original metadata preserved. Four regressions; CI required. Go license confirmed at upstream level, not binary level.

## 0.0.37 — Evidence-bound SkillSpector finding locations (T12.03.05)

- Candidate: primary locations only for known relative paths in the inspected skill inventory; bounded output with explicit unresolved and omitted counts. No snippets, raw messages or occurrence metadata; unchanged rules and thresholds. Three regressions; real CI acceptance required.

## 0.0.36 — Offline installer path hardening (T12.03.04)

- Candidate: reject redirection of standard project paths and links/special files in the source; recheck destination after creating parent directories. Regressions for external links, dangling links and source links. CI not yet accepted; TOCTOU races and Windows junctions NOT_VERIFIED.

## 0.0.35 — SkillSpector security upgrade (T12.03.03)

- Candidate 2.13.7, pinned commit/wheel/lock, unchanged static no-LLM contract and zero-suppression enforcement, repeat CVE review. [CI 45376675127](https://github.com/Sashido01/TESSERA/actions/runs/45376675127) PASS: 494+19 tests; SkillSpector 2.13.7, 17/17 files, complete, 100%, 16 MEDIUM (AE4 6, AST3 6, AST4 3, LP3 1), zero HIGH, risk 53/100 HIGH, exit 1, zero suppressions, both fixtures PASS, 11.37 s. OSV: 74 Python distributions, zero packages with entries, zero source-commit entries; cryptography 50.0.2, langgraph 1.2.20, pyasn1 0.6.5. T12.03.03 COMPLETE within upgrade and repeat OSV scope; new AST3 and threshold exceedance remain open. Release awaits sequential acceptance.

## 0.0.34 — Restrict CI evidence API redirects (T12.03.02)

- Exact GitHub Actions API endpoints, reject redirects before following, verify exact response URL, four regressions. [CI 45376483433](https://github.com/Sashido01/TESSERA/actions/runs/45376483433) PASS: 493+19 tests, four new regressions PASS, Bandit B310 absent in the repeat review; 110 findings (no HIGH), no rule suppression. T12.03.02 COMPLETE within implemented control and CI scope; live network execution separately NOT_VERIFIED.

- Before merge, a shared get_public_json regression was found: the original strict URL allowlist blocked the existing GitHub Release metadata call. Permit only the canonical /releases/tags/vMAJOR.MINOR.PATCH route and one namespace encoded as %2F; arbitrary escaping, extra paths and parameters remain forbidden. Three regressions exercise verify_github_publication through the actual shared transport (ordinary and namespaced tag), changed response URL rejection and invalid routes. Only networking is mocked, validation and response handling are real. Historical PASS missed this defect; repeat acceptance is required.

## 0.0.33 — Portable Microversion Release license and references (T12.03.01)

- Standalone MIT license, portable references, corrected distribution guidance, ZIP and official local installation regressions. Canonical SKILL.md compacted to 8876 UTF-8 bytes; explicit authorization, script table and troubleshooting. [CI 45373618225](https://github.com/Sashido01/TESSERA/actions/runs/45373618225): 486+19 tests PASS. SkillSpector 2.13.6: complete, 17/17 files, 100%, reference_missing 4→0, risk 78→36 (HIGH→MEDIUM), HIGH 2→0, MEDIUM 10, zero suppressions, both fixtures PASS, 19.40 s. NVIDIA: license allowed, RU quality 80.0 (65×0.35 + 80×0.25 + 95×0.25 + 90×0.15), Codex custom provider degraded→loads. Overall CI FAIL only at inherited Go review; release and real activation NOT_VERIFIED.

## 0.0.32 — Dependency CVE and license metadata review (T12.02.02.04)

- Exact installed Python inventory, OSV queries with pagination and negative control, license metadata; Go binary build info for gh/Gitleaks, module and toolchain OSV queries, deps.dev license metadata. Advisory findings, fail-closed execution, no LLM. [CI 45375135316](https://github.com/Sashido01/TESSERA/actions/runs/45375135316) PASS: 477+19 tests; 97 Python package checks, 3 packages with OSV entries; 212 distinct Go modules (gh 155, Gitleaks 66), 8 affected modules across the binaries, Gitleaks stdlib/toolchain and one source-commit entry; 211 Go licenses reported by deps.dev, one NOT_INDEXED. T12.02.02.04 COMPLETE within inventory/query execution scope; CVE remediation, code reachability and legal compatibility remain open.

## 0.0.31 — Direct static SkillSpector review (T12.02.02.03)

- Pinned SkillSpector 2.13.6 source and official wheel, offline lock export, wheel/hash-only separate environment, no LLM, strict scan report and completeness checks, synthetic clean and P1 fixtures, CI and bilingual documentation. [CI 45370414762](https://github.com/Sashido01/TESSERA/actions/runs/45370414762) PASS: 454+19 tests; 16/16 files, 100% coverage, complete_with_caveats (4 reference_missing), risk 78/100 HIGH, exit 1 (threshold 50 exceeded), 12 findings (10 MEDIUM, 2 HIGH), zero suppressions, both synthetic fixtures PASS, 13.32 s. T12.02.02.03 COMPLETE within direct static execution scope; findings and full NVIDIA security acceptance remain open.

## 0.0.30 — Reachable Git history content review (T12.02.02.02)

- Gitleaks scans each distinct reachable UTF-8 blob from local refs and HEAD via stdin; validates complete object inventory, byte coverage, immutable inventory and synthetic removed-secret fixture. [CI 45368434188](https://github.com/Sashido01/TESSERA/actions/runs/45368434188) PASS: 437+19 tests; 585/585 distinct UTF-8 blobs, 5431003 bytes, zero findings, removed-marker fixture PASS, 128.81 s. [CI 45369335974](https://github.com/Sashido01/TESSERA/actions/runs/45369335974) PASS: 443+19 tests; 598 distinct UTF-8 blobs, 5639755 bytes, zero findings; five synthetic rule fixtures PASS; 4 current YAML files and 28 historical rule/blob pairs across 37 commits, zero findings. T12.02.02.02 COMPLETE within declared scope. Unavailable refs and unreachable objects not covered.

## 0.0.29 — Gitleaks text snapshot review (T12.02.02.02)

- Official SHA-256 pinned Gitleaks 8.30.1, separate stdin per tracked UTF-8 file, byte coverage, redaction and exit code checks, negative allow-comment fixture, CI and bilingual documentation. [CI 45367459045](https://github.com/Sashido01/TESSERA/actions/runs/45367459045) PASS: 428+19 tests, 144/144 tracked UTF-8 files, 998544 bytes, zero findings, positive/negative and redaction fixtures PASS; 65.29 s. Snapshot acceptance COMPLETE; history/path-specific rules NOT_VERIFIED; T12.02.02.02 remains PARTIAL.

## 0.0.28 — Direct Bandit static review (T12.02.02.01)

- Isolated review of all tracked Python files with pinned Bandit 1.9.4, strict coverage and report validation, synthetic positive and negative cases, safe aggregates, mandatory CI and bilingual documentation. [CI 45365133732](https://github.com/Sashido01/TESSERA/actions/runs/45365133732) PASS: 414+19 tests, 60 Python files, 87 findings (45 runtime, 42 tests; 2 medium, 85 low, 0 high); clean and negative fixtures PASS; direct review 1.69 s. Direct scan execution COMPLETE; full NVIDIA code-integrity, Gitleaks, SkillSpector and CVEs remain NOT_VERIFIED.

## 0.0.27 — NVIDIA static review and language alternatives (T12.02.01)

- Compare default and localized quality, sanitized finding codes and four dimensions. PII/license/unicode/lint, negative Unicode fixture, six static profiles and Codex scenarios. No LLM, Tier 2/3 or external scanners. [CI 45360122208](https://github.com/Sashido01/TESSERA/actions/runs/45360122208) PASS, 403+19 tests, 75.0/78.8, 18/16 findings, Unicode negative PASS, static profiles confirmed, license not_detected and PII/lint warnings retained. T12.02.01 COMPLETE within fixture scope; T12 PARTIAL. Updated bilingual docs.

## 0.0.26 — Focused NVIDIA SkillEvaluator Tier 1 evaluation (T12.01)

- Pinned official 1.2.0 wheel and 19 dependencies from uv.lock by SHA-256, separate Linux CPython 3.13 environment, schema/quality only without LLM or extras. Verify JSON, exit code and negative case. Findings advisory; execution failure blocks CI. Live acceptance [CI 45358283596](https://github.com/Sashido01/TESSERA/actions/runs/45358283596): schema/quality PASS, 75/100, 18 findings, 393+19 tests PASS; corrected first-run JSON validator name mismatch (QUALITY). T12.01 COMPLETE within stated scope.
- Updated bilingual docs. Full Tier 1, scanners and agent compatibility NOT_VERIFIED; no Tier 2/3.

## 0.0.25 — Isolated multi-skill and independent tag acceptance (T10.03.02)

- Temporary Git repository with two synthetic skills, five annotated tags and independent Git tree checks. Actual local snapshot installs with gh 2.105.0, scoped replacement and rollback, namespace collisions and duplicate refusal. 7 offline tests plus a mandatory CI guard test.
- Clarified low-level InstallLocal versus CLI checkOverwrite; retained defensive guard. Local fixture PASS: [CI 45354011607](https://github.com/Sashido01/TESSERA/actions/runs/45354011607), GH_SKILL_MULTI_FIXTURE_PASS, 383+19 tests. T10.03.02 PARTIAL pending separate remote acceptance. Remote namespaced pin and T16 remain unverified. Updated bilingual docs.

## 0.0.24 — Actual update and guarded re-pin (T10.03.01)

- Actual gh 2.105.0 update --unpin --dry-run and --unpin --all harness against disposable synthetic local edits; verify new Git tree and directory replacement behavior.
- Independently install two exact pins, refuse local edits or staged mutation, retain backup, test injected failure and explicit rollback. 12 offline scenario tests plus mandatory CI guard test.
- T10.03.01 COMPLETE within the harness: [live CI 45352932764](https://github.com/Sashido01/TESSERA/actions/runs/45352932764), GH_SKILL_UPDATE_PASS, 375+19 tests passed; native removal of synthetic local edits confirmed; T10.03.02 (multi-skill collisions and independent tags), crash recovery, concurrent writes and client activation remain unverified. Updated bilingual docs.

## 0.0.23 — Verify remote skill installation at exact tag and SHA (T10.02)

- Added actual official gh 2.105.0 CI acceptance: install from public TESSERA by refs/tags/v0.0.22 and full commit SHA, verify independent Git tree, file inventory and bytes, pin metadata and gh skill list discovery.
- Verify duplicate installation refusal without --force and pinned update --dry-run skipping without file mutation. Isolated HOME and GH_CONFIG_DIR, read-only CI token only, offline negative tests.
- T10.02 COMPLETE: [live CI 45351217500](https://github.com/Sashido01/TESSERA/actions/runs/45351217500) confirmed GH_SKILL_REMOTE_PIN_PASS; 362+19 tests passed. Overall T10 PARTIAL. Applied updates, multi-skill behavior and client activation remain unverified. Updated bilingual docs and ROADMAP.

## 0.0.22 — Record live independent acceptance of the signed ZIP (T09.10)

- At annotated tag `v0.0.21` (commit `0c83ae9ef119a0cfc9d07c83dbae91e5d026e407`), [signing run 45348928593](https://github.com/Sashido01/TESSERA/actions/runs/45348928593) completed SUCCESS; [Attestation 71489191](https://github.com/Sashido01/TESSERA/attestations/71489191), [Actions Artifact 14898798605](https://github.com/Sashido01/TESSERA/actions/runs/45348928593/artifacts/14898798605). Independent verification checked the 105849-byte ZIP, SHA-256 `55db489f0219739e9296fc941fa51fa58d23c3277878fe5e3a352642947eeb73` and all 17 manifest files. The owner on Windows confirmed that digest and supplied official `gh 2.105.0` output: `Verification succeeded!`, one attestation matched SLSA v1, exact repository, commit, tag, signer workflow, OIDC issuer and GitHub-hosted runner. T09.10 COMPLETE, `SIGNED_ARTIFACT=PASS` only for the verified v0.0.21 ZIP.
- Updated bilingual ROADMAP, TRUSTED_BUILD, README and AGENTS. This microversion records evidence; it does not claim a new signature of its own. No GitHub Release was created; overall T09 remains PARTIAL.

## 0.0.21 — Fix ZIP preparation before Sigstore attestation (T09.10)

- Live signing run `45347443989` for `v0.0.19` failed: tag checks and 333+19 tests passed, but the source ZIP builder refused `PACKAGE_RUNTIME_FILE_INVALID`. Sigstore and artifact upload were SKIPPED; no downloadable artifacts exist.
- Root cause: Python imports runtime modules from `skills/microversion-release/scripts/` during tests, creating `__pycache__` which the strict runtime ZIP allowlist correctly rejects.
- Enabled `PYTHONDONTWRITEBYTECODE=1` in both signing and main CI validation jobs. Main CI now performs a mandatory **post-test** reproducible ZIP smoke into `dist/post-tests`, matching the signing order.
- Added negative regression tests for missing bytecode isolation, missing post-test smoke and cache contamination. The strict ZIP allowlist remains unchanged.
- Updated bilingual ROADMAP, TRUSTED_BUILD, README and AGENTS. A fresh live signing run on the newly confirmed annotated version is still required: no attestation has been verified.

**T09.10 status:** PARTIAL / SIGNED_ARTIFACT_NOT_VERIFIED until a real successful signing workflow, downloaded ZIP and independent Sigstore verification.

## 0.0.20 — Safe local Agent Skill installation via official GitHub CLI (T10.01)

- Added real `gh skill install --from-local --dir` and `gh skill list --dir` CI scenarios for `microversion-release`, confined to temporary directories with no access to user profiles.
- Reused SHA-256-verified official `gh 2.105.0`. New `tools/check_official_local_install.py` verifies original source integrity, Markdown body, references and injected source-tracking metadata.
- Checks that `--from-local` cannot combine with `--pin`, refuses preexisting targets before calling the CLI and never publishes a release. Added negative tests.
- Official CLI source review reveals a local `InstallLocal` overwrite risk even without `--force`. Direct repeat local install into a user's existing directory must not be treated as safe; TESSERA's offline fallback remains no-overwrite.
- Updated bilingual roadmap and policies. Actual **remote** pinned installation by tag/SHA and client integration remain NOT_VERIFIED.

**Acceptance:** T10.01 COMPLETE only after a successful live CI run with the real `gh`. Overall T10 PARTIAL, signed ZIP T09.10 remains OPEN.

## 0.0.19 — Actual isolated gh skill publish --dry-run

- Added an official `gh skill publish --dry-run` CI check on a temporary copy of all skills with no GitHub remote or inherited tokens. The exact `gh 2.105.0` release binary is downloaded and SHA-256 verified before execution.
- `tools/run_publish_dry_run.py` verifies CLI identity, positive and negative validation, no remote, and unchanged source files with a SHA-256 tree fingerprint. Errors fail closed without exposing secrets or private paths.
- Added regression tests and bilingual documentation, and updated ROADMAP, README and AGENTS.
- Live GitHub topic/release checks and authenticated remotes are explicitly **out of scope**. T09.10 and agent-client integration remain separate.

**Acceptance:** T11.02 local format validation requires an actually successful CI run; an unsigned package or mocked CLI cannot establish publication readiness.

## 0.0.18 — Upgraded GitHub Actions to Node.js 24

- Pinned official `actions/checkout` v7.0.1, `actions/setup-python` v7.1.0 and `actions/upload-artifact` v7.0.2 by full SHA in the validation and signing workflows. Independently confirmed that the existing pinned `actions/attest` SHA is v4.2.2 and already uses Node.js 24; no needless change was made.
- Added the mandatory `tools/check_actions_runtime.py` check for exact approved SHAs, counts and action inventory in both workflows, plus negative regression tests rejecting rollbacks, floating tags and unknown actions.
- Preserved main protection, annotated tags, separate signing workflow, least privilege, credential removal and ancestry checking.
- Updated bilingual documentation and roadmap. Live signing and independent GitHub attestation remain NOT_VERIFIED.

**Acceptance:** T08.01 needs verified PR/main CI success, a matching annotated tag, and no legacy Node.js 20 warnings from the updated actions. T08 overall remains PARTIAL.

## 0.0.17 — Reference Agent Skills format verification in CI

- Integrated upstream `skills-ref validate` from official `agentskills/agentskills`, pinned to exact SHA `83021e2be457a9b6679148719c1f6074f0ad975e`. The extra checkout runs after TESSERA's own tests and source packaging.
- Pinned `skills-ref` runtime dependencies to versions and wheel SHA-256 hashes; no installation of an unrelated same-named PyPI distribution.
- Added a defensive all-skills wrapper that rejects invalid names, symlinks, missing tooling, timeouts, and unexpected results, with new unit tests.
- Added the bilingual [AGENT_SKILLS_STANDARD](docs/AGENT_SKILLS_STANDARD.en.md) guide and updated the project roadmap and agent rules.

**Limits:** the upstream reference library is expressly for demonstration, not production. Live `gh skill publish --dry-run` and actual client integration remain NOT_VERIFIED. T11 PARTIAL; T11.01 requires a successful CI run.

## 0.0.16 — Reject vulnerable GitHub CLI versions during attestation verification

- Added a mandatory installed `gh` version preflight before `gh attestation verify`. Minimum `2.102.0` includes fixes for GHSA-wjmr-j3rp-mh2g and GHSA-4mq3-hpgx-9cx8 (30 September 2026).
- Unknown, outdated, malformed, or unavailable CLI versions produce `BLOCKED`, never a false `PASS`. The probe has a bounded timeout, and stderr/user paths are not included in reports.
- Added positive/negative regression tests; updated bilingual provenance, trusted-build, and roadmap documentation.
- No claim of an actual signing run or verified publication: T09.10 remains PARTIAL and attestation NOT_VERIFIED.

## 0.0.15 — Offline verification of actual catalog ZIP bytes

- Added `tools/verify_catalog_package.py` to validate archive structure, required files, manifest, every member SHA-256, exact version, and externally supplied full source commit SHA.
- Unsafe paths, symlinks, duplicates, unsupported encoding/compression, limits, and tampered bytes fail closed; ZIP contents are never extracted or executed.
- Added negative unit tests and a bilingual [CATALOG_VERIFICATION](docs/CATALOG_VERIFICATION.en.md) guide.
- Archive internal integrity is distinct from independently verified cryptographic attestation; signing and publication remain NOT_VERIFIED.

**Limits:** live signing, publishing, and agent-client integration remain NOT_VERIFIED; T09 PARTIAL. CI acceptance for this version must be checked after the PR is opened.

## 0.0.14 — Deterministic catalog package and trusted attestation preparation

- Added `tools/build_catalog_package.py`: genuine Agent Skills catalog source ZIP with fixed ZIP metadata, LICENSE, VERSION, runtime skill files, SHA-256 manifest, and exact source Git commit.
- Added separate `build-attested-catalog.yml` **manually dispatched at an annotated tag**, with read-only source permissions and limited GitHub/Sigstore attestation rights. All third-party Actions are pinned to full SHAs; GitHub Releases are not auto-published.
- `release-checks.json` now requires the actual catalog build rather than NOT_APPLICABLE. Ordinary PR CI builds and checks determinism without OIDC signing.
- Added security checks for the signing workflow and negative tests for wrong refs/tags, unsafe files, and source modifications.
- Simplified Git policy: **one working branch per coherent goal and one PR**, not one branch for every intermediate correction. Documented in bilingual [BRANCHING](docs/BRANCHING.en.md).
- Updated canonical Russian and complete English translations of roadmap, VERSIONING, GITHUB_SECURITY, architecture, README, and AGENTS.

**Limits:** executing the workflow against a real tag and validating a genuine signed attestation remain NOT_VERIFIED. The ZIP is stored as a GitHub Actions Artifact, not a GitHub Release; the workflow does not sign executable applications. T09 remains PARTIAL.

## 0.0.13 — Signed release artifact provenance verification

- Added `core/release_provenance.py` to independently hash a local file against GitHub Release metadata and cryptographically verify a Sigstore/SLSA attestation via official `gh attestation verify`.
- Enforced exact repository, source commit SHA, Git tag, specific signing workflow, and SLSA provenance v1 predicate; an arbitrary workflow's claim is not trusted.
- Added fail-closed handling for tampered file bytes, missing publication, unavailable CLI, failed signatures, malformed JSON, and file changes during verification.
- Extended `core/release_report.py` with `--verify-provenance --artifact-file --signer-workflow`; this is disabled by default and excludes local file paths from reports.
- `core/release_certificate.py` separates a verified signed GitHub attestation from **TESSERA's unsigned evidence certificate**; application readiness stays NOT_VERIFIED.
- Added 33 test scenarios, canonical Russian `docs/RELEASE_PROVENANCE.md` and complete English translation, and updated architecture, roadmap, README, AGENTS and technical documentation.

**Limits:** TESSERA does not have a real published and signed artifact. Tests mock the official CLI's outputs; they do not prove live artifact attestation. Trusted build workflow, actual publication, and concurrency controls are future work. T09 remains PARTIAL.

## 0.0.12 — Stream-verified actual release asset bytes

- Added independent `core/release_assets.py`: streaming byte count and SHA-256 verification of attached GitHub Release assets against official API metadata.
- Added bounded-memory streaming, explicit per-file limits, untrusted URL/redirect rejection, and strict matching of repository/tag/filename.
- Extended `core/release_report.py`: `--verify-assets` requires explicit `--verify-publication`; no byte verification is performed by default.
- Preserved the distinction between downloaded byte integrity, build provenance, and application readiness in `core/release_certificate.py`; the certificate SHA-256 remains unsigned.
- Added 32 test scenarios, including corrupted/truncated/oversized bytes, untrusted URLs, missing digests, and unverified publication.
- Added canonical Russian `docs/RELEASE_ASSETS.md` and complete English translation; updated roadmap, architecture, README, AGENTS, reports, and changelogs.

**Limits:** no published TESSERA GitHub Releases existed at inspection time, so a live end-to-end download remains NOT_VERIFIED. Independent build provenance, digital signatures, and executable application readiness are also NOT_VERIFIED; T09 stays PARTIAL.

## 0.0.11 — Verified GitHub Release publication metadata and an evidence certificate

- Added `core/release_publication.py`: read-only verification of published GitHub Release metadata, including exact tag, draft/prerelease flags, publish date, GitHub URL, and asset states.
- Bound the named trusted Git remote to `github.com/owner/repository` so an unrelated URL, local bare Git, or hostname lookalike is not mistaken for GitHub publication.
- Added `core/release_certificate.py`: structured unsigned evidence with reproducible SHA-256 of its own fields and distinct source-publication vs application-readiness statuses.
- Extended `core/release_report.py` with `--verify-publication` and `--format certificate`; publication is neither queried nor created automatically.
- Added 39 positive/negative cases covering metadata, unrelated remotes, missing evidence, unsigned checksums, and report integration.
- Updated roadmap, architecture, README, AGENTS, and bilingual T09.01–T09.05 documentation.

**Limits:** TESSERA had no GitHub Releases at the time of inspection. The implementation does not create one. Live source-publication acceptance is NOT_VERIFIED; asset bytes, signatures, and executable application readiness are not checked. Overall T09 remains PARTIAL.

## 0.0.10 — Independent completed GitHub Actions and evidence-state verification

- Added `core/release_ci.py`: validates a completed GitHub Actions run using the official REST API and exact commit SHA, expected workflow, push to main, and both required jobs.
- Mismatching attempts, missing/skipped/failed required jobs, incomplete API responses, and network failures result in BLOCKED, never a false PASS.
- Added a pure `core/release_state.py` evidence-stage reducer without an invented RELEASED state.
- Extended `core/release_report.py` with explicit `--verify-ci`, trusted GitHub repository and completed run ID, and new CI fields in JSON/Markdown.
- Added 32 positive/negative scenarios covering GitHub API responses, incomplete pagination, SHA/attempt mismatch, and disabled-by-default network access.
- Updated canonical Russian documents and complete English translations, including previously stale branch-protection descriptions.

**Limits:** public workflows can be queried without a mandatory token only on explicit request. A workflow cannot independently confirm its own completed state while still running. T09.04 does not prove application publication; overall T09 remains PARTIAL.

## 0.0.9 — Remote annotated-tag verification and evidence-based reporting

- Added `core/release_remote.py` to check the exact remote `refs/tags/<version>` and compare the **annotated tag object SHA**, rejecting missing refs, mismatches, and network errors.
- Added `core/release_report.py` for structured JSON/Markdown evidence reports combining local Git, Release Preflight, and explicitly requested remote verification.
- By default, reporting performs no publication, build/test execution, or network access. Remote queries and executing project commands require separate explicit flags.
- Added 20 unit tests using temporary local Git repositories, including same-commit/different-tag-object, historical release, and incomplete-evidence cases.
- Added independent remote verification to the automated tagging job after annotated-tag creation.
- Updated canonical Russian docs and full English translations of ROADMAP, README, AGENTS, and the dedicated reporting guide.

**Limits:** `evidence_status=PASS` verifies only requested checks; `release_readiness` remains `NOT_VERIFIED`. External CI/artifact attestation, test adequacy, final RELEASED state and concurrency are not implemented. T09 remains PARTIAL.

## 0.0.8 — Added release preflight and explicitly authorized build/test checks

- Implemented `core/release_preflight.py`: checks VERSION and release notes in the exact commit, worktree cleanliness, and declared build/test configuration.
- Added safe default `--plan` mode, which executes no commands, and explicit `--execute` mode running only approved project-configured argv with `shell=False`.
- Added TESSERA's `release-checks.json`; the missing build artifact is explicitly NOT_APPLICABLE with an explanation, while two test suites are required.
- Added 22 test scenarios for wrong versions, missing release notes, dirty worktrees, invalid configurations, failed checks, and timeouts.
- CI performs `--plan` only, never executing arbitrary PR-supplied commands; `--execute` tests use isolated temporary Git repositories.
- Added canonical Russian documentation, complete English translations, and updated the roadmap.

**Limits:** passing checks only proves locally executed steps returned success; external CI, signatures, remote tags, and GitHub Releases are not verified. T09 remains PARTIAL and `release_readiness=NOT_VERIFIED`. T08 remains PARTIAL pending risky negative-protection tests.

## 0.0.7 — Introduced independent release evidence inspection

- Added `core/release_inspect.py`: read-only inspection of Git history, the `VERSION` file in a specific commit, and annotated tags.
- Added verification of **historical** releases using full commit SHA, without incorrectly requiring the tag to match current HEAD.
- Explicitly reports missing, lightweight, wrongly targeted tags and version mismatches.
- Added 13 unit scenarios, including checks that inspection does not modify Git state.
- Recorded the complete T08 acceptance cycle: invalid PR — FAIL, corrected PR — PASS, squash merge, verified annotated `v0.0.6`.
- Updated canonical Russian documentation, complete English translations, roadmap, and limitations.

**Limits:** the inspector does not run builds/tests or check remotes. PASS proves only tag/recorded-version consistency, not release readiness. T09 remains PARTIAL; T08 remains PARTIAL pending risky administrator and tag-protection negative tests.

## 0.0.6 — Verified rejection of invalid changes through Pull Requests

- Confirmed two active GitHub Rulesets through the API, protecting the main branch and existing tags.
- Created Pull Request #1 with an intentionally incorrect `0.0.99` version rather than `0.0.6`; `validate` failed due to a broken version transition and missing changelog entries.
- Confirmed that tagging was skipped after FAIL and the Pull Request was blocked.
- Prepared the corrected `0.0.6` and bilingual documentation for repeat validation and squash merge.
- Updated public documentation to reflect actual server-side controls without claiming unperformed tests.

**Outstanding validation:** successfully merge the corrected Pull Request and create the annotated `v0.0.6` tag; T08 remains PARTIAL until verified.

## 0.0.5 — Hardened GitHub Actions and documented Git protection

- Pinned official GitHub Actions to full commit SHAs; the validation job no longer persists Git credentials.
- Annotated tag creation now stops if remote `main` changed or existing tags cannot be checked.
- Added a static workflow-security validator and six positive/negative unit tests.
- Documented branch and tag GitHub Rulesets in canonical Russian and complete English translation.
- T08 is PARTIAL/BLOCKED: Rulesets are neither applied nor verified, and concurrent releases are not fully serialized.

## 0.0.4 — Clarified public dependency documentation

- Removed names of excluded third-party products from the current public documentation and the changelog as shown on the main branch.
- Documentation now covers only the approved stack: official GitHub CLI, minimal first-party Python tools, and free validation tools.
- Adopted a rule not to list rejected products by name in public materials.
- Kept canonical Russian documents and full English translations aligned without modifying executable components.

**Limitation:** already published Git commits were not rewritten; older document revisions remain in the repository history.

## 0.0.3 — Architecture and roadmap approved

- Expanded the single roadmap with T08–T17, priorities, prerequisites, and verifiable acceptance criteria.
- Adopted one independent Release Core with thin Codex, Harness, Claude Code, and Hermes adapters.
- Selected official GitHub CLI as the planned preferred distribution tool; retained a minimal Python offline fallback.
- Defined a minimal GitHub CLI and Python distribution stack; limited NVIDIA SkillEvaluator to free Tier 1 after isolated evaluation; excluded Tier 2/3 and mandatory paid AI APIs.
- Planned reference Agent Skills validation with `skills-ref` and separate measurement of NVIDIA Tier 1 quality and resource usage.
- Updated architecture, repository rules, and complete English translations without changing executable scripts.

**Status:** documentation and policy changes only. Planned external tools have not been installed and cross-agent integrations remain unverified.

## 0.0.2 — Skill made portable across agent hosts

- Removed the Harness-only scope of Microversion Release and documented Codex, Claude Code, Hermes, and other compatible hosts.
- Added a safe local installer with preview-first behavior and refusal to overwrite existing skills.
- Made annotated Git tags mandatory for every release, with verification of tag type, message, and target commit.
- Added a release-tag creation/verification helper and tests for missing, lightweight, and incorrect tags.
- Updated canonical Russian documentation and complete English translations. Integration with specific installed agent clients remains NOT_VERIFIED.

## 0.0.1 — Mandatory catalog microversioning introduced

- Applied the same rules to TESSERA itself as to Microversion Release: PATCH+1 for verified changes, planned `.99` release milestones, and continued `.100+` microversions for unfinished tasks.
- Introduced the canonical `VERSION` file and validation of each version transition.
- Configured automated annotated Git tags after successful validation of commits on `main`.
- Updated both Russian and English development and release instructions.
- Preserved previously added English translations, language rules, and published Git history.

**Limitation:** tag creation depends on GitHub Actions permissions. Build artifacts and GitHub Releases are not published automatically.

## 0.0.0 — Initial library (23 November 2026)

- Created the public catalog of portable Agent Skills.
- Added the first skill, Microversion Release, with rules for working microversions and release milestones.
- Documented clear, human-readable Russian commit, tag, and release descriptions.
- Added tests for version calculation and catalog structure.
- Added contribution, security, and roadmap documentation.

**Status:** initial repository state. Automatic integration with an installed Harness, build publication, and GitHub Release publication have not been verified.
