import {admin} from './admin.mjs';
import {GENESIS,validate,authorized,render,escape} from '../live/core.mjs';
import {mergeHistory,summarize,renderNetwork} from './network.mjs';
import {monitorNodes} from './node-monitor.mjs';
import {publicCensus} from '../live/census.mjs';
import {probePeer} from '../live/probe.mjs';
import {forum} from './forum.mjs';
import {PAGES} from './generated.mjs';
export const headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'none'; img-src 'self'; style-src 'self'; frame-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'self'"};
const response=(body,status=200,type='text/html; charset=utf-8')=>new Response(body,{status,headers:{...headers,'Content-Type':type}});
async function bytes(req,max){const reader=req.body?.getReader();if(!reader)return new Uint8Array();const chunks=[];let size=0;while(true){const {value,done}=await reader.read();if(done)break;size+=value.length;if(size>max){await reader.cancel();throw Error('too-large');}chunks.push(value);}const out=new Uint8Array(size);let i=0;for(const c of chunks){out.set(c,i);i+=c.length;}return out;}
async function state(env,key){const row=await env.DB.prepare('SELECT data FROM mainnet_public_state WHERE name=?').bind(key).first();return row?JSON.parse(row.data):null;}
export default {async fetch(req,env,ctx){
 const url=new URL(req.url),path=url.pathname;
 if(path==='/downloads/windows-wsl.zip')return response(req.method==='HEAD'?null:'The WSL package has been withdrawn. Current native Windows and Linux downloads: https://obsoletecoin.pages.dev/downloads.html',410,'text/plain; charset=utf-8');
 try{
  if(path==='/forum/admin'||path.startsWith('/forum/admin/'))return await admin(req,env,PAGES['/forum-template.html'],headers);
  if(path==='/forum'||path.startsWith('/forum/'))return await forum(req,env,PAGES['/forum-template.html'],headers);
  if(req.method==='POST'){
   if(!['/api/feed','/api/probe'].includes(path))return response('Not found',404);
   let data;try{data=await bytes(req,path==='/api/feed'?1500000:1024);}catch{return response('Payload too large',413,'text/plain');}
   if(!await authorized(req,env.OBSOLETE_FEED_KEY,data))return response('Unauthorized',401,'text/plain');
   if(path==='/api/probe'){
    const current=await state(env,'feed');if(!current||Date.now()-current.observed>60000)return response('No fresh peer',409,'text/plain');
    let result;try{result=await probePeer(current.peer,GENESIS);}catch{result={verified:false,peer:current.peer,checked:Date.now()};}
    await env.DB.prepare('INSERT INTO mainnet_public_state(name,observed,data) VALUES(?,?,?) ON CONFLICT(name) DO UPDATE SET observed=excluded.observed,data=excluded.data').bind('probe',result.checked,JSON.stringify(result)).run();
    return response(JSON.stringify(result),200,'application/json');
   }
   let feed;try{feed=validate(JSON.parse(new TextDecoder().decode(data)));}catch{return response('Invalid feed',400,'text/plain');}
   for(let attempt=0;attempt<3;attempt++){
    const rows=await env.DB.prepare("SELECT name,observed,data FROM mainnet_public_state WHERE name IN ('feed','network_history')").all();
    const previous=rows.results.find(r=>r.name==='feed'),history=rows.results.find(r=>r.name==='network_history');
    if(previous&&previous.observed>=feed.observed)return response('Outdated feed',409,'text/plain');
    const old=history?JSON.parse(history.data):null,next=mergeHistory(old,feed),expected=previous?.observed??-1;
    const write=(name,observed,data)=>env.DB.prepare("INSERT INTO mainnet_public_state(name,observed,data) SELECT ?,?,? WHERE COALESCE((SELECT observed FROM mainnet_public_state WHERE name='feed'),-1)=? ON CONFLICT(name) DO UPDATE SET observed=excluded.observed,data=excluded.data").bind(name,observed,JSON.stringify(data),expected);
    const batch=[];
    if(next!==old)batch.push(write('network_history',feed.observed,next));
    batch.push(write('feed',feed.observed,feed));
    const result=await env.DB.batch(batch);
    if(result.at(-1).meta.changes){
     if(env.NODE_CENSUS_ENABLED==='true'&&ctx?.waitUntil)ctx.waitUntil(monitorNodes(env,feed.peer,probePeer).catch(()=>console.warn('public-node-monitor-failed')));
     return response('Accepted',200,'text/plain');
    }
   }
   return response('Concurrent update; retry',409,'text/plain');
  }
  if(!['GET','HEAD'].includes(req.method))return response('Method not allowed',405);
  if(path==='/api/bootstrap'){
   const feed=await state(env,'feed');
   if(!feed || feed.network!=='obsolete' || feed.genesis!==GENESIS || Date.now()-feed.observed>300000)
    return response(JSON.stringify({available:false}),503,'application/json');
   return response(JSON.stringify({chain:feed.network,genesis:feed.genesis,peer:feed.peer,observed:feed.observed}),200,'application/json');
  }
  if(path==='/api/snapshot'){
   const s=await state(env,'feed');return response(JSON.stringify({available:!!s,fresh:!!s&&Date.now()-s.observed<=60000,...s}),s?200:503,'application/json');
  }
  if(path==='/api/nodes')return response(JSON.stringify(publicCensus(await state(env,'node_census'))),200,'application/json');
  if(path==='/api/network'||path==='/live/explorer/network.html'){
   const rows=await env.DB.prepare("SELECT name,data FROM mainnet_public_state WHERE name IN ('feed','network_history','node_census')").all();
   const read=name=>{const r=rows.results.find(r=>r.name===name);return r?JSON.parse(r.data):null;};
   const metrics=summarize(read('feed'),read('network_history'));
   if(metrics)metrics.publicNodes=publicCensus(read('node_census'));
   return path==='/api/network'?response(JSON.stringify({available:!!metrics,...metrics}),metrics?200:503,'application/json'):response(req.method==='HEAD'?null:renderNetwork(metrics));
  }
  if(path==='/explorer/network.html')return response(req.method==='HEAD'?null:PAGES['/explorer/index.html'].replace('src="/live/explorer/index.html"','src="/live/explorer/network.html"'));
  if(path.startsWith('/live/')){
   const s=await state(env,'feed');
   const withPeers=path==='/live/peer'||path==='/live/explorer/index.html';
   const record=withPeers?await state(env,'node_census'):null;
   const peer=path==='/live/peer'?record?.nodes.find(n=>n.peer===s?.peer):null;
   const r=render(s,path,Date.now(),peer,withPeers?publicCensus(record):null);
   return response(req.method==='HEAD'?null:r.html,r.status);
  }
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
