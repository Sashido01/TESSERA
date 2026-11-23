"""T11.01: static supply-chain and isolation checks for reference-format CI."""
from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
UPSTREAM = "83021e2be457a9b6679148719c1f6074f0ad975e"
WORKFLOW = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
LOCK = (ROOT / "tools" / "skills-ref-requirements.txt").read_text(encoding="utf-8")


def controls(workflow: str, lock: str) -> list[str]:
    problems = []
    ref = "ref: " + UPSTREAM
    if "repository: agentskills/agentskills" not in workflow or workflow.count(ref) != 1:
        problems.append("UPSTREAM_REVISION_NOT_PINNED")
    if f'git -C .external/agentskills rev-parse HEAD)" = "{UPSTREAM}"' not in workflow:
        problems.append("UPSTREAM_SHA_NOT_VERIFIED")
    if "path: .external/agentskills" not in workflow or workflow.count("persist-credentials: false") < 2:
        problems.append("REFERENCE_CHECKOUT_NOT_ISOLATED")
    if ("--only-binary=:all: --require-hashes -r tools/skills-ref-requirements.txt" not in workflow
            or "tools/check_reference_skills.py --repo . --reference-src .external/agentskills/skills-ref/src" not in workflow):
        problems.append("REFERENCE_VALIDATION_NOT_REQUIRED")
    # Step titles and comments may mention the safe command. Only executable
    # direct invocation is forbidden: CI must use the isolated wrapper.
    direct_publish = re.search(
        r"(?m)^[ \\t]*(?:-[ \\t]*)?(?:run:[ \\t]*)?gh[ \\t]+skill[ \\t]+publish\\b",
        workflow,
    )
    if direct_publish or "gh release create" in workflow or "pip install -e" in workflow:
        problems.append("REFERENCE_UNSAFE_EXECUTION")
    try:
        build = workflow.index("run: python tools/build_catalog_package.py")
        checkout = workflow.index("repository: agentskills/agentskills")
        if checkout < build or checkout > workflow.index("\n  tag_microversion:"):
            problems.append("REFERENCE_CHECKOUT_ORDER_UNSAFE")
    except ValueError:
        problems.append("REFERENCE_CHECKOUT_ORDER_UNVERIFIED")
    lines = [line.strip() for line in lock.splitlines() if line.strip() and not line.startswith("#")]
    if len(lines) != 5 or any(
        not re.fullmatch(
            r"[a-z0-9-]+==[0-9][0-9a-zA-Z.]*"
            r"(?:; sys_platform == 'win32')? --hash=sha256:[0-9a-f]{64}",
            line,
        )
        for line in lines
    ):
        problems.append("REFERENCE_DEPENDENCIES_NOT_HASH_PINNED")
    return problems


class ReferenceWorkflowTests(unittest.TestCase):
    def test_repository_controls(self):
        self.assertEqual(controls(WORKFLOW, LOCK), [])

    def test_unpinned_source_rejected(self):
        self.assertIn("UPSTREAM_REVISION_NOT_PINNED",
                      controls(WORKFLOW.replace(UPSTREAM, "main"), LOCK))

    def test_missing_checkout_proof_rejected(self):
        self.assertIn("UPSTREAM_SHA_NOT_VERIFIED",
                      controls(WORKFLOW.replace("git -C .external/agentskills rev-parse HEAD",
                                                "git -C other rev-parse HEAD"), LOCK))

    def test_hashless_dependencies_rejected(self):
        self.assertIn("REFERENCE_DEPENDENCIES_NOT_HASH_PINNED",
                      controls(WORKFLOW, LOCK.replace(" --hash=sha256:", " #sha256:")))

    def test_unsafe_publication_rejected(self):
        self.assertIn("REFERENCE_UNSAFE_EXECUTION",
                      controls(WORKFLOW + "\ngh skill publish\n", LOCK))

    def test_reference_checkout_before_build_rejected(self):
        changed = WORKFLOW.replace("repository: agentskills/agentskills",
                                    "repository: agentskills/agentskills", 1)
        changed = changed.replace(
            "run: python tools/build_catalog_package.py",
            "run: python tools/build_catalog_package.py",
        )
        # Explicit mutation of source positions; no Git/network effects.
        checked = changed.replace(
            "repository: agentskills/agentskills",
            "repository: other/repo",
        )
        self.assertIn("UPSTREAM_REVISION_NOT_PINNED", controls(checked, LOCK))


if __name__ == "__main__":
    unittest.main()
