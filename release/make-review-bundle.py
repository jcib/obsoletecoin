"""Export only committed sources plus pinned RandomX; no working-tree secrets."""
import gzip,hashlib,io,json,subprocess,tarfile
from pathlib import Path
base=Path(__file__).resolve().parents[1];out=base/'.local/release';out.mkdir(parents=True,exist_ok=True)
def git(*args,cwd=base):return subprocess.check_output(['git',*args],cwd=cwd)
head=git('rev-parse','HEAD').decode().strip();rx=git('rev-parse','HEAD',cwd=base/'src/randomx').decode().strip()
assert git('ls-tree','HEAD','src/randomx').decode().split()[2]==rx
archive=out/'ObsoleteCoin-Review-Source.tar.gz'
with archive.open('wb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as gz,tarfile.open(fileobj=gz,mode='w') as dest:
 for data in (git('archive','--format=tar','--prefix=obsoletecoin/',head),git('archive','--format=tar','--prefix=obsoletecoin/src/randomx/',rx,cwd=base/'src/randomx')):
  with tarfile.open(fileobj=io.BytesIO(data)) as src:
   for item in src:
    item.uid=item.gid=0;item.uname=item.gname='';item.mtime=0
    dest.addfile(item,src.extractfile(item) if item.isfile() else None)
manifest={'source_commit':head,'randomx_commit':rx,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'contains':'committed source and pinned RandomX only; no wallets, credentials or untracked files','independent_review_completed':False}
(out/'Review-Source.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest))
