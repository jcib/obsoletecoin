"""Export PUBLIC block data from the local testnet node; never reads wallet RPCs."""
import argparse,datetime,json,sys
from decimal import Decimal
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from rpc import RPC,default_data_dir
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
rpc=RPC(default_data_dir()/'obsolete-testnet-v2/.cookie',timeout=60)
info=rpc.call('getblockchaininfo')
assert info['chain']=='obsolete-test'
genesis=rpc.call('getblockhash',0)
assert genesis=='9576894f8fffa098a9b1c04c3a3edb774d9dc7f58413e0906e781ecd8f0ede98'
tip=info['blocks'];first=max(0,tip-1023);blocks=[]
for height in range(first,tip+1):
    block=rpc.call('getblock',rpc.call('getblockhash',height),2)
    assert block['height']==height
    if blocks:assert block['previousblockhash']==blocks[-1]['hash'],'Reorganization during export; retry'
    blocks.append(block)
    if height%100==0:print('Exported public block',height,flush=True)
assert rpc.call('getblockhash',tip)==blocks[-1]['hash'],'Reorganization during export; retry'
record={'network':'obsolete-test','version':'0.2','captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'genesis':genesis,'height':tip,'first_height':first,'bestblockhash':blocks[-1]['hash'],'blocks':blocks}
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(record,default=lambda x:format(x,'f') if isinstance(x,Decimal) else str(x)),encoding='utf-8')
print(json.dumps({'captured_height':tip,'blocks_exported':len(blocks),'output':str(a.output)}))
