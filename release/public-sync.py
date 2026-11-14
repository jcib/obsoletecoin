"""Fresh, wallet-disabled public testnet synchronization in a disposable directory."""
import argparse,json,os,re,subprocess,tempfile,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,required=True);p.add_argument('--peer',required=True);p.add_argument('--minimum-height',type=int,required=True);a=p.parse_args()
assert re.fullmatch(r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}:19777',a.peer)
assert a.minimum_height>0
binary=a.binary.resolve();cli=binary.with_name('bitcoin-cli')
with tempfile.TemporaryDirectory(prefix='obsolete-external-check-') as d:
 log=(Path(d)/'node.log').open('w');cmd=[str(binary),'-chain=obsolete-test','-datadir='+d,'-listen=0','-server=1','-rpcbind=127.0.0.1','-rpcallowip=127.0.0.1','-rpcport=39778','-disablewallet=1','-dnsseed=0','-fixedseeds=0','-discover=0','-connect='+a.peer,'-dbcache=128','-prune=1000','-printtoconsole=1']
 proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
 def rpc(*args):return subprocess.check_output([str(cli),'-chain=obsolete-test','-datadir='+d,'-rpcport=39778',*args],text=True,stderr=subprocess.DEVNULL,timeout=15).strip()
 try:
  deadline=time.monotonic()+600;last=None
  while time.monotonic()<deadline:
   if proc.poll() is not None:raise RuntimeError('Disposable node exited')
   try:
    info=json.loads(rpc('getblockchaininfo'));net=json.loads(rpc('getnetworkinfo'))
    assert info['chain']=='obsolete-test';assert rpc('getblockhash','0')=='9576894f8fffa098a9b1c04c3a3edb774d9dc7f58413e0906e781ecd8f0ede98'
    if info['blocks']!=last:print(json.dumps({'height':info['blocks'],'headers':info['headers'],'connections':net['connections']}),flush=True);last=info['blocks']
    if info['blocks']>=a.minimum_height and info['blocks']==info['headers'] and not info['initialblockdownload'] and net['connections']>0:
     result={'fresh_sync':True,'height':info['blocks'],'hash':info['bestblockhash'],'genesis_verified':True,'wallet_disabled':True,'external_peer':a.peer,'checked_at':int(time.time())};Path('public-sync-result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True);break
   except subprocess.CalledProcessError:pass
   time.sleep(3)
  else:raise RuntimeError('Public node did not synchronize before timeout')
 finally:
  try:rpc('stop');proc.wait(timeout=30)
  except Exception:proc.terminate();proc.wait(timeout=15)
  log.close()
