"""Real two-node integration on disposable local Obsolete testnet data directories."""
import argparse, json, socket, subprocess, tempfile, time, sys, os
from pathlib import Path
from decimal import Decimal
from rpc import RPC, RPCError
from rx import RandomX
from mining import mine, MiningStats
from wallet_recovery import verify_backup
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'test/functional'))
from test_framework.messages import CBlock, from_hex

def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));return sock.getsockname()[1]
def wait(fn,timeout=90):
    end=time.monotonic()+timeout;last=None
    while time.monotonic()<end:
        try:
            value=fn()
            if value:return value
        except (OSError,RPCError) as e:last=e
        time.sleep(.2)
    raise AssertionError('Timed out: '+str(last))
class Node:
    def __init__(self,binary,data,peer=None):
        self.binary=binary;self.data=data;self.peer=peer;self.port=free_port();self.rpcport=free_port()
        self.rpc=RPC(data/'obsolete-testnet-v2/.cookie',self.rpcport,timeout=120);self.proc=None
    def start(self):
        self.data.mkdir(exist_ok=True)
        cmd=[str(self.binary),'-chain=obsolete-test',f'-datadir={self.data}',
             f'-port={self.port}',f'-rpcport={self.rpcport}','-rpcbind=127.0.0.1','-rpcallowip=127.0.0.1',
             '-bind=127.0.0.1','-listen=1','-dnsseed=0','-fixedseeds=0','-discover=0',
             '-server=1','-dbcache=64','-fallbackfee=0.00001000','-maxtipage=315360000','-printtoconsole=0']
        if self.peer:cmd+=['-connect=127.0.0.1:'+str(self.peer)]
        self.log=(self.data/'process.log').open('a')
        self.proc=subprocess.Popen(cmd,stdout=self.log,stderr=subprocess.STDOUT)
        def ready():
            if self.proc.poll() is not None:raise AssertionError((self.data/'process.log').read_text())
            return self.rpc.call('getblockchaininfo')['chain']=='obsolete-test'
        wait(ready)
    def stop(self):
        if self.proc and self.proc.poll() is None:
            try:self.rpc.call('stop')
            except (OSError,RPCError):pass
            try:self.proc.wait(timeout=30)
            except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait()
        if getattr(self,'log',None):self.log.close()

