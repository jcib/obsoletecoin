# Obsolete Coin 0.5.0 experimental mainnet

The Windows x64 desktop application and the Debian 13 x86-64 archive start a local full node on the Obsolete Coin network named `obsolete`. New receive addresses begin with `obs1`. Testnet balances and transaction history belong to a separate blockchain.

## Start the wallet

On Windows, run the mainnet installer or extract the entire portable ZIP and open `ObsoleteCoin.exe`. On Linux, extract the archive, install Python 3, Tk, SQLite and the Debian 13 libevent runtime packages, then run `./Start-Wallet.sh`.

The mainnet wallet uses `~/.obsoletecoin-mainnet` by default. The node keeps its chain, wallet and RPC cookie under the `obsolete-mainnet-v2` subdirectory. Keep a private backup and use the wallet's recovery check after encryption. Other Obsolete Coin installations can remain installed.

The desktop checks the project's public bootstrap record at startup. You can also enter a mainnet peer using **Network  >  Connect peer**, or pass `--peer HOST:19777` when starting the desktop. When zero peers are connected, the displayed height is local. Synchronize before accepting payments or starting the CPU miner.

## Node operators

Use `bitcoind -chain=obsolete` with a dedicated data directory. The P2P port is TCP 19777. Keep RPC 9778 on loopback. The repository includes a wallet-disabled systemd service in `deploy/obsolete-mainnet.service`. On the Dell the service takes over the existing public P2P port and uses loopback RPC 19778 with a separate mainnet data directory. Its testnet services are retired at cutover.

For a chain identity check, run `bitcoin-cli -chain=obsolete getblockhash 0` with the same data directory as your node. The expected block ID and RandomX proof are recorded in the MAIN entry of `docs/genesis.json` for this release. The genesis reward is zero. Mainnet targets 900 seconds per block with per-block ASERT adjustment. Initial difficulty is provisional and based on local CPU measurements.

## Release scope

These packages are unsigned. Compare their SHA-256 hashes against the release manifest. Independent consensus review, multi-operator resilience testing and independent matching builds are outstanding. A miner controlling most of the work can reorganize the chain. The mainnet explorer reads only the verified mainnet feed.
