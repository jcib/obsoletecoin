"""Build the public Pages asset directory and portable Worker sources."""
import argparse,json,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--static',type=Path,required=True)
p.add_argument('--work',type=Path,default=Path(__file__).resolve().parents[2]/'.local');a=p.parse_args()
root=Path(__file__).resolve().parents[2];out=a.work/'pages-dist';src=a.work/'pages-src'
out.mkdir(exist_ok=True);src.mkdir(exist_ok=True)
pages={}
for f in a.static.rglob('*'):
 if not f.is_file():continue
 relative=f.relative_to(a.static);name='/'+relative.as_posix()
 if f.suffix in ('.html','.css'):pages[name]=f.read_text(encoding='utf-8-sig')
 if name in ('/forum-template.html','/downloads/source.tar.gz','/explorer/snapshot.json') or f.suffix.lower() in ('.mp3','.ogg','.wav'):continue
 target=out/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
(src/'generated.mjs').write_text('export const PAGES='+json.dumps(pages)+';\n',encoding='utf-8')
for name,folder in [('admin.mjs','cloudflare'),('admin-auth.mjs','cloudflare'),('node-monitor.mjs','cloudflare'),('census.mjs','live'),('peers.mjs','live'),('probe-protocol.mjs','live'),('network.mjs','cloudflare'),('forum.mjs','cloudflare'),('worker.mjs','cloudflare'),('core.mjs','live'),('probe.mjs','live')]:
 text=(root/'website'/folder/name).read_text(encoding='utf-8-sig').replace("'../live/","'./")
 (src/name).write_text(text,encoding='utf-8')
(out/'_routes.json').write_text(json.dumps({'version':1,'include':['/forum','/forum/*','/api/*','/live/*','/explorer','/explorer/*','/downloads/windows-wsl.zip'],'exclude':[]}),encoding='utf-8')
(out/'_headers').write_text("/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: no-referrer\n  Content-Security-Policy: default-src 'none'; img-src 'self'; style-src 'self'; frame-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'self'\n  X-Frame-Options: SAMEORIGIN\n/downloads/*\n  Cache-Control: public, max-age=3600\n",encoding='utf-8')
print(json.dumps({'pages':len(pages),'output':str(out)}))
with (out/'_headers').open('a',encoding='utf-8') as headers:
 headers.write('/downloads/windows-native-testnet.exe\n  Cache-Control: no-cache\n/downloads/linux-x64.tar.gz\n  Cache-Control: no-cache\n/downloads/SHA256SUMS.txt\n  Cache-Control: no-cache\n')
