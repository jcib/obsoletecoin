"""Exercise this exact unsigned installer with disposable app and wallet paths."""
import argparse,hashlib,json,os,subprocess,sys,tempfile,winreg
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from integration import Node,free_port
p=argparse.ArgumentParser();p.add_argument('installer',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
key=r'Software\Microsoft\Windows\CurrentVersion\Uninstall\ObsoleteCoinMainnet_is1'
try:
 with winreg.OpenKey(winreg.HKEY_CURRENT_USER,key):raise SystemExit('A real installation exists; use a clean Windows test account')
except FileNotFoundError:pass
checks=[]
with tempfile.TemporaryDirectory(prefix='obsolete-installer-') as tmp:
 base=Path(tmp);app=base/'app';data=base/'wallet-data'
 def install():
  subprocess.run([str(a.installer.resolve()),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-',f'/DIR={app}','/TASKS='],check=True,timeout=180)
 def uninstall():
  un=app/'unins000.exe'
  if un.exists():
   subprocess.run([str(un),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART'],check=True,timeout=180)
 def verify_wallet(create=False):
  n=Node(app/'bitcoind.exe',data)
  try:
   n.start();n.rpc.call('createwallet' if create else 'loadwallet','preserve')
   w=n.rpc.for_wallet('preserve')
   if create:return w.call('getnewaddress')
   assert w.call('getaddressinfo',address)['ismine']
  finally:n.stop()
 try:
  install();assert (app/'ObsoleteCoin.exe').is_file();checks.append('installation')
  smoke=base/'smoke.json'
  subprocess.run([str(app/'ObsoleteCoin.exe'),'--self-test',str(smoke),'--rpcport',str(free_port())],check=True,timeout=180)
  assert json.loads(smoke.read_text())['native'];checks.append('installed frozen GUI + node + RandomX mining')
  subprocess.run([str(app/'ObsoleteCoin.exe'),'--chain','obsolete','--self-test',str(smoke)],check=True,timeout=180)
  assert json.loads(smoke.read_text())['address_verified'];checks.append('installed mainnet genesis and receive address')
  address=verify_wallet(True)
  install();verify_wallet();checks.append('reinstallation opens same wallet')
  files={str(x.relative_to(data)):hashlib.sha256(x.read_bytes()).hexdigest() for x in data.rglob('wallet.dat')}
  assert files
  uninstall();assert not (app/'ObsoleteCoin.exe').exists()
  assert all(hashlib.sha256((data/k).read_bytes()).hexdigest()==v for k,v in files.items())
  checks.append('uninstall preserves real disposable wallet bytes')
  install();verify_wallet();checks.append('reinstall after uninstall opens preserved wallet')
 finally:uninstall()
result={'result':'passed','checks':checks,'platform':sys.getwindowsversion().build,'scope':'disposable local paths; no existing user wallet touched','signed':False}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2));print(json.dumps(result))
