"""Linux desktop launcher: packaged testnet node, local wallet and CPU miner."""
import argparse, json, subprocess, sys, tempfile, time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from wallet import Wallet, verify_testnet
from rpc import RPC, RPCError, default_data_dir
from native_wallet import valid_peer, free_port, smoke_test

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--datadir',type=Path,default=default_data_dir())
    p.add_argument('--rpcport',type=int,default=19778)
    p.add_argument('--peer',action='append',default=[])
    p.add_argument('--self-test',type=Path,help='Write smoke-test result; always uses a disposable directory')
    a=p.parse_args()
    if not 1<=a.rpcport<=65535:p.error('Invalid RPC port')
    if a.self_test:a.rpcport=free_port()
    base=Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1]
    binary=base/'bitcoind'
    if not binary.is_file():raise SystemExit('Packaged bitcoind is missing')
    temporary=tempfile.TemporaryDirectory(prefix='obsolete-linux-test-') if a.self_test else None
    data=Path(temporary.name) if temporary else a.datadir.resolve()
    data.mkdir(parents=True,exist_ok=True)
    peers_file=data/'linux-testnet-peers.json'
    peers=json.loads(peers_file.read_text()) if peers_file.exists() and not temporary else []
    if not isinstance(peers,list) or len(peers)>32 or not all(isinstance(x,str) and valid_peer(x) for x in peers):
        raise ValueError('Invalid linux-testnet-peers.json')
    if not all(valid_peer(x) for x in a.peer):p.error('Use peer hostname:port or IPv4:port')
    peers=[] if temporary else list(dict.fromkeys(peers+a.peer))[:32]
    rpc=RPC(data/'obsolete-testnet-v2/.cookie',a.rpcport,timeout=5)
    proc=None;log=None
    try:
        try:verify_testnet(rpc)
        except (OSError,RuntimeError):
            log=(data/'linux-startup.log').open('a')
            cmd=[str(binary),'-chain=obsolete-test',f'-datadir={data}',f'-rpcport={a.rpcport}',
                 '-server=1','-rpcbind=127.0.0.1','-rpcallowip=127.0.0.1','-listen=0','-dnsseed=0','-fixedseeds=0',
                 '-discover=0','-dbcache=128','-maxconnections=16','-fallbackfee=0.00001000',
                 '-prune=0' if temporary else '-prune=1000','-printtoconsole=0']
            cmd += ['-addnode='+peer for peer in peers]
            proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            deadline=time.monotonic()+90
            while True:
                if proc.poll() is not None:raise RuntimeError('Node exited. See linux-startup.log in the data directory.')
                try:verify_testnet(rpc);break
                except (OSError,RPCError):
                    if time.monotonic()>deadline:raise RuntimeError('Node startup timed out')
                    time.sleep(.25)
        if 'obsolete' not in rpc.call('listwallets'):
            known=[w['name'] for w in rpc.call('listwalletdir')['wallets']]
            rpc.call('loadwallet' if 'obsolete' in known else 'createwallet','obsolete')
        wrpc=rpc.for_wallet('obsolete');root=tk.Tk();app=Wallet(root,wrpc)
        app.node_binary=binary;app.mining_library=base/'librandomx.so'
        def save_peer(peer):
            if peer not in peers:peers.append(peer)
            pending=peers_file.with_suffix('.tmp')
            pending.write_text(json.dumps(peers[-32:]))
            pending.replace(peers_file)
        app.peer_added=save_peer
        if a.self_test:
            result=smoke_test(app,root,rpc,binary,data)
            a.self_test.resolve().write_text(json.dumps(result,indent=2))
            app.closing=True
            root.destroy()
        else:root.mainloop()
    except Exception as error:
        if a.self_test:
            a.self_test.resolve().write_text(json.dumps({'native':False,'error':str(error)}))
            raise SystemExit(1)
        error_root=tk.Tk();error_root.withdraw();messagebox.showerror('Obsolete Coin',str(error),parent=error_root);error_root.destroy()
    finally:
        if proc and proc.poll() is None:
            try:rpc.call('stop');proc.wait(timeout=45)
            except (OSError,RuntimeError,subprocess.TimeoutExpired):pass
        if log:log.close()
        if temporary:temporary.cleanup()
if __name__=='__main__':main()
