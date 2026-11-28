# UP02 — local install/update plan

[Русский — оригинал](PROFILE_UPDATE_PLAN.md) | **English — translation**

**PARTIAL, independent candidate.** `python -B tools/profile_plan.py --profile <absolute-skills-root> --stage <absolute-new-stage-root> --baseline <absolute-old-stage-root> --resolution <absolute-resolver-json>`. All roots must exist, be disjoint and trusted. Baseline optional for absent and identical skills; differing existing tree requires an independent clean old-version copy, never a copy of the modified working directory. Resolution selects one, several or all skills and install/update intent; JSON itself is not authority. Never run this code from an unreviewed checkout.

Plan writes nothing, invokes no Git/gh, moves no files and executes no skills. Checks only selected trees including hidden/extra entries and modes, hashes actual bytes (including gh frontmatter), rechecks observed identity. For alias detection lists bounded immediate root names, does not open sibling skill content. On differing structure does not open unexpected working-skill files. BLOCKED on links/reparse/alias, special files, hardlinks, device crossing, overlapping roots, local changes, missing baseline, non-advancing version. PLAN_INSTALL / PLAN_UPDATE / SKIP_MATCHING_STAGE are relative to supplied copies, not upstream proof.

Limits: 512 entries/tree, 16 MiB/tree, 2 MiB/file, depth 8, 4096 direct entries/root, 128 MiB attempted reads and 60 s cooperative budget; not a hard I/O timeout or sandbox. Stable trusted filesystem; persistent change checks do not guarantee protection from TOCTOU, bind mounts, NTFS aliases/ACL or concurrent writers. No automatic authorization: apply_authorized false, source_authenticity NOT_VERIFIED, exclusive_access NOT_VERIFIED, snapshot_atomic false. Independently verify gh metadata/source; Git tree and stage fingerprint are different identifiers. Never copy local edits into baseline to obtain PLAN_UPDATE. Next boundary: independently bind each staging snapshot to exact GitHub tag/tree and gh metadata, crash-safe journal, no-clobber swap and rollback, native Windows/Linux, actual client.

12/12 focused Linux tests PASS (0.052 s, Python 3.13.5), actual synthetic files; exact source e7a2bf4d8e47b12a3dc7561c78a8521c5d0129ac, tests 5b3a5434a538fae82dfbd701f8f469880bf7ab39. Native/full CI pending. Independent branch depends on PR #101, no common version assigned. UP01/UP02/G03/G04/G05 remain PARTIAL.

## UP02.01 — raw tree proof (candidate)

`python -B tools/skill_tree.py --stage <absolute-raw-stage-root> --resolution <absolute-resolver-json>` reconstructs Git SHA-1 blob and tree objects directly from actual raw bytes, using Git directory sort order; requires exact expected tree and VERSION. All published current skill files use mode 100644, verified via GitHub tree inventory. Empty directories, unexpected executable mode, links, aliases and mismatching bytes are refused. Computes the same stage SHA-256 snapshot fingerprint as profile_plan in a single content pass; rechecks all observed entries across the batch. No Git/gh invocation, no writes, no execution, no source credentials. Supplied resolution must be independently authenticated and fresh; matching a supplied OID is not live tag or attestation verification. gh-injected SKILL.md does not match the raw tree and is deliberately refused; semantic validation of actual gh-injected metadata and binding both old/new verified stages to application remain open. No new runtime dependency introduced. 10/10 isolated Linux tests PASS (0.050 s), including actual git write-tree fixture, and combined UP02 22/22 PASS (0.086 s). Exact source 9c3b1d121b52b754364c932d6ba17f3fdfdb0d5d, tests 9e2a3ed7d9b0840420be0865fc64324386b1309b. Native Windows and real gh NOT_VERIFIED. No production updater.

