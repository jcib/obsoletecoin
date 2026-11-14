import sys,tempfile,subprocess,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
from integration import Node,wait
with tempfile.TemporaryDirectory(prefix='obsolete-health-') as tmp:
 a=Node(Path('.local/native-node/bitcoind.exe').resolve(),Path(tmp)/'a');b=Node(a.binary,Path(tmp)/'b',a.port)
 try:
  a.start();b.start();a.rpc.call('createwallet','health');address=a.rpc.for_wallet('health').call('getnewaddress');a.rpc.call('generatetoaddress',2,address,100000)
  wait(lambda:a.rpc.call('getconnectioncount')>0)
  def check():
   r=subprocess.run([sys.executable,'tools/health.py','--datadir',str(a.data),'--rpcport',str(a.rpcport)],capture_output=True,text=True,check=False)
   return r.returncode,json.loads(r.stdout)
  code,result=check();assert code==0 and result['status']=='ok',result
  a.rpc.call('setnetworkactive',False);wait(lambda:a.rpc.call('getconnectioncount')==0)
  code,result=check();assert code==1 and 'no-peers' in result['issues'],result
 finally:b.stop();a.stop()
out={'result':'passed','checks':['connected synced node reports ok','loss of peers reports degraded and nonzero exit'],'scope':'read-only local RPC on disposable nodes'}
Path('.local/readiness/health.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
