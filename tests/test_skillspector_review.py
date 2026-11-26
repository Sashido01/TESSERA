"""Offline report contract tests. Actual scanner execution is separate."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_skillspector_review as s


class SkillSpectorTests(unittest.TestCase):
    def report(self):
        return {"execution_successful": True,
                "metadata": {"skillspector_version": s.VERSION, "llm_requested": False,
                             "llm_available": False, "meta_analysis_applied": False,
                             "inference_usage": []},
                "analysis_completeness": {
                    "execution_successful": True, "status": "complete", "is_complete": True,
                    "total_components": 1, "scanned_components": 1, "fully_inspected_files": 1,
                    "partially_inspected_files": 0, "entirely_uninspected_files": 0,
                    "coverage_percent": 100, "findings_before_filtering": 0,
                    "findings_after_filtering": 0, "ledger_exceptions": [], "scope_exclusions": []},
                "components": [{"path": "SKILL.md", "size_bytes": 100}],
                "issues": [], "suppressed_count": 0,
                "risk_assessment": {"score": 0, "severity": "LOW"}}

    def check(self, data, rc=0, expected=None):
        return s.summary(data, rc, {"SKILL.md": 100} if expected is None else expected)

    def test_clean(self):
        self.assertEqual(self.check(self.report())["analysis_status"], "complete")

    def test_llm_rejected(self):
        data = self.report()
        data["metadata"]["llm_requested"] = True
        with self.assertRaisesRegex(s.InstallCheckError, "PROVENANCE"):
            self.check(data)

    def test_inference_rejected(self):
        data = self.report()
        data["metadata"]["inference_usage"] = [{}]
        with self.assertRaisesRegex(s.InstallCheckError, "PROVENANCE"):
            self.check(data)

    def test_false_complete_rejected(self):
        with self.assertRaisesRegex(s.InstallCheckError, "FALSE_COMPLETE"):
            self.check(self.report(), expected={"SKILL.md": 100, "extra.md": 5})

    def test_wrong_size_rejected(self):
        with self.assertRaisesRegex(s.InstallCheckError, "COMPONENT_MISMATCH"):
            self.check(self.report(), expected={"SKILL.md": 101})

    def test_execution_failure_rejected(self):
        with self.assertRaisesRegex(s.InstallCheckError, "EXECUTION"):
            self.check(self.report(), rc=2)

    def test_risk_exit_is_advisory(self):
        data = self.report()
        data["risk_assessment"]["score"] = 51
        self.assertTrue(self.check(data, rc=1)["risk_threshold_exceeded"])
        with self.assertRaisesRegex(s.InstallCheckError, "RISK_EXIT_MISMATCH"):
            self.check(data, rc=0)
        with self.assertRaisesRegex(s.InstallCheckError, "RISK_EXIT_MISMATCH"):
            self.check(self.report(), rc=1)

    def test_partial_is_retained(self):
        data = self.report()
        data["analysis_completeness"].update({"status": "partial", "is_complete": False,
            "fully_inspected_files": 0, "partially_inspected_files": 1,
            "scanned_components": 0, "coverage_percent": 0})
        self.assertEqual(self.check(data)["analysis_status"], "partial")

    def test_partial_coverage_locations_are_inventory_bound(self):
        data = self.report()
        coverage = data["analysis_completeness"]
        coverage.update({"status": "partial", "is_complete": False,
            "fully_inspected_files": 0, "partially_inspected_files": 1,
            "scanned_components": 0, "coverage_percent": 0})
        coverage["ledger_exceptions"] = [
            {"path": "SKILL.md", "reason_code": "static_parse_limit",
             "start_line": 3, "end_line": 4, "message": "synthetic private detail"},
            {"path": "SKILL.md", "reason_code": "static_parse_limit"},
            {"path": "/private/marker", "reason_code": "static_parse_limit"},
            {"path": "other.md", "reason_code": "static_parse_limit"},
        ]
        result = self.check(data)
        self.assertEqual(result["analysis_status"], "partial")
        self.assertEqual(result["coverage_locations"], [
            {"source": "ledger_exceptions", "reason": "static_parse_limit",
             "file": "SKILL.md", "start_line": None, "end_line": None},
            {"source": "ledger_exceptions", "reason": "static_parse_limit",
             "file": "SKILL.md", "start_line": 3, "end_line": 4}])
        self.assertEqual(result["coverage_locations_unresolved"], 2)
        self.assertEqual(result["coverage_reasons"][0]["count"], 4)
        self.assertNotIn("private", str(result))
        self.assertNotIn("other.md", str(result))

    def test_coverage_locations_bounded(self):
        data = self.report()
        data["analysis_completeness"]["scope_exclusions"] = [
            {"path": "SKILL.md", "reason_code": "fixture",
             "start_line": True, "end_line": 10}] * (s.MAX_LOCATION_ROWS + 2)
        result = self.check(data)
        self.assertEqual(len(result["coverage_locations"]), s.MAX_LOCATION_ROWS)
        self.assertEqual(result["coverage_locations_omitted"], 2)
        self.assertEqual(result["coverage_reasons"][0]["count"], s.MAX_LOCATION_ROWS + 2)
        self.assertIsNone(result["coverage_locations"][0]["start_line"])

    def test_parser_diagnostic_nested_coordinates_and_identifiers(self):
        data = self.report()
        diag = {"cause": "runtime_dependent", "check": "runtime_command_identity",
                "unchecked_scope": "command_word", "location_precision": "source_span",
                "start_line": 5, "end_line": 7, "message": "synthetic private detail"}
        data["analysis_completeness"]["ledger_exceptions"] = [
            {"path": "SKILL.md", "reason_code": "static_parse_limit", "parser_diagnostic": diag}]
        row = self.check(data)["coverage_locations"][0]
        self.assertEqual((row["start_line"], row["end_line"]), (5, 7))
        self.assertEqual(row["parser_cause"], "runtime_dependent")
        self.assertEqual(row["parser_check"], "runtime_command_identity")
        self.assertNotIn("private", str(row))
        diag["check"] = "private_identifier"
        row = self.check(data)["coverage_locations"][0]
        self.assertNotIn("parser_check", row)
        self.assertIsNone(row["start_line"])

    def test_suppression_is_forbidden(self):
        data = self.report()
        data["suppressed_count"] = 1
        with self.assertRaisesRegex(s.InstallCheckError, "SUPPRESSION"):
            self.check(data)

    def test_findings_sanitized(self):
        data = self.report()
        data["issues"] = [{"id": "P1", "severity": "HIGH", "finding": "raw text"}]
        data["analysis_completeness"].update({"findings_before_filtering": 1,
                                             "findings_after_filtering": 1})
        result = self.check(data)
        self.assertEqual(result["findings"], 1)
        self.assertNotIn("raw text", str(result))

    def test_location_is_inventory_bound_and_sanitized(self):
        data = self.report()
        data["issues"] = [{"id": "AST3", "severity": "MEDIUM",
                           "location": {"file": "SKILL.md", "start_line": 3, "end_line": 4},
                           "code_snippet": "synthetic confidential content",
                           "occurrences": [{"file": "external/private.txt", "start_line": 8}]}]
        data["analysis_completeness"].update({"findings_before_filtering": 1,
                                             "findings_after_filtering": 1})
        result = self.check(data)
        self.assertEqual(result["primary_locations"], [
            {"rule": "AST3", "severity": "MEDIUM", "file": "SKILL.md",
             "start_line": 3, "end_line": 4}])
        self.assertEqual(result["primary_locations_unresolved"], 0)
        self.assertEqual(result["location_scope"], "PRIMARY_ONLY_NOT_ALL_OCCURRENCES")
        self.assertNotIn("confidential", str(result))
        self.assertNotIn("external/private", str(result))

    def test_untrusted_location_not_echoed(self):
        for location in (
            {"file": "/private/marker", "start_line": 1},
            {"file": "../marker", "start_line": 1},
            {"file": "unknown.md", "start_line": 1},
            {"file": "SKILL.md", "start_line": True},
            {"file": "SKILL.md", "start_line": 0},
            {"file": "SKILL.md", "start_line": 102},
            {"file": "SKILL.md", "start_line": 3, "end_line": 2},
        ):
            with self.subTest(location=location):
                data = self.report()
                data["issues"] = [{"id": "AST3", "severity": "MEDIUM", "location": location}]
                result = self.check(data)
                self.assertEqual(result["primary_locations"], [])
                self.assertEqual(result["primary_locations_unresolved"], 1)
                self.assertEqual(result["findings"], 1)
                self.assertNotIn("marker", str(result))
                self.assertNotIn("unknown.md", str(result))

    def test_high_occurrences_projected_without_private_data(self):
        data = self.report()
        data["issues"] = [
            {"id": "E2", "severity": "HIGH",
             "location": {"file": "SKILL.md", "start_line": 1},
             "occurrences": [{"file": "SKILL.md", "start_line": 2, "end_line": 3,
                              "source_url": "private source", "code_snippet": "private snippet"},
                             {"file": "SKILL.md", "start_line": 4},
                             {"file": "../private.txt", "start_line": 1},
                             {"file": "SKILL.md", "start_line": True}]},
            {"id": "P1", "severity": "CRITICAL"},
            {"id": "AST3", "severity": "MEDIUM", "occurrences": [{"file": "SKILL.md", "start_line": 8}]},
        ]
        result = self.check(data)
        self.assertEqual(result["high_occurrence_groups"], 2)
        self.assertEqual(result["high_occurrence_groups_missing"], 1)
        self.assertEqual(result["high_occurrences_reported"], 4)
        self.assertEqual(result["high_occurrences_unresolved"], 2)
        self.assertEqual(result["high_occurrence_locations"], [
            {"rule": "E2", "severity": "HIGH", "file": "SKILL.md", "start_line": 2, "end_line": 3},
            {"rule": "E2", "severity": "HIGH", "file": "SKILL.md", "start_line": 4, "end_line": None}])
        self.assertNotIn("private", str(result))
        self.assertEqual(result["findings"], 3)

    def test_high_occurrence_output_limit_and_malformed_group(self):
        data = self.report()
        data["issues"] = [
            {"id": "E2", "severity": "HIGH", "occurrences": [
                {"file": "SKILL.md", "start_line": 1}] * (s.MAX_LOCATION_ROWS + 2)},
            {"id": "AR3", "severity": "HIGH", "occurrences": "private data"},
        ]
        result = self.check(data)
        self.assertEqual(len(result["high_occurrence_locations"]), s.MAX_LOCATION_ROWS)
        self.assertEqual(result["high_occurrences_omitted"], 2)
        self.assertEqual(result["high_occurrences_reported"], s.MAX_LOCATION_ROWS + 2)
        self.assertEqual(result["high_occurrence_groups_missing"], 1)
        self.assertNotIn("private data", str(result))

    def test_location_output_is_bounded_without_hiding_findings(self):
        data = self.report()
        data["issues"] = [{"id": "AST3", "severity": "MEDIUM",
                           "location": {"file": "SKILL.md", "start_line": 1}}] * (s.MAX_LOCATION_ROWS + 2)
        result = self.check(data)
        self.assertEqual(len(result["primary_locations"]), s.MAX_LOCATION_ROWS)
        self.assertEqual(result["primary_locations_omitted"], 2)
        self.assertEqual(result["findings"], s.MAX_LOCATION_ROWS + 2)
        self.assertEqual(result["by_rule"][0]["count"], s.MAX_LOCATION_ROWS + 2)


if __name__ == "__main__":
    unittest.main()
