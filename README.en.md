# TESSERA

[Русский — основной язык](README.md) | **English — translation**

**A shared library of skills for AI agents.** Each skill is a standalone module that can be used, tested, and developed independently.

TESSERA is not a fork of Harness or Codex. It stores portable [Agent Skills](https://agentskills.io/) instructions, scripts, and integration examples. Compatibility and automatic activation must be verified for each specific agent environment.

## Skill catalog

| Skill | Purpose | Status |
| --- | --- | --- |
| [Microversion Release](skills/microversion-release/README.en.md) | Microversions, mandatory annotated release tags, portable use across agents | Standard skill and local helpers prepared; individual agent clients are not yet verified |
| [Project Audit](skills/project-audit/README.en.md) | Evidence-based audit, requirements, architecture, tests and remaining work | 0.0.2, level II candidate with Inventory Engine; agent behavior and independent release NOT_VERIFIED |
| [Repository Workflow](skills/repository-workflow/README.en.md) | Local Git and GitHub, independent tasks, CI, integration and technical debt | 0.0.1, sources and local planner tests; agent acceptance NOT_VERIFIED |

## Repository layout

```text
skills/                 Independent skills, each with a SKILL.md
tools/                  Shared validation tools
docs/                   Rules, architecture, and roadmap
.github/workflows/      Automated checks on changes
```

## Getting started

1. Open the skill you need under `skills/` and read its `README.en.md` or the canonical `README.md` in Russian.
2. Install the **entire skill directory** into your agent's skills directory—not just its `SKILL.md`.
3. Verify that your agent discovers the skill. Automatic activation depends on the agent's configuration.
4. Review repository rules and permissions before allowing an agent to create commits, tags, or published releases.

For Microversion Release, see the [installation guide](skills/microversion-release/README.en.md).

## Validation

Python 3 is required; there are no third-party Python dependencies.

```bash
python tools/validate_skills.py
python tools/check_public_paths.py
python tools/check_translations.py
python tools/check_repository_version.py
python -m unittest discover -s tests -v
python tools/run_skill_tests.py
```

The following version calculator has no side effects:

```bash
python skills/microversion-release/scripts/next_version.py 0.0.99 --mode work
python skills/microversion-release/scripts/next_version.py 0.0.100 --mode release
```

These commands print `0.0.100` and `0.1.0`, respectively. **The second command only calculates a number**; it does not confirm task completion or a successful build.

## Safe official GitHub CLI local installation check

CI tests actual `gh skill install --from-local --dir` followed by `gh skill list` on a temporary skill copy. **Low-level InstallLocal lacks an overwrite check; the CLI checks existing destinations.** Use a fresh directory and an independent guard. Remote `--pin` installation was verified in T10.02. [Details](docs/GH_SKILL_INSTALL.en.md).

**T09.10 — COMPLETE:** the real v0.0.21 ZIP was signed and independently verified (SHA-256, manifest, Sigstore/SLSA). [Evidence](docs/TRUSTED_BUILD.en.md). Acceptance applies only to that file, not later versions. No GitHub Release was created.

## Official GitHub CLI validation without publication

CI additionally runs SHA-256-pinned official `gh 2.105.0` with `gh skill publish --dry-run` on a temporary, tokenless `skills/` snapshot without a GitHub remote. It verifies valid and invalid formats without creating a GitHub Release. It does not validate remote publication readiness. See [GH_SKILL_PUBLISH_DRY_RUN](docs/GH_SKILL_PUBLISH_DRY_RUN.en.md).

## Agent Skills reference validation

CI additionally runs the [pinned upstream `skills-ref` validator](docs/AGENT_SKILLS_STANDARD.en.md) with SHA-256-locked dependencies. This checks format only; it does not establish actual skill activation in agent hosts. Independent `gh skill publish --dry-run` is still NOT_VERIFIED.

## Versioning

**Current catalog version:** see [`VERSION`](VERSION). From this point forward, every independently verified change to TESSERA must increment the catalog microversion, update both changelogs, and use a clear, human-readable Russian commit title. After successful GitHub Actions checks, an annotated `vX.Y.Z` Git tag is created. GitHub Releases are not published automatically.

- **The TESSERA catalog** and **each skill** have independent version histories.
- Work microversions increase PATCH by one. After `.99`, work may continue with `.100`, `.101`, and so on if the task is unfinished.
- After completion and successful mandatory checks, planned milestones are `0.0.99 → 0.1.0`, `0.1.99 → 0.2.0`, and `0.99.99 → 1.0.0`.
- Do not create dummy commits or releases to reach a preferred number. New projects start at `0.0.0`; never rewrite published tags or history.
- Individual skill tags may use namespaces such as `microversion-release/v0.1.0` to avoid collisions with catalog-wide tags.

See the [version policy](docs/VERSIONING.en.md). The historical `0.0.0` baseline is preserved. Mandatory versioning begins at `0.0.1` without rewriting previous commits. No separate build artifacts or GitHub Releases have been published.

## Support for different agent hosts

The first skill uses the common Agent Skills format and can be installed into **Codex, DeepSeek Harness, Claude Code, Hermes**, and other compatible environments. See the [integration guide](skills/microversion-release/references/INTEGRATION.en.md) and the safe installer with a default preview mode. Hermes can also use TESSERA as a skills tap.

An application release **is not complete without a verified annotated Git tag**. Check it with `python skills/microversion-release/scripts/release_tag.py verify 0.1.0 --repo <project-root>`. The script does not replace build and test verification. Actual auto-activation in all agent clients has not been confirmed.

## Roadmap and constraints

The [complete T00–T17 roadmap](docs/ROADMAP.en.md) sets out verifiable steps for Git protection, one shared Release Core, skill distribution, and agent integration. The [dependency policy](docs/DEPENDENCIES.en.md) defines the approved stack: official GitHub CLI as the **planned preferred distribution mechanism after real-world verification**, plus a minimal Python installer for offline use and custom profiles.

NVIDIA SkillEvaluator is permitted **only at Tier 1**, after compatibility and resource evaluation without paid AI APIs. Tier 2 and Tier 3 must not be used. The reference `skills-ref` validator is planned for standard-format checks; TESSERA's own microversion and tagging tests remain mandatory.

**CI security:** all external GitHub Actions are pinned to reviewed full SHAs and use Node.js 24. `tools/check_actions_runtime.py` checks exact pins and action inventory. See [GITHUB_SECURITY](docs/GITHUB_SECURITY.en.md). Live signed ZIP remains NOT_VERIFIED.

## GitHub protection

The [Rulesets setup guide](docs/GITHUB_SECURITY.en.md) documents branch and tag protection. **Rulesets are active:** Pull Requests, `validate`, and an up-to-date branch are required, and published tags are protected. The negative CI acceptance test behaved as expected. Both negative and positive Pull Request cases and creation of a new annotated tag are verified. Destructive tag-rewrite tests have not been performed.

## Independent release verification

T09 begins with a [read-only Git evidence inspector](docs/RELEASE_CORE.en.md). It validates a version and annotated tag against an exact commit without modifying the repository. **It does not establish build success or release readiness**; those checks are future work.

## Release preflight

A [Release Preflight](docs/RELEASE_PREFLIGHT.en.md) and a `release-checks.json` plan are available. By default it only validates configuration, version, and release notes: `python core/release_preflight.py --repo . --version 0.0.8 --plan`. Running build/test commands requires explicit `--execute` with a trusted configuration. The result **does not prove publication of a release**.

## Evidence reports and remote tags

[T09.03](docs/RELEASE_REPORT.en.md) documents verification of an annotated tag object SHA on a Git remote and machine/human-readable evidence reports. By default, reporting is local and runs no project commands; network queries require `--verify-remote`, and build/test execution requires `--execute-checks`. **PASS covers only explicitly requested checks, not application release readiness.**

## Completed GitHub Actions verification

[T09.04](docs/RELEASE_CI.en.md) adds independent verification of a completed GitHub Actions run by exact commit SHA and required jobs. Explicit `--verify-ci`, a trusted repository and run ID are required. No paid AI APIs are involved; network queries are disabled by default. `CI_VERIFIED` is not RELEASED.

## GitHub Release publication and evidence certificates

[T09.05](docs/RELEASE_PUBLICATION.en.md) introduces independent verification of published GitHub Release metadata and a reproducible unsigned evidence certificate. Git tags plus passing CI do not amount to a GitHub Release. `--verify-publication` and `--format certificate` do not publish a release or verify downloaded file contents. **No TESSERA GitHub Releases were present at the time of inspection**; automatic publication is not included.

## Actual release asset byte verification

[T09.06](docs/RELEASE_ASSETS.en.md) adds streaming size/SHA-256 verification of real attached GitHub Release assets, enabled **only explicitly** with `--verify-publication --verify-assets`. The verifier writes no files. Independent build provenance and application readiness remain `NOT_VERIFIED`. TESSERA has no GitHub Releases at the time of the check, so live end-to-end acceptance remains open.

## Signed artifact provenance verification

[T09.07](docs/RELEASE_PROVENANCE.en.md) adds independent GitHub Sigstore/SLSA attestation verification through the **official GitHub CLI**. It requires a real local release asset, verified publication metadata, exact source commit SHA, and an explicitly trusted signing workflow. Disabled by default. **No GitHub Release asset exists yet; live verification of that distribution mechanism remains NOT_VERIFIED. The signed v0.0.21 Actions Artifact was separately verified in T09.10.**

**Security:** attestation verification requires GitHub CLI `2.102.0+`; vulnerable or unrecognized versions fail closed. The genuine signed v0.0.21 catalog ZIP has been verified. See [RELEASE_PROVENANCE](docs/RELEASE_PROVENANCE.en.md).

## Genuine catalog source package and trusted build

[T09.08](docs/TRUSTED_BUILD.en.md) introduces a deterministic Agent Skills source ZIP with a checkable `MANIFEST.json` and a separate opt-in GitHub attestation workflow. Signing requires **manual dispatch at an annotated release tag** and does not create a GitHub Release. Live signing and independent verification passed for v0.0.21. Other versions require separate acceptance. The [branch policy](docs/BRANCHING.en.md) states: one branch per coherent goal/PR, not per intermediate change.

## Independent offline catalog ZIP verification

The [T09.09 verifier](docs/CATALOG_VERIFICATION.en.md) checks a downloaded source ZIP without extraction: archive members, MANIFEST.json, actual SHA-256 bytes, and an externally supplied commit SHA. This **does not** establish a GitHub signature or publication. Live attestation and end-to-end ZIP verification passed separately in T09.10 for v0.0.21.

## Contributing

See [contribution guidelines](CONTRIBUTING.en.md), [security policy](SECURITY.en.md), [changelog](CHANGELOG.en.md), [community rules](CODE_OF_CONDUCT.en.md), and the [MIT license](LICENSE).

**Important:** neither SKILL.md nor the version calculator guarantees execution after every agent action. Enforced checks require project-level rules or an event-based integration.

## Languages

**Russian is the source of truth.** Create and review the Russian documentation first, then update the corresponding English translation within the same change. See the [translation policy](docs/I18N.en.md).

---
Original project: [Sashido01/TESSERA](https://github.com/Sashido01/TESSERA).

**T10.02 — COMPLETE:** isolated remote install with official `gh 2.105.0` using a fully qualified Git ref and SHA, file and metadata checks, pinned update --dry-run and duplicate refusal. [Live CI PASS](https://github.com/Sashido01/TESSERA/actions/runs/45351217500). [Details](docs/GH_SKILL_INSTALL.en.md). Agent-client activation remains unverified.

**T10.03.01 — COMPLETE (harness):** actual update and guarded staged re-pin harness; local edits block the guarded transition. Native update is tested against synthetic edits. [Live CI PASS](https://github.com/Sashido01/TESSERA/actions/runs/45352932764); native local-edit removal confirmed. Do not apply this harness to user profiles. [Details](docs/GH_SKILL_INSTALL.en.md).

**T10.03.02:** local fixture for independent skill tags and actual official gh installation/collisions; [Live CI PASS](https://github.com/Sashido01/TESSERA/actions/runs/45354011607) for the local fixture. T10.03.02 PARTIAL: remote namespaced pin and T16 remain unverified. [Details](docs/GH_SKILL_INSTALL.en.md).

**T12.01 — COMPLETE within schema/quality:** focused NVIDIA SkillEvaluator 1.2.0 evaluation (schema/quality, --no-llm, advisory), [live CI PASS: 75/100](https://github.com/Sashido01/TESSERA/actions/runs/45358283596). [Scope and dependencies](docs/NVIDIA_TIER1.en.md). Full Tier 1 unverified; Tier 2/3 forbidden.

**T12.02.01:** [NVIDIA local static checks and profiles](docs/NVIDIA_STATIC_REVIEW.en.md), no LLM; default and localized quality, PII/license/unicode/lint, six simulated profiles. [Live CI PASS](https://github.com/Sashido01/TESSERA/actions/runs/45360122208): 75.0/78.8, 18/16 findings; T12.02.01 COMPLETE within fixture scope. Not actual agent execution. T12.02 PARTIAL.

**T12.02.02.01:** [direct Bandit review](docs/BANDIT_REVIEW.en.md) COMPLETE within direct scan execution scope. [CI 45365133732](https://github.com/Sashido01/TESSERA/actions/runs/45365133732) PASS: 414+19 tests, 60 Python files, 87 findings (45 runtime, 42 tests; 2 medium, 85 low, 0 high); clean and negative fixtures PASS; direct review 1.69 s. Full NVIDIA code-integrity and other scanners remain unverified.

**T12.02.02.02:** [Gitleaks](docs/GITLEAKS_REVIEW.en.md) — [CI 45367459045](https://github.com/Sashido01/TESSERA/actions/runs/45367459045) PASS: 428+19 tests, 144/144 tracked UTF-8 files, 998544 bytes, zero findings, positive/negative and redaction fixtures PASS; 65.29 s. Snapshot acceptance COMPLETE; history/path-specific rules NOT_VERIFIED; T12.02.02.02 remains PARTIAL.

**0.0.30:** [CI 45368434188](https://github.com/Sashido01/TESSERA/actions/runs/45368434188) PASS: 437+19 tests; 585/585 distinct UTF-8 blobs, 5431003 bytes, zero findings, removed-marker fixture PASS, 128.81 s. [CI 45369335974](https://github.com/Sashido01/TESSERA/actions/runs/45369335974) PASS: 443+19 tests; 598 distinct UTF-8 blobs, 5639755 bytes, zero findings; five synthetic rule fixtures PASS; 4 current YAML files and 28 historical rule/blob pairs across 37 commits, zero findings. T12.02.02.02 COMPLETE within declared scope.

**T12.02.02.03:** [direct static SkillSpector 2.13.6](docs/SKILLSPECTOR_REVIEW.en.md), [CI 45370414762](https://github.com/Sashido01/TESSERA/actions/runs/45370414762) PASS: 454+19 tests; 16/16 files, 100% coverage, complete_with_caveats (4 reference_missing), risk 78/100 HIGH, exit 1 (threshold 50 exceeded), 12 findings (10 MEDIUM, 2 HIGH), zero suppressions, both synthetic fixtures PASS, 13.32 s. T12.02.02.03 COMPLETE within direct static execution scope; findings and full NVIDIA security acceptance remain open.

**T12.02.02.04:** [dependency and license metadata review](docs/DEPENDENCY_REVIEW.en.md) — [CI 45375135316](https://github.com/Sashido01/TESSERA/actions/runs/45375135316) PASS: 477+19 tests; 97 Python package checks, 3 packages with OSV entries; 212 distinct Go modules (gh 155, Gitleaks 66), 8 affected modules across the binaries, Gitleaks stdlib/toolchain and one source-commit entry; 211 Go licenses reported by deps.dev, one NOT_INDEXED. T12.02.02.04 COMPLETE within inventory/query execution scope; CVE remediation, code reachability and legal compatibility remain open.

**T12.03.01:** [portable skill license and references](docs/SKILL_PORTABILITY.en.md); live CI pending.

[CI 45373618225](https://github.com/Sashido01/TESSERA/actions/runs/45373618225): 486+19 tests PASS. SkillSpector 2.13.6: complete, 17/17 files, 100%, reference_missing 4→0, risk 78→36 (HIGH→MEDIUM), HIGH 2→0, MEDIUM 10, zero suppressions, both fixtures PASS, 19.40 s. NVIDIA: license allowed, RU quality 80.0 (65×0.35 + 80×0.25 + 95×0.25 + 90×0.15), Codex custom provider degraded→loads. Overall CI FAIL only at inherited Go review; release and real activation NOT_VERIFIED.

**T12.03.02:** [CI evidence network restriction](docs/RELEASE_CI_SECURITY.en.md) — [CI 45376483433](https://github.com/Sashido01/TESSERA/actions/runs/45376483433) PASS: 493+19 tests, four new regressions PASS, Bandit B310 absent in the repeat review; 110 findings (no HIGH), no rule suppression. T12.03.02 COMPLETE within implemented control and CI scope; live network execution separately NOT_VERIFIED.

**T12.03.03:** [SkillSpector 2.13.7 security upgrade](docs/SKILLSPECTOR_UPGRADE.en.md) — [CI 45376675127](https://github.com/Sashido01/TESSERA/actions/runs/45376675127) PASS: 494+19 tests; SkillSpector 2.13.7, 17/17 files, complete, 100%, 16 MEDIUM (AE4 6, AST3 6, AST4 3, LP3 1), zero HIGH, risk 53/100 HIGH, exit 1, zero suppressions, both fixtures PASS, 11.37 s. OSV: 74 Python distributions, zero packages with entries, zero source-commit entries; cryptography 50.0.2, langgraph 1.2.20, pyasn1 0.6.5. T12.03.03 COMPLETE within upgrade and repeat OSV scope; new AST3 and threshold exceedance remain open. Release awaits sequential acceptance.


**T12.03.02 regression correction:** Before merge, a shared get_public_json regression was found: the original strict URL allowlist blocked the existing GitHub Release metadata call. Permit only the canonical /releases/tags/vMAJOR.MINOR.PATCH route and one namespace encoded as %2F; arbitrary escaping, extra paths and parameters remain forbidden. Three regressions exercise verify_github_publication through the actual shared transport (ordinary and namespaced tag), changed response URL rejection and invalid routes. Only networking is mocked, validation and response handling are real. Historical PASS missed this defect; repeat acceptance is required.
