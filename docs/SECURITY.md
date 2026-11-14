# Security and launch status

Experimental, unaudited private test network. Bitcoin-derived code does not give
a new chain Bitcoin's hash power, peer diversity, review or economic security.

## Majority-work attacks

An attacker with enough hash power can build a competing valid chain, reorganize
blocks, reverse their own payments, double-spend or censor transactions. Work
alone does not forge someone else's signature or bypass subsidy limits. Four
confirmations do not guarantee safety against a dominant miner.

This version uses ordinary cumulative-work selection. There is no hidden central
checkpoint key, validator committee, privileged mint or hardcoded reorganization
limit pretending to solve the problem. Additional finality needs an explicit
trust model and design. More independent miners and peers help, but do not prove
immunity. Test balances must not be marketed as valuable, final or investment-ready.

## Outstanding before public launch

The reserved candidate network is blocked at startup. Public launch requires an
independent fork/RandomX-header-sync review, adversarial network and DoS testing,
hash-rate/difficulty simulations, initial-difficulty calibration, a launch/genesis
decision, recovery exercises, reproducible release builds and independent miners.
These are outstanding work, not guarantees supplied by the initial CI.
A future timestamp-format upgrade is also required before the inherited 32-bit
header time reaches its limit in 2106; see SPEC.md.

Do not merely remove the guard and reuse private-testnet distribution. The easy
initial target is for tests; it is unsuitable as a fair-launch claim. Per-block
ASERT can still allow bursts and cannot guarantee a fixed issuance duration.

## Wallet boundary

RPC binds to localhost and requires a cookie. The Python client refuses redirects
and cannot contact an arbitrary remote RPC host. Protect cookies like secrets.
Never commit wallet files, cookies, passwords, private keys or debug dumps.
Initial GUI-created wallets are unencrypted until Encrypt is chosen. Encryption
and backup are explicit operations; keep the passphrase separately and securely.

Inherited publicly known cryptographic test vectors are fixtures, not funded
keys. Neither code nor CI needs trading-bot secrets, exchange credentials or home
server access. Report problems privately to the owner while this repository is private.
