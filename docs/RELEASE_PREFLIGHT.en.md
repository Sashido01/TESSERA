# Release Preflight — readiness checks before tagging (T09.02)

[Русский — оригинал](RELEASE_PREFLIGHT.md) | **English — translation**

## Purpose

`core/release_preflight.py` verifies that the requested version and release notes exist **in a specific Git commit** and that required build/test commands are declared in the target project's `release-checks.json`.

**The default `--plan` mode never executes user-provided commands.** Only explicit `--execute` runs the approved commands of a trusted target project. Agent adapters must not auto-execute commands obtained from an untrusted Pull Request.

## Two modes

```bash
# Read configuration, VERSION, release notes, and Git state only.
python core/release_preflight.py --repo <project-root> --version 0.0.8 --plan

# Execute trusted project checks explicitly.
python core/release_preflight.py --repo <project-root> --version 0.0.8 --execute --expected-commit <full-commit-sha>
```

On successful `--plan`, report `stage=PREPARED`, `checks_status=NOT_RUN`. After a successful explicit `--execute`, report `stage=VALIDATED`, `checks_status=PASS`. Any failed prerequisite or check results in `stage=BLOCKED`. **Neither mode claims RELEASED status** or a published Git tag.

## Configuration format

Example for a project with a build process:

```json
{
  "schema_version": 1,
  "version_file": "VERSION",
  "release_notes": ["CHANGELOG.md"],
  "build": [
    {
      "id": "package-build",
      "argv": ["python", "-m", "build"],
      "cwd": ".",
      "timeout_seconds": 300
    }
  ],
  "tests": [
    {
      "id": "unit-tests",
      "argv": ["python", "-m", "unittest", "discover", "-s", "tests"],
      "cwd": ".",
      "timeout_seconds": 300
    }
  ]
}
```

This illustrates the schema, not a claim that `python -m build` is installed or appropriate for every project. Projects without a build artifact may replace the `build` array with a **justified** `{"not_applicable_reason": "..."}`. At least one test step is mandatory. TESSERA's own [release-checks.json](../release-checks.json) explains why a separate build artifact is not applicable and declares two test suites.

## Safety controls

- Requires a clean Git worktree; otherwise `WORKTREE_DIRTY`.
- Requires exact `HEAD` matching the expected commit SHA; otherwise `HEAD_CHANGED`.
- The configuration must be committed and match a strict schema. Unknown fields, duplicate JSON keys, missing tests, and invalid timeouts fail.
- Configuration, VERSION, release notes, and working directories must remain inside the Git root; parent traversal and symlink escapes are refused.
- Commands are argument **arrays**, invoked with `shell=False`. Explicit commands can still perform arbitrary actions, so `--execute` is only for trusted projects after user authorization.
- Step timeouts are 1–900 seconds. Results contain the step ID/type, exit code, and duration; command output is intentionally omitted from JSON to reduce accidental secret exposure.
- Execution stops on the first failed, timed-out, or unlaunchable check. Git HEAD and cleanliness are rechecked afterward.
- No Git writes, tagging, or remote access are performed by the inspector. **Commands executed through `--execute` may themselves change files**; automatic rollback is not implemented.

## Collecting evidence after tagging

A separate [T09.03](RELEASE_REPORT.en.md) stage combines actual preflight results with local and remote tag inspection, without presenting a successful test command as a published application release. Remote checks and test execution use separate explicit flags.

## What PASS actually proves

`preflight_status=PASS` means version/release-note/Git-state prerequisites passed. `checks_status=PASS` means the **actually executed** declared commands returned zero and the checked invariants were preserved. When a build is explicitly inapplicable, `build_status=NOT_APPLICABLE`, not PASS.

The tool **does not verify** whether the tests are meaningful, external CI log authenticity, commit signatures, annotated tags, remote repositories, or GitHub Releases. `release_readiness` always remains `NOT_VERIFIED` until later release-stage coordination is implemented. This is **T09.02**; overall T09 remains PARTIAL.

## Testing and CI

```bash
python -m unittest discover -s tests -v
```

TESSERA's required CI only runs `--plan`. Test cases for `--execute` use **temporary Git repositories**. Commands from untrusted Pull Requests are never automatically executed.
