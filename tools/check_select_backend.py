"""Exercise the production select() branch on Linux with the core regression.

Requires a completed Unix Makefiles CMake build. This is not Windows OS validation.
The original source is also tested, to establish that the regression catches the bug.
"""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import shutil
import hashlib

p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[1];build=a.build.resolve()
out=root/'.local/upgrade-select';out.mkdir(parents=True,exist_ok=True)
flags={}
for line in (build/'src/util/CMakeFiles/bitcoin_util.dir/flags.make').read_text().splitlines():
    if ' = ' in line:
        key,value=line.split(' = ',1);flags[key]=shlex.split(value)
link=shlex.split((build/'src/test/CMakeFiles/test_bitcoin.dir/link.txt').read_text())
result={}
for label in ('before','after'):
    if label=='after':source=(root/'src/util/sock.cpp').read_bytes()
    elif shutil.which('git'):source=subprocess.check_output(['git','show','HEAD:src/util/sock.cpp'],cwd=root)
    else:
        # WSL installations may use host Git only. Export the original file with
        # host Git into this exact fixture path before running the comparison.
        source=(out/'baseline-sock.cpp').read_bytes()
    unit=out/(label+'.cpp')
    unit.write_bytes(b'#include <compat/compat.h>\n#undef USE_POLL\n'+source)
    obj=out/(label+'.o');binary=out/(label+'-test')
    subprocess.run([link[0],*flags.get('CXX_DEFINES',[]),*flags['CXX_INCLUDES'],*flags['CXX_FLAGS'],
                    '-c',str(unit),'-o',str(obj)],check=True)
    command=[arg for arg in link if not arg.startswith('-Wl,--dependency-file=')]
    command[command.index('-o')+1]=str(binary)
    command.insert(1,str(obj))
    subprocess.run(command,cwd=build/'src/test',check=True)
    run=subprocess.run([str(binary),'--run_test=sock_tests/paused_receive_ignores_urgent_data','--log_level=test_suite'],
                       capture_output=True,text=True)
    (out/(label+'.log')).write_text(run.stdout+run.stderr)
    if label=='before':
        assert run.returncode!=0 and 'events.at(receiver).occurred' in run.stdout+run.stderr,run.stdout+run.stderr
    else:assert run.returncode==0,run.stdout+run.stderr
    result[label]={'exit_code':run.returncode,'expected_result':True,'source_sha256':hashlib.sha256(source).hexdigest()}
result['scope']='Production select branch on Linux; before fails, patched source passes. Not a Windows build.'
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
