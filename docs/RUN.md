# Run the private test network

Use a dedicated account/directory. `tools/node.py` explicitly uses `obsolete-test`
and `~/.obsoletecoin`, a 128 MiB DB cache, pruning near 1 GB of block files, and
at most 16 peers. Total storage/RAM is higher: wallets, indexes and RandomX caches
also consume resources. Measure on the Dell before permanent installation.

The node runs in the foreground; Ctrl-C shuts it down. No systemd service, firewall
rule, router forwarding, SSH change or trading-bot restart is automatic. Begin
with LAN-only peers and limit P2P 19595 to participating machines. RPC is local,
cookie-authenticated, on 19596; never expose it publicly.

```sh
python3 tools/node.py --listen                  # home server
python3 tools/node.py --peer 192.168.1.X:19595    # laptop; YOUR server IP
python3 tools/wallet95.py                       # local wallet
```

Each machine has its own node and local cookie. Mining on the laptop uses its CPU;
mining on the server uses the server CPU. No RPC credentials need to be shared.
The reference miner is single-threaded RandomX light mode, not an optimized
multi-core miner. CPU power use and fan activity increase. Stop using Ctrl-C or
Mine / Stop. An already submitted mining batch may finish after closing the UI.
Keep server mining off when you want to limit contention with other services.

Open / Create loads or creates wallet `obsolete`. Receive creates a fresh native
SegWit address. Mine / Stop rewards an address inside the local wallet. To mine to
another wallet, use `python3 tools/mine.py --address YOUR_TOBS1_ADDRESS`.

Rewards mature after 100 blocks (~25 hours at target). Early testnet blocks can
arrive much faster because initial difficulty is intentionally trivial. An
immature balance cannot be spent. Target time is not a transfer ETA.

A newly GUI-created wallet is initially unencrypted. Choose Encrypt, then make a
new Backup. Unlock is temporary (60 seconds). The UI does not export private keys
or save passphrases to disk/logs. Wallet and backup files contain sensitive keys:
keep them outside GitHub, with secure offline copies and a protected passphrase.
Loss of keys/passphrase cannot be recovered by the project.

CLI examples after starting the local node:

```sh
build/bin/bitcoin-cli -chain=obsolete-test -datadir="$HOME/.obsoletecoin" createwallet obsolete
build/bin/bitcoin-cli -chain=obsolete-test -datadir="$HOME/.obsoletecoin" -rpcwallet=obsolete getnewaddress
build/bin/bitcoin-cli -chain=obsolete-test -datadir="$HOME/.obsoletecoin" getblockchaininfo
```

Do not reuse other coins' data directories, wallets or addresses. Integration
tests use temporary local nodes/wallets and remove them afterward. They never
connect to the real home server. No bot, exchange account or EC2 instance is used.
