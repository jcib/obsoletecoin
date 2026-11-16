"""Run desktop/miner checks with the existing pinned Windows build runtime."""
import argparse
import os
import subprocess
import sys
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--screenshot',action='store_true')
p.add_argument('--bindir',type=Path,default=Path('.local/native-node'))
a=p.parse_args()
root=Path(__file__).resolve().parents[1]
os.chdir(root)
os.environ['TCL_LIBRARY']=str(root/'.local/tk-scripts/tcl_library')
os.environ['TK_LIBRARY']=str(root/'.local/tk-scripts/tk_library')
commands=[['-m','unittest','discover','-s','tests','-v'],
          ['-m','unittest','discover','-s','tools','-p','test_wallet*.py','-v'],
          ['tools/integration.py','--bindir',str(a.bindir),'--library',str(a.bindir/'librandomx.dll')]]
if a.screenshot:
    commands=[['tools/ui_smoke.py','--screenshot','.local/readiness/wallet-upgrade.png']]
for command in commands:subprocess.run([sys.executable,'-B',*command],check=True)
