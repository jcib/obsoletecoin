"""Exercise the C++ production ASERT routine; simulation is not a hash-security audit."""
import argparse, hashlib, json, math, random, subprocess, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
source=(ROOT/'src/pow.cpp').read_text();start=source.index('arith_uint256 CalculateASERT(');end=source.index('// GetNextASERTWorkRequired:',start)
code=source[start:end]
with tempfile.TemporaryDirectory(prefix='obsolete-asert-') as tmp:
    tmp=Path(tmp);cpp=tmp/'asert.cpp'
    cpp.write_text('#include <arith_uint256.h>\n#include <cassert>\n#include <cstdlib>\n#include <iostream>\n'+code+\
        '\nint main(){uint32_t bits;long long t,h;while(std::cin>>bits>>t>>h){arith_uint256 ref,limit;ref.SetCompact(bits);limit.SetCompact(0x207fffff);std::cout<<CalculateASERT(ref,900,t,h,limit,21600).GetCompact()<<std::endl;}}')
    binary=tmp/'asert'
    subprocess.run(['g++','-std=c++20','-O2','-ffunction-sections','-fdata-sections','-I'+str(ROOT/'src'),str(cpp),str(ROOT/'src/arith_uint256.cpp'),'-Wl,--gc-sections','-o',str(binary)],check=True)
    process=subprocess.Popen([str(binary)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
    def target(bits):return (bits&0x7fffff)*2**(8*((bits>>24)-3))
    def call(bits,t,h):
        process.stdin.write(f'{bits} {int(t)} {h}\n');process.stdin.flush();return int(process.stdout.readline())
    bits=0x1e0fffff;ref=target(bits);limit=target(0x207fffff)
    for h in [0,1,100,100000,3900000]:
        assert call(bits,900*(h+1),h)==bits
        assert target(call(bits,900*(h+1)+21600,h))>ref
        assert target(call(bits,900*(h+1)-21600,h))<ref
    records=[]
    for name,multiplier in [('steady',lambda h:1),('100x-arrival',lambda h:100 if 100<=h<600 else 1),('99pct-departure',lambda h:.01 if 100<=h<600 else 1),('timestamp-forward-2h',lambda h:1),('testnet-easy-start',lambda h:1)]:
        rng=random.Random(7);anchor=0x207fffff if name=='testnet-easy-start' else bits
        now=0;intervals=[];targets=[];observed=0
        for h in range(1000):
            current=call(anchor,observed+900,h)
            current_target=target(current);assert 0<current_target<=limit
            interval=max(1,int(rng.expovariate(1/(900*ref/current_target/multiplier(h)))))
            now+=interval;observed=now+(7200 if name=='timestamp-forward-2h' and h>=100 else 0)
            intervals.append(interval);targets.append(current_target)
        records.append({'scenario':name,'blocks':1000,'elapsed_seconds':now,'longest_interval_seconds':max(intervals),'first_100_mean_seconds':sum(intervals[:100])/100,'last_100_mean_seconds':sum(intervals[-100:])/100,'min_target_over_reference':min(targets)/ref,'max_target_over_reference':max(targets)/ref})
    process.stdin.close();process.wait();assert process.returncode==0
result={'source_sha256':hashlib.sha256(code.encode()).hexdigest(),'implementation':'verbatim CalculateASERT from src/pow.cpp','seed':7,'scenarios':records,'limitations':['Poisson arrival model, not measured network hashrate','Forward timestamp scenario is a sensitivity test, not proof of admissible timestamps','Initial production difficulty cannot be selected without independent miner benchmarks','No-miner case produces zero blocks; difficulty does not adjust without another block']}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2));print(json.dumps(result))
