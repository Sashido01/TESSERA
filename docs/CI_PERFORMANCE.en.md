# TESSERA CI performance

[Русский — оригинал](CI_PERFORMANCE.md) | **English — translation**

## First T19.02 candidate

Move the host/Docker Gitleaks history pair into independent history_checks. All other existing checks remain in catalog_checks. Both run on the same GitHub SHA with full history, without persisted credentials, using existing pinned Actions and mandatory Docker preflight. Image and binary retain their pinned digests. No report caching or blob exclusions. Host/container compare the same reachable-local-ref snapshot within history job; unfetched remote refs are not covered. Only minimal setup is duplicated, not the audit.

Required check retains its name validate: always runs and requires result=success from both jobs. Failure, cancellation and skipped required group do not satisfy gate. tag_microversion retains needs: validate. Workflow and pinned Action guards updated and regression scenarios added. Candidate CI remains NOT_VERIFIED. Do not assign root microversion until integration slot.

Baseline main 45568501762: 943 s; history 488 s. PR 45569400436: 700 s; history 345 s. Ideal calculation without overhead — max(488,455)=488 s and max(345,355)=355 s; not a forecast of actual speed. Two runners may queue; setup and catalog growth affect time. Acceptance: compare real p50/p95 and queue/runner-minutes on comparable runs, demonstrate both groups mandatory and tag. If no improvement, measure cause; do not add complexity for job count.

Local Bash control (25 November 2026): all 16 success/failure/cancelled/skipped combinations PASS, only success/success accepted; missing either variable rejected (2/2). This proves command logic, not GitHub scheduling. Add repeatable CI control and named-job checking in Release Core.

## T19.03 — second parallelization candidate

Main v0.0.69 (CI 45584865396): 625 s through validate, catalog 621 s, history 401 s. Four independent Gitleaks source/path steps took 111+66+25+25=227 s; integrated NVIDIA Tier 1 (129 s) remains in catalog. Move only the four steps into source_secret_checks, preserving host/container pairs in one job, exact SHA, full checkout, pinned Gitleaks and Docker preflight; catalog retains Gitleaks for integrated Tier 1 and Go checks. History and tag job unchanged byte-for-byte. Required validate demands success of three groups. Tests cover 64 status combinations (4³), three missing variables, mandatory source scope and three-group independent report. Historical two-group reports remain compatible; presence of source job requires both original groups. Without checking historical workflow configuration a wholly omitted new group in forged API data is not detected by this report; live gate mandatory. Idealized maximum without overhead: max(621−227,401,227)=401 s, not forecast. Third runner adds usage and may queue; accept only with live CI and measurements. NOT_VERIFIED, no version assigned.
