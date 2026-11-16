# Wallet, miner and security upgrade evidence

Source changes and a local Windows candidate based on `05079264a93d405df73c144479ab8601c5463473`.
The measurements and JSON files below record the pre-publication validation state.
They did not update a public node or installed wallet. Publication is tracked
separately; see the [0.4.0 release notes](../../../release/RELEASE-NOTES-0.4.0.md).

## Public release

Windows [v0.4.0-testnet-rc1](https://github.com/jcib/obsoletecoin/releases/tag/v0.4.0-testnet-rc1)
was published on 16 November 2026 from source commit
`0f6021f2fca075932bd619f6ed1a3954913a9727`. The website was updated in deployment
`d5116b08` at https://obsoletecoin.pages.dev/. Linux/WSL downloads remain at 0.3.0-rc1.

`publication.json` records anonymous verification of all six GitHub assets, both
website installer URLs, their SHA-256 hashes, the release tag's source commit and
five public pages. The versioned installer URL avoids cached older downloads.
The published binaries are the exact locally validated files recorded below.
Additional GitHub Linux and Windows CI runs were still in progress at publication;
the release's validation claims refer to the completed local checks.

## Windows desktop and miner

Initial validation used CPython 3.14.10 with the pinned Tcl/Tk 9.0.4 runtime and the
previously built native testnet node/RandomX DLL. That initial run validated the
Python changes. The subsequent native rebuild is recorded below.

- 9 client/security-watch tests and 15 wallet/mining tests cover the final source.
- Real two-node integration passed: external mining with two workers at 50% duty,
  seed transition 63/64, exact completed-hash telemetry, witness transaction inclusion,
  synchronization, maturity, signed desktop transfer, insufficient funds, duplicate
  credit prevention, invalid proof/subsidy/timestamp/difficulty rejection, greater-work
  reorganization, restart and encrypted wallet restore.
- The recovery checker restored offline and rejected wrong passphrases and another
  wallet's backup. The real wallet was not replaced.
- Tk rendered without callback errors, including all controls at 1020x940 and
  vertical scrolling at 940x640. Local preview: `.local/readiness/wallet-upgrade.png`.
- The final confirmation dialog suppresses automatic polling while awaiting input.

## Native Windows 0.4.0 candidate

The node and both RandomX libraries were rebuilt locally with MSYS2 UCRT64 GCC
16.2.0, using `release/build-native-msys.sh`. Core CTest finished in 417.56 seconds:
148 passed, zero failed, one optional `script_assets_tests` skipped because its
external data is absent. The Windows socket, send-pause and 64-bit storage
regressions all passed. The fee-estimator suite was slow under CTest and also
passed when run separately; no source workaround or test exclusion was needed.

The rebuilt native node then passed the 9 client/security-watch tests, 15 wallet
tests, expanded two-node integration and the adversarial checks listed above.
See `windows-core.json` and `windows-adversarial.json` for results and scope.

The final frozen executable opened the real Tk interface, mined at least two
blocks using two threads at 50% activity, synchronized a second local node, and
verified an encrypted backup offline. All nodes and wallets used disposable
directories. See `final-smoke.json`.

`artifacts/windows-0.4.0-testnet` contains an Inno Setup installer, portable ZIP,
extracted portable application and SHA256SUMS.txt. Every file in PROVENANCE.json
was checked and the ZIP passed its CRC check. `windows-package.json` records the
artifact hashes. The installer was compiled but not executed against the existing
installation; its payload is the tested portable directory. The candidate is
unsigned and has not been published. Source and toolchain hashes are included.

## Local performance observation

`mining-benchmark.json` records four five-second fixed-header runs of the pinned
native RandomX library. Initialization is excluded; compilation was running on the
host at the same time. This is a local microbenchmark, not a network/miner forecast.

| Threads | Activity | H/s | Process CPU / elapsed (core equivalents) |
| --- | --- | --- | --- |
| 1 | 25% | 12.18 | 0.27 |
| 1 | 100% | 43.70 | 0.99 |
| 2 | 50% | 44.79 | 1.01 |
| 2 | 100% | 84.40 | 1.97 |

The observations support real parallel hashing and approximate duty control.
They do not establish an exact total-machine CPU cap or a universal speedup.

## Linux core

Fresh Debian/WSL GCC 14.2 Release build completed successfully.

- CTest: 148 suites passed, zero failed, one optional suite (`script_assets_tests`)
  skipped because its external `script_assets_test.json` data is not installed.
  Included RandomX, headers synchronization, monetary consensus, wallet, network,
  storage and the three added security regressions. Total test time: 98.57 seconds.
- The production `select()` branch was separately compiled on Linux. The new urgent
  data regression failed against the original source (exit 201) and passed against
  the patched source (exit 0). See `select-regression.json` for source hashes.
  This exercises that backend but is not a native Windows OS build.
- The expanded two-node integration passed on the rebuilt Linux node, including
  external mining across seed 64, witness transfer, reorganization, restart and
  offline recovery with wrong-password/wrong-wallet rejection.
- Adversarial regression passed: conflicting spends across a partition, unauthenticated
  RPC rejection, 16 oversized P2P headers, abrupt termination and peer-assisted recovery,
  plus fresh synchronization from genesis. See `adversarial.json`. After the abrupt
  kill the node initially reopened at height 0 and recovered from its peer; this is
  not evidence of immediate persistence of every recently mined block.
- Five 1,000-block ASERT simulations passed their assertions using the production
  calculation verbatim. See `difficulty.json`; these are models, not live network
  predictions. Parameters and the long-gap limitations are unchanged.
- The official advisory-index check completed with no disclosures newer than the
  recorded review date. This does not claim exhaustive vulnerability detection.

The final additional backup-capability guard (watch-only versus private keys/external
signer) is covered by the final Windows Python suite. The preceding Linux Python run
contained 9 client/security-watch and 14 wallet/miner tests, all passing.

The original socket fixture was exported with host Git because this WSL installation
has no `git` executable. When reproducing there, save `git show HEAD:src/util/sock.cpp`
from the unmodified base revision to `.local/upgrade-select/baseline-sock.cpp`.

## Release limits

The native Windows rebuild and local checks are complete. Installer lifecycle
testing in a clean Windows account, independent matching builds and signing remain
outstanding for this candidate. The existing Windows CI workflow includes the
added regressions and expanded integration; no new CI run or public release is
claimed by this local build.

This review is not independent. Mainnet launch gates in `docs/MAINNET-READINESS.md`
remain open. See `docs/SECURITY-REVIEW-2026-11-16.md` for the scope and upstream sources.
