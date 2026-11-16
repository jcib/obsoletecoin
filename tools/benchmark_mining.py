"""Local RandomX microbenchmark; no node, wallet, peers or block submissions."""
import argparse
import json
import threading
import time
from pathlib import Path
from mining import find_library
from rx import RandomX


def measure(library,threads,duty,seconds):
    engines=[]
    try:
        # Exclude allocation/JIT startup from throughput and CPU-use measurements.
        for _ in range(threads):engines.append(RandomX(library,bytes(32)))
        counts=[0]*threads
        gate=threading.Event()
        deadline=0
        def worker(index):
            gate.wait()
            nonce=0
            while time.monotonic()<deadline:
                start=time.monotonic()
                for _ in range(8):
                    if time.monotonic()>=deadline:break
                    engines[index].hash(bytes(76)+nonce.to_bytes(4,'little'))
                    nonce=(nonce+1)&0xffffffff
                    counts[index]+=1
                active=time.monotonic()-start
                if duty<100:time.sleep(min(active*(100-duty)/duty,max(0,deadline-time.monotonic())))
        workers=[threading.Thread(target=worker,args=(i,)) for i in range(threads)]
        for worker_thread in workers:worker_thread.start()
        cpu=time.process_time();start=time.monotonic();deadline=start+seconds;gate.set()
        for worker_thread in workers:worker_thread.join()
        elapsed=time.monotonic()-start;cpu=time.process_time()-cpu
        return dict(threads=threads,activity_percent=duty,elapsed_seconds=elapsed,
                    hashes=sum(counts),hashes_per_worker=counts,hps=sum(counts)/elapsed,
                    process_cpu_seconds=cpu,cpu_core_equivalents=cpu/elapsed)
    finally:
        for engine in engines:engine.close()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--library',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seconds',type=float,default=5);a=p.parse_args()
    if not 1<=a.seconds<=60:p.error('Use 1..60 seconds per scenario')
    result={'scope':'Local fixed-header microbenchmark; excludes initialization; host load affects results',
            'scenarios':[measure(find_library(a.library),threads,duty,a.seconds) for threads,duty in [(1,25),(1,100),(2,50),(2,100)]]}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
