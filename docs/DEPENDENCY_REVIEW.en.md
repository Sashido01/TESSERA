# T12.02.02.04 — dependency and license review

[Русский — оригинал](DEPENDENCY_REVIEW.md) | **English — translation**

Only public package identifiers and exact versions are used. [OSV querybatch](https://google.github.io/osv.dev/post-v1-querybatch/) is a free API without LLM or token, POST requests to a fixed HTTPS endpoint, strict response size and pagination coverage validation. Negative control checks known advisories of an old requests release without installing it. No source code, owner Git data or keys are sent. Network or schema failure blocks the check; no records does not guarantee absence of vulnerabilities.

Python: independent inventory of all installed distributions in pinned NVIDIA Tier 1 and SkillSpector environments; for skills-ref, exact active hash-pinned requirements. Query upstream commit SHA separately. License-Expression, known legacy declarations, classifiers and license file record counts are metadata-level evidence, not a legal compatibility analysis.

Go: read build info of SHA-256-verified gh 2.105.0 and Gitleaks 8.30.1 using go version -m (never execute audited binaries), verify root module, exact dependencies, replacements and available VCS revision. Query OSV for actual Go modules, stdlib/toolchain and pinned upstream SHAs. Go module licenses are external metadata from [deps.dev API v3](https://docs.deps.dev/api/v3/), data source CC-BY 4.0; empty/unavailable results explicitly UNKNOWN/NOT_VERIFIED. Go parser is a preinstalled CI tool, version recorded; not an additional runtime skill dependency.

Findings advisory until reviewed; an OSV ID is not evidence of reachable vulnerable code and no ID is not proof of security. Full license analysis, native non-Go components and vulnerabilities outside databases remain NOT_VERIFIED. Actual acceptance required; no paid API, Tier 2/3 or automatic dependency remediation.

Go build metadata can contain a `(devel)` dependency. If a versioned replacement is present, audit that replacement; otherwise record the module as an explicit unversioned coverage gap. Never query a guessed version. Other unknown version formats fail closed. A successful execution with unresolved modules means PARTIAL coverage, not complete CVE coverage.

## Actual Python review and remediation candidates

[CI 45370973461](https://github.com/Sashido01/TESSERA/actions/runs/45370973461): 4 skills-ref, 21 SkillEvaluator and 72 SkillSpector distributions checked, plus one upstream commit per environment. OSV negative controls passed. Findings in SkillSpector only: cryptography 49.0.0 (GHSA-g6cj-pr64-35w5 / PYSEC-2026-3552, same CVE-2026-69247), langgraph 1.2.6 (GHSA-3fx2-cqw9-xr3c), pyasn1 0.6.4 (GHSA-2qm8-x737-gmw5, GHSA-9m75-vc3g-4x39, GHSA-fm9c-5rcf-2q5p, GHSA-mm57-4v3p-rchx). Two license metadata UNKNOWN. No findings in the two other environments; this is not a security guarantee.

Official advisories identify patched versions [cryptography 50.0.0](https://github.com/pyca/cryptography/security/advisories/GHSA-g6cj-pr64-35w5), [langgraph 1.2.14 and SDK 0.4.6](https://github.com/advisories/GHSA-3fx2-cqw9-xr3c), and [pyasn1 0.6.5](https://github.com/advisories/GHSA-2qm8-x737-gmw5). Upstream [SkillSpector v2.13.7 lock](https://github.com/NVIDIA/SkillSpector/blob/v2.13.7/uv.lock) already selects cryptography 50.0.2, langgraph 1.2.20, SDK 0.4.10 and pyasn1 0.6.5. Candidate for separate verified upgrade, not an automatic dependency replacement. Reachability in static no-LLM execution and absence of other advisories in the new environment remain NOT_VERIFIED. Go review still BLOCKED at metadata completeness; distinguish absent root, zero dependencies and count limit without exposing local paths.

CI 45373906360 observed gh: one mod row, 154 dep rows; Gitleaks: zero mod rows, 66 dep rows including one unversioned. Upstream v8.30.1 .goreleaser.yml builds main.go; a synthetic local Go 1.23.2 file build reproduced path command-line-arguments, no mod row and root dep (devel). The exception is restricted to that pinned Gitleaks archive, exact entrypoint and root dependency. The checker independently hashes both pinned archives and compares exact member bytes with the binary before reading build metadata. The root release version is taken from verified archive release metadata, not claimed as embedded build metadata. Remaining unversioned dependencies stay PARTIAL. Actual CI still required.

## Actual Go acceptance

[CI 45375135316](https://github.com/Sashido01/TESSERA/actions/runs/45375135316) PASS: 477+19 tests; 97 Python package checks, 3 packages with OSV entries; 212 distinct Go modules (gh 155, Gitleaks 66), 8 affected modules across the binaries, Gitleaks stdlib/toolchain and one source-commit entry; 211 Go licenses reported by deps.dev, one NOT_INDEXED. T12.02.02.04 COMPLETE within inventory/query execution scope; CVE remediation, code reachability and legal compatibility remain open.

- Both official archive digests and member bytes match; all recorded module versions are covered (no unresolved modules). gh source revision MATCH, Go 1.27.4. Gitleaks root release identity from pinned archive, VCS revision NOT_RECORDED, Go 1.24.11.
- gh: github.com/gorilla/websocket v1.5.3 (GO-2026-6278).
- Gitleaks: github.com/andybalholm/brotli v1.1.2-0.20250424173009-453214e765f3, github.com/klauspost/compress v1.17.11, github.com/nwaples/rardecode/v2 v2.1.0, github.com/ulikunitz/xz v0.5.12, golang.org/x/crypto v0.35.0, golang.org/x/sys v0.30.0, golang.org/x/text v0.22.0. 117 advisory identifiers including stdlib/toolchain, plus CVE-2026-124039 in source-commit query. Aliases can overlap; do not count identifiers as independent vulnerabilities.
- License gaps: tiktoken 0.13.0 and tqdm 4.68.3 UNKNOWN in installed Python metadata; github.com/STARRY-S/zip v0.2.1 NOT_INDEXED by deps.dev. License file entries exist for both Python packages, not yet substantively reviewed.
- As of 2026-11-24 the GitHub API latest stable releases are gh v2.105.0 and Gitleaks v8.30.1. No newer official stable binary established by this check. Evaluate exposure, patched upstream sources and bounded scanner execution; do not silently replace releases or suppress findings. SkillSpector 2.13.7 is a separate upgrade candidate.
- Go direct review 4.84 s. Evidence remains point-in-time, not a vulnerability-free claim.
