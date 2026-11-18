"""Explicit node launcher; no installation, mining or service changes implicit."""
import argparse, os, subprocess
from pathlib import Path
from coin_network import MAINNET, TESTNET
from rpc import default_data_dir

def main():
    p=argparse.ArgumentParser(description='Obsolete Coin full node')
    base=Path(__file__).resolve().parents[1]
    binary=base/'build/bin/bitcoind'
    if not binary.exists(): binary=base/'bitcoind'
    p.add_argument('--binary',default=str(binary))
    p.add_argument('--chain',choices=['obsolete','obsolete-test'],default='obsolete')
    p.add_argument('--datadir',type=Path)
    p.add_argument('--peer',action='append',default=[])
    p.add_argument('--port',type=int,default=19777)
    p.add_argument('--rpcport',type=int)
    p.add_argument('--listen',action='store_true',help='Accept P2P connections; RPC remains loopback only')
    a=p.parse_args()
    network = MAINNET if a.chain == MAINNET.chain else TESTNET
    if a.datadir is None: a.datadir = Path.home()/'.obsoletecoin-mainnet' if network == MAINNET else default_data_dir()
    if a.rpcport is None: a.rpcport = network.rpc
    if not Path(a.binary).is_file():p.error('Node binary missing. Build using docs/BUILD.md, or set --binary to the extracted bitcoind executable.')
    a.datadir.mkdir(parents=True,exist_ok=True)
    cmd=[str(Path(a.binary).resolve()),f'-chain={network.chain}',f'-datadir={a.datadir.resolve()}',
         '-server=1','-rpcbind=127.0.0.1','-rpcallowip=127.0.0.1',
         f'-port={a.port}',f'-rpcport={a.rpcport}',f'-listen={int(a.listen)}',
         '-dnsseed=0','-fixedseeds=0','-dbcache=128','-maxconnections=16',
         '-fallbackfee=0.00001000','-prune=1000','-printtoconsole=1']
    cmd += ['-addnode='+x for x in a.peer]
    try: return subprocess.call(cmd)
    except KeyboardInterrupt: return 130
if __name__=='__main__': raise SystemExit(main())
