"""Switch the Dell's existing public P2P port to mainnet and retain the test chain."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parent
UNIT = 'obsolete-mainnet.service'
FEED = 'obsolete-mainnet-explorer.service'
OLD_NODE = 'obsoletecoin-testnet.service'
OLD_FEED = 'obsoletecoin-explorer.service'
DATA = '/var/lib/obsolete-mainnet'
DEST = Path('/opt/obsolete-mainnet')
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('stage', type=Path)
parser.add_argument('manifest_hash')
args = parser.parse_args()
if os.geteuid() != 0:
    parser.error('Use sudo on the node host')
manifest = (args.stage/'deployment.json').read_bytes()
if hashlib.sha256(manifest).hexdigest() != args.manifest_hash:
    raise SystemExit('Deployment manifest checksum mismatch')
record = json.loads(manifest)

def run(*cmd):
    return subprocess.run(cmd, check=True, text=True, capture_output=True).stdout.strip()

def active(unit):
    return subprocess.run(['systemctl','is-active','--quiet',unit]).returncode == 0

def install(source, dest, mode):
    content = source.read_bytes()
    if hashlib.sha256(content).hexdigest() != record['files'][source.relative_to(args.stage).as_posix()]:
        raise SystemExit(f'Checksum mismatch for {source.name}')
    dest.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=dest.parent,delete=False) as temp:
        temp.write(content)
        os.fchmod(temp.fileno(), mode)
        temp.flush()
        os.fsync(temp.fileno())
    os.replace(temp.name, dest)

def cli(*params):
    return run('runuser','-u','obsoletecoin','--',str(DEST/'bin/bitcoin-cli'),'-chain=obsolete',
               '-datadir='+DATA,'-rpcport=19778',*params)

for name in ('bitcoind','bitcoin-cli'):
    install(args.stage/name,DEST/'bin'/name,0o755)
for name in ('tools/rpc.py','website/live/publisher.py'):
    install(args.stage/name,DEST/name,0o644)
for unit in (UNIT,FEED):
    dest=Path('/etc/systemd/system')/unit
    install(args.stage/'deploy'/unit,dest,0o644)
    run('systemd-analyze','verify',str(dest))
run('systemctl','daemon-reload')
previous = [unit for unit in (OLD_NODE,OLD_FEED) if active(unit)]
try:
    run('systemctl','stop',OLD_FEED,OLD_NODE)
    run('systemctl','start',UNIT)
    deadline=time.monotonic()+90
    while True:
        try:
            if cli('getblockhash','0') != record['genesis'] or json.loads(cli('getblockchaininfo'))['chain'] != 'obsolete':
                raise RuntimeError('Unexpected mainnet identity')
            break
        except subprocess.CalledProcessError:
            if time.monotonic() >= deadline or not active(UNIT): raise
            time.sleep(1)
    run('systemctl','start',FEED)
    run('systemctl','enable',UNIT,FEED)
    run('systemctl','disable',OLD_FEED,OLD_NODE)
except Exception:
    run('systemctl','stop',FEED,UNIT)
    if previous: run('systemctl','start',*previous)
    raise
print(json.dumps({'chain':'obsolete','genesis':record['genesis'],'height':int(cli('getblockcount')),
                  'p2p':19777,'mainnet_active':active(UNIT),'testnet_active':active(OLD_NODE)}))
