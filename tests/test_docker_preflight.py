"""Offline checks for the synthetic Docker profile."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import check_docker_preflight as p


class DockerPreflightTests(unittest.TestCase):
    def report(self):
        return {"uid": 65534, "pid": 1, "interfaces": ["lo"], "blocked": True,
                "root_readonly": True, "tmp_writable": True, "host_file_hidden": True,
                "docker_socket_hidden": True, "cap_effective": 0, "no_new_privs": 1,
                "seccomp": 2, "memory": 134217728, "swap": 0, "pids": 32,
                "net": "net:[123]", "cpu": [50000, 100000]}

    def test_profile(self):
        argv = p.create_args("fixture", "pass")
        for flag in ("--pull=never", "--network=none", "--read-only", "--cap-drop=ALL",
                     "--security-opt=no-new-privileges=true", "--user=65534:65534",
                     "--memory=128m", "--memory-swap=128m", "--cpus=0.5", "--pids-limit=32"):
            self.assertIn(flag, argv)
        self.assertNotIn("--privileged", argv)
        self.assertFalse(any(x.startswith(("--mount", "--volume", "-v")) for x in argv))
        self.assertIn(p.IMAGE, argv)

    def test_report(self):
        p.validate(self.report(), "net:[456]")

    def test_isolation_failure(self):
        for change in ({"uid": 0}, {"net": "net:[456]"}, {"blocked": False},
                       {"root_readonly": False}, {"host_file_hidden": False},
                       {"docker_socket_hidden": False}, {"cap_effective": 1},
                       {"no_new_privs": 0}, {"seccomp": 0}):
            with self.subTest(change=change), self.assertRaisesRegex(RuntimeError, "CONTROL_FAILED"):
                p.validate({**self.report(), **change}, "net:[456]")

    def test_resource_failure(self):
        for change in ({"memory": 0}, {"swap": 1}, {"pids": 64}, {"cpu": [100000, 100000]}):
            with self.subTest(change=change), self.assertRaisesRegex(RuntimeError, "CONTROL_FAILED"):
                p.validate({**self.report(), **change}, "net:[456]")


if __name__ == "__main__":
    unittest.main()
