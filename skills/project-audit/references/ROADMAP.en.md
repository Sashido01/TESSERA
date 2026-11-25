# Project Audit evolution

[Русский — оригинал](ROADMAP.md) | **English — translation**

| Level | Scope | Candidate status |
|---|---|---|
| I | Instructions, directions, evidence, report, scenarios | PARTIAL: source exists; actual agent not verified |
| II | Deterministic inventory, Git, evidence register | PARTIAL: inventory accepted in PR #71; Git Inspector candidate; evidence core open |
| III | Pluggable analyzers, graphs, traceability | NOT_STARTED |
| IV | Cross-session state, DELTA, freshness | NOT_STARTED |
| V | Independent challenge, semantic indexes, formal methods | NOT_STARTED |

Next acceptance: reference Agent Skills validator, TESSERA static checks, actual installation and activation in Codex and DeepSeek Harness, E01–E20 with comparison. No mandatory paid APIs. Seven logical graphs (structure, semantics, dependencies, requirements, checks, history, evidence) are planned, not implemented. Independent release requires mandatory checks and the exact annotated tag.

Git Inspector — next level II candidate, 13/13 local Linux tests; four exact Git blobs retested and transferred. Two observations do not establish an atomic snapshot or content hash. Release Core v0.0.70 verified, Inventory Engine PR #71 merged; main CI and tag v0.0.71 still require verification. Next separate component — Evidence Core: strict links between observation, SHA/digest and evidence scope, explicit UNKNOWN/STALE, no claim of full integrity. Full CI and native Windows remain open.
