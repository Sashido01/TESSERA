# TESSERA agent guidelines

[Русский — основной язык](AGENTS.md) | **English — translation**

TESSERA is a public library of portable Agent Skills. Canonical repository: `Sashido01/TESSERA`.

1. Read the README, repository rules, and existing skills before making changes. Do not confuse TESSERA with an application that consumes one of its skills.
2. Place each skill in `skills/<name>/SKILL.md`; the frontmatter `name` must match the directory. Follow the Agent Skills specification.
3. Keep skills independent. Place environment-specific integrations for Harness, Codex, or other tools separately, and never promise automatic activation without verification.
4. After changes, run `python tools/validate_skills.py`, `python tools/check_public_paths.py`, `python tools/check_translations.py`, `python -m unittest discover -s tests -v`, and the tests of affected skills. Record actual results.
5. Follow the [version policy](docs/VERSIONING.en.md). New projects start at `0.0.0`; PATCH may exceed 99 for unfinished tasks. Never create dummy commits.
6. Write Git commits and release descriptions in clear, concrete **Russian**, following the canonical rules. Do not claim tests, builds, or publications that are not verified.
7. Do not publish secrets, private configuration, personal data, the owner's absolute working directories, or unrelated project files. Local paths may be used in the current environment but must never appear in public documentation, examples, commits, or release notes. Use placeholders such as `<project-root>` and `<skills-dir>`. Never force-push or rewrite other people's tags and history.
8. Publishing a GitHub Release or modifying remote repository settings is a separate action. A README or tag alone does not mean that an application was published.
9. Do not rewrite historical releases. If a skill's policy conflicts with an existing project's rules, preserve the project's constraints and report the conflict.
10. Before completion, report actual versions, commits, test results, changes, and remaining limitations.
11. **Language priority:** `README.md`, `AGENTS.md`, `SKILL.md`, other ordinary `*.md` files, and release communication are authored in Russian first. Translations use `*.en.md`. Keep English copies complete and updated within the same change. The skill's English reference lives at `references/SKILL.en.md`; never replace its canonical Russian `SKILL.md`. Check [docs/I18N.en.md](docs/I18N.en.md).
