# Forum administration verification

Additive website-only change. No node, miner, wallet, publisher or unrelated service
changes. Existing public messages remain unchanged during deployment.

Local checks:
- Actual Workerd/D1: protected routes, configured-host restriction, sign-in Origin and
  pre-session verification, one-use login and moderation tokens, cookie attributes,
  escaped HTML, anonymous rejection, hidden alias/body exclusion, close/reopen enforcement,
  restore without data loss, audit trail, logout revocation, expiry and concurrent limits.
- Chrome at 1440, 390 and 360 pixels, JavaScript disabled: full sign-in/moderation/logout
  flow and public visibility changes; no horizontal overflow. Corrected same-origin
  form referrer handling after testing Chrome's actual Origin behavior.
- Public forum regression: topics/replies, injection escaping, CSRF, duplicate forms,
  posting limits, feed authentication/replay and chain reorganization.
- Existing explorer/core, network calculations and census D1 tests pass.

Planned credential provisioning: a generated administrator password in the current
Windows user's Credential Manager; only its secret verifier/signing key in Pages.
Provisioning is awaiting explicit owner approval after automatic review requested it.
No real password, session cookie, private credential or production message body is
included in this evidence. Authentication is single-admin/password-only; no MFA claim.
See website/README.md for setup, recovery, limits and moderation semantics.
