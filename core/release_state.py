"""T09.04: pure state reduction; no status represents publication of an app."""
from __future__ import annotations


def evidence_stage(
    *,
    problems: list[str],
    local_tag_status: str,
    remote_tag_status: str,
    checks_status: str,
    ci_status: str = "NOT_CHECKED",
) -> str:
    """Return the strongest observed evidence, never a RELEASED claim."""
    if problems or local_tag_status != "PASS":
        return "BLOCKED"
    if ci_status == "PASS":
        return "CI_AND_REMOTE_TAG_VERIFIED" if remote_tag_status == "PASS" else "CI_VERIFIED"
    if ci_status not in ("NOT_CHECKED",):
        return "BLOCKED"
    if remote_tag_status == "PASS" and checks_status == "PASS":
        return "REMOTE_TAG_VERIFIED_CHECKS_PASSED"
    if remote_tag_status == "PASS":
        return "REMOTE_TAG_VERIFIED_CHECKS_NOT_RUN"
    if remote_tag_status not in ("NOT_CHECKED",):
        return "BLOCKED"
    if checks_status == "PASS":
        return "LOCAL_TAG_VERIFIED_CHECKS_PASSED"
    if checks_status not in ("NOT_RUN",):
        return "BLOCKED"
    return "LOCAL_TAG_VERIFIED_CHECKS_NOT_RUN"
