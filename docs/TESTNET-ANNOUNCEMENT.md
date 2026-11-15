# Obsolete Coin (OBSC) - CPU-mined testnet looking for testers

It's tacky, cheap, and slow.

Obsolete Coin is an experimental proof-of-work coin with a retro desktop wallet
and a plain-HTML website. The first node runs on a Dell Micro 7040 from 2016.

- RandomX CPU mining; included miner is a single-thread reference implementation.
- 15-minute target block interval, with per-block ASERT difficulty adjustment.
- Maximum authorized issuance: 1,000,000,000 OBSC; eight decimal places.
- Native Windows x64 test wallet/node/miner; Linux package; WSL alternative.
- Explorer updates automatically from the first node and shows data freshness.

We are looking for volunteers to test fresh synchronization, mining, transfers,
wallet restarts and encrypted backups. Independent full-node operators are welcome.

Website and downloads: https://obsoletecoin.pages.dev/
Connection instructions and current peer: https://obsoletecoin.pages.dev/join.html
Explorer: https://obsoletecoin.pages.dev/explorer/index.html
Forum: https://obsoletecoin.pages.dev/forum
Run a node: https://obsoletecoin.pages.dev/nodes.html
Source code: https://github.com/jcib/obsoletecoin

This is TESTNET, not mainnet. Test coins have no monetary value, the chain can be
reset, and balances will not become mainnet coins. Initial test difficulty is easy,
so actual block intervals vary. Mining rewards require 100-block maturity.
The chain already contains locally mined test rewards; this is not a fresh mainnet launch.

This code has not had an independent security
audit. Local and CI tests cover transfers, reorganizations and several failure cases,
but do not prove safety. A dominant miner can reorganize this small network.
The first home node has no uptime guarantee. There is no investment offer, exchange
listing, promised return or scheduled mainnet launch.

Please report OS, package version, reproduction steps, block height and redacted errors.
Never share wallet files, keys, passphrases or RPC credentials.

---
Operator note: anonymous website/download checks, external P2P genesis handshake,
and fresh synchronization passed. Mining and desktop transfers were also verified
on disposable nodes. The website and forum are hosted on Cloudflare Pages.
This document is ready for the owner to post; it was not sent to a forum.
