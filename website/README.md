# Website, forum and live testnet explorer

Production destination: https://obsoletecoin.pages.dev/

The site uses plain HTML/CSS and local GIFs. There is no music or browser JavaScript.
The forum supports topics and replies with a public alias, without registration.
Aliases are not verified or reserved.

The CSS news marquee sits at the very top of every page, before the branding.
Edit `NEWS` in `build.py` to describe the latest implemented development changes.
It has no buttons or links, pauses on hover, and becomes wrapped static text for
reduced-motion users. The second visual copy is hidden from assistive technology.

## Cloudflare Pages

cloudflare/wrangler.jsonc identifies the dedicated obsoletecoin Pages project and
its separate D1 database. The other account projects are unrelated.

Build a fresh static directory, then the Pages Worker:

~~~sh
python website/build.py --snapshot SNAPSHOT.json --output STATIC_DIR --live --public-web-only
python website/cloudflare/build.py --static STATIC_DIR
node website/cloudflare/build.mjs TOOLCHAIN_DIRECTORY
~~~

TOOLCHAIN_DIRECTORY contains an installed esbuild dependency. Output is
.local/pages-dist. Do not deploy the repository root. Install cloudflare/schema.sql
in the dedicated D1 database, configure the secrets below, and deploy from the
website/cloudflare directory using Wrangler Pages.

`release/downloads.json` selects the current Windows package and its verified hash;
the build refuses a mismatched installer. Installer links contain the version to
avoid cached older downloads. Portable ZIPs exceeding the Pages per-file limit are
linked to the corresponding GitHub release. A distributable build includes both
publications as described in `AGENTS.md`.

Public downloads are static assets with SHA-256 checksums. The complete source
archive, node data, source maps, personal paths and credentials are not published.
All current download files are below Pages' 25 MiB per-file limit. Larger future
packages need a separate download store. GitHub source is public.

## Runtime secrets

- OBSOLETE_FEED_KEY: dedicated HMAC key shared only with the node publisher.
- FORUM_SECRET: independent key for short-lived form/session tokens and
  pseudonymous posting-rate identifiers.

Generate new independent keys for this destination. Store them through Cloudflare's
secret configuration, never in source, HTML, shell arguments or a committed file.
The former hosting bypass token must never be sent to Pages.

## Forum

Routes: /forum, /forum/new, /forum/thread/UUID.
Topics and replies are persisted in D1, with pagination and UTC timestamps.
No attachments, HTML rendering, private messages or user accounts are implemented.

POSTs require a same-origin browser request, signed session/form tokens, a one-use
nonce and bounded field lengths. HTML output is escaped; SQL uses bound parameters.
A honeypot and transactional posting limits reject automated floods, duplicates
and concurrent rate-limit races. Current limits: 10 posts per network identifier
per hour, at least 10 seconds between posts, and 100 posts per site per hour.
Topics accept at most 1,000 posts. These limits do not promise complete spam prevention.

No raw IP is stored in the forum database. A daily keyed hash is kept only in the
rate-limit table; stale rate rows are removed when new submissions are processed.
The hosting provider may maintain its own network/security logs.

Moderation is available at /forum/admin, with a separate administrator password.
The public forum links to this sign-in page. Forum aliases confer no permissions.
The administrator can close/reopen and hide/restore topics, hide/restore individual
messages, and review a private action log. Hiding removes the message body and alias
from public output; the original remains available to the administrator for restoration.
Public reply totals include hidden-message placeholders. Hidden topics return 404.
No permanent deletion or public registration for administrator roles is provided.

The random 256-bit administrator password is stored in Windows Credential Manager
under ObsoleteCoin/ForumAdmin. Run tools/forum_admin_access.py on that Windows
account to reveal/copy it and open the panel. It is not stored in the repository,
wallet, browser URL or a plaintext password file. Save a copy in a password manager
if access from another computer is needed.

FORUM_ADMIN_AUTH is a dedicated Cloudflare Pages secret containing SHA-256 of that
random password. It also signs administrator session/form tokens and must itself be
treated as a secret. This construction relies on a generated high-entropy password;
do not substitute a human-chosen password or publish the hash. It is unrelated to
the existing feed/forum secrets and all wallet/other-service credentials.
Changing this secret and deploying invalidates old signed sessions; D1 session rows
also allow immediate logout revocation. There is no anonymous password-reset route.
Credential recovery or rotation requires the owner's Cloudflare access.

Sessions last one hour and use Secure, HttpOnly, SameSite=Strict cookies scoped to
/forum/admin. The database stores hashed session identifiers only. Sign-in forms
expire after 15 minutes and successful sign-ins consume their nonce. Mutations use
action/path/session-bound, one-use signed forms; cross-origin requests are rejected.
Only the configured SITE_ORIGIN accepts administrator access, not deployment aliases.
Pages are private/no-store/noindex and cannot be framed. Passwords never appear in
HTML responses or logs. Login attempts are limited atomically to 10 per network
identifier and 100 globally per 15-minute bucket; rate identifiers are keyed,
rotate daily and expire after two days. No raw IP or message content is stored in
the moderation audit log. This is single-administrator authentication, without MFA.

Deployment order: export a private backup of the dedicated D1 database; apply
cloudflare/admin-schema.sql (additive, idempotent tables/index); set FORUM_ADMIN_AUTH
through the secret store; deploy the tested Worker. Preserve the two existing secrets.
No existing forum posts, aliases, locks or visibility values are changed by migration.

