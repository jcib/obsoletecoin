# Website, forum and live testnet explorer

Production destination: https://obsoletecoin.pages.dev/

The site uses plain HTML/CSS and local GIFs. There is no music or browser JavaScript.
The forum supports topics and replies with a public alias, without registration.
Aliases are not verified or reserved.

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

Public downloads are static assets with SHA-256 checksums. The complete source
archive, node data, source maps, personal paths and credentials are not published.
All current download files are below Pages' 25 MiB per-file limit. Larger future
packages need a separate download store. GitHub remains private.

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

Moderation is restricted to the owner's authenticated Cloudflare D1 tools.
To close or hide a topic, update its locked or hidden field by exact topic UUID.
Deleting a thread cascades to its posts. Export the dedicated database before
destructive moderation. Never accept SQL commands from public forum users.

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
