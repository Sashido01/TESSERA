# Tasks and dependencies

[Русский — оригинал](TASKS.md) | **English — translation**

Use one current task source: existing roadmap, local register or GitHub Issues with dependencies. Do not require a duplicate local Issues database. Build a helper snapshot from the source; it never changes the original register.

States: BACKLOG, READY, IN_PROGRESS, WAIT_DEPENDENCY, WAIT_CI, CI_FAILED, READY_TO_INTEGRATE, WAIT_RELEASE, WAIT_OWNER, BLOCKED, COMPLETE. COMPLETE requires real evidence and satisfied dependencies. Record goal, acceptance criteria, observation time, branch/PR/run and blocker in the main register. Old results do not carry over to changed SHAs.

## Optional local planner

```bash
python scripts/plan_tasks.py --tasks <task-snapshot.json>
```

Snapshot format:

```json
{"streams":["core","skill-a"],"tasks":[{"id":"T01","stream":"core","priority":"P0","status":"WAIT_CI","depends_on":[],"write_scope":["core"],"resources":[],"read_only":false,"evidence":[]},{"id":"S01","stream":"skill-a","priority":"P1","status":"READY","depends_on":[],"write_scope":["skills/skill-a"],"resources":[],"read_only":false,"evidence":[]}]}
```

Checks unique IDs, unknown/cyclic dependencies, COMPLETE without evidence references, overlapping declared scopes and resources (including nested paths, case-insensitive). Selects at most one ready task per stream in the given order; at equal priority CI_FAILED first. WAIT_CI and other holding states do not block independent work. Path `.` reserves the entire write scope. Empty scope is allowed only for explicitly read_only work. On NO_READY_WORK reconcile blockers and choose only justified research.

Limitation: the helper does not verify truth of evidence references, GitHub state, hidden dependencies, actual filesystem identities/symlinks, or atomically reserve resources. It is advisory over the supplied snapshot. Recheck freshness and agree on task ownership before acting.

### Portability clarification 0.0.2

Scopes use casefold + NFC; equivalent Unicode paths conservatively conflict. Reserved Windows device names (including extensions) and surrogate characters are rejected. CLI rejects duplicate JSON keys. DAG traversal visits each node and edge once (O(V+E), excluding other planning stages); a 1,000-task chain was tested. This does not compare filesystem identity: 8.3 aliases, hardlinks, junctions, symlinks and external processes require separate reconciliation. Read-only does not reserve writes: coordinate source stability separately. 17/17 Linux tests; native Windows and actual agent execution unverified.
