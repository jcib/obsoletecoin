# Obsolete Coin website

A portable English-language GeoCities-inspired site: plain HTML, local CSS and SVG, no JavaScript, external fonts, analytics or runtime framework.

Slogan: **It's tacky, cheap, and slow, but it's also tough and hard-wearing.**

Private website: https://obsoletecoin.pages.dev

Includes downloads, network specifications, mining instructions, FAQ, a mainnet readiness checklist, GitHub links, and a static explorer generated from real public testnet block data. Native Windows without WSL remains planned, not available.

## Build

Run from the repository root with Python 3.10 or newer. Downloads currently use the verified test packages at `../ObsoleteCoin-Windows-WSL.zip` and `.local/artifact/obsoletecoin-linux-experimental.tar.gz`.

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
