import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from plan_tasks import PlanError, plan


def task(name, stream="core", status="READY", deps=(), scope=None, resources=(), priority="P1", read_only=False, evidence=()):
    return {"id": name, "stream": stream, "status": status, "priority": priority,
            "depends_on": list(deps), "write_scope": ([name] if scope is None else list(scope)),
            "resources": list(resources), "read_only": read_only, "evidence": list(evidence)}


def run(*tasks):
    return plan({"streams": ["core", "skill-a", "skill-b"], "tasks": list(tasks)})


def selected(result):
    return [t["id"] for t in result["selection"]]


class PlannerTests(unittest.TestCase):
    def test_stream_order(self):
        self.assertEqual(selected(run(task("b", "skill-b"), task("a", "skill-a"), task("c"))), ["c", "a", "b"])

    def test_ci_wait_does_not_stop_independent_streams(self):
        result = run(task("c", status="WAIT_CI"), task("a", "skill-a"), task("b", "skill-b"))
        self.assertEqual(selected(result), ["a", "b"])
        self.assertEqual(result["waiting"], ["c"])

    def test_dependency(self):
        result = run(task("a", status="WAIT_CI"), task("b", "skill-a", deps=["a"]))
        self.assertEqual(selected(result), [])
        self.assertEqual(result["deferred"]["b"]["dependencies"], ["a"])
        self.assertEqual(selected(run(task("a", status="COMPLETE", evidence=["run-1"]), task("b", "skill-a", deps=["a"]))), ["b"])

    def test_parent_child_casefold_conflict(self):
        result = run(task("a", status="IN_PROGRESS", scope=["skills/A"]), task("b", "skill-a", scope=["skills/a/file.py"]))
        self.assertEqual(result["deferred"]["b"]["conflicts"], ["a"])

    def test_selected_tasks_cannot_share_resources(self):
        result = run(task("a", resources=["GPU"]), task("b", "skill-a", resources=["gpu"]))
        self.assertEqual(selected(result), ["a"])
        self.assertEqual(result["deferred"]["b"]["conflicts"], ["a"])

    def test_read_only_research_is_independent(self):
        self.assertEqual(selected(run(task("a", status="WAIT_CI", scope=["."]),
                                      task("b", "skill-a", scope=[], read_only=True))), ["b"])

    def test_priority_and_one_per_stream(self):
        self.assertEqual(selected(run(task("a", priority="P2"), task("z", priority="P0"))), ["z"])

    def test_failed_ci_is_resumed(self):
        result = run(task("a", status="CI_FAILED"), task("b", "skill-a"))
        self.assertEqual(result["selection"][0]["action"], "FIX_CI")
        self.assertEqual(selected(result), ["a", "b"])

    def test_no_ready_work(self):
        self.assertEqual(run(task("a", status="WAIT_OWNER"))["status"], "NO_READY_WORK")

    def test_invalid_dependency_and_cycle(self):
        with self.assertRaisesRegex(PlanError, "UNKNOWN_DEPENDENCY"):
            run(task("a", deps=["missing"]))
        with self.assertRaisesRegex(PlanError, "DEPENDENCY_CYCLE"):
            run(task("a", deps=["b"]), task("b", deps=["a"]))

    def test_duplicate_id(self):
        with self.assertRaisesRegex(PlanError, "TASK_STATE"):
            run(task("a"), task("a", "skill-a"))

    def test_invalid_scope(self):
        for value in ("../outside", "C:/private", "/absolute", "a//b", "a/*"):
            with self.subTest(value=value), self.assertRaisesRegex(PlanError, "PLAN_SCOPE"):
                run(task("a", scope=[value]))
        with self.assertRaisesRegex(PlanError, "SCOPE_UNKNOWN"):
            run(task("a", scope=[]))

    def test_no_unsubstantiated_completion(self):
        with self.assertRaisesRegex(PlanError, "COMPLETE_WITHOUT_EVIDENCE"):
            run(task("a", status="COMPLETE"))
        with self.assertRaisesRegex(PlanError, "COMPLETE_DEPENDENCY_OPEN"):
            run(task("a"), task("b", status="COMPLETE", deps=["a"], evidence=["receipt"]))


if __name__ == "__main__":
    unittest.main()
