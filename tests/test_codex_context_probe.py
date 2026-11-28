"""Privacy and malformed-context regressions, without Git or real secrets."""
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import codex_context_probe as p


class GuardedEnvironment(dict):
    def __getitem__(self, key):
        if key.startswith("GIT_CONFIG_VALUE_"):
            raise AssertionError("configuration value read")
        return super().__getitem__(key)


class ContextProbeTests(unittest.TestCase):
    def test_known_labels_without_reading_values(self):
        env = GuardedEnvironment({"GIT_CONFIG_COUNT": "2",
            "GIT_CONFIG_KEY_0": "core.hooksPath", "GIT_CONFIG_VALUE_0": "private fixture",
            "GIT_CONFIG_KEY_1": "protocol.file.allow", "GIT_CONFIG_VALUE_1": "private fixture",
            "GIT_PAGER": "fixture"})
        before = dict(env)
        report = p.observe(env)
        self.assertEqual(report["context_shape"], "WELL_FORMED")
        self.assertEqual(report["key_labels"], [
            {"index": 0, "label": "core.hookspath"}, {"index": 1, "label": "protocol.file.allow"}])
        self.assertNotIn("private fixture", json.dumps(report))
        self.assertEqual(dict(env), before)
        self.assertFalse(report["release_authorized"])

    def test_unknown_key_and_name_never_reproduced(self):
        env = GuardedEnvironment({"GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "url.synthetic-private.example.insteadof",
            "GIT_CONFIG_VALUE_0": "private fixture", "GIT_SYNTHETIC_PRIVATE_NAME": "fixture"})
        report = p.observe(env)
        self.assertEqual(report["key_labels"], [{"index": 0, "label": "OTHER"}])
        self.assertTrue(report["other_git_names_present"])
        self.assertNotIn("private", json.dumps(report).lower())

    def test_absence_and_zero_are_only_shape_observations(self):
        for env in ({}, {"GIT_CONFIG_COUNT": "0"}):
            result = p.observe(env)
            self.assertEqual(result["context_shape"], "WELL_FORMED")
            self.assertEqual(result["indexed_pair_count"], 0)
            self.assertEqual(result["policy_compatibility"], "NOT_VERIFIED")
            self.assertFalse(result["release_authorized"])

    def test_malformed_pairs_do_not_inspect_any_key(self):
        for env in ({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.hookspath"},
                    {"GIT_CONFIG_KEY_0": "core.hookspath", "GIT_CONFIG_VALUE_0": "fixture"},
                    {"GIT_CONFIG_COUNT": "01"},
                    {"GIT_CONFIG_COUNT": "65"},
                    {"GIT_CONFIG_COUNT": "0", "GIT_CONFIG_VALUE_0": "fixture"},
                    {"GIT_CONFIG_COUNT": "0", "GIT_CONFIG_KEY_private": "fixture"},
                    {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_00": "fixture",
                     "GIT_CONFIG_VALUE_00": "fixture"}):
            with self.subTest(case=len(env)):
                result = p.observe(GuardedEnvironment(env))
                self.assertEqual(result["context_shape"], "MALFORMED")
                self.assertEqual(result["key_labels"], [])
                self.assertIsNone(result["indexed_pair_count"])

    def test_case_alias_is_not_treated_as_known(self):
        report = p.observe({"GIT_CONFIG_COUNT": "0", "git_config_key_0": "fixture"})
        self.assertEqual(report["context_shape"], "MALFORMED")

    def test_duplicate_known_labels_remain_distinct(self):
        env = GuardedEnvironment({"GIT_CONFIG_COUNT": "2",
            "GIT_CONFIG_KEY_0": "safe.directory", "GIT_CONFIG_VALUE_0": "fixture",
            "GIT_CONFIG_KEY_1": "safe.directory", "GIT_CONFIG_VALUE_1": "fixture"})
        self.assertEqual(p.observe(env)["key_labels"], [
            {"index": 0, "label": "safe.directory"}, {"index": 1, "label": "safe.directory"}])


if __name__ == "__main__":
    unittest.main()