def run(binary,library):
    with tempfile.TemporaryDirectory(prefix='obsolete-integration-') as temp:
        base=Path(temp);a=Node(binary,base/'a');b=Node(binary,base/'b',a.port)
        guard_dir=base/'launch-guard';guard_dir.mkdir()
        for chain in ('obsolete','main'):
            rejected=subprocess.run([str(binary),'-chain='+chain,'-datadir='+str(guard_dir),'-listen=0'],capture_output=True,text=True,timeout=20)
            assert rejected.returncode!=0 and 'Mainnet is not released' in rejected.stderr, rejected.stderr
        try:
            a.start();b.start();wait(lambda:a.rpc.call('getconnectioncount')>0)
            for n in (a,b):n.rpc.call('createwallet','test')
            wa=a.rpc.for_wallet('test');wb=b.rpc.for_wallet('test')
            addr=wa.call('getnewaddress','','bech32');other=wb.call('getnewaddress','','bech32')
            assert addr.startswith('tobs1') and other.startswith('tobs1')
            # Actual RandomX mining crosses the initial-seed/genesis-seed boundary at 64.
            miner=subprocess.run([sys.executable,str(ROOT/'tools/mine.py'),'--address',addr,
                                  '--cookie',str(a.rpc.cookie),'--rpcport',str(a.rpcport),'--blocks','1','--library',str(library)],
                                 capture_output=True,text=True,timeout=120)
            assert miner.returncode==0 and 'Found block' in miner.stdout,miner.stderr
            a.rpc.call('generatetoaddress',61,addr,1000000)
            telemetry=MiningStats(2,50)
            assert mine(a.rpc,addr,max_blocks=3,threads=2,duty=50,library=library,stats=telemetry)==3
            assert telemetry.hashes>=3 and telemetry.snapshot()['average_hps']>0
            assert a.rpc.call('getblockcount')==65
            blocks=a.rpc.call('generatetoaddress',37,addr,1000000)
            assert len(blocks)==37 and a.rpc.call('getblockcount')==102
            wait(lambda:b.rpc.call('getbestblockhash')==blocks[-1])
            assert wa.call('getbalances')['mine']['trusted']>=5000
            # Exercise the real desktop's send flow against the running wallet.
            import tkinter as tk
            from unittest.mock import patch
            from wallet import Wallet
            desktop=tk.Tk();desktop.withdraw()
            app=Wallet(desktop,wa)
            def idle():
                desktop.update()
                return not app.busy
            wait(idle)
            assert app.snapshot is not None,app.status.get()
            try:
                with patch('wallet.simpledialog.askstring',side_effect=[other,'12.34000000']), \
                     patch('wallet.messagebox.askyesno',return_value=True), \
                     patch('wallet.messagebox.showinfo'):
                    app.send();wait(idle)
                    assert app.status.get().startswith('Transfer submitted: '),app.status.get()
                    txid=app.status.get().split(': ',1)[1]
            finally: desktop.destroy()
            wait(lambda:txid in b.rpc.call('getrawmempool'))
            assert mine(a.rpc,addr,max_blocks=1,threads=2,library=library)==1
            tip=a.rpc.call('getbestblockhash')
            wait(lambda:b.rpc.call('getbestblockhash')==tip)
            assert Decimal(str(wb.call('getbalances')['mine']['trusted']))==Decimal('12.34')
            try:wa.call('sendtoaddress',other,'1000000000','','',False,True,None,None,False,1)
            except RPCError as e:assert e.code==-6
            else:raise AssertionError('Insufficient balance accepted')
            # Re-submit the same spend: cannot credit the recipient twice.
            raw=wa.call('gettransaction',txid)['hex']
            try:a.rpc.call('sendrawtransaction',raw)
            except RPCError:pass
            assert Decimal(str(wb.call('getbalances')['mine']['trusted']))==Decimal('12.34')
            # A candidate extending the active tip must be connected, so its
            # subsidy is checked immediately (an equal-work side block can defer it).
            proposal=a.rpc.call('generateblock',addr,[],False)
            original=from_hex(CBlock(),proposal['hex'])
            seed=bytes.fromhex(a.rpc.call('getblockhash',0))[::-1]
            target=(original.nBits & 0x007fffff) << (8*((original.nBits>>24)-3))
            with RandomX(library,seed) as rx:
                bad=from_hex(CBlock(),original.serialize().hex())
                for nonce in range(10000):
                    bad.nNonce=nonce
                    if int.from_bytes(rx.hash(bad.serialize()[:80]),'little')>target:break
                result=a.rpc.call('submitblock',bad.serialize().hex())
                assert isinstance(result,str),('Invalid proof accepted',result)
                excess=from_hex(CBlock(),original.serialize().hex())
                excess.vtx[0].vout[0].nValue+=1
                excess.hashMerkleRoot=excess.calc_merkle_root()
                for nonce in range(100000):
                    excess.nNonce=nonce
                    if int.from_bytes(rx.hash(excess.serialize()[:80]),'little')<=target:break
                else:raise AssertionError('Could not mine overpay test block')
                result=a.rpc.call('submitblock',excess.serialize().hex())
                assert result=='bad-cb-amount',result
                # Solve each malformed header with valid work so contextual checks,
                # rather than an invalid proof, reject timestamps and difficulty.
                for kind,expected in [('past','time-too-old'),('future','time-too-new'),('difficulty','bad-randomx-pow')]:
                    candidate=from_hex(CBlock(),original.serialize().hex())
                    if kind=='past':candidate.nTime=a.rpc.call('getblockchaininfo')['mediantime']
                    elif kind=='future':candidate.nTime=int(time.time())+3*3600
                    else:candidate.nBits-=1
                    candidate_target=(candidate.nBits & 0x007fffff) << (8*((candidate.nBits>>24)-3))
                    for nonce in range(100000):
                        candidate.nNonce=nonce
                        if int.from_bytes(rx.hash(candidate.serialize()[:80]),'little')<=candidate_target:break
                    else:raise AssertionError('Could not solve malformed header fixture')
                    # RandomX contextual validation reports wrong nBits as bad-randomx-pow.
                    rejection=a.rpc.call('submitblock',candidate.serialize().hex())
                    assert rejection==expected,(kind,rejection)
            # Real competing branches: disconnect, mine a longer competing fork, reconnect.
            b.rpc.call('setnetworkactive',False)
            wait(lambda:a.rpc.call('getconnectioncount')==0)
            a.rpc.call('generatetoaddress',1,addr,100000)
            fork=b.rpc.call('generatetoaddress',3,other,100000)
            b.rpc.call('setnetworkactive',True)
            wait(lambda:a.rpc.call('getbestblockhash')==fork[-1])
            balance=wb.call('getbalances');tip=b.rpc.call('getbestblockhash')
            b.stop();b.start();b.rpc.call('loadwallet','test') if 'test' not in b.rpc.call('listwallets') else None
            assert b.rpc.call('getbestblockhash')==tip
            assert wb.call('getbalances')==balance
            # Protect, back up and actually restore a disposable descriptor wallet.
            phrase='obsolete-integration-only-not-a-real-secret'
            wb.call('encryptwallet',phrase)
            try:wb.call('walletpassphrase','wrong-test-passphrase',60)
            except RPCError as e:assert e.code==-14
            else:raise AssertionError('Wrong wallet passphrase accepted')
            wb.call('walletpassphrase',phrase,60)
            backup=base/'disposable-wallet-backup.dat'
            wb.call('backupwallet',str(backup))
            wb.call('walletlock')
            assert backup.is_file() and backup.stat().st_size>0
            check=verify_backup(wb,backup,binary,phrase)
            assert check['matched'] and check['encrypted'] and not check['balances_rescanned']
            try:verify_backup(wb,backup,binary,'wrong-test-passphrase')
            except RPCError as error:assert error.code==-14
            else:raise AssertionError('Recovery accepted a wrong passphrase')
            try:verify_backup(wa,backup,binary,phrase)
            except ValueError as error:assert 'does not match' in str(error)
            else:raise AssertionError('Recovery accepted another wallet backup')
            b.rpc.call('restorewallet','recovered',str(backup))
            recovered=b.rpc.for_wallet('recovered')
            assert recovered.call('getbalances')==balance
            assert recovered.call('getwalletinfo')['unlocked_until']==0
            # Run the packaged laptop entry point against a real home-style peer.
            laptop=subprocess.run([sys.executable,str(ROOT/'tools/laptop.py'),
                '--server','127.0.0.1:'+str(b.port),'--datadir',str(base/'laptop'),
                '--port',str(free_port()),'--rpcport',str(free_port()),
                '--binary',str(binary),'--blocks','1','--library',str(library)],capture_output=True,text=True,timeout=180)
            assert laptop.returncode==0 and 'Found block' in laptop.stdout,(laptop.stdout,laptop.stderr)
            print(json.dumps({'result':'passed','height':b.rpc.call('getblockcount'),
                'checks':['CLI RandomX mining','measured two-thread mining','external miner seed boundary 64','external miner includes witness spend','offline backup verification and wrong-password/wrong-wallet rejection','laptop launcher mining against peer','seed boundary 64','two-node synchronization',
                          'coinbase maturity','desktop signed transfer','insufficient funds','no duplicate credit',
                          'invalid proof rejected','overpaying coinbase rejected','past/future timestamps and wrong difficulty rejected','chainwork reorganization',
                          'restart and wallet persistence','encryption and wrong-passphrase rejection','wallet backup and restore']}))
        except Exception:
            for n in (a,b):
                f=n.data/'obsolete-testnet-v2/debug.log'
                if f.exists():print('\n'.join(f.read_text(errors='replace').splitlines()[-35:]))
            raise
        finally:b.stop();a.stop()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--bindir',type=Path,required=True);p.add_argument('--library',type=Path,required=True);args=p.parse_args()
    run((args.bindir/('bitcoind.exe' if os.name=='nt' else 'bitcoind')).resolve(),args.library.resolve())
