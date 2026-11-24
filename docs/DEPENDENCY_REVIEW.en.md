# T12.02.02.04 — dependency and license review

[Русский — оригинал](DEPENDENCY_REVIEW.md) | **English — translation**

Only public package identifiers and exact versions are used. [OSV querybatch](https://google.github.io/osv.dev/post-v1-querybatch/) is a free API without LLM or token, POST requests to a fixed HTTPS endpoint, strict response size and pagination coverage validation. Negative control checks known advisories of an old requests release without installing it. No source code, owner Git data or keys are sent. Network or schema failure blocks the check; no records does not guarantee absence of vulnerabilities.

Python: independent inventory of all installed distributions in pinned NVIDIA Tier 1 and SkillSpector environments; for skills-ref, exact active hash-pinned requirements. Query upstream commit SHA separately. License-Expression, known legacy declarations, classifiers and license file record counts are metadata-level evidence, not a legal compatibility analysis.

Go: read build info of SHA-256-verified gh 2.105.0 and Gitleaks 8.30.1 using go version -m (never execute audited binaries), verify root module, exact dependencies, replacements and available VCS revision. Query OSV for actual Go modules, stdlib/toolchain and pinned upstream SHAs. Go module licenses are external metadata from [deps.dev API v3](https://docs.deps.dev/api/v3/), data source CC-BY 4.0; empty/unavailable results explicitly UNKNOWN/NOT_VERIFIED. Go parser is a preinstalled CI tool, version recorded; not an additional runtime skill dependency.

Findings advisory until reviewed; an OSV ID is not evidence of reachable vulnerable code and no ID is not proof of security. Full license analysis, native non-Go components and vulnerabilities outside databases remain NOT_VERIFIED. Actual acceptance required; no paid API, Tier 2/3 or automatic dependency remediation.

Go build metadata can contain a `(devel)` dependency. If a versioned replacement is present, audit that replacement; otherwise record the module as an explicit unversioned coverage gap. Never query a guessed version. Other unknown version formats fail closed. A successful execution with unresolved modules means PARTIAL coverage, not complete CVE coverage.
