# Experimental protocol v0.2

The executable network is `obsolete-test`. `obsolete` is a disabled experimental
candidate, not a public-mainnet launch commitment. Private testnet distribution
and trivial initial difficulty are not a fair public launch.

## Monetary consensus

Amounts use signed 64-bit integers: 100,000,000 atoms per OBSC. `MAX_MONEY` is
100,000,000,000,000,000 atoms. This range check supplements UTXO conservation and
per-block coinbase validation; the cap is not merely a transfer or UI limit.

For heights 1..3,900,000, basic subsidy is
`500000000000 >> floor((height - 1) / 100000)` atoms. Genesis pays nothing.
Only at height 3,900,000, add 1,300,000 atoms for accumulated rounding loss.
The last reward is 1,300,001 atoms (0.01300001 OBSC); subsequent subsidy is zero.
The authorized sum is exactly 1 billion OBSC. Unclaimed subsidy is not recovered
later. Fees transfer existing coins, and mining can continue after subsidy ends.

Issuance follows height, not wall time. No miners means no new blocks. A hash-rate
burst can accelerate blocks before difficulty catches up. There is no guaranteed
111-year deadline. At a steady target interval, a halving takes about 2.85 years.

The inherited header timestamp is an unsigned 32-bit Unix time and reaches its
limit in 2106. The theoretical 111-year subsidy schedule extends beyond that
date: a reviewed consensus upgrade would be needed beforehand. This prototype
does not promise an unchanged century-long protocol.

## Work, validation and timing

- RandomX output is a 256-bit little-endian integer <= compact target.
- Work input is the canonical 80-byte header, nonce at byte 76 (32-bit LE).
- Block ID is SHA256d of the header, distinct from its RandomX work hash.
- ASERT adjusts every block, fixed genesis anchor, target 900s, half-life 21,600s.
  No minimum-difficulty exception. Initial test target is easy: `0x207fffff`.
- Fixed RandomX seed for heights 0..63. Subsequently use the block hash at
  `floor((height - 64) / 2048) * 2048`, in internal LE byte order. Period 2,048
  blocks (~21.3 days); lag 64 blocks (~16 hours).
- Greatest cumulative work selects the chain, not peer count or simply length.
- Inherited UTXO/signature validation, SegWit, Taproot, timestamp and median-time
  rules; maximum block weight 4,000,000. Mining rewards mature after 100 blocks.
- Submission has no artificial sleep. Slowness comes from the target block time.
- No privileged minting RPC, transfer tax, lottery, burn, yield or promised return.

## Identity

| Network | Selection | Magic | P2P / RPC | SegWit prefix |
| --- | --- | --- | --- | --- |
| Test | `obsolete-test` | `4f425432` | 19777 / 19778 | `tobs1` |
| Disabled candidate | `obsolete` | `4f425332` | 9777 / 9778 | `obs1` |

Subdirectories: `obsolete-testnet-v2`, `obsolete-mainnet-v2`. Neither new chain has DNS
seeds, fixed peers, assumed-valid blocks or inherited minimum chainwork. Peers
must be explicitly configured. Test genesis block ID:
`9576894f8fffa098a9b1c04c3a3edb774d9dc7f58413e0906e781ecd8f0ede98`.
Constants and proofs are pinned in `genesis.json` and
`src/consensus/obsolete_genesis.h`; reproduce with `tools/genesis.py --verify`.

Wallet test fee: 1 atom/vbyte, paid to miners. Node relay/mempool policy may require
a higher fee. RandomX favors CPUs but does not prove ASIC impossibility or equal
rewards per miner. The supplied reference miner uses a single light-mode thread.
