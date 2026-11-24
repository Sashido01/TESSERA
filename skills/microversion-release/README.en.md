# Microversion Release

[Русский — оригинал](README.md) | **English — translation**

**Portable Agent Skill for Codex, DeepSeek Harness, Claude Code, Hermes, and other compatible agents.** It guides microversioning, human-readable commits, and mandatory verification of annotated release tags. The canonical entry point is the Russian [SKILL.md](SKILL.md); its full English reference is [SKILL.en.md](references/SKILL.en.md).

## Microversions and releases

- New projects start at `0.0.0`. Each independently verified change increments PATCH.
- When a task is unfinished at `.99`, work may continue with `.100`, `.101`, etc., without an artificial cap.
- After genuine completion and required checks, the next release is `0.0.99 → 0.1.0`, `0.1.99 → 0.2.0`, or `0.99.99 → 1.0.0`. Completion at `0.0.107` can lead to `0.1.0`.
- **Every release must have an annotated Git tag pointing to the exact release commit.** Missing or incorrect tags mean `BLOCKED / RELEASE_NOT_TAGGED`, never COMPLETE. Release descriptions use clear, natural Russian.

## Integration with agent hosts

| Host | Project skill directory |
| --- | --- |
| Codex | `<project-root>/.agents/skills/` |
| DeepSeek Harness | `<project-root>/.dsh/skills/` |
| Claude Code | `<project-root>/.claude/skills/` |
| Hermes | `<project-root>/.hermes/skills/` or `<project-root>/.agents/skills/` |
| Other compatible agent | Explicitly specified `<skills-dir>` |

Example from a cloned TESSERA repository:

```bash
python skills/microversion-release/scripts/install.py --platform codex --project-root <project-root>
python skills/microversion-release/scripts/install.py --platform codex --project-root <project-root> --apply
```

The default is `DRY-RUN`; no files are modified until `--apply`. Existing skill directories are **never overwritten**. For custom profiles use `--platform generic --target-root <skills-dir> --apply`, after verifying the actual destination.

The installer rejects symbolic links and redirected components of the standard project path, as well as links and special files in the source skill. An explicit `--target-root` resolves to the user-selected directory; this does not authorize following links inside the skill. Checks assume a trusted filesystem without concurrent path substitution; TOCTOU race protection and native Windows junction tests remain NOT_VERIFIED.

Hermes also supports installation via the GitHub skills catalog:

```bash
hermes skills tap add Sashido01/TESSERA
hermes skills install Sashido01/TESSERA/skills/microversion-release
```

Project-level Hermes trust may be required. See the complete [integration guide](references/INTEGRATION.en.md) / [Russian original](references/INTEGRATION.md).

## Calculator and release-tag validation

From the installed skill directory:

```bash
python scripts/next_version.py 0.0.99 --mode work
python scripts/next_version.py 0.0.107 --mode release
python scripts/release_tag.py verify 0.1.0 --repo <project-root>
python scripts/release_tag.py create 0.1.0 --repo <project-root> --message "Релиз 0.1.0 — исправлен запуск приложения"
python -m unittest discover -s tests -v
```

`release_tag.py create` creates **only a local annotated tag**, after successful checks and authorization to write Git data. It does not push, build an application, or replace other release requirements. See [mandatory release tags](references/RELEASE_TAGS.en.md).

## Compatibility and limitations

The portable structure and CLI can be validated in TESSERA CI. **Installation, automatic activation, and enforcement in actual installed Codex, Harness, Claude, and Hermes clients remain NOT_VERIFIED.** A SKILL.md file does not replace audited lifecycle hooks, Git/CI verification, or concurrency locking. Never rewrite the published history of an existing project.

## License

MIT. The complete license travels with the skill: [LICENSE.txt](LICENSE.txt).
