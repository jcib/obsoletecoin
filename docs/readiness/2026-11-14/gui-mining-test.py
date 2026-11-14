import sys,tempfile,time,json,tkinter as tk
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path('tools').resolve()))
from integration import Node,wait
from wallet import Wallet
with tempfile.TemporaryDirectory(prefix='obsolete-gui-mining-') as tmp:
 a=Node(Path('.local/native-node/bitcoind.exe').resolve(),Path(tmp)/'a');b=Node(a.binary,Path(tmp)/'b',a.port);root=None
 try:
  a.start();b.start();a.rpc.call('createwallet','miner');w=a.rpc.for_wallet('miner');a.rpc.call('generatetoaddress',2,w.call('getnewaddress'),100000)
  wait(lambda:a.rpc.call('getconnectioncount')>0)
  root=tk.Tk();root.withdraw();app=Wallet(root,w)
  def ready():root.update();return not app.busy
  wait(ready)
  initial=a.rpc.call('getblockcount')
  with patch('wallet.messagebox.askyesno',return_value=True):app.toggle_mine()
  wait(lambda:a.rpc.call('getblockcount')>initial)
  app.toggle_mine();app.miner.join(timeout=30);assert not app.miner.is_alive()
  a.rpc.call('setnetworkactive',False);wait(lambda:a.rpc.call('getconnectioncount')==0)
  before=a.rpc.call('getblockcount')
  with patch('wallet.messagebox.askyesno',return_value=True):app.toggle_mine()
  app.miner.join(timeout=10);assert not app.miner.is_alive()
  assert a.rpc.call('getblockcount')==before
 finally:
  if root:root.destroy()
  b.stop();a.stop()
result={'result':'passed','checks':['GUI starts real native CPU mining','GUI stop joins mining worker','GUI refuses mining without peers'],'scope':'disposable local nodes, same GUI sources as frozen package'}
Path('.local/readiness/gui-mining.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
