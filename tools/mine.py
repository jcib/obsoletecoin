"""Solo CPU miner. The full node and CPU work both run on this computer.

A light RandomX VM (approximately 256 MiB) is used by the core. Start a second
node on a laptop, peer it with the server, and run this script on the laptop.
This intentionally simple reference miner is single threaded and not optimized.
"""
import argparse, time
from pathlib import Path
from rpc import RPC, RPCError, default_data_dir

def mine(rpc,address,stop=None,max_blocks=None,maxtries=256):
    info=rpc.call('getblockchaininfo')
    if info['chain']!='obsolete-test': raise ValueError('This miner only supports Obsolete testnet')
    if not rpc.call('validateaddress',address)['isvalid']: raise ValueError('Invalid testnet payout address')
    count=0
    while stop is None or not stop.is_set():
        # Finite batches make Ctrl-C and stale-tip recovery responsive. This RPC
        # performs real RandomX in the local node; it does not fake block creation.
        hashes=rpc.call('generatetoaddress',1,address,maxtries)
        for block in hashes:
            count+=1
            print('Found block',block,flush=True)
        if max_blocks is not None and count>=max_blocks: return count
        if not hashes: time.sleep(0.05)
    return count

def main():
    p=argparse.ArgumentParser(description='Obsolete Coin reference CPU miner (local node required)')
    p.add_argument('--address',required=True)
    p.add_argument('--cookie',type=Path,default=default_data_dir()/'obsolete-testnet-v2/.cookie')
    p.add_argument('--rpcport',type=int,default=19778)
    p.add_argument('--blocks',type=int,default=None)
    a=p.parse_args()
    if a.blocks is not None and a.blocks<1:p.error('--blocks must be positive')
    print('Mining TEST OBSC on this computer. Ctrl-C to stop. No guaranteed block time.',flush=True)
    try: mine(RPC(a.cookie,a.rpcport,timeout=120),a.address,max_blocks=a.blocks)
    except KeyboardInterrupt: print('\nMining stopped. A submitted batch may finish shortly.')
if __name__=='__main__':main()
