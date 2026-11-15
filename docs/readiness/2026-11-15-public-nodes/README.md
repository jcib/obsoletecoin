# Public-node observation verification

Scope: website monitor only. No node, wallet, miner, publisher or consensus
deployment is required. Existing Cloudflare D1 and feed authentication are reused.

Passed before deployment:
- Adversarial P2P tests with simulated transports: fragmented messages, handshake,
  genesis, wrong magic/checksum/genesis, non-node services, EOF, timeout, size bounds.
- Public IPv4/port filter; private, reserved, mapped/host/alternate formats rejected.
- Address packet parsing, invalid sizes, stale/future announcements, deduplication.
- Counter success/failure, expiry, stale display, candidate cap, rotating checks,
  dynamic seed priority and aggregate-only API privacy.
- Actual Workerd/disposable D1: eight concurrent jobs admit one scan; lease takeover
  prevents a late overwrite; reads cannot scan; authenticated feed/replay preserved;
  both panels render the census and failed checks/expired checks disappear.
- Existing explorer validation and network-history calculations pass.
- Chrome with JavaScript disabled at 1440, 390 and 360 pixels: both explorer panels,
  counters, expandable explanation and no horizontal overflow.
- Pages bundle and legacy shared-module build syntax checks pass.

See website/README.md for coverage, bounds and interpretation. Fixtures are isolated;
their endpoint IPs are not contacted by the tests. No public forum posts are created.
