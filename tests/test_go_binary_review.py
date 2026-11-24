"""Offline tests of the pinned Govulncheck streaming protocol."""
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import check_go_binary_review as g


def encode(*rows):
    return "\n".join(json.dumps(row) for row in rows).encode()


class BinaryReviewTests(unittest.TestCase):
    def extraction(self, symbols=True):
        body = {"goVersion": "go1.26.11", "goos": "linux", "goarch": "amd64",
                "modules": [{"Path": "example.invalid/test"}]}
        if symbols:
            body["pkgSymbols"] = [{"pkg": "example.invalid/test", "name": "Run"}]
        return g.extract_evidence(encode({"name": "govulncheck-extract", "version": "0.1.0"}, body))

    def config(self):
        return {"config": {"protocol_version": "v1.0.0", "scanner_name": "govulncheck",
                           "scanner_version": "v0.0.0-" + g.PIN[:12] + "-20261124",
                           "db": g.DB, "scan_mode": "binary", "scan_level": "symbol"}}

    def sbom(self):
        return {"SBOM": {"go_version": "go1.26.11", "modules": [{"path": "stdlib"}]}}

    def finding(self):
        return {"finding": {"osv": "GO-2026-0001", "trace": [
            {"module": "example.invalid/test", "package": "example.invalid/test", "function": "Run"}]}}

    def test_clean_stream(self):
        result = g.scan_evidence(encode(self.config(), self.sbom()), self.extraction())
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["call_reachability"], "NOT_VERIFIED")

    def test_symbols_and_stripped_fallback_distinct(self):
        raw = encode(self.config(), self.sbom(), {"osv": {"id": "GO-2026-0001",
                     "details": "synthetic private text"}}, self.finding(), self.finding())
        self.assertEqual(g.scan_evidence(raw, self.extraction())["findings"],
                         [{"id": "GO-2026-0001", "level": "SYMBOL_REPORTED"}])
        result = g.scan_evidence(raw, self.extraction(False))
        self.assertEqual(result["findings"][0]["level"], "MODULE_ONLY_FALLBACK")
        self.assertNotIn("synthetic private text", str(result))

    def test_missing_config_sbom_or_advisory_rejected(self):
        for raw in (encode(self.sbom()), encode(self.config()),
                    encode(self.config(), self.sbom(), self.finding())):
            with self.subTest(raw=raw), self.assertRaises(g.InstallCheckError):
                g.scan_evidence(raw, self.extraction())

    def test_wrong_scanner_or_mode_rejected(self):
        for key, value in (("scanner_version", "v0.0.0-wrong"), ("scan_mode", "source"),
                           ("db", "https://example.invalid")):
            cfg = self.config()
            cfg["config"][key] = value
            with self.subTest(key=key), self.assertRaises(g.InstallCheckError):
                g.scan_evidence(encode(cfg, self.sbom()), self.extraction())

    def test_wrong_platform_and_malformed_extraction_rejected(self):
        for raw in (encode({"name": "bad", "version": "0.1.0"}, {}),
                    encode({"name": "govulncheck-extract", "version": "0.1.0"},
                           {"goVersion": "go1.26.11", "goos": "windows", "goarch": "amd64"})):
            with self.assertRaises(g.InstallCheckError):
                g.extract_evidence(raw)

    def scanner_meta(self):
        return ("govulncheck: go1.26.11\n"
                "\tpath\tgolang.org/x/vuln/cmd/govulncheck\n"
                "\tmod\tgolang.org/x/vuln\t(devel)\n"
                "\tdep\tgolang.org/x/mod\tv0.43.0\n"
                "\tbuild\tvcs.revision=" + g.PIN + "\n"
                "\tbuild\tvcs.modified=false\n").encode()

    def test_scanner_inventory_checks_dependencies_toolchain_and_commit(self):
        def lookup(queries):
            self.assertEqual(len(queries), 5)
            self.assertEqual(queries[-1], {"commit": g.PIN})
            self.assertEqual({row["package"]["name"] for row in queries[:-1]},
                             {"golang.org/x/vuln", "golang.org/x/mod", "stdlib", "toolchain"})
            return [["GO-2026-0001"], [], [], [], ["GO-2026-0002"]]
        result = g.scanner_inventory(self.scanner_meta(), lookup)
        self.assertEqual(result["modules"], 2)
        self.assertEqual(result["findings"][0]["module"], "golang.org/x/mod")
        self.assertEqual(result["source_commit_ids"], ["GO-2026-0002"])

    def test_scanner_inventory_refuses_modified_or_missing_revision(self):
        for raw in (self.scanner_meta().replace(b"modified=false", b"modified=true"),
                    self.scanner_meta().replace(g.PIN.encode(), b"0" * 40),
                    self.scanner_meta().replace(b"v0.43.0", b"(devel)")):
            with self.subTest(raw=raw), self.assertRaises(g.InstallCheckError):
                g.scanner_inventory(raw, lambda _: self.fail("invalid scanner must not be queried"))

    def test_control_requires_exact_expected_fictitious_advisory(self):
        clean = {"findings": []}
        found = {"findings": [{"id": "GO-9999-9999"}]}
        g.control_expected(clean, False)
        g.control_expected(found, True)
        for report, expected in ((clean, True), (found, False),
                                 ({"findings": [{"id": "GO-2026-0001"}]}, True)):
            with self.subTest(report=report), self.assertRaises(g.InstallCheckError):
                g.control_expected(report, expected)


if __name__ == "__main__":
    unittest.main()
