# Mainnet readiness - 14 November 2026

**BLOCKED for mainnet. Working unsigned native test candidate prepared.** No mainnet activation, public server or signing identity was created. The owner requested files and tests first. This work is not an independent audit or a security guarantee.

## Completed evidence

- Windows native core: 149 CTest suites passed. Linux: 149 suites passed, with Debian 13 runtime/mining/wallet recovery. Tested core source: 46beda64f6b88419238c13a03c4a81679a94a80a. Subsequent commits change tooling, desktop and documentation, not consensus.
- Real Windows 11 and Debian integration: CPU mining, RandomX seed boundary 64, synchronization, reward maturity, desktop signed transfer with exact fee, insufficient funds, duplicate-credit prevention, invalid proof, overpaying subsidy, past/future timestamps and wrong difficulty rejection, greater-work reorganization, restart, encryption and backup restoration.
- Both platforms: conflicting spends on partitioned branches, losing-spend conflict after reorganization, rejection of unauthenticated RPC, 16 oversized P2P headers without a crash, abrupt termination followed by peer recovery and fresh from-genesis synchronization.
- Actual ENOSPC in a private 700 MiB Linux tmpfs: persisted height 2 recovered and mining resumed to height 3 after freeing space. No real node disk was filled.
- Native x64 wallet/node needs neither WSL nor installed Python. Runtime: CPython 3.14.10 and Tcl/Tk 9.0.4. Retro UI, dates/details, exact fee/total before signing, saved testnet peers and a peer/sync check before GUI mining.
- Frozen executable starts its own disposable node and mines real test blocks. The unsigned installer passes installation, GUI/mining, reinstallation, uninstall preserving wallet bytes, and reinstall/open of that same wallet on Windows 11 build 26300. No existing wallet or active miner was used.
- Two clean GUI builds on the same machine match all 952 files. Two installer compilations with identical inputs also match byte for byte. This does not establish independent reproducibility of the node or complete release.
- Prepared build/install/signing scripts, dependency hash lock, license notices, manifests, source exporter for review, health JSON probe, service/config templates and launch/recovery runbook.

Machine-readable results: [readiness/2026-11-14](readiness/2026-11-14). Reproduction: [release/README.md](../release/README.md). Native user instructions: [WINDOWS-NATIVE.md](WINDOWS-NATIVE.md). Review scope: [INDEPENDENT-REVIEW.md](INDEPENDENT-REVIEW.md).

## Open launch gates

| Priority | Area | Current state | Acceptance before launch |
|---|---|---|---|
| P0 | Independent consensus/security review | Not performed | Independent examination of inherited fork and Obsolete delta; fix and retest critical/high findings. |
| P0 | Difficulty/fair launch | Simulations added; initial production difficulty undecided | Review results with measured independent miner rates, then publish calibrated launch parameters. Easy private-test difficulty is unsuitable for a fair-launch claim. |
| P0 | Network/genesis | Mainnet startup guard retained | Reviewed public launch/genesis specification and clean distribution. No migration of test balances. |
| P0 | Infrastructure and hash power | Templates only; no new servers/domain | Independent operators/miners across failure domains; empty-peer bootstrap, alert delivery, recovery exercises and concentration-risk assessment. Peer count is not hash security. |
| P0 | Adversarial/stability campaign | Local and CI regressions expanded | Sustained public testnet with independent operators; hostile-traffic/resource-budget tests; no unexplained divergence or unresolved severe failures. |
| P0 | Release authenticity/reproducibility | Working unsigned Windows installer; local GUI repeat match | Owner signing certificate, signed manifests, independent matching full builds, dependency review and every claimed Windows version tested. |
| P1 | Wallet fee/recovery | Implemented and tested | Retest each exact release and future upgrade; explicit encryption/private backups remain necessary. |
| P1 | Operations | Runbook, templates and read-only probe | Independently deployed monitoring/alerts, clocks, disk limits, power recovery and incident response. |
| P1 | Explorer | Dated static snapshot | Keep capture date explicit. Automated refresh must never expose wallet RPC. |
| P2 | Timestamp horizon | uint32 limit in 2106 | Reviewed future upgrade; no unchanged century-long protocol claim. |

## Observed limits

The ASERT harness compiles CalculateASERT verbatim from production C++. Five seeded, 1,000-block Poisson scenarios cover steady mining, 100x arrival/departure, 99% departure, forward timestamp sensitivity and easy testnet start. The burst/departure scenario contains a 72,554-second gap (about 20.2 hours). This is a model result, not an observed outage or prediction. Difficulty convergence cannot guarantee smooth intervals or a fixed emission duration. Timestamp sensitivity does not prove an entire adversarial timestamp sequence admissible; real-node tests separately reject too-old and too-far-future blocks.

After abrupt process kills, the fixtures initially reopened at height 0 and then recovered the correct tip from a surviving peer. This supports recovery with peers, not instantaneous durability of every recently mined block. Clean stop/restart and encrypted-wallet restoration are tested separately. Physical power failure, corruption and loss of all replicas remain outside these fixtures. Sixteen malformed messages are a bounded regression, not a DoS-capacity audit.

Neither four confirmations nor these tests prevent majority-work attacks. No fixed test duration or node count proves safety. Next: independent review, public testnet rehearsal, independent full rebuilds and official signing. Do not remove the mainnet guard to bypass the gates.

## CI reference

- [Native core: 149 suites](https://github.com/jcib/obsoletecoin/actions/runs/43593357782).
- [Linux: 149 suites and Debian recovery](https://github.com/jcib/obsoletecoin/actions/runs/43593357813).
- Expanded workflow results are recorded in the evidence index once completed; running workflows are not passes.
