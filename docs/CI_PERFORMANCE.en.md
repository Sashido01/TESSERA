# TESSERA CI performance

[Русский — оригинал](CI_PERFORMANCE.md) | **English — translation**

## First T19.02 candidate

Move the host/Docker Gitleaks history pair into independent history_checks. All other existing checks remain in catalog_checks. Both run on the same GitHub SHA with full history, without persisted credentials, using existing pinned Actions and mandatory Docker preflight. Image and binary retain their pinned digests. No report caching or blob exclusions. Host/container compare the same reachable-local-ref snapshot within history job; unfetched remote refs are not covered. Only minimal setup is duplicated, not the audit.

Required check retains its name validate: always runs and requires result=success from both jobs. Failure, cancellation and skipped required group do not satisfy gate. tag_microversion retains needs: validate. Workflow and pinned Action guards updated and regression scenarios added. Candidate CI remains NOT_VERIFIED. Do not assign root microversion until integration slot.

Baseline main 45568501762: 943 s; history 488 s. PR 45569400436: 700 s; history 345 s. Ideal calculation without overhead — max(488,455)=488 s and max(345,355)=355 s; not a forecast of actual speed. Two runners may queue; setup and catalog growth affect time. Acceptance: compare real p50/p95 and queue/runner-minutes on comparable runs, demonstrate both groups mandatory and tag. If no improvement, measure cause; do not add complexity for job count.
