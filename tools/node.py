"""Explicit testnet launcher; no installation, mining or service changes implicit."""
import argparse, os, subprocess
from pathlib import Path
from rpc import default_data_dir

def main():
    p=argparse.ArgumentParser(description='Obsolete Coin experimental testnet node')
    base=Path(__file__).resolve().parents[1]
    binary=base/'build/bin/bitcoind'
    if not binary.exists(): binary=base/'bitcoind'
    p.add_argument('--binary',default=str(binary))
    p.add_argument('--datadir',type=Path,default=default_data_dir())
    p.add_argument('--peer',action='append',default=[])
    p.add_argument('--port',type=int,default=19777)
    p.add_argument('--rpcport',type=int,default=19778)
    p.add_argument('--listen',action='store_true',help='Accept P2P connections; RPC remains loopback only')
    a=p.parse_args()
    if not Path(a.binary).is_file():p.error('Node binary missing. Build using docs/BUILD.md, or set --binary to the extracted bitcoind executable.')
    a.datadir.mkdir(parents=True,exist_ok=True)
    cmd=[str(Path(a.binary).resolve()),'-chain=obsolete-test',f'-datadir={a.datadir.resolve()}',
         '-server=1','-rpcbind=127.0.0.1','-rpcallowip=127.0.0.1',
         f'-port={a.port}',f'-rpcport={a.rpcport}',f'-listen={int(a.listen)}',
         '-dnsseed=0','-fixedseeds=0','-dbcache=128','-maxconnections=16',
         '-fallbackfee=0.00001000','-prune=1000','-printtoconsole=1']
    cmd += ['-addnode='+x for x in a.peer]
    try: return subprocess.call(cmd)
    except KeyboardInterrupt: return 130
if __name__=='__main__': raise SystemExit(main())
