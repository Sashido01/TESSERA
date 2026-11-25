# CI speed and evidence

[Русский — оригинал](CI.md) | **English — translation**

Speed is a process quality criterion. Measure runner queue time, time to first useful result, full critical path, p50/p95, reruns and runner-minutes. Do not confuse individual job durations with wall-clock.

1. Run existing native local checks before pushing. FAST — format, metadata and affected tests; FULL — every mandatory check. Do not call FAST full acceptance.
2. With GitHub Actions, measure job/step timings first; move heavy independent checks into parallel jobs. Preserve read-only permissions, pinned Actions, identical SHA, validated inputs and isolation. Final required check always runs and requires success of each mandatory stage; skipped/cancelled/failure means rejection. Do not skip an entire required workflow using paths.
3. Use native matrix, needs, concurrency, dependency caching and reusable workflows only when they simplify the process. Cancel only obsolete non-release checks for the same candidate; never cancel release/acceptance of a unique accepted SHA. CI queue does not replace integration queue.
4. Select affected tests using changes and evidenced dependencies; unknown dependencies require FULL. Cache only verifiable data tied to tool versions, configuration and source digests; do not trust PR caches for privileged releases. Do not reduce secrets history coverage without demonstrating equivalence.
5. Bind successful PR checks to exact HEAD and current base; verify the actual integration result and tag separately. Fix failures in the same branch. Never disable checks for speed.

Sources: [GitHub required checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks?apiVersion=2022-11-28), [concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency), [dependency caching](https://docs.github.com/en/actions/concepts/workflows-and-actions/dependency-caching), [reusable workflows](https://docs.github.com/en/actions/concepts/workflows-and-actions/reusing-workflow-configurations).
