# Mainnet readiness - 14 November 2026

Status: BLOCKED. This is a source/evidence review, not an independent security audit or a certification. No mainnet activation was performed. Ticker OBSC changes display only: addresses, genesis, atomic units and balances remain compatible.

| Priority | Area / evidence | Status | Acceptance before launch |
|---|---|---|---|
| P0 | docs/SECURITY.md explicitly lists outstanding independent review; consensus fork and RandomX header validation | Blocker | Independent reviewer examines consensus delta, signatures, emission, RandomX verification and header sync; all critical/high findings fixed and retested. |
| P0 | Easy initial test difficulty; ASERT six-hour half-life in network parameters | Blocker | Reproducible simulations of rapid hash increases/decreases, timestamp manipulation and miner departure; reviewed launch difficulty and documented issuance outcomes. |
| P0 | Reserved mainnet disabled, private test distribution | Blocker | Fresh public launch/genesis specification, announced release process, distinct network identity; no test balances transferred. Do not just remove the startup guard. |
| P0 | Home node and private peer setup, no public seed infrastructure established | Blocker | Independently operated public peers across failure domains, bootstrap from an empty peer database, independent miners, and documented concentration risks. Node count is not hash security. |
| P0 | Native Windows package absent; WSL launcher available | Blocker | Native Windows wallet/node, signed installer, verified upgrade/uninstall preserving wallets; supported Windows versions tested. |
| P0 | Existing CI does not establish long-duration/adversarial coverage | Blocker | Recorded multi-node partition/reorg/double-spend, invalid proof, DoS, restart, disk exhaustion, restore and from-genesis sync exercises; sustained testnet campaign with no unexplained divergence or unresolved severe failures. |
| P0 | Current downloads have checksums, not signed reproducible release evidence | Blocker | Independent matching release builds, signed manifests, dependency provenance and binary/source correspondence. |
| P1 | Wallet encryption and backup are explicit; sending currently confirms amount without exact fee | Pending | Exact fee and total shown before signing/broadcast; backup restoration verified with encrypted wallet and locked/unlocked paths, insufficient funds and invalid address behavior tested. |
| P1 | Operational procedures incomplete for public network | Pending | Monitoring/alerts for sync, peers, disk, memory and stalls; incident/update policy, vulnerability reporting and recovery runbook. Verify home AC recovery and independent redundancy. |
| P1 | Explorer is dated static data | Verified limitation | Keep capture date explicit; automated refresh is optional and must never expose wallet RPC. |
| P2 | Inherited uint32 timestamp limit | Documented | Define upgrade policy before 2106; no claim the complete emission calendar works forever without upgrades. |

## Evidence and limits

Existing security notes: docs/SECURITY.md. Parameters: docs/SPEC.md and src/kernel/chainparams.cpp. Desktop: tools/wallet.py. Release work in this change adds date/time, transaction details, incremental history and OBSC labels; it does not resolve consensus or infrastructure blockers. Test results from this change are recorded in website/README.md and tools/test_wallet_history.py.

Fastest reasonable route: finish and verify the desktop/release pipeline while independent consensus review and difficulty simulations proceed, then run a public testnet rehearsal with independent operators. Set a launch date only after P0 gates close and security-relevant P1 issues are resolved. No fixed number of nodes, confirmations or test days proves immunity to a majority-work attacker.

Reference transaction fields: https://bitcoincore.org/en/doc/32.0.0/rpc/wallet/gettransaction/ and https://github.com/monero-ecosystem/monero-GUI-guide/blob/master/en/ch07.md .
