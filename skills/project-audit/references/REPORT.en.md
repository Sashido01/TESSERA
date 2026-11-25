# Report template

[Русский — оригинал](REPORT.md) | **English — translation**

## R1. Context
Goal, source, snapshot, profile, mode, authorization, limitations, initial and final state.

## R2. Coverage
For each direction: applicability (reason), inspected scope, status (checked/partial/not checked/not applicable), evidence, remaining work. Fully checked directions / applicable directions; partial separately. If denominator unknown do not calculate a percentage. Coverage is not readiness.

## R3. Requirement matrix
ID, source, criterion, implementation, test, evidence, status, confidence, remainder. A test file is not a run result. A component without a trace to the goal warrants investigation, not an automatic defect.

## R4. Findings
ID, priority (P0 critical/blocking, P1 material, P2 improvement), scope, observation, evidence, consequence, confidence, challenge, recommendation, correction criterion. Separate hypotheses and refuted findings.

## R5. Checks and risks
Commands, actual results, skips, environment and snapshot; historical reports separately. Include risks, blockers, unverified areas and owner actions.

## R6. Plan
Task, priority, dependencies, acceptance criterion, access, independent work. Do not invent features. An audit is not a completed fix. Identify release-blocking criteria separately.

If authorized to save separate reports, use Markdown and JSON/JSONL. Automated generation and strict schema are not implemented yet.
