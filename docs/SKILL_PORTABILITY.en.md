# T12.03.01 — portable skill license and documentation

[Русский — оригинал](SKILL_PORTABILITY.md) | **English — translation**

Isolated SkillSpector 2.13.6 reported four reference_missing findings ([CI 45370414762](https://github.com/Sashido01/TESSERA/actions/runs/45370414762)); the documentation indeed contained four links outside the skill directory. NVIDIA License Compliance previously returned not_detected. These are confirmed portability issues.

Fix: standalone LICENSE.txt with exact root MIT bytes, license: MIT in canonical frontmatter, self-contained RU/EN guidance, immutable v0.0.30 external links for optional reading only. The ZIP builder includes the standalone license. Regressions verify its presence and bytes in the ZIP, symlink rejection, preservation by actual gh skill install --from-local, rejection when lost, and resolution of simple relative Markdown links only against the package contents (not a general Markdown parser, external URL availability or fragment verification).

No scanner rules disabled, no thresholds or weights changed. No score improvement is claimed before new CI. Real agent-client scenarios, full legal compatibility, MP3/RA1 risk and other findings remain separate tasks.

Status: implementation prepared; actual CI acceptance required.
