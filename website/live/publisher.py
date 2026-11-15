"""Publish a bounded, allowlisted public chain view; never calls wallet RPCs."""
import argparse, datetime, hashlib, hmac, ipaddress, json, os, sys, time, urllib.request
from decimal import Decimal
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from rpc import RPC
GENESIS='9576894f8fffa098a9b1c04c3a3edb774d9dc7f58413e0906e781ecd8f0ede98'
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*a,**k): return None
OPENER=urllib.request.build_opener(NoRedirect)
def encode(v): return json.dumps(v,separators=(',',':'),ensure_ascii=True).encode()
def public_block(b):
    txs=[]
    for t in b['tx']:
        ins=[{'coinbase':True} if 'coinbase' in v else {'txid':v['txid'],'vout':v['vout']} for v in t['vin']]
        outs=[{'n':v['n'],'atoms':str(int(Decimal(str(v['value']))*100000000)), 'address':v['scriptPubKey'].get('address',''), 'type':v['scriptPubKey']['type']} for v in t['vout']]
        txs.append({'txid':t['txid'],'vin':ins,'vout':outs})
    return {'height':b['height'],'hash':b['hash'],'previous':b.get('previousblockhash','0'*64),'time':b['time'],'bits':b['bits'],'size':b['size'],'tx':txs}
def collect(rpc,cache,peer):
    info=rpc.call('getblockchaininfo')
    if info['chain']!='obsolete-test' or rpc.call('getblockhash',0)!=GENESIS: raise ValueError('wrong-network')
    if info['initialblockdownload'] or info['headers']!=info['blocks']: raise ValueError('sync-incomplete')
    tip=info['blocks'];first=max(0,tip-1023);blocks=[]
    if cache and cache[-1]['hash']==info['bestblockhash']:
        blocks=cache
    else:
        old={b['hash']:b for b in cache}
        for height in range(first,tip+1):
            bh=rpc.call('getblockhash',height)
            b=old.get(bh) or public_block(rpc.call('getblock',bh,2))
            if b['height']!=height or (blocks and b['previous']!=blocks[-1]['hash']): raise ValueError('reorg-during-export')
            blocks.append(b)
    end=rpc.call('getblockchaininfo')
    if end['bestblockhash']!=info['bestblockhash'] or end['blocks']!=tip: raise ValueError('tip-changed-during-export')
    net=rpc.call('getnetworkinfo');pool=rpc.call('getmempoolinfo')
    result={'network':'obsolete-test','genesis':GENESIS,'observed':int(time.time()*1000),'height':tip,'tip':info['bestblockhash'],'first':blocks[0]['height'],'blocks':blocks,'connections':net['connections'],'mempool':pool['size'],'peer':peer}
    while len(encode(result))>1400000 and len(blocks)>1:
        blocks=blocks[len(blocks)//4 or 1:];result['blocks']=blocks;result['first']=blocks[0]['height']
    if len(encode(result))>1400000: raise ValueError('single-block-too-large-for-explorer')
    return result

def publish(origin,key,record):
    body=encode(record);stamp=str(int(time.time()));path='/api/feed'
    signature=hmac.new(key.encode(),stamp.encode()+b'\n'+path.encode()+b'\n'+body,hashlib.sha256).hexdigest()
    headers={'User-Agent':'ObsoleteCoin-Explorer/0.3 (+https://obsoletecoin.pages.dev)','Content-Type':'application/json','X-Obsolete-Time':stamp,'X-Obsolete-Signature':signature}
    req=urllib.request.Request(origin+path,data=body,headers=headers,method='POST')
    with OPENER.open(req,timeout=12) as response:
        if response.status!=200: raise RuntimeError('publish-rejected')

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);a=p.parse_args();c=json.loads(a.config.read_text(encoding='utf-8-sig'))
    if c['origin']!='https://obsoletecoin.pages.dev':raise ValueError('unexpected-origin')
    rpc=RPC(Path('/var/lib/obsoletecoin/obsolete-testnet-v2/.cookie'),19778,timeout=10)
    cache=[];peer='';ip_at=0
    while True:
        started=time.monotonic()
        try:
            if time.time()-ip_at>300:
                with OPENER.open('https://api.ipify.org',timeout=5) as r:address=r.read(64).decode().strip()
                if not ipaddress.IPv4Address(address).is_global:raise ValueError('non-public-address')
                peer=address+':19777';ip_at=time.time()
            record=collect(rpc,cache,peer);publish(c['origin'],c['key'],record);cache=record['blocks']
            print(json.dumps({'published_at':record['observed'],'height':record['height'],'first':record['first']}),flush=True)
        except Exception as e:
            # Do not log URLs, request headers, cookie values or arbitrary exception text.
            print(json.dumps({'status':'unavailable','error_type':type(e).__name__}),flush=True)
        time.sleep(max(1,15-(time.monotonic()-started)))
if __name__=='__main__':main()
