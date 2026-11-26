# Mandatory execution — T13 candidate

[Русский — оригинал](ENFORCEMENT.md) | **English — translation**

Owner approved mandatory Microversion Release enforcement in Codex and DeepSeek Harness for 0.1.0. Separate skill loading, hook invocation and independent acceptance; none substitutes for the others. Start with a new disposable repository without a remote. Do not automatically modify existing projects, global settings, permissions, hook trust or sandbox.

## Basic project profile

Explicit trusted Git root, existing baseline commit, linear history, root VERSION and CHANGELOG.md (## MAJOR.MINOR.PATCH headings); optional required CHANGELOG.en.md with --bilingual. Check up to 32 new commits: each must modify VERSION, applicable changelogs and at least one non-metadata path; next PATCH or allowed milestone, including .100+. Every .0 release and release baseline requires its exact local annotated v-tag with nonempty annotation. Never creates tags. Independent monorepo skill tags remain the separate release_tag.py/Release Core contract; not checked by this basic profile.

Invocation: trusted Python with -E, -s and -B; absolute scripts/completion_gate.py path; check mode; --repo and --baseline with actual values, optionally --bilingual. Pass separate arguments, never construct a string from unreviewed data.

Exit 0 STRUCTURE_VERIFIED is only structural; 1 BLOCKED. Zero commits may be valid for read-only work, not evidence of completed change. Repeat Git status, ls-files -v (refuse assume-unchanged/skip-worktree), HEAD and tag refs. Ignored files, full submodule history, test substance, baseline authenticity, atomicity, reverted races and Git trust are not established. Not a sandbox. 30 s Git budget, up to 5 s per command, 2 MiB post-capture limit; no hard memory/descendant bound. All inherited Git_* except GIT_PAGER block before Git, including #81. Never strip production context for PASS. May be stricter than release_tag.py.

## Independent owner/controller

Run `guarded_run.py` from a verified skill copy **outside agent writable scope** in an ordinary trusted owner terminal, separate from the agent sandbox. Explicitly authorized independent verification, not sandbox bypass or proof of Git access inside the agent. Provide absolute reviewed executables outside the project (Windows .exe only; Node CLI uses trusted node.exe and absolute script in argv), argv and timeouts. Never run untrusted project/commands; executable/argv/context must be approved by owner and tests may execute project code. Wrapper never expands or changes host permissions.

Without --execute: PLAN_ONLY, validates inputs and baseline, runs no agent/tests. With --execute: launch the specified agent, verify Git independently of its text/exit 0, run agreed test command and recheck exact SHA/version/release tag objects. No-op blocked by default; --allow-no-change only for an explicitly read-only task. No tests after agent/structure failure. Any failure, timeout, invalid structure or changed final state yields BLOCKED exit 1. ACCEPTANCE_CHECKS_PASSED exit 0 means only two executed commands and structural checks; not RELEASED or proof of adequate tests or hook loading. Stdout JSON; child output sent to stderr, potentially private; never publish stderr/argv. Up to 64 args / 32 KiB per command, agent timeout 1–3600 s and test timeout 1–900 s; direct process termination does not guarantee descendants stop.

Argument **schema** (replace paths, actual client flags and reviewed commands; first without --execute):
| Argument | Value |
| --- | --- |
| Interpreter | Trusted absolute Python; options -E, -s, -B |
| Script | Absolute scripts/guarded_run.py path |
| --repo | Selected Git root |
| --baseline | Full SHA of existing baseline |
| --expected-version | Required exact owner-approved target version |
| --agent-exe | Reviewed absolute client executable |
| --agent-arg | Repeat for each reviewed argument, e.g. exec and --json for Codex; prompt as a separate argument |
| --test-exe | Reviewed absolute test executable |
| --test-arg | Repeat for each approved test argument |
| --execute | Only after PLAN_ONLY review and owner authorization |
Not a ready shell command. For Codex check version, exec --help and permissions; for Harness check actual headless profile/CLI, do not copy Codex flags. No approval/sandbox/trust bypass. GUI sessions require separately observed hook and independent acceptance; wrapper cannot control an already running GUI.

## Stop adapter

Mode stop reads up to 256 KiB JSON from stdin, requires event Stop, boolean stop_hook_active, absolute cwd matching explicit root. Reads no transcript, never uses payload cwd to choose repository, never prints payload. Owner supplies a new marker in an existing trusted private directory outside root, writable for one hook file creation but not for agent deletion/substitution. Do not expand permissions for marker; unavailable marker means no forced continuation, external gate remains mandatory. Exclusive creation, no overwrite/delete. One marker per approved run, never reuse. On first failure decision:block requests one continuation, subsequently continue:false with stopReason; invalid input/marker does not invoke Git outside scope or loop. JSON exit 0 is protocol success, not task PASS.

Project hook config schema (not a ready file): the root hooks object contains a Stop array. Each Stop entry contains a hooks array; its entry has type set to command, the command field with the owner's reviewed absolute command, and a numeric execution time limit (full field name: hooks.Stop[0].hooks[0].timeout), set to 45 seconds. Preserve existing handlers; do not overwrite config. Do not install a non-executable example.

Before enabling the hook, owner assembles the actual host-shell command: trusted absolute Python with -E, -s, -B; absolute scripts/completion_gate.py; stop; --repo, --baseline, --marker with reviewed values; optional --bilingual. Verify path quoting and run a protocol fixture manually before connecting. Do not interpolate prompt/payload values. Codex: project .codex/hooks.json, preserve existing content, review/trust exact definition via /hooks; no trust bypass. Harness: experimental @deepseek-ai/dsh-hooks-codex with configPath pointing to reviewed file, separate profile only. Upstream Stop **always** sends stop_hook_active=false and ignores continue:false; hook load/execution failures may allow agent continuation. Marker only bounds repeated continuation requests, not a veto. External controller mandatory in both clients. Missing/failing hook means client activation NOT_VERIFIED, not PASS; never accept successful model text.

Sources: [Codex Hooks](https://learn.chatgpt.com/docs/hooks), [Codex exec](https://learn.chatgpt.com/docs/non-interactive-mode), [Harness bridge](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/experimental/hooks-codex/README.md).

## Acceptance

Linux Git 2.47.3 / Python 3.13.5 — 26/26 methods: 16 Git/Stop fixture and 10 actual child-process wrapper fixture; verified Git blobs match tested files. Synthetic agents/tests do not establish actual Codex/Harness. Full catalog/Windows require candidate CI. Actual each-client acceptance: positive 0.0.99 → 0.1.0 with exact tag and approved tests; negative missing/lightweight/wrong tag, skip, dirty, no-op, missing/failing hook, unsafe Git context, test refusal and no infinite continuation. Observe client hook invocation and wrapper exit. Record client version/profile, exact tag/commit, JSON and test outcome without private data. Close #81 only after demonstrated least-privilege invocation and real native Windows/Codex trials. No production enablement before acceptance.

## Exact target (0.0.5 candidate)

Guarded Run schema_version 2 requires --expected-version even for PLAN_ONLY. Validates format, refuses target below baseline and requires change by default. If agent produces valid microversion 0.0.100 instead of requested 0.1.0, RUN_TARGET_VERSION_MISMATCH before tests; missing release tag yields RUN_STRUCTURE_FAILED. For read-only work specify baseline version and explicit --allow-no-change. ACCEPTANCE_CHECKS_PASSED does not establish test adequacy, Stop observation, remote or release readiness. Four new regression methods including actual Git release and negative tag check. Native CI required.
