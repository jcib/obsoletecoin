"""Command-line entry point for measured local RandomX mining."""
import argparse
from pathlib import Path
from rpc import RPC, RPCError, default_data_dir
from mining import mine, MiningStats
from coin_network import MAINNET, TESTNET

def main():
    p=argparse.ArgumentParser(description='Obsolete Coin reference CPU miner (local node required)')
    p.add_argument('--address',required=True)
    p.add_argument('--chain',choices=['obsolete','obsolete-test'],default='obsolete')
    p.add_argument('--cookie',type=Path)
    p.add_argument('--rpcport',type=int)
    p.add_argument('--blocks',type=int,default=None)
    p.add_argument('--threads',type=int,default=1)
    p.add_argument('--activity',type=int,default=100,help='Approximate active time per thread, 1..100 percent')
    p.add_argument('--library',type=Path)
    a=p.parse_args()
    network = MAINNET if a.chain == MAINNET.chain else TESTNET
    data = Path.home()/'.obsoletecoin-mainnet' if network == MAINNET else default_data_dir()
    if a.cookie is None: a.cookie = data/network.directory/'.cookie'
    if a.rpcport is None: a.rpcport = network.rpc
    if a.blocks is not None and a.blocks<1:p.error('--blocks must be positive')
    print(f'Mining {network.label} OBSC on this computer. Ctrl-C to stop. No guaranteed block time.',flush=True)
    stats=MiningStats(a.threads,a.activity)
    try: mine(RPC(a.cookie,a.rpcport,timeout=30),a.address,max_blocks=a.blocks,threads=a.threads,duty=a.activity,library=a.library,stats=stats,network=network)
    except KeyboardInterrupt: print('\nMining stopped. A submitted batch may finish shortly.')
    finally:
        s=stats.snapshot()
        print(f"{s['hashes']} hashes | {s['average_hps']:.2f} H/s average | {s['blocks']} accepted blocks")
if __name__=='__main__':main()
