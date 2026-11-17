"""Pinned network identities used by the desktop wallet, miner and backup verifier."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Network:
    chain: str
    label: str
    genesis: str
    directory: str
    address_prefix: str
    p2p: int
    rpc: int

    def verify(self, rpc):
        info = rpc.call('getblockchaininfo')
        if info['chain'] != self.chain:
            raise ValueError(f'Only Obsolete {self.label.lower()} is supported by this wallet')
        if rpc.call('getblockhash', 0) != self.genesis:
            raise ValueError(f'Wrong {self.label.lower()} genesis')
        return info


TESTNET = Network('obsolete-test', 'TESTNET',
                  '9576894f8fffa098a9b1c04c3a3edb774d9dc7f58413e0906e781ecd8f0ede98',
                  'obsolete-testnet-v2', 'tobs1', 19777, 19778)

MAINNET = Network('obsolete', 'MAINNET',
                  '39edafd04ad371911d1d17c38c40d16878b550489bc3df92530a7c813b0de133',
                  'obsolete-mainnet-v2', 'obs1', 19777, 9778)
