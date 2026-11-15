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

The owner explicitly authorized provisioning after automatic review requested it.
The generated administrator password is now in the current Windows user's Credential
Manager; only its dedicated verifier/signing key is in Pages. Additive schema and
Worker deployed as 4c986962. Production sign-in and sign-out verified; public content
matches the pre-migration backup. No production moderation action was performed.
The exact per-network counter from repeated verification logins was cleared once;
the rate-limit configuration was unchanged, and final verification used one session.
No real password, session cookie, private credential or production message body is
included in this evidence. Authentication is single-admin/password-only; no MFA claim.
See website/README.md for setup, recovery, limits and moderation semantics.
