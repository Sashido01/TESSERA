# Microversion Release changelog

[Русский — оригинал](CHANGELOG.md) | **English — translation**

## 0.0.5 — Exact target and fixture protection

- Guarded Run requires --expected-version, rejects wrong target before tests; new regression scenarios exact release, missing tag, invalid/old target, CI required.
- Old mutating Git fixtures refuse inherited Git_* before writes; new isolated fixtures use only explicit system-context allowlist. Production Git context remains fail-closed.

## 0.0.4 — Completion gate and mandatory acceptance

- Basic completion_gate.py checks exact linear history from baseline, VERSION/CHANGELOG, release tags and index flags. Stop adapter with one continuation. No commits or tags created.
- guarded_run.py: independent owner-controlled process, PLAN_ONLY by default, approved agent/tests with --execute, no-op refusal and unchanged checked SHA/tag verification. 26/26 Linux tests with disposable Git fixtures and actual child processes; full CI and actual clients NOT_VERIFIED for candidate.

## 0.0.3 — Inherited Git context diagnostics

- The context command reports recognized blocking names only, without executing Git or modifying the environment. Orphaned indexed Git config overrides are rejected. Three new skill test methods; actual host integration #81 remains open. CI and independent tag required.

## 0.0.2 — Windows installer compatibility

- Safe output to legacy console encodings; tests compare canonical paths including Windows short names. Redirect and overwrite protections retained. Native CI rerun required.

## 0.0.1 — Independent version baseline

- Establish the baseline of the existing skill; prior history remains in the catalog changelog. Runtime behavior is unchanged. Independent release requires its own verified annotated tag; activation in actual clients is not verified.
