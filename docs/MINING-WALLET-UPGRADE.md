# Mining and wallet improvements (Windows 0.4.0)

These changes follow v0.3.0-testnet-rc1. The Windows x64 installer and portable ZIP
are released as [v0.4.0-testnet-rc1](https://github.com/jcib/obsoletecoin/releases/tag/v0.4.0-testnet-rc1)
and linked from the [website](https://obsoletecoin.pages.dev/downloads).
They include the rebuilt native node with the security backports. The chain remains
experimental testnet v0.2. The binaries are unsigned. Linux/WSL packages remain at
0.3.0-rc1; existing installations do not update themselves.

## Mining

Choose 1–4 threads (limited by detected CPU count) and 25/50/75/100% activity in the
desktop mining panel. Defaults are one thread and 50% activity. Each worker uses
about 256 MiB plus its VM; the full node uses additional memory. Activity is a short
work/rest duty cycle per worker, not an exact operating-system CPU ceiling.

The panel updates every second with actual completed hashes, a recent H/s average,
session elapsed time, accepted blocks and stale/rejected work. H/s includes waiting
time and is neither an earnings estimate nor the network hashrate. Accepted blocks
can later be reorganized out. Stopping shows zero current H/s while retaining session
counts. Stop is checked between hashes; in-progress library initialization/RPC may
take longer. A local node, pinned testnet genesis, completed initial synchronization
and at least one peer are required. Connection loss stops mining with an explanation.

Workers use separate RandomX light VMs and unique coinbases. The node supplies fees,
transactions, target and branch-specific seed through `getblocktemplate`. Workers
refresh work at short intervals and submit normally validated blocks. The library is
the existing pinned RandomX, not a new cryptographic implementation.

CLI example (same local wallet/node cookie as before):

```sh
python tools/mine.py --address tobs1... --threads 2 --activity 50 --library /path/to/librandomx.so
```

The complete distribution discovers its bundled library. Developer layouts can pass
`--library` explicitly. CLI defaults to one thread and 100% activity.

## Wallet

Network and balance data refresh every five seconds while no operation/dialog is
active. The status distinguishes offline, synchronizing and caught up with connected
peers. The last state is not a claim of global network consensus. Failed refreshes
explicitly mark the displayed balance as potentially stale.

Available, pending and immature balances stay separate. Newly mined rewards have
100 additional blocks to wait: approximately 25 hours at the target interval, with
no fixed-time guarantee. Immature transaction details show the remaining blocks
using Core's `101 - confirmations` maturity calculation.

Use **Protect / check recovery**:

1. Encrypt the wallet and store its passphrase separately.
2. Save a fresh private backup after encryption and keep a copy on another device.
3. Select a backup and enter its passphrase. Verification starts a temporary offline
   testnet node, restores that file and compares its public descriptors with the open
   wallet. An encrypted backup must unlock successfully. Wrong-wallet copies fail;
   a watch-only copy cannot pass as a backup of a wallet with private keys.

Verification does not replace the live wallet or rescan transaction balances. It does
not prove recovery after total device loss or possession of every imported external
signing key. The temporary copy is removed on normal completion; this is ordinary
file cleanup, not a secure-erasure guarantee. Store backups privately.
