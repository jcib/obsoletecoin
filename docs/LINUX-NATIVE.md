# Obsolete Coin 0.4.0 — native Linux x86-64

This package has the same wallet, mining and security features as Windows
0.4.0-testnet-rc1. It contains compiled Linux node/CLI/wallet binaries, the RandomX
library and the Python/Tk desktop. The reference environment is Debian 13 x86-64.
It is an unsigned experimental TESTNET release; mainnet remains disabled.

## Start the wallet

Install runtime dependencies on Debian 13:

```sh
sudo apt-get update
sudo apt-get install --no-install-recommends python3 python3-tk \
  libevent-2.1-7t64 libevent-core-2.1-7t64 libevent-extra-2.1-7t64 \
  libevent-pthreads-2.1-7t64 libsqlite3-0 libstdc++6 libgcc-s1
```

Extract the entire `ObsoleteCoin-0.4.0-Testnet-Linux-x64.tar.gz` archive, enter
`obsoletecoin-linux`, and run:

```sh
./Start-Wallet.sh
```

A graphical Linux desktop is required for the wallet window. The launcher starts
the packaged node and opens the `obsolete` wallet. Choose **Network > Connect peer**
and use the current peer shown at https://obsoletecoin.pages.dev/join.html.
Peer choices are saved. Wait for synchronization, then choose mining threads and
activity and select **Mine / Stop**. Hash rate, hashes, elapsed time and accepted
blocks are measured by the same mining engine as the Windows wallet.

Use **Protect / check recovery** to encrypt, back up and verify an encrypted copy
offline. Keep the backup and its passphrase privately and separately.
The initial wallet is not encrypted until you encrypt it.

## Data and compatibility

Close the old wallet/node before upgrading. Existing Linux wallet data remains in
`~/.obsoletecoin`; application extraction does not overwrite it. Local RPC uses
port 19778 with cookie authentication and listens only on loopback. The desktop
node uses outbound P2P connections. Closing the wallet stops only a node it started.

Another data directory can be selected with
`./Start-Wallet.sh --datadir /path/to/data --rpcport 19779`.
For a headless dedicated node, use `python3 -B tools/node.py --listen --peer HOST:19777`.
Keep RPC private. The native Linux archive is not a Windows package.

Mining rewards require 100 additional blocks after inclusion. Test coins have no
monetary value. Neither confirmations nor these local checks establish resistance
to majority-hash-power attacks.

Check the published SHA-256 before extraction. `PROVENANCE.json` records packaged
files and build inputs; `dependencies.txt` records system library requirements.
Other distributions, macOS and ARM are not validated by this Debian x86-64 build.
