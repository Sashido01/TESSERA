# TESSERA changelog

[Русский — основной язык](CHANGELOG.md) | **English — translation**

This file tracks changes to the **shared catalog**. Individual skills may maintain their own version histories.

## 0.0.4 — Clarified public dependency documentation

- Removed names of excluded third-party products from the current public documentation and the changelog as shown on the main branch.
- Documentation now covers only the approved stack: official GitHub CLI, minimal first-party Python tools, and free validation tools.
- Adopted a rule not to list rejected products by name in public materials.
- Kept canonical Russian documents and full English translations aligned without modifying executable components.

**Limitation:** already published Git commits were not rewritten; older document revisions remain in the repository history.

## 0.0.3 — Architecture and roadmap approved

- Expanded the single roadmap with T08–T17, priorities, prerequisites, and verifiable acceptance criteria.
- Adopted one independent Release Core with thin Codex, Harness, Claude Code, and Hermes adapters.
- Selected official GitHub CLI as the planned preferred distribution tool; retained a minimal Python offline fallback.
- Defined a minimal GitHub CLI and Python distribution stack; limited NVIDIA SkillEvaluator to free Tier 1 after isolated evaluation; excluded Tier 2/3 and mandatory paid AI APIs.
- Planned reference Agent Skills validation with `skills-ref` and separate measurement of NVIDIA Tier 1 quality and resource usage.
- Updated architecture, repository rules, and complete English translations without changing executable scripts.

**Status:** documentation and policy changes only. Planned external tools have not been installed and cross-agent integrations remain unverified.

## 0.0.2 — Skill made portable across agent hosts

- Removed the Harness-only scope of Microversion Release and documented Codex, Claude Code, Hermes, and other compatible hosts.
- Added a safe local installer with preview-first behavior and refusal to overwrite existing skills.
- Made annotated Git tags mandatory for every release, with verification of tag type, message, and target commit.
- Added a release-tag creation/verification helper and tests for missing, lightweight, and incorrect tags.
- Updated canonical Russian documentation and complete English translations. Integration with specific installed agent clients remains NOT_VERIFIED.

## 0.0.1 — Mandatory catalog microversioning introduced

- Applied the same rules to TESSERA itself as to Microversion Release: PATCH+1 for verified changes, planned `.99` release milestones, and continued `.100+` microversions for unfinished tasks.
- Introduced the canonical `VERSION` file and validation of each version transition.
- Configured automated annotated Git tags after successful validation of commits on `main`.
- Updated both Russian and English development and release instructions.
- Preserved previously added English translations, language rules, and published Git history.

**Limitation:** tag creation depends on GitHub Actions permissions. Build artifacts and GitHub Releases are not published automatically.

## 0.0.0 — Initial library (23 November 2026)

- Created the public catalog of portable Agent Skills.
- Added the first skill, Microversion Release, with rules for working microversions and release milestones.
- Documented clear, human-readable Russian commit, tag, and release descriptions.
- Added tests for version calculation and catalog structure.
- Added contribution, security, and roadmap documentation.

**Status:** initial repository state. Automatic integration with an installed Harness, build publication, and GitHub Release publication have not been verified.
