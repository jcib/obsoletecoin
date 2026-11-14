"""Start a local testnet node, connect to the home node and mine into a local wallet."""
import argparse,json,subprocess,sys,time
from pathlib import Path
from rpc import RPC,RPCError,default_data_dir
from mine import mine

def main():
    p=argparse.ArgumentParser(description='Obsolete Coin laptop test miner')
    p.add_argument('--server',required=True,help='Home node IPv4 address:port')
    p.add_argument('--datadir',type=Path,default=default_data_dir())
    p.add_argument('--rpcport',type=int,default=19778)
    p.add_argument('--port',type=int,default=19777)
    p.add_argument('--binary',type=Path)
    p.add_argument('--blocks',type=int)
    a=p.parse_args()
    import ipaddress
    try:
        host,port=a.server.rsplit(':',1);ipaddress.IPv4Address(host)
        assert 1<=int(port)<=65535
    except (ValueError,AssertionError):p.error('Use an IPv4 address and port, for example 192.0.2.36:19777')
    if a.blocks is not None and a.blocks<1:p.error('--blocks must be positive')
    root=Path(__file__).resolve().parents[1]
    binary=a.binary or (root/'bitcoind' if (root/'bitcoind').is_file() else root/'build/bin/bitcoind')
    if not binary.is_file():p.error('Extract the complete experimental Linux package first')
    a.datadir.mkdir(parents=True,exist_ok=True)
    rpc=RPC(a.datadir/'obsolete-testnet-v2/.cookie',a.rpcport,timeout=120)
    proc=None;log=None
    try:
        try:rpc.call('getblockchaininfo')
        except (OSError,RPCError):
            log=(a.datadir/'laptop-node.log').open('a')
            proc=subprocess.Popen([str(binary.resolve()),'-chain=obsolete-test',f'-datadir={a.datadir.resolve()}',
                f'-connect={a.server}',f'-port={a.port}',f'-rpcport={a.rpcport}',
                '-listen=0','-dnsseed=0','-fixedseeds=0','-discover=0','-server=1',
                '-rpcbind=127.0.0.1','-rpcallowip=127.0.0.1','-dbcache=128','-prune=1000',
                '-maxtipage=315360000','-fallbackfee=0.00001000','-printtoconsole=0'],stdout=log,stderr=subprocess.STDOUT)
        print('Starting local node and connecting to '+a.server+' ...',flush=True)
        deadline=time.monotonic()+120
        genesis=json.loads((root/'docs/genesis.json').read_text(encoding='utf-8'))['TEST']['hash']
        while True:
            if proc and proc.poll() is not None:raise RuntimeError('Node exited. See '+str(a.datadir/'laptop-node.log'))
            try:
                info=rpc.call('getblockchaininfo')
                if info['chain']!='obsolete-test' or rpc.call('getblockhash',0)!=genesis:raise RuntimeError('Wrong network or old genesis; refusing to mine')
                peers=rpc.call('getpeerinfo')
                if any(x.get('addr')==a.server for x in peers) and info['headers']==info['blocks'] and not info['initialblockdownload']:break
            except (OSError,RPCError):pass
            if time.monotonic()>deadline:raise RuntimeError('Home node not ready/reachable; mining has not started')
            time.sleep(.5)
        wallet='obsolete'
        if wallet not in rpc.call('listwallets'):
            known=[x['name'] for x in rpc.call('listwalletdir')['wallets']]
            rpc.call('loadwallet' if wallet in known else 'createwallet',wallet)
        wrpc=rpc.for_wallet(wallet);address=wrpc.call('getnewaddress','laptop mining','bech32')
        print('Mining TEST OBSC into your LOCAL wallet: '+address,flush=True)
        print('One CPU thread. Rewards mature after 100 blocks. Ctrl-C stops mining.',flush=True)
        mine(rpc,address,max_blocks=a.blocks)
        print('Mining session complete.',flush=True)
    except KeyboardInterrupt:print('\nStopping mining and local node...',flush=True)
    finally:
        if proc and proc.poll() is None:
            try:rpc.call('stop')
            except (OSError,RPCError):pass
            try:proc.wait(timeout=45)
            except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=15)
        if log:log.close()
if __name__=='__main__':main()
