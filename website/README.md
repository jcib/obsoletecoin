# Obsolete Coin website and live testnet explorer

The current publication uses a small Worker to serve the existing plain HTML/CSS
site and an HTML iframe that refreshes every 15 seconds without reloading audio.
No browser JavaScript, wallet RPC forwarding or wallet-key collection is used.

`website/live/publisher.py` runs as the dedicated node account on the Dell. It reads
only public blockchain/network/mempool RPCs over loopback, verifies the v0.2 genesis,
rejects incomplete synchronization and checks the tip again after constructing its
view. A cached canonical window of at most 1024 blocks is replaced on reorganizations.
The window shrinks if needed to stay below 3.5 MB. Large single blocks beyond that
limit stop the feed explicitly; data becomes stale, rather than falsely current.

Only allowlisted block/transaction fields leave the server. The publisher signs each
request with an HMAC secret stored in a protected server configuration and the Sites
runtime secret store. Requests expire after two minutes. R2 conditional writes reject
replayed/older observations and concurrent overwrites. The server-rendered explorer
marks observations older than 60 seconds stale, even if the last block itself is old.
Address output history is not a spendable balance; unconfirmed transaction details
and blocks outside current coverage are not indexed.

Assets/downloads are R2 objects locked to SHA-256 hashes and sizes compiled into the
Worker. The ingestion credential cannot replace a download with different bytes.
MP3 byte ranges are supported. Credentials never enter generated HTML or Git.

Build: `python website/build.py --snapshot .local/site/snapshot.json --output .local/public-static --live`,
then `python website/live/build_worker.py --static .local/public-static --site .local/site`.
The Site checkout has `build.mjs` to rebuild its exact Worker source. Package/publish
through the Sites helper, then seed exact hash-checked assets before opening access.
Do not run the one-time Dell installer against an already configured node.

Checks cover allowlisting, wrong network, stale data, exact amounts, HMAC expiration,
route binding, replay rejection, R2 conditional writes, canonical tip rollback and
immutable asset uploads. Chrome with JavaScript disabled at 1440/390/360 validates
navigation, iframe refresh, uninterrupted audio, mobile layout and download hashes.

## Earlier static publications (historical evidence)

# Obsolete Coin website

A portable English-language GeoCities-inspired site: plain HTML, local CSS and SVG, no JavaScript, external fonts, analytics or runtime framework.

Slogan: **It's tacky, cheap, and slow.**

Website: https://obsoletecoin.pages.dev

Includes downloads, network specifications, mining instructions, FAQ, a mainnet readiness checklist, GitHub links, and a static explorer generated from real public testnet block data. An unsigned native Windows test installer is now available; mainnet remains blocked.

## Build

Run from the repository root with Python 3.10 or newer. Downloads use `../ObsoleteCoin-Windows-WSL.zip`, `.local/release/ObsoleteCoin-Linux-Testnet.tar.gz` and `.local/release/ObsoleteCoin-Testnet-Setup.exe`, verified against their release provenance.

1. On the Linux/WSL account running the local testnet node: `python3 -B website/export_snapshot.py --output .local/site/snapshot.json`. The exporter reads the local RPC cookie for authentication and calls public blockchain RPCs only. The cookie and wallet data are never exported. It captures at most 1024 recent blocks and checks chain continuity.
2. `python -B website/build.py --snapshot .local/site/snapshot.json --output .local/site/dist`
3. `python -B website/check.py .local/site/dist`
4. Optional local preview: `python -B -m http.server 8765 --bind 127.0.0.1 --directory .local/site/dist`

Use a fresh output directory when replacing an older snapshot, so stale generated pages do not remain. Upload only the generated static files to any HTML host. No RPC endpoint needs to be exposed. Downloads include SHA256 checksums.

## Explorer scope

Every page displays its capture date. This is a static blockchain archive, not a live explorer. Address pages show outputs within the captured range, not a wallet balance. Updating requires a new export, build and publication; no automatic task has been installed. Source repository and first Sites publication remain private during testing.

## Verification of the first version

Captured 14 November 2026 at 10:55:30 UTC, blocks 0 through 264. Link validation: 541 HTML pages, 11,857 local references, no broken links and no scripts. Chrome checked with JavaScript disabled at 1440, 390 and 360 pixels; no horizontal overflow. Downloaded both packages through the UI and verified their hashes. Followed explorer links through block, transaction and address pages, and exercised native HTML FAQ disclosure controls.

## OBSC update verification

Updated slogan and technical copy, sanitized Dell photo, OBSC labels and new download packages verified in Chrome at 1440, 390 and 360 pixels with JavaScript disabled. All 541 pages and local references validated. Wallet date/state tests and Tk smoke passed; a simulated RPC GUI exercise verified 20 then 40 rows and transaction details. Read-only WSL checks validated dates on 21 actual transactions and gettransaction details. Updated wallet UI installed in the existing WSL tools directory without restarting mining or changing wallet data. Reopen the wallet to load the new interface. Mainnet remains blocked; see docs/MAINNET-READINESS.md.

## GeoCities reference redesign

Layout follows the supplied SiliconValley/1000 reference: blue tiled background, yellow type, cyan/magenta links, four illustrated navigation columns and black tables with yellow borders. Removed the requested sidebar/footer badges and header labels. User-provided floppy-disk-3d.gif is used for disk images and the favicon. GifCities asset sources are documented in ASSETS.md. All assets are local; no archive scripts or visitor trackers.

Validation: 541 HTML pages and 16,186 local references, zero broken links or scripts. Chrome with JavaScript disabled at 1440/390/360 pixels: images loaded, GIF favicon correct, removed text absent, no horizontal overflow; downloads, explorer navigation and FAQ work. Package hashes unchanged.

## Animated title and shared wallet theme

CSS stepped horizontal stretch/contraction, disabled for reduced-motion preference. User icon in the header, supplied Download and Mining GIFs in navigation, GifCities Windows and Tux animations in wallet download cards. GIF provenance in ASSETS.md.

Wallet GUI now uses the same blue background tile, yellow text/borders, black panels and cyan controls. Assets ship in tools/assets for both Linux and Windows-through-WSL. Only wallet UI files were updated in the installed WSL application; no node restart or wallet-data changes. Tk smoke passed on Windows and Debian/WSLg, and history tests passed. The later native test candidate is documented in docs/WINDOWS-NATIVE.md. Both archives verified to preserve their node binaries.

Browser verification: 1440/390/360 pixels, all image sources and favicon load, animation is enabled normally and disabled with reduced motion, navigation/downloads/explorer/FAQ work, zero horizontal overflow. 541 HTML pages, 16,186 local links, zero scripts/broken links.

## Native candidate and music update

Short slogan and Slow life, slow money appear across all generated pages. Horizontal stretch/contraction respects reduced motion. Native HTML audio controls request autoplay of the supplied music.mp3, with Memories OST by P l a y s t a s i s credited in the footer alongside the GeoCities inspiration link. Browsers may require pressing Play. No scripts or trackers. Downloads now include the tested unsigned native Windows installer; WSL remains an alternative. Linux uses the updated tested artifact.

Current verification: 541 pages, 17,270 local references, zero broken links and zero scripts. Chrome at 1440/390/360 pixels verifies audio decoding/playback, new slogans, title stretch keyframes, reduced motion, credits, navigation and download hashes. Native installer SHA256: bb609242e745d812c0bdcab44f07602507e0e974252ff9aeab7f9916f9748a25.
