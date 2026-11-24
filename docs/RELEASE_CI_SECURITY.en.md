# T12.03.02 — safe GitHub CI evidence verification

[Русский — оригинал](RELEASE_CI_SECURITY.md) | **English — translation**

## Reason

Bandit B310 in core/release_ci.py: old code allowed urllib.request.urlopen to follow redirects and checked the final hostname only after the request. An unexpected host could be contacted before rejection. This is a destination restriction defect; no confirmed disclosure incident.

## Change

Allow only exact HTTPS api.github.com/repos/OWNER/REPO/actions/runs/ID and .../jobs?per_page=100 URLs. Validate paths, identifiers and parameters before connection. NoAPIRedirect rejects 301/302/303/307/308 before the next request, even to a different path on the same host. Check exact response URL before reading body. Retain 15-second timeout and 2 MiB limit. No tokens or new dependencies.

## Acceptance

Four regressions: reject redirects, reject invalid URLs before network, correct opener/timeout, changed response URL. They do not substitute for live networking checks or prove process network isolation. No Bandit suppression. B310 may remain a heuristic warning; evaluate the actual control and tests, not warning counts. Actual CI required; other Bandit findings open.

[CI 45376483433](https://github.com/Sashido01/TESSERA/actions/runs/45376483433) PASS: 493+19 tests, four new regressions PASS, Bandit B310 absent in the repeat review; 110 findings (no HIGH), no rule suppression. T12.03.02 COMPLETE within implemented control and CI scope; live network execution separately NOT_VERIFIED.

## Pre-merge regression correction

Before merge, a shared get_public_json regression was found: the original strict URL allowlist blocked the existing GitHub Release metadata call. Permit only the canonical /releases/tags/vMAJOR.MINOR.PATCH route and one namespace encoded as %2F; arbitrary escaping, extra paths and parameters remain forbidden. Three regressions exercise verify_github_publication through the actual shared transport (ordinary and namespaced tag), changed response URL rejection and invalid routes. Only networking is mocked, validation and response handling are real. Historical PASS missed this defect; repeat acceptance is required.
