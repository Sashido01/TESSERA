# Project Audit changelog

[Русский — оригинал](CHANGELOG.md) | **English — translation**

## 0.0.3 — Local Git state observation

Git Inspector: HEAD (including unborn/detached), status/ref/remote counts, repeated observations, explicit STALE. Local Linux tests 13/13; no file names or remote URLs emitted; not an atomic snapshot or content check. Updated instructions, documentation and structural regression. Windows and full acceptance open.

Correct false DEVICE_BOUNDARY on Windows (#80), strengthen metadata-only regression (#77); 21/21 Linux Inventory Engine tests, simulated Windows RED→GREEN. Native Windows CI and scanner verdict still unverified.

## 0.0.2 — Bounded metadata inventory

Optional local tool, relative paths, counters, markers, limits, visible exclusions, metadata SHA-256 (not contents), no known redirects or device traversal. 17 local Linux tests; Windows, full CI and independent release unverified. Level II PARTIAL.

Independent local test plan prepared; preflight depends on PR #70 and still requires CI.

## 0.0.1 — Level I candidate

Bilingual instructions, 30 directions, FAST/FULL/DEEP, evidence, coverage, report, 20 behavioral scenarios, five evolution levels. DELTA and tooling are planned. Actual agent trials and independent publication have not been performed.
