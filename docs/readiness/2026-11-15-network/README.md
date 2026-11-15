# Network observations - 2026-11-15

The network dashboard derives metrics from the existing authenticated public feed.
It adds no remote RPC, changes no consensus rules, and restarts neither the Dell
node nor its publisher. No wallet/private key data or peer-IP list is collected.

Checks passed:
- Compact target and expected-work arithmetic, difficulty-1 reference, 24/96/672
  windows, sparse or equal timestamps, partial coverage.
- Canonical extension, shorter-chain rollback, competing branch, missing overlap,
  bounded 4,097-header history, 100-event retention.
- Split reward outputs, duplicate addresses in one block, genesis exclusion,
  stale-feed rendering and escaped address text.
- Real Workerd/D1 transactional feed/archive consistency and concurrent writes.
- Existing forum authentication, posting and feed-replay regression tests.
- JavaScript-disabled Chrome at 1440/390/360 widths: dashboard, responsive layout,
  supplied forum GIF and obsolete-coin.gif favicon.

Limits: observations cannot count exact active miners or prove independence;
historical work estimates are not instantaneous telemetry. Daily rows follow block
timestamps and can contain partial days. The 90-minute block-delay notice is an
operational hint, not evidence of an attack. Events between feed snapshots may be
missed. Retention is bounded by block/event count, not a guaranteed calendar period.

The native miner currently reports discovered blocks, not measured H/s. No false
local hash counter was added; a real counter would require a separately tested
native-node and wallet release. This change delivers the public network panel.

The owner authorized publishing the GitHub repository after scoped redaction of
historical account names and home-network endpoints. The original history is kept
in an ignored local backup. Old readiness records retain their historical meaning,
but personal endpoints are now documentation examples. Original commit IDs may
change; published packages are still identified by their unchanged SHA-256 hashes.
The draft release is not published by changing repository visibility.


## Publication verified

GitHub is public and its metadata was verified anonymously. The source history was
checked after redaction; 24 commit IDs changed while the reviewed current tree was
preserved. Eleven older CI packages containing the identified personal references
were retired only after their private backups matched GitHub's SHA-256 digests.
The workflow logs and remaining artifacts were retained. Public distribution files
are unchanged by this source-history cleanup.

Cloudflare serves the new network panel, replacement forum GIF and coin favicon.
Anonymous Chrome checks passed on desktop and mobile with JavaScript disabled.
The first production observation covered blocks 0 through 342; the 672-block
window is correctly marked partial. The Dell reported zero peer connections at
that observation; this is not a claim that the whole network has no miners.
