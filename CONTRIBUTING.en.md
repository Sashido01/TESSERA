# Contributing to TESSERA

[Русский — основной язык](CONTRIBUTING.md) | **English — translation**

Thanks for suggesting improvements. The goal is to make small, understandable, and verifiable changes.

## Before making changes

- Look through existing skills and issues to avoid duplicating work.
- For a new skill, create `skills/<slug>/SKILL.md` and `skills/<slug>/README.md`. Use lowercase Latin letters, digits, and hyphens in the slug.
- Give `SKILL.md` valid YAML frontmatter with `name` and `description`. The description should explain when the skill is relevant.
- Write precise instructions; do not claim capabilities that do not exist or hide unsafe actions.
- Provide instructions and tests for scripts. Do not require secrets or machine-specific paths.
- **Write Russian documentation first.** Add the matching `.en.md` translation for every user-facing document in the same change. For a skill's `SKILL.md`, place the English reference under `references/SKILL.en.md`; keep the main file in Russian. See [translation policy](docs/I18N.en.md).

## Validation

```bash
python tools/validate_skills.py
python tools/check_public_paths.py
python tools/check_translations.py
python tools/check_repository_version.py
python -m unittest discover -s tests -v
python -m unittest discover -s skills/microversion-release/tests -v
```

If a test environment is unavailable, explicitly list the checks you could not perform.

## Commits and pull requests

- For **every TESSERA change**, calculate the next catalog microversion from `VERSION`, update the root `VERSION` file and both changelogs. Use PATCH+1 for a working change, or the verified release transition defined in the [version policy](docs/VERSIONING.en.md).
- After successful validation on `main`, the workflow creates an annotated Git tag. Do not bypass checks or forcibly replace tags.
- Write commit messages in plain Russian, for example «Исправлен расчёт следующей версии при переходе через 99», not “misc fixes” or “bump.”
- Describe the purpose, changes, actual checks, limitations, and compatibility risks in your pull request.
- Prefer one related task per pull request.
- Never rewrite published tags or another contributor's history.
- Use private vulnerability reporting when available; do not disclose secrets in issues.

## Licensing

By submitting changes, you acknowledge that the project is distributed under the MIT license.
