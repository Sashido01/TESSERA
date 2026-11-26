#!/usr/bin/env python3
"""Owner-controlled outer gate: explicit agent command, Git structure, explicit tests."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

import completion_gate as gate

MAX_ARGS = 64
MAX_ARG_BYTES = 32768


def command(executable, args, root):
    gate.require(executable.is_absolute(), 'RUN_EXECUTABLE_NOT_ABSOLUTE')
    actual = executable.resolve(strict=True)
    gate.require(actual.is_file() and os.access(actual, os.X_OK) and
                 not actual.is_relative_to(root), 'RUN_EXECUTABLE_UNTRUSTED_LOCATION')
    if os.name == 'nt':
        gate.require(actual.suffix.lower() == '.exe', 'RUN_EXECUTABLE_TYPE')
    gate.require(len(args) <= MAX_ARGS and all(isinstance(a, str) and '\0' not in a for a in args)
                 and sum(len(a.encode('utf-8')) for a in args) <= MAX_ARG_BYTES, 'RUN_ARGUMENT_LIMIT')
    return [str(actual), *args]


def outcome(status, reason=None, **facts):
    result = {'schema_version': 1, 'status': status, 'release_readiness': 'NOT_VERIFIED',
              'client_skill_activation': 'NOT_VERIFIED', **facts}
    if reason is not None:
        result['reason'] = reason
    return result


def guarded_run(repo, baseline, agent_exe, agent_args, test_exe, test_args, *, execute=False,
                bilingual=False, allow_no_change=False, agent_timeout=900, test_timeout=300):
    facts = {'agent_exit_code': None, 'test_exit_code': None, 'structure': None}
    try:
        root = repo.resolve(strict=True)
        gate.require(not Path(__file__).resolve().is_relative_to(root) and
                     not Path(gate.__file__).resolve().is_relative_to(root), 'RUN_GATE_INSIDE_PROJECT')
        gate.require(type(agent_timeout) is int and 1 <= agent_timeout <= 3600 and
                     type(test_timeout) is int and 1 <= test_timeout <= 900, 'RUN_TIMEOUT_LIMIT')
        agent = command(agent_exe, agent_args, root)
        tests = command(test_exe, test_args, root)
        initial = gate.check(root, baseline, bilingual)
        facts['structure'] = initial
        if initial['status'] != 'STRUCTURE_VERIFIED' or initial['commits_checked'] != 0:
            return outcome('BLOCKED', 'RUN_INITIAL_BASELINE_INVALID', **facts)
        if not execute:
            return outcome('PLAN_ONLY', **facts)

        # Commands and their environment come from the trusted owner, not the agent.
        # Never change host permissions or print agent prompts/argv as evidence.
        def run(argv, timeout):
            return subprocess.run(argv, cwd=root, stdin=subprocess.DEVNULL, stdout=sys.stderr,
                                  stderr=sys.stderr, timeout=timeout, check=False).returncode

        try:
            facts['agent_exit_code'] = run(agent, agent_timeout)
        except subprocess.TimeoutExpired:
            return outcome('BLOCKED', 'RUN_AGENT_TIMEOUT', **facts)
        observed = gate.check(root, baseline, bilingual)
        facts['structure'] = observed
        if facts['agent_exit_code'] != 0:
            return outcome('BLOCKED', 'RUN_AGENT_FAILED', **facts)
        if observed['status'] != 'STRUCTURE_VERIFIED':
            return outcome('BLOCKED', 'RUN_STRUCTURE_FAILED', **facts)
        if observed['tag_objects'][:len(initial['tag_objects'])] != initial['tag_objects']:
            return outcome('BLOCKED', 'RUN_BASELINE_TAG_CHANGED', **facts)
        if not allow_no_change and observed['commits_checked'] == 0:
            return outcome('BLOCKED', 'RUN_NO_CHANGE', **facts)
        try:
            facts['test_exit_code'] = run(tests, test_timeout)
        except subprocess.TimeoutExpired:
            return outcome('BLOCKED', 'RUN_TEST_TIMEOUT', **facts)
        final = gate.check(root, baseline, bilingual)
        facts['structure'] = final
        if final != observed:
            return outcome('BLOCKED', 'RUN_POST_TEST_STATE_CHANGED', **facts)
        if facts['test_exit_code'] != 0:
            return outcome('BLOCKED', 'RUN_TEST_FAILED', **facts)
        return outcome('ACCEPTANCE_CHECKS_PASSED', **facts)
    except (gate.GateError, OSError, UnicodeError, ValueError, RuntimeError) as exc:
        return outcome('BLOCKED', str(exc) if isinstance(exc, gate.GateError) else 'RUN_RUNTIME_FAILED', **facts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--agent-exe', required=True, type=Path)
    parser.add_argument('--agent-arg', action='append', default=[])
    parser.add_argument('--test-exe', required=True, type=Path)
    parser.add_argument('--test-arg', action='append', default=[])
    parser.add_argument('--agent-timeout', type=int, default=900)
    parser.add_argument('--test-timeout', type=int, default=300)
    parser.add_argument('--bilingual', action='store_true')
    parser.add_argument('--allow-no-change', action='store_true')
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    result = guarded_run(args.repo, args.baseline, args.agent_exe, args.agent_arg,
                         args.test_exe, args.test_arg, execute=args.execute, bilingual=args.bilingual,
                         allow_no_change=args.allow_no_change, agent_timeout=args.agent_timeout,
                         test_timeout=args.test_timeout)
    print(json.dumps(result, sort_keys=True))
    return int(result['status'] == 'BLOCKED')


if __name__ == '__main__':
    sys.exit(main())
