# Project Audit evolution

[Русский — оригинал](ROADMAP.md) | **English — translation**

| Level | Scope | Candidate status |
|---|---|---|
| I | Instructions, directions, evidence, report, scenarios | PARTIAL: source exists; actual agent not verified |
| II | Deterministic inventory, Git, evidence register | PARTIAL: inventory candidate; Git and evidence core open |
| III | Pluggable analyzers, graphs, traceability | NOT_STARTED |
| IV | Cross-session state, DELTA, freshness | NOT_STARTED |
| V | Independent challenge, semantic indexes, formal methods | NOT_STARTED |

Next acceptance: reference Agent Skills validator, TESSERA static checks, actual installation and activation in Codex and DeepSeek Harness, E01–E20 with comparison. No mandatory paid APIs. Seven logical graphs (structure, semantics, dependencies, requirements, checks, history, evidence) are planned, not implemented. Independent release requires mandatory checks and the exact annotated tag.

Next independent level II component — Git Inspector: local candidate and 13/13 Linux tests prepared on 25 November 2026; not included in current inventory release. Two Git observations do not establish an atomic snapshot or content hash. Integrate separately after Inventory Engine. Local preflight plan added for the current candidate, depending on acceptance of PR #70; full CI and native Windows remain open.
