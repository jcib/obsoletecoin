# Public testnet website and downloads - 2026-11-15 (Madrid)

Owner authorized website and binary downloads only. GitHub jcib/obsoletecoin stays
private; release 445295928 remains a draft. No forum message was posted.

Website: https://obsoletecoin.pages.dev/
Join/downloads: https://obsoletecoin.pages.dev/join.html
Explorer: https://obsoletecoin.pages.dev/explorer/index.html

## Evidence

- Router NAT Internet interface corrected by owner; external Cloudflare handshake
  verifies testnet genesis (cloud-handshake.json).
- Fresh Debian full node on external GitHub runner synchronized 0 -> 305 with
  headers equal, no IBD and wallet disabled. Run 43652013461; external-sync.json.
- Anonymous home/join/explorer and all three downloads return 200. SHA256 matches
  the already tested packages. No credentials used; anonymous-http.json.
- Full review source archive is absent from the public route manifest and returns
  404; SHA256SUMS lists only the three binary packages. GitHub links say private.
- Unauthenticated feed/probe POST requests return 401. Feed reads remain public.
- Chrome without login, JavaScript disabled, at 1440/390/360 px: block/transaction/
  address navigation and no overflow; 15-second explorer refresh; audio continues
  across refresh; installer hash and MP3 byte-range verified. anonymous-browser.json.
- Site source 118ea43a4ad6b79bb20a1fe916b073e4855829e7; successful deployment
  appgdep_6af8ecd18dd4819195d5c214465e2f62; access policy public, revision 2.
- Core feed validation/authentication/reorg/escaping/amount/staleness checks pass.

Cloudflare rejects Python's default user agent with 403/1010; anonymous requests
with a browser user agent and real Chrome succeed. Hosting injects its own inline
script; application HTML has no scripts and works with JavaScript disabled.

## Limits

Experimental testnet only. Mainnet remains disabled and blocked by its readiness
requirements. Windows installer remains unsigned. No independent consensus audit
or independent standing mining infrastructure is claimed. Current height 305 is
not evidence of continuous mining: new blocks require active miners. Home IP is
dynamic; use the current peer on the join page. Explorer refreshes every 15 seconds
and explicitly marks data stale after 60 seconds. One node is not high availability.

No trading configuration, ledger, orders or service restart was part of publication.
Original upstream license notices in binary packages are preserved. Repository and
full review archive were not made public. Forum draft: ../../TESTNET-ANNOUNCEMENT.md.
