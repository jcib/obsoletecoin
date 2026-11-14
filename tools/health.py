"""Read-only local testnet health snapshot; emits no wallet or peer identities."""
import argparse,json,shutil,time
from pathlib import Path
from rpc import RPC,default_data_dir
p=argparse.ArgumentParser()
p.add_argument('--datadir',type=Path,default=default_data_dir())
p.add_argument('--rpcport',type=int,default=19778)
p.add_argument('--max-tip-age',type=int,default=14400)
p.add_argument('--min-free-mib',type=int,default=1024)
a=p.parse_args()
try:
 rpc=RPC(a.datadir/'obsolete-testnet-v2/.cookie',a.rpcport,timeout=10)
 chain=rpc.call('getblockchaininfo');net=rpc.call('getnetworkinfo')
 free=shutil.disk_usage(a.datadir).free//(1024*1024)
 age=max(0,int(time.time())-chain['time']);issues=[]
 if chain['chain']!='obsolete-test':issues.append('wrong-network')
 if chain['initialblockdownload'] or chain['headers']!=chain['blocks']:issues.append('sync-incomplete')
 if net['connections']==0:issues.append('no-peers')
 if age>a.max_tip_age:issues.append('old-tip-check-miners')
 if free<a.min_free_mib:issues.append('low-disk')
 result={'checked_at':int(time.time()),'network':chain['chain'],'height':chain['blocks'],'headers':chain['headers'],'tip':chain['bestblockhash'],'tip_age_seconds':age,'connections':net['connections'],'free_mib':free,'issues':issues,'status':'degraded' if issues else 'ok'}
except Exception:
 result={'checked_at':int(time.time()),'status':'unavailable','issues':['local-rpc-or-disk-check-failed']}
print(json.dumps(result))
raise SystemExit(0 if result['status']=='ok' else 1)
