#!/usr/bin/env python3
"""Integrated static Tier 1, with explicit scanner scope and no raw CI reports."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

from check_nvidia_tier1 import VERSION, REPORT, NAME, require
from check_official_local_install import fixture_env, tree_fingerprint, InstallCheckError

CHECKS = "schema,version,security,pii,license,code-integrity,unicode,quality,lint,harness,dependency"
VALIDATORS = {
    "Schema & Repository Governance", "Semantic Version Validation", "Security Scan",
    "PII Scan", "License Compliance", "Code Risk Analysis", "Secrets Detection",
    "Code Integrity & Hygiene", "Unicode Smuggling Detection", "QUALITY",
    "SCRIPT_LINT", "Harness Compatibility", "Dependency Vulnerability Audit",
}
SCANNERS = {"Security Scan": ("skillspector", "2.13.7"),
            "Code Risk Analysis": ("bandit", "1.9.4"),
            "Secrets Detection": ("gitleaks", "8.30.1")}
GITLEAKS_SHA = "88f91962aa2f93ac6ab281d553b9e125f5197bbbce38f9f2437f7299c32e5509"
MAX_REPORT = 16 * 1024 * 1024
SEMGREP_VERSION = "1.182.0"
SEMGREP_RULES_BLOB = "3ef2067b69ef50f09b39c933771f751bc227b3db"
SEMGREP_RULES_SHA256 = "fff4537f6679a52c48e024e001b73e163b24587635a028e5c012583f19876abf"
SEMGREP_RULES_SIZE = 3376
SEMGREP_CONTROL_RULE = "skillevaluator.python.dynamic-code-execution"

# Explicitly support the pinned upstream SecretsValidator argument contract only.
# No arbitrary flags, reports on disk, or silent fallback to an older scanner.
SHIM = r'''import sys
sys.path.insert(0, TOOLS)
from check_integrated_gitleaks import main
sys.exit(main(sys.argv[1:], ROOT, BINARY))
'''


def summary(report, rc):
    require(isinstance(report, dict) and report.get("version") == VERSION
            and rc in (0, 1), "FULL_TIER1_VERSION_OR_EXIT")
    workflow = report.get("workflow")
    require(isinstance(workflow, dict) and workflow.get("tier") == 1
            and isinstance(workflow.get("stages"), dict)
            and workflow["stages"].get("llm") == {
                "status": "skipped", "reason": "LLM checks disabled by --no-llm."},
            "FULL_TIER1_SCOPE")
    rows = report.get("results")
    require(isinstance(rows, list) and len(rows) == len(VALIDATORS)
            and all(isinstance(r, dict) for r in rows)
            and {r.get("validator") for r in rows} == VALIDATORS, "FULL_TIER1_VALIDATORS")
    states = {}
    for row in rows:
        name = row["validator"]
        status = row.get("status")
        require(status in ("passed", "failed", "skipped", "incomplete")
                and isinstance(row.get("skipped"), bool)
                and isinstance(row.get("incomplete_scans"), list)
                and isinstance(row.get("passed"), bool), "FULL_TIER1_ROW")
        findings = row.get("findings")
        require(isinstance(findings, list) and len(findings) <= 10000, "FULL_TIER1_FINDINGS")
        counts = {s: 0 for s in ("critical", "high", "medium", "low", "info")}
        high_attribution = {"aggregate_risk_gate": 0, "other_high": 0}
        for item in findings:
            require(isinstance(item, dict) and isinstance(item.get("severity"), str)
                    and item["severity"].lower() in counts, "FULL_TIER1_FINDING")
            severity = item["severity"].lower()
            counts[severity] += 1
            if name == "Security Scan" and severity == "high":
                # Only the exact pinned upstream structured identifier denotes the
                # aggregate gate. Unknown identifiers remain other HIGH findings.
                is_gate = (item.get("category") == "SECURITY"
                           and item.get("check_name") == "skillspector_risk_score")
                high_attribution["aggregate_risk_gate" if is_gate else "other_high"] += 1
        scanners = row.get("scanners", {})
        require(isinstance(scanners, dict), "FULL_TIER1_SCANNERS")
        if name in SCANNERS:
            scanner, version = SCANNERS[name]
            require(scanners.get(scanner) == version, "FULL_TIER1_SCANNER_VERSION:" + scanner)
            require(not row["skipped"] and not row["incomplete_scans"]
                    and status in ("passed", "failed"), "FULL_TIER1_SCANNER_INCOMPLETE:" + scanner)
        if name == "Code Risk Analysis":
            require(scanners.get("semgrep") == SEMGREP_VERSION, "FULL_TIER1_SCANNER_VERSION:semgrep")
        states[name] = {"status": status.upper(), "skipped": row["skipped"],
                        "incomplete": bool(row["incomplete_scans"]), "findings": counts}
        if name == "Security Scan":
            states[name]["high_attribution"] = high_attribution
    overall = report.get("overall_passed")
    require(type(overall) is bool and (rc == 0) == overall, "FULL_TIER1_EXIT_MISMATCH")
    require(isinstance(report.get("incomplete_scans"), list), "FULL_TIER1_INCOMPLETE_FIELD")
    incomplete = bool(report["incomplete_scans"]) or any(
        r["incomplete"] or r["skipped"] or r["status"] not in ("PASSED", "FAILED")
        for r in states.values())
    return {"validators": states, "policy_verdict": "PASS" if overall else "FAIL",
            "coverage": "PARTIAL" if incomplete else "ALL_VALIDATOR_ROWS",
            "scanner_versions": {**{s: v for s, v in SCANNERS.values()}, "semgrep": SEMGREP_VERSION},
            "semgrep": "EXECUTED", "certification": "NOT_VERIFIED"}


def executable(path):
    path = path.resolve(strict=True)
    require(path.is_file() and os.access(path, os.X_OK), "FULL_TIER1_EXECUTABLE")
    return path


CONTROL_RULE = "tessera-probe"

def control_result(result, marker, *, detected):
    """Validate the live shim output without exposing the marker or raw report."""
    require(len(result.stdout) <= MAX_REPORT and len(result.stderr) <= MAX_REPORT,
            "FULL_TIER1_CONTROL_OUTPUT_LIMIT")
    require(marker not in result.stdout and marker not in result.stderr,
            "FULL_TIER1_CONTROL_REDACTION")
    require(result.returncode == (10 if detected else 0), "FULL_TIER1_CONTROL_EXIT")
    rows = json.loads(result.stdout)
    if not detected:
        require(rows is None or rows == [], "FULL_TIER1_CONTROL_CLEAN")
        return
    require(isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict),
            "FULL_TIER1_CONTROL_FINDING")
    row = rows[0]
    require(row.get("RuleID") == CONTROL_RULE and row.get("Secret") == "REDACTED"
            and row.get("File") in ("probe.txt", "./probe.txt"),
            "FULL_TIER1_CONTROL_FINDING")


def live_shim_control(run, shim, temp):
    """Exercise the exact upstream argument shape against the real pinned binary."""
    fixture = temp / "redaction-control"
    fixture.mkdir()
    config = temp / "redaction-control.toml"
    config_bytes = (b'[[rules]]\nid = "tessera-probe"\n'
                    b'description = "Nonfunctional synthetic control"\n'
                    b'regex = \'TESSERA_PROBE_[A-Z0-9]{12}\'\n')
    config.write_bytes(config_bytes)
    target = fixture / "probe.txt"
    marker = b"TESSERA_" + b"PROBE_" + b"A7B4C9D2E6F8"
    args = ["detect", "--source", ".", "--report-format", "json", "--report-path", "-",
            "--exit-code", "10", "--config", str(config), "--no-git"]
    for detected, content in ((False, b"plain control\n"), (True, marker + b"\n")):
        target.write_bytes(content)
        result = run(shim, args, cwd=fixture)
        control_result(result, marker, detected=detected)
        require(set(fixture.iterdir()) == {target} and not target.is_symlink()
                and target.read_bytes() == content and not config.is_symlink()
                and config.read_bytes() == config_bytes, "FULL_TIER1_CONTROL_MUTATION")
    return {"clean": "PASS", "detection": "PASS", "stdout_stderr_redaction": "PASS",
            "fixture_entries_unchanged": "PASS", "scope": "LIVE_PINNED_SHIM_CUSTOM_RULE"}


def semgrep_control_result(result, target, *, detected):
    require(len(result.stdout) <= MAX_REPORT and len(result.stderr) <= MAX_REPORT,
            "FULL_TIER1_SEMGREP_OUTPUT")
    require(result.returncode == (1 if detected else 0), "FULL_TIER1_SEMGREP_EXIT")
    report = json.loads(result.stdout)
    require(isinstance(report, dict) and report.get("errors") == []
            and isinstance(report.get("results"), list), "FULL_TIER1_SEMGREP_REPORT")
    paths = report.get("paths")
    require(isinstance(paths, dict) and isinstance(paths.get("scanned"), list)
            and len(paths["scanned"]) == 1, "FULL_TIER1_SEMGREP_COVERAGE")

    def same_path(value):
        return isinstance(value, str) and (target.parent / value).resolve() == target

    require(same_path(paths["scanned"][0]), "FULL_TIER1_SEMGREP_COVERAGE")
    rows = report["results"]
    require(len(rows) == int(detected), "FULL_TIER1_SEMGREP_FINDINGS")
    if detected:
        row = rows[0]
        require(isinstance(row, dict) and row.get("check_id") == SEMGREP_CONTROL_RULE
                and same_path(row.get("path")), "FULL_TIER1_SEMGREP_FINDINGS")


def semgrep_rules_ok(raw):
    # SHA-256 verifies the exact reviewed upstream bytes; the Git blob OID
    # identifies provenance only, and neither constitutes a wheel signature.
    require(len(raw) == SEMGREP_RULES_SIZE
            and hashlib.sha256(raw).hexdigest() == SEMGREP_RULES_SHA256,
            "FULL_TIER1_SEMGREP_RULES")


def semgrep_control(run, semgrep, rules, temp):
    raw = rules.read_bytes()
    semgrep_rules_ok(raw)
    fixture = temp / "semgrep-control"
    fixture.mkdir()
    target = fixture / "probe.py"
    args = ["scan", "--config", str(rules), "--json", "--quiet", "--metrics", "off",
            "--disable-version-check", "--no-rewrite-rule-ids", "--error", str(target)]
    # These are scanned as text, never executed.
    for detected, content in ((False, b"def probe(value):\n    return str(value)\n"),
                              (True, b"def probe(value):\n    return eval(value)\n")):
        target.write_bytes(content)
        result = run(semgrep, args, 90, cwd=fixture)
        semgrep_control_result(result, target, detected=detected)
        require(set(fixture.iterdir()) == {target} and not target.is_symlink()
                and target.read_bytes() == content and rules.read_bytes() == raw,
                "FULL_TIER1_SEMGREP_MUTATION")
    return {"clean": "PASS", "detection": "PASS", "coverage": "PASS",
            "rules_blob": SEMGREP_RULES_BLOB, "rules_sha256": SEMGREP_RULES_SHA256,
            "fixture_preserved": "PASS"}


def bandit_control(run, shim, temp, ini):
    from check_integrated_bandit import exclusions, INI_BLOB, INI_SHA256
    fixture = temp / "bandit-control"
    fixture.mkdir()
    target = fixture / "probe.py"
    ignored = fixture / "tests"
    ignored.mkdir()
    (ignored / "test_probe.py").write_bytes(b"eval('1 + 1')\n")
    (fixture / ".bandit").write_text("[bandit]\nskips=B307\n", encoding="utf-8")
    args = ["-r", str(fixture), "-f", "json", "-q", "-ll", "--exclude",
            exclusions(fixture), "--ini", str(ini), "--ignore-nosec"]
    for detected, content in ((False, b"answer = 42\n"), (True, b"eval('1 + 1')  # nosec\n")):
        target.write_bytes(content)
        result = run(shim, args, 115)
        require(result.returncode == int(detected), "FULL_TIER1_BANDIT_CONTROL_EXIT")
        report = json.loads(result.stdout)
        require(report.get("errors") == [] and isinstance(report.get("results"), list)
                and (not report["results"] if not detected else
                     len(report["results"]) == 1 and report["results"][0]["test_id"] == "B307"
                     and report["results"][0]["filename"] == str(target)), "FULL_TIER1_BANDIT_CONTROL")
        require(target.read_bytes() == content, "FULL_TIER1_BANDIT_CONTROL_MUTATION")
    return {"clean": "PASS", "detection": "PASS", "ignored_nosec_and_skill_ini": "PASS",
            "excluded_test": "PASS", "fixture_preserved": "PASS",
            "ini_blob": INI_BLOB, "ini_sha256": INI_SHA256}


def skillspector_control(run, shim, temp):
    from check_skillspector_container import fixture_text
    from check_integrated_skillspector import checked_report
    root = temp / "sp-controls"
    root.mkdir()
    for label in ("clean", "negative"):
        skill = root / ("fixture-" + label)
        skill.mkdir()
        content = fixture_text(label)
        (skill / "SKILL.md").write_bytes(content)
        result = run(shim, ["scan", str(skill), "--format", "json", "--no-llm"], 165)
        report = checked_report(result.returncode, result.stdout, {"SKILL.md": len(content)})
        require(report["findings"] == 0 if label == "clean" else
                any(row["rule"] == "P1" for row in report["by_rule"]), "FULL_TIER1_SP_CONTROL")
        require((skill / "SKILL.md").read_bytes() == content, "FULL_TIER1_SP_MUTATION")
    require(run(shim, ["scan", str(root), "--format", "json", "--no-llm"]).returncode == 2,
            "FULL_TIER1_SP_REJECT")
    return {"clean": "PASS", "detection": "PASS", "source_preserved": "PASS", "reject_scope": "PASS"}


def accept(repo, cli, skillspector, bandit, gitleaks, semgrep, semgrep_rules, bandit_packages, sp_packages):
    repo = repo.resolve(strict=True)
    cli, skillspector, bandit, gitleaks, semgrep = map(executable, (cli, skillspector, bandit, gitleaks, semgrep))
    semgrep_rules = semgrep_rules.resolve(strict=True)
    bandit_packages = bandit_packages.resolve(strict=True)
    sp_packages = sp_packages.resolve(strict=True)
    bandit_ini = semgrep_rules.parent / "bandit.ini"
    from check_integrated_bandit import ini_ok
    ini_ok(bandit_ini.read_bytes())
    require(hashlib.sha256(gitleaks.read_bytes()).hexdigest() == GITLEAKS_SHA,
            "FULL_TIER1_GITLEAKS_HASH")
    original = repo / "skills"
    before = tree_fingerprint(original)
    with tempfile.TemporaryDirectory(prefix="tessera-full-tier1-") as folder:
        temp = pathlib.Path(folder)
        env = fixture_env(temp)
        private_bin = temp / "bin"
        private_bin.mkdir()
        private_tmp = temp / "tmp"
        private_tmp.mkdir()
        shim = private_bin / "gitleaks"
        require(not any(c.isspace() for c in sys.executable), "FULL_TIER1_PYTHON_PATH")
        shim.write_text("#!" + sys.executable + "\nBINARY = " + repr(str(gitleaks))
                        + "\nROOT = " + repr(str(temp)) + "\nTOOLS = "
                        + repr(str(pathlib.Path(__file__).resolve().parent)) + "\n" + SHIM,
                        encoding="utf-8")
        shim.chmod(0o700)
        bandit_shim = private_bin / "bandit"
        receipts = temp / "bandit-receipts"
        receipts.mkdir()
        bandit_shim.write_text("#!" + sys.executable + "\nimport sys\nsys.path.insert(0, "
                               + repr(str(pathlib.Path(__file__).resolve().parent))
                               + ")\nfrom check_integrated_bandit import main\nsys.exit(main(sys.argv[1:], "
                               + repr(str(temp)) + ", " + repr(str(bandit_packages)) + ", "
                               + repr(str(bandit_ini)) + "))\n", encoding="utf-8")
        bandit_shim.chmod(0o700)
        sp_shim = private_bin / "skillspector"
        sp_receipts = temp / "sp-receipts"
        sp_receipts.mkdir()
        sp_shim.write_text("#!" + sys.executable + "\nimport sys\nsys.path.insert(0, "
                           + repr(str(pathlib.Path(__file__).resolve().parent))
                           + ")\nfrom check_integrated_skillspector import main\nsys.exit(main(sys.argv[1:], "
                           + repr(str(temp)) + ", " + repr(str(sp_packages)) + "))\n", encoding="utf-8")
        sp_shim.chmod(0o700)
        env.update({"PATH": os.pathsep.join((str(private_bin), str(cli.parent), "/usr/bin", "/bin")),
                    "SKILLEVALUATOR_SKILLSPECTOR_PATH": str(sp_shim),
                    "SKILLEVALUATOR_BANDIT_PATH": str(bandit_shim),
                    "SKILLEVALUATOR_SEMGREP_PATH": str(semgrep),
                    "SKILLEVALUATOR_REQUIRE_SEMGREP": "1",
                    "SEMGREP_SEND_METRICS": "off",
                    "SEMGREP_ENABLE_VERSION_CHECK": "0",
                    "SKILLEVALUATOR_RUNTIME_DIR": str(temp / "runtime"),
                    "TMPDIR": str(private_tmp), "PYTHONNOUSERSITE": "1",
                    "PYTHONDONTWRITEBYTECODE": "1", "PYTHONSAFEPATH": "1",
                    "PIP_NO_INDEX": "1", "UV_OFFLINE": "1", "CI": "true"})
        require(shutil.which("gitleaks", path=env["PATH"]) == str(shim)
                and shutil.which("bandit", path=env["PATH"]) == str(bandit_shim)
                and shutil.which("skillspector", path=env["PATH"]) == str(sp_shim)
                and shutil.which("semgrep", path=env["PATH"]) is None,
                "FULL_TIER1_SCANNER_RESOLUTION")
        def run(path, args, timeout=15, *, cwd=temp):
            return subprocess.run([str(path), *args], cwd=cwd, env=env,
                                  stdin=subprocess.DEVNULL, capture_output=True,
                                  timeout=timeout, check=False)
        version = run(cli, ["--version"])
        require(version.returncode == 0 and version.stdout.strip() ==
                ("skillevaluator, version " + VERSION).encode(), "FULL_TIER1_CLI_VERSION")
        version = run(sp_shim, ["--version"], 165)
        require(version.returncode == 0 and version.stdout.strip() ==
                b"SkillSpector v2.13.7", "FULL_TIER1_SKILLSPECTOR_VERSION")
        sp_probe = skillspector_control(run, sp_shim, temp)
        version = run(bandit_shim, ["--version"], 115)
        require(version.returncode == 0 and re.search(rb"\bbandit 1\.9\.4\b", version.stdout),
                "FULL_TIER1_BANDIT_VERSION")
        bandit_probe = bandit_control(run, bandit_shim, temp, bandit_ini)
        version = run(semgrep, ["--version"], 30)
        require(version.returncode == 0 and version.stdout.strip() == SEMGREP_VERSION.encode(),
                "FULL_TIER1_SEMGREP_VERSION")
        semgrep_probe = semgrep_control(run, semgrep, semgrep_rules, temp)
        version = run(shim, ["version"])
        require(version.returncode == 0 and version.stdout.strip() == b"8.30.1",
                "FULL_TIER1_GITLEAKS_VERSION")
        require(run(shim, ["detect", "--report-path", "unexpected.json"]).returncode == 2
                and not (temp / "unexpected.json").exists(), "FULL_TIER1_SHIM_REJECT")
        control = live_shim_control(run, shim, temp)
        source = temp / "skills"
        shutil.copytree(original, source)
        require(tree_fingerprint(source) == before, "FULL_TIER1_SNAPSHOT")
        results = {}
        for skill in sorted(source.iterdir()):
            require(skill.is_dir() and not skill.is_symlink() and NAME.fullmatch(skill.name)
                    and (skill / "SKILL.md").is_file(), "FULL_TIER1_SKILL")
            # No third-party dependency resolution in this candidate. The actual
            # skill has no Python dependency manifest; future manifests need a
            # separate pinned audit contract rather than implicit network calls.
            require(not any(p.is_file() for p in skill.rglob("*")
                    if p.name in ("pyproject.toml", "Pipfile", "Pipfile.lock", "setup.py", "setup.cfg")
                    or p.name.startswith("requirements")), "FULL_TIER1_DEPENDENCY_MANIFEST")
            out = temp / "reports" / skill.name
            result = run(cli, ["tier1", str(skill), "--no-llm", "--checks", CHECKS,
                               "--min-score", "70", "-r", "json", "-o", str(out)], 180)
            report = out / REPORT
            require(report.is_file() and not report.is_symlink()
                    and 0 < report.stat().st_size <= MAX_REPORT, "FULL_TIER1_REPORT_MISSING")
            results[skill.name] = summary(json.loads(report.read_text(encoding="utf-8")), result.returncode)
            require(any(x.name.startswith(skill.name + "-") for x in receipts.iterdir()),
                    "FULL_TIER1_BANDIT_RECEIPT")
            require(any(x.name.startswith(skill.name + "-") for x in sp_receipts.iterdir()),
                    "FULL_TIER1_SP_RECEIPT")
        require(results and tree_fingerprint(source) == before
                and tree_fingerprint(original) == before, "FULL_TIER1_SOURCE_MUTATED")
        require(not (temp / "runtime" / "skillspector").exists()
                and not (temp / "runtime" / "gitleaks").exists()
                and not (temp / "runtime" / "bandit").exists(), "FULL_TIER1_MANAGED_FALLBACK")
        require(hashlib.sha256(gitleaks.read_bytes()).hexdigest() == GITLEAKS_SHA,
                "FULL_TIER1_GITLEAKS_CHANGED")
    return {"execution": "PASS", "scope": "INTEGRATED_STATIC_TIER1", "checks": CHECKS.split(","),
            "llm": "DISABLED", "semgrep": "EXECUTED", "skills": results,
            "semgrep_control": semgrep_probe,
            "policy": "ADVISORY_FINDINGS", "certification": "NOT_VERIFIED",
            "live_shim_control": control, "gitleaks_isolation": "DOCKER_RESTRICTED_SNAPSHOT",
            "bandit_isolation": "DOCKER_RESTRICTED_SNAPSHOT", "bandit_control": bandit_probe,
            "skillspector_isolation": "DOCKER_RESTRICTED_SNAPSHOT", "skillspector_control": sp_probe}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "cli", "skillspector", "bandit", "gitleaks", "semgrep", "semgrep-rules", "bandit-packages", "sp-packages"):
        parser.add_argument("--" + name, type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        result = accept(args.repo, args.cli, args.skillspector, args.bandit, args.gitleaks,
                        args.semgrep, args.semgrep_rules, args.bandit_packages, args.sp_packages)
    except (InstallCheckError, OSError, ValueError, UnicodeError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + (str(exc) if isinstance(exc, InstallCheckError)
                              else "FULL_TIER1_RUNTIME_FAILED"), file=sys.stderr)
        return 1
    print("FULL_TIER1_EXECUTION_PASS: " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
