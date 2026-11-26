# Project Audit evolution

[Русский — оригинал](ROADMAP.md) | **English — translation**

| Level | Scope | Candidate status |
|---|---|---|
| I | Instructions, directions, evidence, report, scenarios | PARTIAL: source exists; actual agent not verified |
| II | Deterministic inventory, Git, evidence register | PARTIAL: Inventory and Git Inspector accepted in the catalog; Evidence Core accepted in 0.0.4 |
| III | Pluggable analyzers, graphs, traceability | NOT_STARTED |
| IV | Cross-session state, DELTA, freshness | PARTIAL — planner candidate, no evidence reuse |
| V | Independent challenge, semantic indexes, formal methods | NOT_STARTED |

Next acceptance: reference Agent Skills validator, TESSERA static checks, actual installation and activation in Codex and DeepSeek Harness, E01–E20 with comparison. No mandatory paid APIs. Seven logical graphs (structure, semantics, dependencies, requirements, checks, history, evidence) are planned, not implemented. Independent release requires mandatory checks and the exact annotated tag.

Git Inspector was accepted in TESSERA v0.0.76 / Project Audit 0.0.3; the full native Windows suite was accepted in PR #74. Evidence Core was accepted in Project Audit 0.0.4: explicit schema, exact scopes and binding to a declared snapshot, with conflicting PASS/FAIL retained. Its 15 tests passed on Windows 11 / Python 3.14.3. Main CI 45658775191 SUCCESS, annotated project-audit/v0.0.4 → be6a126f08ffbb49b721b50e030b2a6d82c7d4f3. Actual agent use NOT_VERIFIED.
