import {GENESIS,validate,authorized,render,escape} from '../live/core.mjs';
import {probePeer} from '../live/probe.mjs';
import {forum} from './forum.mjs';
import {PAGES} from './generated.mjs';
export const headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'none'; img-src 'self'; style-src 'self'; frame-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'self'"};
const response=(body,status=200,type='text/html; charset=utf-8')=>new Response(body,{status,headers:{...headers,'Content-Type':type}});
async function bytes(req,max){const reader=req.body?.getReader();if(!reader)return new Uint8Array();const chunks=[];let size=0;while(true){const {value,done}=await reader.read();if(done)break;size+=value.length;if(size>max){await reader.cancel();throw Error('too-large');}chunks.push(value);}const out=new Uint8Array(size);let i=0;for(const c of chunks){out.set(c,i);i+=c.length;}return out;}
async function state(env,key){const row=await env.DB.prepare('SELECT data FROM public_state WHERE name=?').bind(key).first();return row?JSON.parse(row.data):null;}
export default {async fetch(req,env){
 const url=new URL(req.url),path=url.pathname;
 try{
  if(path==='/forum'||path.startsWith('/forum/'))return await forum(req,env,PAGES['/forum-template.html'],headers);
  if(req.method==='POST'){
   if(!['/api/feed','/api/probe'].includes(path))return response('Not found',404);
   let data;try{data=await bytes(req,path==='/api/feed'?1500000:1024);}catch{return response('Payload too large',413,'text/plain');}
   if(!await authorized(req,env.OBSOLETE_FEED_KEY,data))return response('Unauthorized',401,'text/plain');
   if(path==='/api/probe'){
    const current=await state(env,'feed');if(!current||Date.now()-current.observed>60000)return response('No fresh peer',409,'text/plain');
    let result;try{result=await probePeer(current.peer,GENESIS);}catch{result={verified:false,peer:current.peer,checked:Date.now()};}
    await env.DB.prepare('INSERT INTO public_state(name,observed,data) VALUES(?,?,?) ON CONFLICT(name) DO UPDATE SET observed=excluded.observed,data=excluded.data').bind('probe',result.checked,JSON.stringify(result)).run();
    return response(JSON.stringify(result),200,'application/json');
   }
   let feed;try{feed=validate(JSON.parse(new TextDecoder().decode(data)));}catch{return response('Invalid feed',400,'text/plain');}
   const result=await env.DB.prepare('INSERT INTO public_state(name,observed,data) VALUES(?,?,?) ON CONFLICT(name) DO UPDATE SET observed=excluded.observed,data=excluded.data WHERE excluded.observed>public_state.observed').bind('feed',feed.observed,JSON.stringify(feed)).run();
   return response(result.meta.changes?'Accepted':'Outdated feed',result.meta.changes?200:409,'text/plain');
  }
  if(!['GET','HEAD'].includes(req.method))return response('Method not allowed',405);
  if(path==='/api/snapshot'){
   const s=await state(env,'feed');return response(JSON.stringify({available:!!s,fresh:!!s&&Date.now()-s.observed<=60000,...s}),s?200:503,'application/json');
  }
  if(path.startsWith('/live/')){const s=await state(env,'feed'),probe=path==='/live/peer'?await state(env,'probe'):null;const r=render(s,path,Date.now(),probe);return response(req.method==='HEAD'?null:r.html,r.status);}
  if(path==='/explorer/search'){
   const q=(url.searchParams.get('q')||'').trim();let to;
   if(/^\d{1,10}$/.test(q))to='/explorer/blocks/'+Number(q)+'.html';else if(/^[0-9a-f]{64}$/.test(q))to='/explorer/transactions/'+q+'.html';else if(/^[a-zA-Z0-9]{20,100}$/.test(q))to='/explorer/addresses/'+q+'.html';else return response('Enter a block height, transaction ID or address.',400,'text/plain');
   return new Response(null,{status:303,headers:{...headers,Location:to}});
  }
  const normalized=path==='/'?'/index.html':['/explorer','/explorer/'].includes(path)?'/explorer/index.html':path;
  if(normalized==='/forum-template.html')return response('Not found',404);
  if(PAGES[normalized])return response(req.method==='HEAD'?null:PAGES[normalized],200,normalized.endsWith('.css')?'text/css; charset=utf-8':'text/html; charset=utf-8');
  if(/^\/explorer\/(blocks\/\d{1,10}|transactions\/[0-9a-f]{64}|addresses\/[a-zA-Z0-9]{1,100})\.html$/.test(path))return response(PAGES['/explorer/index.html'].replace('src="/live/explorer/index.html"','src="/live'+escape(path)+'"'));
  if(env.ASSETS)return env.ASSETS.fetch(req);
  return response('Not found',404,'text/plain');
 }catch{return response('Temporarily unavailable. Please retry.',503,'text/plain');}
}};
