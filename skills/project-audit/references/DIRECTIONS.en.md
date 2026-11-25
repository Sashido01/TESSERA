# Audit directions

[Русский — оригинал](DIRECTIONS.md) | **English — translation**

In FULL/DEEP consider all A01–A30; in FAST identify selected directions. Record applicability, scope and evidence. Lack of access does not mean non-applicability.

| ID | Direction / scenario | Check / criterion |
|---|---|---|
| A01 | Goals | Purpose, success criteria |
| A02 | Requirements | Register, conflicts, acceptance criteria |
| A03 | Roadmap | Statuses, dependencies, gaps |
| A04 | Inventory | Files, assets, languages, entry points |
| A05 | History | Decisions and goal changes |
| A06 | Architecture | Boundaries, relations, responsibilities |
| A07 | Functionality | Claimed versus actual behavior |
| A08 | Code quality | Defects, types, complexity |
| A09 | Technical debt | Duplication, dead code, stubs |
| A10 | Storage | Integrity, migrations, recovery |
| A11 | Failures | Error handling and data loss |
| A12 | Performance | Speed, resources, load |
| A13 | Concurrency | Races, locks, cancellation |
| A14 | UX | Interface states, accessibility |
| A15 | Compatibility | OS, versions, devices |
| A16 | Unit tests | Execution and assertion strength |
| A17 | Integrations | Component interactions |
| A18 | E2E | User scenarios |
| A19 | Negative cases | Failures, invalid input |
| A20 | Requirement coverage | Criteria, tests, evidence links |
| A21 | Security | Permissions, trust boundaries, leaks |
| A22 | Dependencies | Versions, licenses, advisory applicability |
| A23 | Git | Snapshot, history, branches, tags |
| A24 | CI/CD | Runs, SHA, skips, protection |
| A25 | Versions | Version and history consistency |
| A26 | Documentation | Behavior matches description |
| A27 | Installation | Clean install, update, rollback |
| A28 | Artifacts | Bytes, hashes, origin, execution |
| A29 | Operations | Logs, diagnostics, backups |
| A30 | Readiness | Blocking criteria, remaining work, order |

## Profiles (composable)
Desktop — startup, DPI, states, installer. Web — API, browser, accessibility. Mobile — permissions, devices, lifecycle. CLI — arguments, exit codes, errors. Library — API, compatibility, package. AI/ML — data, model, inference, metrics, license. AI-agent/Agent Skills — instructions, activation, permissions, actions, evals. Database — migrations, transactions, recovery. Network — protocols, timeouts, disconnection. DevOps — configuration, CI, infrastructure. Embedded/IoT — hardware and measurements; without hardware do not claim runtime PASS. Research — hypotheses, sources, method, reproducibility. Documentation — completeness, contradictions, currency. Non-software projects — adapt directions; do not impose Git and builds.

Prefer reviewed native project tools. Additional analyzers are optional.
