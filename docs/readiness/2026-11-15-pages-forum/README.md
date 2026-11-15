# Pages migration and testnet verification - 2026-11-15

Production: https://obsoletecoin.pages.dev/
Pages deployment: 46243cd2-dcb2-4fe0-9919-310dc20e590a.
The previous website redirects GET/HEAD requests to the corresponding Pages path.
Other request methods are rejected rather than forwarding credentials.

## Completed changes

- Removed the music player, audio delivery and music footer credit.
- Removed website copy describing the Windows package as unsigned. The installer
  itself is unchanged; this wording change does not add a code-signing certificate.
- Added a plain-HTML forum with aliases, topics, replies, UTC dates and pagination.
- Added the supplied forum GIF and a guide for independent node operators.
- Deployed the website, static downloads, live explorer and D1 forum on Pages.
- With explicit owner authorization, provisioned two new independent destination
  keys and changed the Dell publisher to the new authenticated feed.
- Restarted only the explorer publisher. The node and unrelated trading service
  remained unchanged. Removed the old hosting bypass token from publisher config.
- Updated the repository README, public website screenshot and announcement draft.
  The GitHub repository and release remain private. No announcement was posted.

## Evidence

- runtime.json: real local Workerd/D1 topic creation and replies; HTML/SQL payloads
  rendered as text; origin/token checks, duplicate and posting limits; feed HMAC,
  replay rejection and canonical reorganization handling.
- forum-concurrency.json: two simultaneous local submissions produce one success
  and one rate rejection, using an atomic database transaction.
- browser-local.json: JavaScript-disabled Chrome at 1440/390/360 widths, with real
  desktop form submission. Mobile forms were inspected, not submitted separately.
- browser-public.json: anonymous desktop/mobile browsing, explorer navigation,
  forum forms and layout checks. No public test messages were created.
- public-downloads.json: all three full anonymous downloads match their published
  SHA-256 checksums; music and source archive are not served.
- publisher.json: two new feed observations, authenticated publication, correct
  public testnet height/genesis and external P2P probe.
- redirect.json: old root, join, explorer and forum paths redirect correctly.
- wallet-integration.json: two disposable native Windows nodes; real RandomX mining,
  synchronization, reward maturity, desktop send/receive of 12.34 OBSC, invalid
  block rejection, reorganization, restart, encryption and backup restoration.
  These tests did not spend user funds or modify the public testnet.
- final-public.json: final production feed freshness and node-guide check.

The former-host redirect is a separately committed/deployed hosting artifact.
The Pages release was deployed from the reviewed working tree before its final
documentation commit, so its source metadata names the preceding commit.

## Operational limits

This is an experimental testnet; coins have no monetary value and balances may
reset. These results are not an independent security audit or a mainnet approval.
The public network still depends heavily on its first node and independent mining
power remains important. An unchanged height alone is not a publisher outage:
feed observation time and chain height are checked separately.

The Windows desktop app initiates outbound connections. Public inbound operators
should follow the Linux/WSL node guide and expose only P2P TCP 19777, never RPC.
Being online as a node does not earn mining rewards.

Aliases are unverified. Forum limits reduce spam but do not eliminate it; moderation
uses authenticated Cloudflare D1 tools. Export the database before destructive
moderation. No raw IP is stored in forum tables; the provider may retain network
logs, and pseudonymous rate rows expire through cleanup on subsequent submissions.

The explorer refreshes every 15 seconds, marks old data stale and indexes a bounded
recent canonical window. Its address history is not a spendable wallet balance.
The first node remains on the Dell; moving web hosting does not move the P2P node.
