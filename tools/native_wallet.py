"""Native desktop entry point. Starts only the packaged TESTNET node, with loopback RPC."""
import argparse, json, os, socket, subprocess, sys, tempfile, threading, time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from wallet import Wallet
from rpc import RPC, RPCError, default_data_dir
GENESIS='9576894f8fffa098a9b1c04c3a3edb774d9dc7f58413e0906e781ecd8f0ede98'

def valid_peer(value):
    import re
    return bool(re.fullmatch(r'[A-Za-z0-9.-]+:[0-9]{1,5}',value)) and 1<=int(value.rsplit(':',1)[1])<=65535

def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        return sock.getsockname()[1]

def smoke_test(app, root, rpc, binary, data):
    """Exercise the packaged GUI/miner/recovery only on disposable local nodes."""
    from wallet_recovery import verify_backup
    def wait(predicate, timeout=90):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            root.update()
            try:
                if predicate():return
            except (OSError,RPCError):pass
            time.sleep(.05)
        raise RuntimeError('Native self-test timed out: '+app.status.get())
    wait(lambda:not app.busy)
    assert app.snapshot is not None,app.status.get()
    wrpc=rpc.for_wallet('obsolete')
    address=wrpc.call('getnewaddress')
    assert len(RPC(rpc.cookie,rpc.port,timeout=120).call('generatetoaddress',2,address,100000))==2
    peer_data=data/'self-test-peer';peer_data.mkdir()
    peer_port,peer_rpcport=free_port(),free_port()
    peer_rpc=RPC(peer_data/'obsolete-testnet-v2/.cookie',peer_rpcport,timeout=5)
    with (peer_data/'startup.log').open('w') as log:
        peer=subprocess.Popen([str(binary),'-chain=obsolete-test',f'-datadir={peer_data}',
            f'-port={peer_port}',f'-rpcport={peer_rpcport}','-bind=127.0.0.1',
            '-rpcbind=127.0.0.1','-rpcallowip=127.0.0.1','-server=1','-listen=1',
            '-connect=0','-dnsseed=0','-fixedseeds=0','-discover=0','-dbcache=32',
            '-printtoconsole=0'],stdout=log,stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        try:
            wait(lambda:peer_rpc.call('getblockhash',0)==GENESIS)
            rpc.call('addnode',f'127.0.0.1:{peer_port}','onetry')
            wait(lambda:peer_rpc.call('getblockcount')==2 and rpc.call('getconnectioncount')>0)
            wait(lambda:not app.busy)
            app.threads.set(2 if (os.cpu_count() or 1)>1 else 1);app.activity.set(50)
            confirm=messagebox.askyesno
            try:
                messagebox.askyesno=lambda *args,**kwargs:True
                app.toggle_mine()
            finally:messagebox.askyesno=confirm
            wait(lambda:app.mining_stats is not None and app.mining_stats.snapshot()['blocks']>=2)
            app.toggle_mine()
            wait(lambda:not app.miner.is_alive())
            stats=app.mining_stats.snapshot()
            assert stats['hashes']>=stats['blocks']>=2 and stats['average_hps']>0,stats
            wait(lambda:peer_rpc.call('getbestblockhash')==rpc.call('getbestblockhash'))
            passphrase='Disposable self-test passphrase'
            wrpc.call('encryptwallet',passphrase)
            backup=data/'self-test-backup.dat';wrpc.call('backupwallet',str(backup))
            recovery=verify_backup(wrpc,backup,binary,passphrase)
            assert recovery['matched'] and recovery['encrypted'],recovery
            return {'native':True,'chain':'obsolete-test','ui':True,'mainnet_enabled':False,
                    'bootstrap_blocks':2,'mining':stats,'recovery':recovery}
        finally:
            app.mining.set()
            if app.miner:app.miner.join(timeout=45)
            if peer.poll() is None:
                try:peer_rpc.call('stop')
                except (OSError,RPCError):pass
                try:peer.wait(timeout=30)
                except subprocess.TimeoutExpired:peer.kill();peer.wait()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--datadir',type=Path,default=default_data_dir())
    p.add_argument('--rpcport',type=int,default=29778)
    p.add_argument('--peer',action='append',default=[])
    p.add_argument('--self-test',type=Path,help='Write smoke-test result; always uses a disposable directory')
    a=p.parse_args()
    if not 1<=a.rpcport<=65535:p.error('Invalid RPC port')
    if a.self_test:a.rpcport=free_port()
    base=Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1]
    binary=base/'bitcoind.exe'
    if not binary.is_file():raise SystemExit('Packaged bitcoind.exe is missing')
    temporary=tempfile.TemporaryDirectory(prefix='obsolete-native-test-') if a.self_test else None
    data=Path(temporary.name) if temporary else a.datadir.resolve()
    data.mkdir(parents=True,exist_ok=True)
    peers_file=data/'native-testnet-peers.json'
    peers=json.loads(peers_file.read_text()) if peers_file.exists() and not temporary else []
    if not isinstance(peers,list) or len(peers)>32 or not all(isinstance(x,str) and valid_peer(x) for x in peers):
        raise ValueError('Invalid native-testnet-peers.json')
    if not all(valid_peer(x) for x in a.peer):p.error('Use peer hostname:port or IPv4:port')
    peers=[] if temporary else list(dict.fromkeys(peers+a.peer))[:32]
    rpc=RPC(data/'obsolete-testnet-v2/.cookie',a.rpcport,timeout=5)
    proc=None;log=None
    def verify():
        assert rpc.call('getblockchaininfo')['chain']=='obsolete-test','Wrong network'
        assert rpc.call('getblockhash',0)==GENESIS,'Wrong genesis'
    try:
        try:verify()
        except (OSError,RuntimeError):
            log=(data/'native-startup.log').open('a')
            cmd=[str(binary),'-chain=obsolete-test',f'-datadir={data}',f'-rpcport={a.rpcport}',
                 '-server=1','-rpcbind=127.0.0.1','-rpcallowip=127.0.0.1','-listen=0','-dnsseed=0','-fixedseeds=0',
                 '-discover=0','-dbcache=128','-maxconnections=16','-fallbackfee=0.00001000',
                 '-prune=0' if temporary else '-prune=1000','-printtoconsole=0']
            cmd += ['-addnode='+peer for peer in peers]
            proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            deadline=time.monotonic()+90
            while True:
                if proc.poll() is not None:raise RuntimeError('Node exited. See native-startup.log in the data directory.')
                try:verify();break
                except (OSError,RPCError):
                    if time.monotonic()>deadline:raise RuntimeError('Node startup timed out')
                    time.sleep(.25)
        if 'obsolete' not in rpc.call('listwallets'):
            known=[w['name'] for w in rpc.call('listwalletdir')['wallets']]
            rpc.call('loadwallet' if 'obsolete' in known else 'createwallet','obsolete')
        wrpc=rpc.for_wallet('obsolete');root=tk.Tk();app=Wallet(root,wrpc)
        app.node_binary=binary;app.mining_library=base/'librandomx.dll'
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
