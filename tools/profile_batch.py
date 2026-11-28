"""Read-only batch preflight binding selected stages to independent raw trees.

No filesystem writes, external calls, authorization or atomic snapshot claim.
Both supplied resolutions must come from an independently trusted resolver.
"""
from __future__ import annotations

from catalog_index import REPO, require
from profile_plan import disjoint, identity, metadata, ordinary_root, plan, read_resolution
from gh_stage import verify
from profile_journal import encode


def preflight(profile, stage, raw, resolution, *, baseline=None,
              baseline_raw=None, baseline_resolution=None):
    """Return records only when every selected decision and proof agrees.

    Baseline proofs may cover only selected skills. Every planned update
    requires the independently pinned previous version, not a local guess.
    """
    desired = read_resolution(resolution)
    names = {row["id"] for row in desired["skills"]}
    old_inputs = (baseline, baseline_raw, baseline_resolution)
    require(all(x is None for x in old_inputs) or all(x is not None for x in old_inputs),
            "BATCH_BASELINE_INPUT")
    roots = [ordinary_root(p) for p in (profile, stage, raw, baseline, baseline_raw)
             if p is not None]
    disjoint(roots)
    identities = [identity(metadata(p)) for p in roots]
    require(metadata(profile).st_dev == metadata(stage).st_dev, "BATCH_CROSS_DEVICE")

    new_proof = verify(raw, stage, resolution)
    current = {row["id"]: row for row in new_proof["skills"]}
    require(set(current) == names and len(current) == len(new_proof["skills"]),
            "BATCH_NEW_PROOF_SET")
    old = {}
    if baseline is not None:
        previous = read_resolution(baseline_resolution)
        old_names = {row["id"] for row in previous["skills"]}
        require(old_names <= names, "BATCH_BASELINE_SELECTION")
        old_proof = verify(baseline_raw, baseline, baseline_resolution)
        old = {row["id"]: row for row in old_proof["skills"]}
        require(set(old) == old_names and len(old) == len(old_proof["skills"]),
                "BATCH_OLD_PROOF_SET")

    planned = plan(profile, stage, baseline, resolution)
    rows = planned["decisions"]
    require({row["id"] for row in rows} == names and len(rows) == len(names),
            "BATCH_PLAN_SET")
    require(all(row["decision"] in ("PLAN_INSTALL", "PLAN_UPDATE", "SKIP_MATCHING_STAGE")
                for row in rows), "BATCH_PLAN_BLOCKED")
    records, skipped = [], []
    for row in rows:
        name = row["id"]
        proof = current[name]
        require((row["desired_version"], row["stage_sha256"]) ==
                (proof["version"], proof["stage_sha256"]), "BATCH_STAGE_CHANGED")
        if row["decision"] == "SKIP_MATCHING_STAGE":
            require(row["observed_version"] == proof["version"], "BATCH_SKIP_VERSION")
            skipped.append({"id": name, "version": proof["version"],
                            "sha256": proof["stage_sha256"]})
            continue
        update = row["decision"] == "PLAN_UPDATE"
        if update:
            require(name in old, "BATCH_BASELINE_PROOF_REQUIRED")
            require((row["observed_version"], row["baseline_sha256"]) ==
                    (old[name]["version"], old[name]["stage_sha256"]),
                    "BATCH_BASELINE_CHANGED")
        record = {"schema_version": 1, "repository": REPO, "id": name,
                  "operation": "update" if update else "install", "phase": "PREPARED",
                  "old_version": old[name]["version"] if update else None,
                  "old_sha256": old[name]["stage_sha256"] if update else None,
                  "new_version": proof["version"], "new_sha256": proof["stage_sha256"]}
        encode(record)  # Strict journal schema; never write a journal here.
        records.append(record)
    require([identity(metadata(ordinary_root(p))) for p in roots] == identities,
            "BATCH_ROOT_CHANGED")
    return {"status": "BATCH_PREFLIGHT_OBSERVED", "selection": desired["selection"],
            "operation": desired["operation"], "selected_count": len(names),
            "records": records, "skipped": skipped,
            "pins": [current[row["id"]] for row in desired["skills"]],
            "apply_authorized": False, "snapshot_atomic": False,
            "source_authenticity": "NOT_VERIFIED", "exclusive_access": "NOT_VERIFIED",
            "live_ref_freshness": "NOT_VERIFIED", "lockfile": "NOT_VERIFIED"}