Tests: node website/cloudflare/test_admin.mjs TOOLCHAIN_DIRECTORY uses real Workerd
and disposable D1. The public forum regression remains test_runtime.mjs. Browser tests
exercise sign-in, hide/restore, close/reopen, audit and logout with JavaScript disabled.
Never use the live forum for synthetic moderation tests or post test messages there.

## Explorer

The dedicated publisher reads allowlisted public chain/network/mempool RPCs through
loopback, never wallet RPCs. It verifies the testnet genesis and canonical tip.
Requests carry HMAC signatures bound to the timestamp, path and body.

D1 replaces the latest canonical feed only for a newer observation, atomically.
This permits a genuine chain reorganization while rejecting replayed observations.
The public view refreshes every 15 seconds and marks data older than 60 seconds stale.

The publisher bounds its canonical window to 1,024 blocks and 1.4 MB. It reduces
coverage when necessary. A single block exceeding that limit leaves the feed stale
instead of showing invented live data. Address output history is not a spendable
wallet balance. Unconfirmed transaction details are not indexed.

The public API has no wallet proxy and exposes no RPC cookie or credentials.
The optional operator probe checks the advertised public P2P peer and genesis.
It requires the feed HMAC key.

## Verification

Local Workerd/D1 tests cover creating topics, replies, injection payloads, CSRF,
duplicate submissions, rate limits, authenticated feed updates and reorganizations.
Chrome with JavaScript disabled verifies desktop/mobile layouts and actual form
submission. Public deployment checks validate anonymous downloads, hashes and feed
freshness. Evidence is under docs/readiness/2026-11-15-pages-forum/.

The former Site becomes a redirect only after Pages and the publisher are verified.

Run test_runtime.mjs against a fresh disposable local D1 database, passing the local URL and a public snapshot fixture. It refuses non-local targets and does not post test messages to the public forum.


## Network observations

/explorer/network.html and /api/network expose historical network estimates derived
from the existing authenticated public feed. No additional node RPC or wallet access
is needed. The Dell publisher, mining software and consensus rules are unchanged.

The monitor retains at most 4,097 canonical block headers and 100 chain-change events
in D1. Feed and archive updates use an atomic compare-and-swap transaction; concurrent
or older observations cannot replace a newer feed or leave its history at another tip.
Unchanged tips do not rewrite the archive. Missing overlap resets coverage instead of
retaining unproven ancestors. Reorganizations are recorded only when observed; events
between publisher snapshots can be missed.

Power estimates use exact integer expected work from each compact target, divided by
the minimum/maximum timestamps of windows of 24, 96 and 672 block intervals. Windows
shorter than requested are labelled partial. Zero time spans return unavailable.
Difficulty is relative to the conventional 0x1d00ffff target. These are historical
estimates, not live miner telemetry, and do not automatically fall to zero when mining
stops. The last block time, feed freshness and a 90-minute delay notice are separate.

Daily rows summarize retained canonical headers using miner-provided UTC timestamps;
boundary days and coverage gaps may be incomplete. Reward statistics cover at most
672 blocks available in the current detailed feed, exclude genesis and zero outputs,
deduplicate an address within each block, and report split payouts without assuming
one address equals one miner. Top 50 addresses are displayed; totals include all.
Connections describe only the first node's peers. No peer IP list is published.

Run node website/cloudflare/test_network.mjs for arithmetic, fork, gap, retention,
payout and stale-data checks. Workerd tests also verify concurrent D1 feed updates.

## Public-node observations

The explorer and network panel distinguish first-node connections from detected
reachable public nodes. /api/nodes exposes only aggregate observations, never the
discovered address list. /api/network includes the same publicNodes summary.

Cloudflare initiates a bounded P2P crawl after accepted publisher feeds. An atomic
D1 lease permits one batch about every five minutes; public GETs cannot start scans.
Each batch probes the advertised first node and up to three least-recently-checked
candidates in parallel, with a ten-second deadline per connection. No Dell service,
wallet, consensus code, RPC permissions or signing keys are changed.

Candidates come only from the first node's advertised endpoint and legacy P2P addr
responses from verified nodes. The crawler requests getaddr, verifies network magic,
version/services, checksums and the genesis header hash. Mere TCP reachability does
not count. It accepts literal public IPv4 on TCP 19777, rejects private/reserved
addresses, hostnames and other ports, and bounds messages/bytes and retained state.
No IP-range sweep is performed. The internal D1 list holds up to 256 endpoints;
unrefreshed candidates expire after 24 hours. Addresses are deduplicated by endpoint,
not operator. IPv6, Tor, other ports, undiscovered and non-listening nodes are excluded.

The displayed number counts endpoints whose latest probe succeeded within 30 minutes.
A failed recheck removes the endpoint immediately. A result expires even if the monitor
stops; after ten minutes without a completed batch the UI marks monitoring stale.
Known candidates and recent checks make incomplete coverage visible. At high node
counts the bounded budget will undercount; this is not an exhaustive network census.
A peer can imitate the handshake/genesis, and multiple endpoints may belong to one
operator. Verification is not proof of independent ownership, full synchronization,
honest consensus validation or hash power.

Short crawler sessions can temporarily appear in the first node's connection count.
A scan failure does not block feed ingestion or alter the blockchain. If the publisher
stops, no new scan starts. NODE_CENSUS_ENABLED=false disables future batches without
deleting history; stale observations expire normally.

Run node website/live/test_census.mjs for isolated adversarial protocol and count
tests. Run node website/cloudflare/test_census_runtime.mjs TOOLCHAIN_DIRECTORY to
check the actual bundled Worker and disposable D1 storage, including lease concurrency.
