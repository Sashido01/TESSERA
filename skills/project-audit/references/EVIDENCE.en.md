# Evidence protocol

[Русский — оригинал](EVIDENCE.md) | **English — translation**

## Local register

When useful, validate an explicitly supplied JSON file with [Evidence Core](EVIDENCE_CORE.en.md). This checks register structure, references and binding to the declared snapshot; it does not collect evidence from the project. `PASS_RECORDED` and `FAIL_RECORDED` mean only that such entries exist; conflicts are retained. Source authenticity, completeness, project integrity and actual execution remain `NOT_VERIFIED`.

## Sources
Distinguish source observation, an actual check result, external/owner-reported evidence and auditor inference. Record ID, source, coordinates, audited snapshot, time, scope and limitations. For execution also record reviewed command, tool version, environment, exit code, result and digest of available output. Do not preserve secrets or private data.

## Confidence and status
Confidence: CONFIRMED — directly supported; SUPPORTED — indirect evidence; HYPOTHESIS — needs verification; REFUTED — disproved; NOT_VERIFIED — insufficient evidence.
Implementation: COMPLETE, PARTIAL, NOT_IMPLEMENTED, NOT_STARTED, BLOCKED, NOT_VERIFIED, NOT_APPLICABLE. COMPLETE requires evidenced acceptance criteria. Failure to find an implementation is not proof of absence under incomplete search.

## Freshness
Bind evidence to SHA and working state when available; otherwise state the limitation. Account for local changes, configuration, dependencies, test suite and environment. Historical CI on another SHA does not prove a new snapshot. If sources changed, mark STALE and repeat applicable checks or retain NOT_VERIFIED.

## Contradictions
Compare docs, defaults, implementation, tests and actual outcomes. Preserve both sides when they conflict. Challenge material findings with counterexamples or alternative explanations; state limits if unavailable. A successful build, tag or static scan alone is not proof of product behavior.