Upstream gh v2.105.0 installer source confirms RecordInstall is called even with an explicit staging directory, independently of writing skill files; lockfile uses user home. Therefore staging with the actual user HOME can mutate shared lock metadata before safe replacement. Use a separately authorized isolated fixture home for actual acceptance, not an invented environment override to bypass restrictions. Actual lockfile reconciliation after safe update is a separate open requirement. [Installer source](https://github.com/cli/cli/blob/v2.105.0/internal/skills/installer/installer.go), [frontmatter source](https://github.com/cli/cli/blob/v2.105.0/internal/skills/frontmatter/frontmatter.go).

## Additional plan stability checks

After all selected operations recheck ordinary roots, alias observations, all metadata of observed trees (ancestors before descendants) and explicitly absent targets. Do not rely only on parent-directory mtime. Windows cross-method stat/fstat uses comparable fields with birthtime, same-method retains mode/ctime/attributes; reparse/zero inode refused. Three new regression methods: first stage mutation after second skill, previously absent target appearing with synthetic unchanged root stat, Windows ctime/attribute simulation. Combined isolated Linux 25/25 PASS (0.101 s). Exact profile_plan 9b23c5177b85fae81e88752a95ff10fdb87c7c9e, tests ee39642039440c38ff953e6d73b8d4a212c0f729; raw tree source/test unchanged. Native CI and actual gh open; not atomic, no apply authority or guarantee of exclusive access.

## Verify gh staging metadata (0.0.98 candidate)

0.0.97 main 4f0e5ec0175e42bf67afceef3360497d1261d140, CI 46062411446 SUCCESS, annotated tag object 726389b4f834b243413ab84ef36d9379bbd1684d.

UP02.02: read-only gh_stage binds supplied raw Git tree to installed staging and checks the exact five github-* metadata fields, original frontmatter fields, body, other file bytes, modes and stage fingerprint. Narrow YAML subset (plain/simple quoted scalars and >- without complex constructs); unsupported forms BLOCKED. Actual gh serialization, lockfile, live refs, apply authorization, atomicity and rollback NOT_VERIFIED. From 0.0.98 the tool is required in ZIP; 0.0.97 remains compatible. Ten fixture tests and package gate; native/full CI pending.

## Read-only recovery classification (0.0.99)

PR #105 CI 46065687896 PASS, squash b94fd6855f2a32179f6804cd8e562f7f5ca1f2f4; main CI/tag pending.

UP02.03: read-only single-skill recovery classifier. Compares a bounded strict journal with actual profile/stage/backup fingerprints, requires disjoint ordinary same-volume roots and rechecks observed identities. Distinguishes NOT_STARTED, OLD_IN_BACKUP, NEW_PRESENT, NEW_PRESENT_OLD_RETAINED; ambiguity and phase mismatch BLOCKED. Ten disposable fixture tests cover interruption between rename and phase record, local edit and missing stage. Does not create journals, rename/delete, authorize apply or prove durability. Next: separate writer with no-clobber primitives and crash recovery, fixtures first. Diagnostic candidate not included in runtime ZIP before acceptance.

## Append-only transaction phase journal (0.0.100)

0.0.99 main 67ad5669abb80819b0183ed4cc9234b377f27802, CI 46118526414 SUCCESS, annotated tag object 4501f60a678567e4efdacdd78e4a52c9005a871b.

UP02.03: append-only single-skill phase journal, separate canonical JSON records, strict phase sequence and immutable fields, O_CREAT|O_EXCL, file flush/fsync and postcheck. Partial records and unknown files block progress, existing records never overwritten. Nine fixture tests include collision and fsync failure. Library only for trusted exclusive directory: parent directory durability, ACL/races, actual crash, moves and rollback NOT_VERIFIED. No profile writes; not yet included in runtime ZIP.

## Move skills without overwriting (0.0.101)

PR #107 passed CI 46119327281 and was merged. Main verification and tag are pending.

Added a verified-directory no-overwrite move library: Windows rename and Linux renameat2(RENAME_NOREPLACE). Unsupported platforms or missing support fail closed; no unsafe fallback. Checks expected fingerprint, disjoint same-device roots, absent destination and identity after move. Nine disposable-directory tests. This is a primitive for trusted exclusive roots, not an installer: ACLs, ancestor races, power-loss durability, journal integration and rollback remain open. CI does not touch real profiles; not yet in the ZIP.

## Test the complete update cycle (0.0.102)

PR #108 passed CI 46120392984 and was merged. Main verification and tag pending.

Journal, move and recovery observation are integrated into one isolated fixture cycle. Install and update use automatically created temporary directories, including eight simulated interruption scenarios. Old tree remains in backup, neighboring skill unchanged. Six test methods. Not actual process termination, power-loss proof or a production updater. No arbitrary profile path or automatic rollback; ZIP unchanged.

## Added crash interruption tests (0.0.103)

PR #109 passed CI 46122145983 and was merged. Main verification and tag pending.

Added tests that forcibly terminate a child process at eight install/update boundaries. A fresh process reads the journal and inspects actual directories. Backup and neighboring skill preservation are checked. Three test methods; CI pending. Temporary fixtures only, no automatic recovery or power-loss proof.

## Added rollback of an installed update (0.0.104)

PR #110 passed CI 46124170657 and was merged. Main verification and tag pending.

Added rollback of an already installed update: the previous skill is restored to the profile, the newer copy retained in staging. A separate rollback journal leaves forward history intact. Explicit retry resumes a consistent phase; mismatched content or journal blocks writes. Nine temporary-directory tests include two interrupted reverse moves. Library for trusted exclusive roots, not a production installer. Recovery before new installation, first-install rollback, real rollback process termination and power loss remain open.

## Added cancellation of unfinished updates (0.0.105)

PR #111 passed CI 46128158068 and was merged. Main verification and tag pending.

Added cancellation of a first install and an unfinished update without deleting files. The previous version is restored from backup and the new version retained in staging. Cancellation uses a separate journal. Nine temporary-directory tests; CI pending. An already installed update requires separate rollback. Production CLI, concurrent-access protection and power-loss durability remain open.

## Added resumption of interrupted updates (0.0.106)

PR #112 passed CI 46133430573 and was merged. Main verification and tag pending.

Integrated single-skill install/update with explicit resumption of interrupted operations. Checks expected versions, fingerprints, journal, backup and result. Cancellation or rollback blocks forward resumption of the same operation. Ten disposable-directory tests, including mismatched content and corrupt reverse journal. Library for trusted exclusive roots, not a production installer; authorization, provenance, concurrency protection, batch operations, power-loss durability and production CLI remain open. ZIP unchanged.

## Added batch update preflight (0.0.107)

PR #113 passed CI 46136393123 and was merged. Main verification and tag pending.

Integrated preflight for one, multiple or all selected skills. New and independently prepared previous version fingerprints are checked against the plan and exact Git trees. One blocked skill prevents returning any transaction records; matching versions are skipped. The gh comparison now uses the same raw bytes included in the Git tree without rereading. Twelve disposable-directory tests. Read-only step: resolution authenticity, live refs, lockfile, exclusive access and batch execution remain unverified. ZIP unchanged.

## Added sequential skill updates (0.0.108)

PR #114 passed CI 46138842130 and was merged. Main verification and tag pending.

Added sequential application of selected skills. All selected items are checked before writes; a separate write-once receipt binds the initial plan and journals. Errors stop the operation; verified skills are not applied again. Ten disposable-directory tests. Batch is not atomic: partial completion remains for explicit resumption. Source trust, exclusive access, power-loss durability, lockfile, production CLI and live acceptance remain open.
