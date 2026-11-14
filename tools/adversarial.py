"""Bounded adversarial exercises against disposable loopback nodes only."""
import argparse,http.client,json,socket,struct,tempfile,time
from pathlib import Path
from integration import Node,wait
from rpc import RPCError
p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
checks=[]
with tempfile.TemporaryDirectory(prefix='obsolete-adversarial-') as tmp:
    base=Path(tmp);n=Node(a.binary.resolve(),base/'a');b=Node(a.binary.resolve(),base/'b',n.port);c=None
    try:
        n.start();b.start();wait(lambda:n.rpc.call('getconnectioncount')>0)
        n.rpc.call('createwallet','funded');w=n.rpc.for_wallet('funded');addr=w.call('getnewaddress');n.rpc.call('generatetoaddress',102,addr,1000000)
        wait(lambda:n.rpc.call('getbestblockhash')==b.rpc.call('getbestblockhash'))
        backup=base/'test-wallet.dat';w.call('backupwallet',str(backup));b.rpc.call('restorewallet','copy',str(backup));wb=b.rpc.for_wallet('copy')
        # One UTXO, two valid competing spends on disconnected branches.
        utxo=w.call('listunspent',1)[0];value=utxo['amount'];destination=w.call('getnewaddress');wb.call('getnewaddress');other=wb.call('getnewaddress')
        def spend(wallet,to):
            raw=wallet.call('createrawtransaction',[{'txid':utxo['txid'],'vout':utxo['vout']}],{to:str(value-__import__('decimal').Decimal('0.001'))})
            signed=wallet.call('signrawtransactionwithwallet',raw);assert signed['complete'];return signed['hex']
        first=spend(w,destination);second=spend(wb,other)
        b.rpc.call('setnetworkactive',False);wait(lambda:n.rpc.call('getconnectioncount')==0)
        tx1=n.rpc.call('sendrawtransaction',first);tx2=b.rpc.call('sendrawtransaction',second);assert tx1!=tx2
        n.rpc.call('generatetoaddress',1,addr,1000000);fork=b.rpc.call('generatetoaddress',3,other,1000000)
        b.rpc.call('setnetworkactive',True);wait(lambda:n.rpc.call('getbestblockhash')==fork[-1])
        assert w.call('gettransaction',tx1)['confirmations']<0
        assert wb.call('gettransaction',tx2)['confirmations']>0
        checks.append('Conflicting spend loses confirmations after greater-work reorganization')
        conn=http.client.HTTPConnection('127.0.0.1',n.rpcport,timeout=5);conn.request('POST','/',json.dumps({'method':'getblockcount','params':[]}));assert conn.getresponse().status==401;conn.close();checks.append('Unauthenticated RPC rejected')
        # Bounded malformed-header traffic, not a stress/capacity certification.
        for i in range(16):
            with socket.create_connection(('127.0.0.1',n.port),timeout=5) as sock:
                sock.sendall(bytes.fromhex('4f425432')+b'version'+bytes(5)+struct.pack('<I',0xffffffff)+bytes(4))
        assert n.rpc.call('getbestblockhash')==fork[-1];checks.append('16 oversized P2P message headers do not crash node')
        height=n.rpc.call('getblockcount');n.proc.kill();n.proc.wait();n.log.close();n.start()
        restart_height=n.rpc.call('getblockcount')
        n.rpc.call('addnode','127.0.0.1:'+str(b.port),'onetry')
        wait(lambda:n.rpc.call('getbestblockhash')==fork[-1],timeout=120)
        checks.append('Abrupt process termination recovers and resynchronizes with peer')
        c=Node(a.binary.resolve(),base/'fresh',n.port);c.start();wait(lambda:c.rpc.call('getbestblockhash')==n.rpc.call('getbestblockhash'),timeout=120)
        checks.append('Fresh node syncs from genesis after recovery')
        result={'result':'passed','checks':checks,'height':height,'immediate_restart_height':restart_height,'limits':['Loopback only, 16 malformed messages; not public-network DoS capacity testing','No sustained independent-miner campaign','No real ENOSPC/full-disk injection in this test']}
        a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2));print(json.dumps(result))
    finally:
        if c:c.stop()
        b.stop();n.stop()
