"""Assemble only explicit runtime inputs; never copy wallets or workspace secrets."""
import argparse, hashlib, json, shutil, subprocess, sys
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--gui',type=Path,default=Path('.local/native-dist/ObsoleteCoin'))
p.add_argument('--node',type=Path,default=Path('.local/native-node'))
p.add_argument('--output',type=Path,default=Path('.local/native-package'))
a=p.parse_args()
if a.output.exists():raise SystemExit('Output must be a new directory; refusing to mix releases')
assert (a.gui/'ObsoleteCoin.exe').is_file()
assert (a.node/'bitcoind.exe').is_file()
shutil.copytree(a.gui,a.output)
for item in a.node.iterdir():
 if item.is_dir():
  if item.name=='licenses':shutil.copytree(item,a.output/'licenses'/'native')
 elif item.suffix.lower() in ('.exe','.dll','.txt','.json'):shutil.copy2(item,a.output/item.name)
licenses=a.output/'licenses';licenses.mkdir(exist_ok=True)
for src,name in [('COPYING','ObsoleteCoin-MIT.txt'),('src/randomx/LICENSE','RandomX.txt'),('.local/python314/LICENSE.txt','Python.txt')]:
 path=Path(src)
 if path.is_file():shutil.copy2(path,licenses/name)
for source in ['src/secp256k1/COPYING','src/leveldb/LICENSE','src/leveldb/AUTHORS','src/crc32c/LICENSE','src/crc32c/AUTHORS','src/minisketch/LICENSE','src/crypto/ctaes/COPYING','docs/THIRD_PARTY.md']:
 path=Path(source);shutil.copy2(path,licenses/(path.parent.name+'-'+path.name))
bootloader=Path('.local/build-venv314/Lib/site-packages/pyinstaller-6.22.0.dist-info/licenses/COPYING.txt')
if bootloader.is_file():shutil.copy2(bootloader,licenses/'PyInstaller.txt')
shutil.copy2('docs/WINDOWS-NATIVE.md',a.output/'READ-ME.txt')
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
source_files=['tools/native_wallet.py','tools/wallet.py','tools/rpc.py','tools/mine.py','release/build-wallet.ps1','release/requirements-build.txt','release/requirements-build.lock','release/prepare-tk.py']
source_files += ['tools/mining.py','tools/rx.py','tools/wallet_recovery.py']
source_files += [str(x).replace('\\','/') for x in Path('tools/assets').rglob('*') if x.is_file()]
manifest={'network':'obsolete-test','unsigned':True,'mainnet_enabled':False,'gui_base_commit':head,'gui_sources':{x:hashlib.sha256(Path(x).read_bytes()).hexdigest() for x in source_files},'node':json.loads((a.node/'node-provenance.json').read_text()),'runtime':'CPython 3.14.10','files':{}}
for item in sorted(a.output.rglob('*')):
 if item.is_file():manifest['files'][item.relative_to(a.output).as_posix()]=hashlib.sha256(item.read_bytes()).hexdigest()
(a.output/'PROVENANCE.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'directory':str(a.output),'files':len(manifest['files'])}))
