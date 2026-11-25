import pathlib
import sys
import subprocess
import tempfile
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

    def test_unicode_normalization_conflict(self):
        result = run(task("a", status="IN_PROGRESS", scope=["src/Café"]),
                     task("b", "skill-a", scope=["src/Cafe\u0301/file.py"]))
        self.assertEqual(result["deferred"]["b"]["conflicts"], ["a"])

    def test_reserved_windows_names_rejected(self):
        for value in ("src/CON.txt", "AUX", "src/lpt¹.log", "src/COM1 .txt", "NUL", "CONOUT$", "a/\ud800"):
            with self.subTest(value=repr(value)), self.assertRaisesRegex(PlanError, "PLAN_SCOPE"):
                run(task("a", scope=[value]))
        self.assertEqual(selected(run(task("a", scope=["src/com10.txt"]))), ["a"])

    def test_long_dependency_chain(self):
        rows = [task(f"t{i:04d}", status="COMPLETE", evidence=["receipt"],
                     deps=[f"t{i-1:04d}"] if i else []) for i in range(999)]
        rows.append(task("last", deps=["t0998"]))
        self.assertEqual(selected(run(*rows)), ["last"])
        rows[0]["depends_on"] = ["last"]
        with self.assertRaisesRegex(PlanError, "DEPENDENCY_CYCLE"):
            run(*rows)

    def test_cli_duplicate_keys_rejected(self):
        runner = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "plan_tasks.py"
        with tempfile.TemporaryDirectory() as temp:
            data = pathlib.Path(temp) / "tasks.json"
            data.write_text('{"streams":["core"],"tasks":[],"tasks":[]}', encoding="utf-8")
            proc = subprocess.run([sys.executable, "-B", str(runner), "--tasks", str(data)],
                                  capture_output=True, text=True, timeout=10, check=False)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("PLAN_DUPLICATE_KEY", proc.stderr)

    def test_no_unsubstantiated_completion(self):
        with self.assertRaisesRegex(PlanError, "COMPLETE_WITHOUT_EVIDENCE"):
            run(task("a", status="COMPLETE"))
        with self.assertRaisesRegex(PlanError, "COMPLETE_DEPENDENCY_OPEN"):
            run(task("a"), task("b", status="COMPLETE", deps=["a"], evidence=["receipt"]))


if __name__ == "__main__":
    unittest.main()
