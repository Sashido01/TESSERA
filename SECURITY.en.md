# Security policy

[Русский — основной язык](SECURITY.md) | **English — translation**

## Supported versions

TESSERA is an early-stage Agent Skills library. A long-term support matrix has not been established. Check the current branch and the status of each individual skill.

## Reporting a vulnerability

If GitHub private vulnerability reporting is enabled, use **Security → Report a vulnerability**. Otherwise, do not publish exploit details, tokens, or personal data in public issues. Contact the repository owner through an appropriate private channel.

## Trust boundaries

- `SKILL.md` is a set of instructions, not an enforcement mechanism for agent actions.
- Do not automatically trust scripts or commands provided by unknown skills.
- Inspect files and permissions before installing, especially for skills that can perform Git operations or access the network.
- Calculating a version number does not prove that tests passed, a commit or tag was created, or a release is ready.
- Do not publish secrets, private logs, authentication files, or other projects' configurations.
