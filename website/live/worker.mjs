import {GENESIS,validate,authorized,render,escape} from './core.mjs';
import {probePeer} from './probe.mjs';
import {PAGES,ASSETS} from './generated.mjs';
const headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'none'; img-src 'self'; style-src 'self'; media-src 'self'; frame-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'self'"};
const response=(body,status=200,type='text/html; charset=utf-8')=>new Response(body,{status,headers:{...headers,'Content-Type':type}});
async function bytes(req,max){const reader=req.body?.getReader();if(!reader)return new Uint8Array();const chunks=[];let size=0;while(true){const r=await reader.read();if(r.done)break;size+=r.value.length;if(size>max){await reader.cancel();throw Error('too-large');}chunks.push(r.value);}const out=new Uint8Array(size);let i=0;for(const c of chunks){out.set(c,i);i+=c.length;}return out;}
async function jsonObject(bucket,key){const r=await bucket.get(key);return r?{object:r,value:await r.json()}:null;}
export default {async fetch(req,env){
 const url=new URL(req.url);const path=url.pathname;
 try{
  if(req.method==='POST'){
   if(path!=='/api/feed'&&path!=='/api/probe'&&!/^\/api\/asset\/[0-9a-f]{64}$/.test(path))return response('Not found',404);
   const data=await bytes(req,path.startsWith('/api/asset/')?35000000:4000000);
   if(!await authorized(req,env.OBSOLETE_FEED_KEY,data))return response('Unauthorized',401);
   if(path.startsWith('/api/asset/')){
    const sha=path.split('/').at(-1),entry=Object.values(ASSETS).find(a=>a.sha===sha);if(!entry||data.length!==entry.size)return response('Invalid asset',400);
    const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',data))).map(x=>x.toString(16).padStart(2,'0')).join('');if(digest!==sha)return response('Hash mismatch',400);
    await env.BUCKET.put('assets/'+sha,data,{httpMetadata:{contentType:entry.type}});return response('Stored',200,'text/plain');
   }
   if(path==='/api/probe'){
    const current=await jsonObject(env.BUCKET,'feed.json');if(!current||Date.now()-current.value.observed>60000)return response('No fresh peer',409);
    let result;try{result=await probePeer(current.value.peer,GENESIS);}catch{result={verified:false,peer:current.value.peer,checked:Date.now()};}
    await env.BUCKET.put('probe.json',JSON.stringify(result));return response(JSON.stringify(result),200,'application/json');
   }
   let feed;try{feed=validate(JSON.parse(new TextDecoder().decode(data)));}catch{return response('Invalid feed',400);}
   const old=await jsonObject(env.BUCKET,'feed.json');if(old&&old.value.observed>=feed.observed)return response('Outdated feed',409);
   const written=await env.BUCKET.put('feed.json',JSON.stringify(feed),{onlyIf:old?{etagMatches:old.object.etag}:{etagDoesNotMatch:'*'},httpMetadata:{contentType:'application/json'}});
   return response(written?'Accepted':'Concurrent update',written?200:409,'text/plain');
  }
  if(!['GET','HEAD'].includes(req.method))return response('Method not allowed',405);
  const asset=ASSETS[path];
  if(asset){
   const obj=req.method==='HEAD'?await env.BUCKET.head('assets/'+asset.sha):await env.BUCKET.get('assets/'+asset.sha,{range:req.headers});
   if(!obj)return response('File temporarily unavailable',503,'text/plain');
   const h={...headers,'Cache-Control':'public, max-age=3600','Content-Type':asset.type,'ETag':'"'+asset.sha+'"','Accept-Ranges':'bytes'};
   let status=200;if(req.headers.has('Range')&&obj.range){const start=obj.range.offset??Math.max(0,obj.size-obj.range.suffix),length=obj.range.length??(obj.size-start);h['Content-Range']=`bytes ${start}-${start+length-1}/${obj.size}`;h['Content-Length']=String(length);status=206;}else h['Content-Length']=String(obj.size);
   return new Response(req.method==='HEAD'?null:obj.body,{status,headers:h});
  }
  if(path==='/explorer/search'){
   const q=(url.searchParams.get('q')||'').trim();let to;
   if(/^\d{1,10}$/.test(q))to='/explorer/blocks/'+Number(q)+'.html';else if(/^[0-9a-f]{64}$/.test(q))to='/explorer/transactions/'+q+'.html';else if(/^[a-zA-Z0-9]{20,100}$/.test(q))to='/explorer/addresses/'+q+'.html';else return response('Enter a block height, transaction ID or address.',400,'text/plain');
   return new Response(null,{status:303,headers:{...headers,Location:to}});
  }
  if(path.startsWith('/live/')||path==='/api/snapshot'){
   const stored=await jsonObject(env.BUCKET,'feed.json');const s=stored?.value||null;
   if(path==='/api/snapshot')return response(JSON.stringify({available:!!s,fresh:!!s&&Date.now()-s.observed<=60000,...s}),s?200:503,'application/json');
   const probe=path==='/live/peer'?(await jsonObject(env.BUCKET,'probe.json'))?.value:null;
   const r=render(s,path,Date.now(),probe);return response(req.method==='HEAD'?null:r.html,r.status);
  }
  const normalized=path==='/'?'/index.html':path;
  if(PAGES[normalized])return response(req.method==='HEAD'?null:PAGES[normalized],200,normalized.endsWith('.css')?'text/css; charset=utf-8':normalized.endsWith('.txt')?'text/plain; charset=utf-8':'text/html; charset=utf-8');
  if(/^\/explorer\/(blocks\/\d{1,10}|transactions\/[0-9a-f]{64}|addresses\/[a-zA-Z0-9]{1,100})\.html$/.test(path)){
   return response(PAGES['/explorer/index.html'].replace('src="/live/explorer/index.html"','src="/live'+escape(path)+'"'));
  }
  return response(PAGES['/404.html']||'Not found',404);
 }catch{return response('Temporarily unavailable. Please retry.',503,'text/plain');}
}};
