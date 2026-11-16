# Obsolete Coin 0.4.0-rc1 — Windows testnet

This Windows x64 release adds configurable CPU mining, wallet recovery checks and
three security backports. It includes the rebuilt native node, wallet tools,
RandomX library and desktop application. No Python or WSL installation is needed.
The chain remains experimental testnet v0.2; mainnet is disabled.

## Downloads

- **ObsoleteCoin-Testnet-Setup.exe**: per-user Windows installer.
- **ObsoleteCoin-0.4.0-Testnet-Windows-x64.zip**: portable application. Extract the
  complete archive and open ObsoleteCoin.exe with its DLLs and _internal folder.
- **Windows-PROVENANCE.json**, **Native-SOURCE-HASHES.json**, **SHA256SUMS.txt**:
  package contents, build-source hashes and checksums.

Close the previous application before upgrading. Back up your wallet privately.
The application keeps its existing data in `%USERPROFILE%\.obsoletecoin`.
Current peer and synchronization instructions: https://obsoletecoin.pages.dev/join.html

Linux and Windows/WSL downloads remain at 0.3.0-testnet-rc1; they do not acquire
these changes from this Windows release. Their existing packages remain available
at https://github.com/jcib/obsoletecoin/releases/tag/v0.3.0-testnet-rc1.

## Changes

- Choose 1–4 CPU mining threads, subject to CPU count, and activity per thread.
  See actual hashes, hash rate, elapsed time, accepted and stale/rejected blocks.
- Automatic wallet refresh and clearer separation of available, pending and
  immature balances. Confirmation dialogs suspend background polling.
- Restore a backup on an isolated offline node, verify its passphrase and wallet
  identity/signing capabilities, and leave the live wallet untouched.
- Verify the expected testnet genesis before wallet/miner operations.
- Backport CVE-2026-117349 (persistent send-pause timeout), CVE-2026-117350
  (TCP urgent data bypassing receive backpressure), and CVE-2026-117346
  (64-bit block/undo offsets and Windows file operations).
- Add a weekly/manual upstream security advisory check to the repository workflow.

## Validation and provenance

The Windows core passed 148 CTest suites with zero failures; one optional suite
was skipped because its external script test data was absent. The build also
passed 24 Python tests, two-node mining/transfer/reorganization/recovery integration,
and bounded adversarial checks. The exact frozen application mined with two
threads and verified an encrypted backup in disposable local nodes. Linux core
and integration checks also passed on the corresponding source.

The installer was compiled from the validated portable payload. Installation,
upgrade and uninstallation were not repeated against the existing real installation.
See docs/readiness/2026-11-16-wallet-mining-security for the complete test scope.

These are the already validated local binaries, without a subsequent rebuild.
The build manifests record base commit 05079264a93d405df73c144479ab8601c5463473
plus the working-tree source hashes. The release source includes those changes;
the publication commit is not represented as an embedded binary build commit.

The binaries are unsigned. Checksums detect mismatches, not publisher identity.
Independent security review, independent matching builds and mainnet readiness
remain outstanding. No wallet files, RPC credentials or private keys are included.
