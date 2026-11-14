"""Run ONLY inside a private mount namespace on a dedicated tmpfs fixture."""
import argparse,errno,json,os,shutil,time
from pathlib import Path
from integration import Node,wait
from rpc import RPCError
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=a.root.resolve();assert str(root).startswith('/tmp/obsolete-disk-')
assert os.path.ismount(root),'Fixture must be its own filesystem'
assert shutil.disk_usage(root).total<=800*1024*1024,'Refuse any real/full-sized filesystem'
n=Node(a.binary.resolve(),root/'node');fill=root/'filler';saved=0
try:
 n.start();n.rpc.call('createwallet','fixture');w=n.rpc.for_wallet('fixture');addr=w.call('getnewaddress');n.rpc.call('generatetoaddress',2,addr,100000)
 n.stop();n.start();saved=n.rpc.call('getblockcount');assert saved==2
 with fill.open('wb') as f:
  chunk=bytes(1024*1024)
  try:
   while True:f.write(chunk)
  except OSError as e:
   assert e.errno==errno.ENOSPC
 try:n.rpc.call('generatetoaddress',1,addr,100000)
 except (OSError,RPCError):pass
 n.stop();fill.unlink();n.start()
 assert n.rpc.call('getblockcount')>=saved
 restored=n.rpc.call('generatetoaddress',1,addr,100000);assert len(restored)==1
 result={'result':'passed','fixture':'private tmpfs <=800 MiB','enospc':True,'persisted_height':saved,'recovered_height':n.rpc.call('getblockcount'),'limits':'Tests recovery after space restored; not physical disk corruption or power-loss durability'}
 a.output.write_text(json.dumps(result,indent=2));print(json.dumps(result))
finally:
 n.stop()
 if fill.exists():fill.unlink()
