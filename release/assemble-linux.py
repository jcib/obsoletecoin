"""Assemble explicit Linux runtime inputs; never include wallets or WSL wrappers."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

p=argparse.ArgumentParser()
p.add_argument('--bindir',type=Path,required=True)
p.add_argument('--library',type=Path,required=True)
p.add_argument('--inputs',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
if a.output.exists():raise SystemExit('Output must be a new directory')
digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
inputs=json.loads(a.inputs.read_text())
for name,expected in inputs['sources'].items():
    if digest(Path(name))!=expected:raise SystemExit('Source changed after build input capture: '+name)
a.output.mkdir(parents=True)
for name in ('bitcoind','bitcoin-cli','bitcoin-wallet'):
    shutil.copy2(a.bindir/name,a.output/name);(a.output/name).chmod(0o755)
shutil.copy2(a.library,a.output/'librandomx.so');(a.output/'librandomx.so').chmod(0o755)
sources=['linux_wallet.py','native_wallet.py','wallet.py','rpc.py','mine.py','mining.py','rx.py','wallet_recovery.py','node.py','health.py']
(a.output/'tools').mkdir()
for name in sources:shutil.copy2(Path('tools')/name,a.output/'tools'/name)
shutil.copytree('tools/assets',a.output/'tools/assets')
shutil.copy2('release/Start-Wallet.sh',a.output/'Start-Wallet.sh');(a.output/'Start-Wallet.sh').chmod(0o755)
shutil.copy2('docs/LINUX-NATIVE.md',a.output/'README.md')
shutil.copy2('COPYING',a.output/'COPYING')
(a.output/'VERSION').write_text('0.4.0-testnet-rc1\n')
licenses=a.output/'licenses';licenses.mkdir()
for source in ['src/randomx/LICENSE','src/secp256k1/COPYING','src/leveldb/LICENSE','src/leveldb/AUTHORS',
               'src/crc32c/LICENSE','src/crc32c/AUTHORS','src/minisketch/LICENSE','src/crypto/ctaes/COPYING','docs/THIRD_PARTY.md']:
    path=Path(source);shutil.copy2(path,licenses/(path.parent.name+'-'+path.name))
dependencies=''
for name in ('bitcoind','bitcoin-cli','bitcoin-wallet','librandomx.so'):
    output=subprocess.check_output(['ldd',str((a.output/name).resolve())],text=True)
    if 'not found' in output:raise SystemExit('Missing runtime dependency: '+name)
    dependencies+=name+'\n'+output+'\n'
(a.output/'dependencies.txt').write_text(dependencies)
manifest={'version':'0.4.0-testnet-rc1','network':'obsolete-test','mainnet_enabled':False,
          'unsigned':True,'platform':'Debian 13 x86-64','build_inputs':inputs,
          'compiler':subprocess.check_output(['c++','--version'],text=True).splitlines()[0],
          'runtime':subprocess.check_output(['python3','--version'],text=True).strip(),
          'source_sha256':{str(Path('tools')/name):digest(Path('tools')/name) for name in sources},
          'files':{f.relative_to(a.output).as_posix():digest(f) for f in sorted(a.output.rglob('*')) if f.is_file()}}
(a.output/'PROVENANCE.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'directory':str(a.output),'files':len(manifest['files']),'version':manifest['version']}))
