# T12.03.01 — portable skill license and documentation

[Русский — оригинал](SKILL_PORTABILITY.md) | **English — translation**

Isolated SkillSpector 2.13.6 reported four reference_missing findings ([CI 45370414762](https://github.com/Sashido01/TESSERA/actions/runs/45370414762)); the documentation indeed contained four links outside the skill directory. NVIDIA License Compliance previously returned not_detected. These are confirmed portability issues.

Fix: standalone LICENSE.txt with exact root MIT bytes, license: MIT in canonical frontmatter, self-contained RU/EN guidance, immutable v0.0.30 external links for optional reading only. The ZIP builder includes the standalone license. Regressions verify its presence and bytes in the ZIP, symlink rejection, preservation by actual gh skill install --from-local, rejection when lost, and resolution of simple relative Markdown links only against the package contents (not a general Markdown parser, external URL availability or fragment verification).

No scanner rules disabled, no thresholds or weights changed. No score improvement is claimed before new CI. Real agent-client scenarios, full legal compatibility, MP3/RA1 risk and other findings remain separate tasks.

Status: implementation prepared; actual CI acceptance required.

Canonical SKILL.md shortened from 11279 to 8876 UTF-8 bytes, below the pinned static profile's 10000-byte custom-provider recommendation. The microversion rules, mandatory tag gate, explicit authorization, coordination and reporting remain; prerequisites, script table, examples and troubleshooting are explicit. Description begins with purpose, no experimental blanket tool permissions added. Regression checks byte limit and required markers; real client activation remains NOT_VERIFIED.

## Preliminary actual acceptance

[CI 45373618225](https://github.com/Sashido01/TESSERA/actions/runs/45373618225): 486+19 tests PASS. SkillSpector 2.13.6: complete, 17/17 files, 100%, reference_missing 4→0, risk 78→36 (HIGH→MEDIUM), HIGH 2→0, MEDIUM 10, zero suppressions, both fixtures PASS, 19.40 s. NVIDIA: license allowed, RU quality 80.0 (65×0.35 + 80×0.25 + 95×0.25 + 90×0.15), Codex custom provider degraded→loads. Overall CI FAIL only at inherited Go review; release and real activation NOT_VERIFIED.
