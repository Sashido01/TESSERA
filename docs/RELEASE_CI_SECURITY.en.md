# T12.03.02 — safe GitHub CI evidence verification

[Русский — оригинал](RELEASE_CI_SECURITY.md) | **English — translation**

## Reason

Bandit B310 in core/release_ci.py: old code allowed urllib.request.urlopen to follow redirects and checked the final hostname only after the request. An unexpected host could be contacted before rejection. This is a destination restriction defect; no confirmed disclosure incident.

## Change

Allow only exact HTTPS api.github.com/repos/OWNER/REPO/actions/runs/ID and .../jobs?per_page=100 URLs. Validate paths, identifiers and parameters before connection. NoAPIRedirect rejects 301/302/303/307/308 before the next request, even to a different path on the same host. Check exact response URL before reading body. Retain 15-second timeout and 2 MiB limit. No tokens or new dependencies.

## Acceptance

Four regressions: reject redirects, reject invalid URLs before network, correct opener/timeout, changed response URL. They do not substitute for live networking checks or prove process network isolation. No Bandit suppression. B310 may remain a heuristic warning; evaluate the actual control and tests, not warning counts. Actual CI required; other Bandit findings open.
