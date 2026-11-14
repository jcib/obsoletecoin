// Obsolete Coin consensus specification tests. MIT; see COPYING.
#include <chainparamsbase.h>
#include <arith_uint256.h>
#include <consensus/amount.h>
#include <consensus/brisvia_emission.h>
#include <consensus/obsolete_genesis.h>
#include <kernel/chainparams.h>
#include <pow.h>
#include <boost/test/unit_test.hpp>
BOOST_AUTO_TEST_SUITE(brisvia_consensus_guards_tests)
BOOST_AUTO_TEST_CASE(obsolete_emission_full_schedule) {
    const auto params = CChainParams::BrisviaTestNet();
    const auto& c = params->GetConsensus();
    BOOST_REQUIRE_EQUAL(c.nBrisviaInitialSubsidy, 5000 * COIN);
    BOOST_REQUIRE_EQUAL(c.nSubsidyHalvingInterval, 100000);
    BOOST_REQUIRE_EQUAL(c.nBrisviaTailSubsidy, 0);
    int64_t total = 0;
    for (int h = 0; h <= 3900001; ++h) {
        const auto reward = BrisviaGetBlockSubsidy(h,c.nBrisviaInitialSubsidy,0,c.nSubsidyHalvingInterval);
        total += reward;
        BOOST_REQUIRE(total <= MAX_MONEY);
    }
    BOOST_CHECK_EQUAL(total, 1000000000LL * COIN);
    BOOST_CHECK_EQUAL(ObsoleteSubsidy(0),0);
    BOOST_CHECK_EQUAL(ObsoleteSubsidy(100000),5000*COIN);
    BOOST_CHECK_EQUAL(ObsoleteSubsidy(100001),2500*COIN);
    BOOST_CHECK_EQUAL(ObsoleteSubsidy(3900000),1300001);
    BOOST_CHECK_EQUAL(ObsoleteSubsidy(3900001),0);
    BOOST_CHECK_EQUAL(ObsoleteSubsidy(2147483647),0);
}
BOOST_AUTO_TEST_CASE(obsolete_network_and_genesis) {
    const auto test = CChainParams::BrisviaTestNet();
    const auto main = CChainParams::BrisviaMain();
    for (const auto* p : {test.get(),main.get()}) {
        const auto& c = p->GetConsensus();
        BOOST_CHECK(c.fPowRandomX);
        BOOST_CHECK(!c.fPowAllowMinDifficultyBlocks);
        BOOST_CHECK(!c.fPowNoRetargeting);
        BOOST_CHECK_EQUAL(c.nPowTargetSpacing,900);
        BOOST_CHECK_EQUAL(c.nASERTHalfLife,21600);
        BOOST_CHECK(c.nMinimumChainWork.IsNull());
        BOOST_CHECK(c.defaultAssumeValid.IsNull());
        BOOST_CHECK(p->FixedSeeds().empty());
        BOOST_CHECK(p->DNSSeeds().empty());
        BOOST_CHECK_EQUAL(p->GenesisBlock().vtx[0]->GetValueOut(),0);
        BOOST_CHECK(CheckRandomXProofOfWorkContextual(p->GenesisBlock(),nullptr,0,c,nullptr)==PoWCheckResult::VALID);
    }
    BOOST_CHECK_EQUAL(test->GenesisBlock().GetHash().GetHex(),OBSOLETE_TEST_HASH);
    BOOST_CHECK_EQUAL(main->GenesisBlock().GetHash().GetHex(),OBSOLETE_MAIN_HASH);
    BOOST_CHECK(test->GenesisBlock().GetHash()!=main->GenesisBlock().GetHash());
    BOOST_CHECK(test->MessageStart()!=main->MessageStart());
    BOOST_CHECK_EQUAL(test->Bech32HRP(),"tobs");
    BOOST_CHECK_EQUAL(main->Bech32HRP(),"obs");
    BOOST_CHECK_EQUAL(test->GetDefaultPort(),19595);
    BOOST_CHECK_EQUAL(main->GetDefaultPort(),9595);
}
BOOST_AUTO_TEST_CASE(obsolete_asert_hashrate_response) {
    auto c = CChainParams::BrisviaTestNet()->GetConsensus();
    // Use a target below the floor so both directions can be observed.
    const uint32_t bits = 0x1e0fffff;
    const int64_t start = 1794614400;
    c.asertAnchorParams = Consensus::Params::ASERTAnchor{0,bits,start-900};
    CBlockHeader candidate;
    candidate.nTime = start+101*900;
    const auto scheduled = GetNextASERTWorkRequiredFromValues(100,start+100*900,&candidate,c);
    const auto fast = GetNextASERTWorkRequiredFromValues(100,start+100*900-21600,&candidate,c);
    const auto slow = GetNextASERTWorkRequiredFromValues(100,start+100*900+21600,&candidate,c);
    BOOST_CHECK_EQUAL(scheduled,bits);
    arith_uint256 normal,hard,easy;
    normal.SetCompact(scheduled);hard.SetCompact(fast);easy.SetCompact(slow);
    BOOST_CHECK(hard < normal);
    BOOST_CHECK(easy > normal);
    arith_uint256 half = normal, twice = normal;
    half >>= 1;
    twice <<= 1;
    BOOST_CHECK_EQUAL(half.GetCompact(),fast);
    // Compact encoding may discard low bits: do not assert unencoded precision.
    BOOST_CHECK_EQUAL(twice.GetCompact(),slow);
}
BOOST_AUTO_TEST_SUITE_END()
