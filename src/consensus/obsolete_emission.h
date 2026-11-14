// Copyright (c) 2026 Obsolete Coin contributors. MIT; see COPYING.
#ifndef OBSOLETE_CONSENSUS_EMISSION_H
#define OBSOLETE_CONSENSUS_EMISSION_H
#include <cstdint>
static constexpr int64_t OBSOLETE_COIN = 100000000;
static constexpr int64_t OBSOLETE_CAP = 1000000000LL * OBSOLETE_COIN;
static constexpr int OBSOLETE_HALVING = 100000;
static constexpr int OBSOLETE_LAST_REWARD = 3900000;
// Integer-halving rounding leaves 1,300,000 atoms. Pay them ONCE at the last
// rewarded height. This caps authorized issuance; unclaimed rewards stay lost.
inline constexpr int64_t ObsoleteSubsidy(int height)
{
    if (height <= 0 || height > OBSOLETE_LAST_REWARD) return 0;
    const int era = (height - 1) / OBSOLETE_HALVING;
    return ((5000LL * OBSOLETE_COIN) >> era) +
        (height == OBSOLETE_LAST_REWARD ? 1300000 : 0);
}
#endif
