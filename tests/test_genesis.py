import json
import struct
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from genesis import GENESIS_PARAMETERS, POW_LIMIT, genesis_parts, target_from_bits


class GenesisTests(unittest.TestCase):
    def test_wallet_genesis_matches_each_committed_proof(self):
        from coin_network import MAINNET, TESTNET
        records = json.loads((Path(__file__).resolve().parents[1]/'docs/genesis.json').read_text())
        self.assertEqual(MAINNET.genesis, records['MAIN']['hash'])
        self.assertEqual(TESTNET.genesis, records['TEST']['hash'])
        self.assertNotEqual(MAINNET.genesis, TESTNET.genesis)
        self.assertNotEqual(MAINNET.directory, TESTNET.directory)

    def test_candidate_parameters_only_affect_candidate_header(self):
        testnet = genesis_parts('TEST')
        candidate = genesis_parts('MAIN')
        time, bits = 1794700800, 0x1e0fffff
        with patch.dict(GENESIS_PARAMETERS, MAIN=(time, bits)):
            self.assertEqual(testnet, genesis_parts('TEST'))
            self.assertEqual(candidate[3][:-8] + struct.pack('<II', time, bits),
                             genesis_parts('MAIN')[3])

    def test_work_threshold_follows_compact_bits(self):
        self.assertEqual(target_from_bits(0x207fffff), POW_LIMIT)
        self.assertEqual(target_from_bits(0x1e0fffff), 0xfffff << 216)
        self.assertEqual(target_from_bits(0x02012300), 0x123)
        for bits in (0, 0x20800001, 0x2100ffff):
            with self.subTest(bits=bits), self.assertRaises(ValueError):
                target_from_bits(bits)
