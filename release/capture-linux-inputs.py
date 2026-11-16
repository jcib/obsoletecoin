"""Record Linux build inputs before compiling and assembling a distributable."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
names=subprocess.check_output(['git','ls-files','--recurse-submodules','-z','src','cmake','CMakeLists.txt']).decode().split('\0')
names=[n for n in names if n and Path(n).is_file()]
names+=['tools/linux_wallet.py','tools/native_wallet.py','tools/wallet.py','tools/rpc.py','tools/mine.py',
        'tools/mining.py','tools/rx.py','tools/wallet_recovery.py','tools/node.py','tools/health.py',
        'release/Start-Wallet.sh','release/assemble-linux.py','docs/LINUX-NATIVE.md']
result={'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'working_tree_changes_included':bool(subprocess.check_output(['git','status','--porcelain'])),
        'sources':{n:hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in sorted(names)}}
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(result,indent=2)+'\n')
print('Recorded',len(names),'build inputs')
