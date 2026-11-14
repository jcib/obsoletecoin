"""Convert tested static HTML into an HTML Worker plus hash-locked R2 assets."""
import argparse,hashlib,json,mimetypes,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--static',type=Path,required=True);p.add_argument('--site',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2];site=a.site.resolve();src=a.static.resolve();live=site/'worker';live.mkdir(exist_ok=True)
pages={};assets={}
for path in src.rglob('*'):
 if not path.is_file():continue
 name='/'+path.relative_to(src).as_posix()
 if name=='/downloads/source.tar.gz':continue
 if path.suffix in ('.html','.css','.txt') and not name.startswith('/downloads/'):
  pages[name]=path.read_text(encoding='utf-8')
 elif name.startswith(('/assets/','/downloads/')):
  data=path.read_bytes();assets[name]={'sha':hashlib.sha256(data).hexdigest(),'size':len(data),'type':mimetypes.guess_type(path.name)[0] or 'application/octet-stream'}
(live/'generated.mjs').write_text('export const PAGES='+json.dumps(pages)+';\nexport const ASSETS='+json.dumps(assets)+';\n',encoding='utf-8')
for name in ('core.mjs','probe.mjs','worker.mjs'):shutil.copyfile(root/'website/live'/name,live/name)
manifest=json.loads((site/'.openai/hosting.json').read_text(encoding='utf-8-sig'));manifest.pop('static',None);manifest.update(r2='BUCKET',d1=None)
(site/'.openai/hosting.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Keep previous deployment output as a local rollback artifact, never delete it.
if (site/'dist').exists() and not (site/'dist/server').exists():
 backup=site.parent/'site-static-before-live'
 if backup.exists():raise RuntimeError('Refusing to replace existing rollback directory')
 (site/'dist').rename(backup)
output=site/'dist/server';output.mkdir(parents=True,exist_ok=True)
# A dependency-free bundle: only the platform sockets import remains external.
code=(live/'core.mjs').read_text(encoding='utf-8-sig')+'\n'+(live/'generated.mjs').read_text(encoding='utf-8-sig')+'\n'+(live/'probe.mjs').read_text(encoding='utf-8-sig').replace('const enc=new TextEncoder();','const probeEncoder=new TextEncoder();').replace('enc.encode(', 'probeEncoder.encode(')+'\n'+(live/'worker.mjs').read_text(encoding='utf-8-sig')
code='\n'.join(l for l in code.splitlines() if not (l.startswith('import ') and "'./" in l))
code=code.replace('export const ', 'const ').replace('export function ', 'function ').replace('export async function ', 'async function ')
(output/'index.js').write_text(code,encoding='utf-8')
(site/'dist/.openai').mkdir(exist_ok=True);(site/'dist/.openai/hosting.json').write_text(json.dumps(manifest))
(site/'package.json').write_text('{"private":true,"type":"module"}\n')
(site/'asset-manifest.json').write_text(json.dumps(assets,indent=2)+'\n')
print(json.dumps({'pages':len(pages),'assets':len(assets),'worker_bytes':(output/'index.js').stat().st_size}))
