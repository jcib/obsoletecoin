# Source security maintenance — 16 November 2026

Scope: implementing-agent review of the working tree based on commit
`05079264a93d405df73c144479ab8601c5463473`. This is not an independent audit.
Published v0.3.0-testnet-rc1 packages are not replaced by editing this repository.
Mainnet remains disabled. Consensus parameters, genesis and emission are unchanged.

## Upstream findings

The three October disclosures are applicable to the inherited source. Their source
fixes were backported from the Bitcoin Core 30.x [30.4 changes](https://github.com/bitcoin/bitcoin/pull/36664),
without replacing the fork's version, chain parameters or release metadata.

| Advisory | Source finding and action |
| --- | --- |
| [CVE-2026-117349](https://bitcoincore.org/en/2026/10/28/disclose-fpausesend-oom/) | Missing persistent send-pause timeout. Track the transition into backpressure at both enqueue/send paths and disconnect after the timeout even if traffic continues. |
| [CVE-2026-117350](https://bitcoincore.org/en/2026/10/28/disclose-tcp-oom/) | The select backend watched exceptional socket events while reads were paused. Register exception events only when receiving is requested. |
| [CVE-2026-117346](https://bitcoincore.org/en/2026/10/28/disclose-undo-overflow/) | Block/undo offsets and file operations used narrow types. Carry 64-bit positions through storage and use 64-bit seek/tell/truncate on Windows. 32-bit platforms and FAT32 remain outside the supported storage configuration. |
| [CVE-2025-62859](https://bitcoincore.org/en/2026/11/10/disclose-cve-2025-62859/) | Existing `PartiallyDownloadedBlock::FillBlock` checks witness mutation before reporting success; both compact-block callers supply SegWit activation. Fix already present. |
| [CVE-2025-62860](https://bitcoincore.org/en/2026/11/10/disclose-cve-2025-62860/) | Existing incoming-onion handling passes no proxy IP into range-whitelist matching. Fix already present. |
| [CVE-2025-62861](https://bitcoincore.org/en/2026/11/10/disclose-cve-2025-62861/) | Existing `SingleTRUCChecks`/sibling eviction is gated by `!args.m_bypass_limits`. Fix already present. |

Regression additions exercise paused send timeout despite fresh send/receive times,
paused receive with local TCP urgent data, and serialization/seek above 4 GiB without
writing a multi-gigabyte fixture. These are bounded regressions, not load certification.
The `select()` regression also fails on the original source and passes on the patch
when that production backend is compiled on Linux. The native Windows rebuild also
passed these regressions, its full available CTest suite and the expanded integration;
see the platform evidence linked below for scope and remaining release limits.

## Fork-specific review

- RandomX input remains the canonical 80-byte header with little-endian nonce and
  result. Existing official-vector, serialization and endianness tests are retained.
- Seed lookup follows the candidate's branch, including indexed side branches and
  the bounded 2,112-header transient ring. Existing tests cover 63/64, 2111/2112 and
  4159/4160 boundaries. Live disposable-node integration now also mines across 64
  using the external worker engine.
- Expected difficulty and target bounds are resolved before expensive header work.
  ASERT constants and integer arithmetic are unchanged. Existing equivalence tests,
  invalid-target/timestamp cases and difficulty simulation remain relevant.
- The RandomX cache is keyed by seed, with serialized construction, per-VM hashing
  locks and retry backoff. The new desktop miner owns separate light VMs and does
  not turn validator RPC concurrency into nominal mining threads.
- Subsidy and UTXO conservation remain enforced by the node. The full emission
  schedule test and real overpaying-coinbase rejection are retained. External mining
  includes node-selected transactions and the witness commitment, then submits the
  complete block for normal validation.
- Wallet operations now also check the pinned testnet genesis. Backup verification
  uses an offline temporary node, compares public descriptors and checks encrypted
  backup passwords and signing capabilities; it does not overwrite or rescan the live wallet.

No claim is made that this inspection excludes other vulnerabilities. Remaining
launch gates include independent review, sustained hostile-traffic/resource testing,
independent full builds, signing and operational independence. Local resource failures,
cache pressure under adversarial branches and majority-work attacks remain review
areas. Do not close the mainnet gate based on this report.

## Maintenance

`python tools/check_upstream_security.py` reads the official advisory index and fails
when it sees a disclosure published after `reviewed_through` in
`security-upstream.json`. The `security-watch.yml` workflow prepares a weekly/manual
check; it becomes scheduled only when published on the default GitHub branch.
It does not apply patches, publish messages, detect backdated edits, or establish
applicability. Advance the review date only after examining new entries and recording
decisions and tests here or in a successor report.

## Reproduction

- `tools/check-upgrade-linux.sh`: fresh core/RandomX build and CTest suites.
- `python -B -m unittest discover -s tests -v` and wallet tests under `tools`.
- `tools/integration.py`: disposable peers, external mining, transfers, rejection,
  competing branches, restarts and offline recovery (including wrong password/wallet).
- `tools/adversarial.py`: disposable peer traffic, partition and recovery checks.
- `tools/ui_smoke.py`: real Tk rendering and callback checks.

Validation results and platform limits are recorded in
[the upgrade evidence](readiness/2026-11-16-wallet-mining-security/README.md).
