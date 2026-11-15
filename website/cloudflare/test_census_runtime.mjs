import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {resolve} from 'node:path';
import {readFile} from 'node:fs/promises';
import {createHmac} from 'node:crypto';
import {monitorNodes} from './node-monitor.mjs';
import {publicCensus,INTERVAL} from '../live/census.mjs';
const require=createRequire(resolve(process.argv[2],'package.json'));
const {Miniflare,convertV4MiniflareOptions}=require('miniflare');
const mf=new Miniflare(convertV4MiniflareOptions({modules:true,scriptPath:resolve('.local/pages-dist/_worker.js'),
 compatibilityDate:'2026-11-10',d1Databases:['DB'],bindings:{NODE_CENSUS_ENABLED:'false',OBSOLETE_FEED_KEY:'local-test-only',FORUM_SECRET:'local-forum-only',SITE_ORIGIN:'http://localhost'},port:0,host:'127.0.0.1'}));
const peer='8.8.8.8:19777',other='9.9.9.9:19777';
try{
 await mf.ready;const db=await mf.getD1Database('DB');
 await db.prepare('CREATE TABLE public_state(name TEXT PRIMARY KEY,observed INTEGER NOT NULL,data TEXT NOT NULL)').run();
 const missing=await (await mf.dispatchFetch('http://localhost/api/nodes')).json();
 assert.equal(missing.count,null);assert.equal(missing.available,false);
 let calls=0;
 const probe=async p=>{calls++;await new Promise(r=>setTimeout(r,20));return {verified:true,peer:p,peers:[other,other,'127.0.0.1:19777']};};
 const env={DB:db},now=Date.now();
 const runs=await Promise.all(Array.from({length:8},()=>monitorNodes(env,peer,probe,now)));
 assert.equal(runs.filter(Boolean).length,1);assert.equal(calls,1);
 let census=await (await mf.dispatchFetch('http://localhost/api/nodes')).json();
 assert.equal(census.count,1);assert.equal(census.known,2);assert.equal(census.checkedRecently,1);
 assert.ok(!JSON.stringify(census).includes(peer));assert.ok(!JSON.stringify(census).includes(other));
 // Reads never start scans.
 await mf.dispatchFetch('http://localhost/api/nodes');assert.equal(calls,1);
 assert.equal(await monitorNodes(env,peer,probe,now+1000),false);
 await db.prepare("UPDATE public_state SET observed=? WHERE name='node_census_lease'").bind(now-INTERVAL).run();
 await monitorNodes(env,peer,probe,Date.now());assert.equal(calls,3);
 census=await (await mf.dispatchFetch('http://localhost/api/nodes')).json();assert.equal(census.count,2);
 await db.prepare("UPDATE public_state SET observed=? WHERE name='node_census_lease'").bind(now-INTERVAL).run();
 await monitorNodes(env,peer,async p=>{if(p===peer)throw Error('offline');return {verified:true,peer:p,peers:[]};},Date.now());
 census=await (await mf.dispatchFetch('http://localhost/api/nodes')).json();assert.equal(census.count,1);
 // A lease takeover prevents a late scan from overwriting the newer observation.
 await db.prepare("UPDATE public_state SET observed=? WHERE name='node_census_lease'").bind(now-INTERVAL).run();
 let release,start;const gate=new Promise(r=>release=r),started=new Promise(r=>start=r);
 const late=monitorNodes(env,peer,async p=>{start();await gate;return {verified:true,peer:p,peers:[]};},Date.now());
 await started;
 await db.prepare("UPDATE public_state SET observed=observed+1 WHERE name='node_census_lease'").run();
 release();await late;
 census=await (await mf.dispatchFetch('http://localhost/api/nodes')).json();assert.equal(census.count,1);
 // The bundled Worker still ingests signed feeds and exposes both counters.
 const feed=JSON.parse(await readFile('.local/preview-feed.json'));feed.observed=Date.now();
 const body=JSON.stringify(feed),stamp=String(Math.floor(Date.now()/1000));
 const signed={'X-Obsolete-Time':stamp,'X-Obsolete-Signature':createHmac('sha256','local-test-only').update(stamp+'\n/api/feed\n'+body).digest('hex')};
 assert.equal((await mf.dispatchFetch('http://localhost/api/feed',{method:'POST',body})).status,401);
 assert.equal((await mf.dispatchFetch('http://localhost/api/feed',{method:'POST',headers:signed,body})).status,200);
 assert.equal((await mf.dispatchFetch('http://localhost/api/feed',{method:'POST',headers:signed,body})).status,409);
 const index=await (await mf.dispatchFetch('http://localhost/live/explorer/index.html')).text();
 assert.match(index,/FIRST-NODE CONNECTIONS/);assert.match(index,/Detected reachable public nodes/);
 assert.match(index,/class="public-node-count">1</);assert.ok(!index.includes(other));
 const metrics=await (await mf.dispatchFetch('http://localhost/api/network')).json();
 assert.equal(metrics.publicNodes.count,1);assert.equal(metrics.connections,feed.connections);
 const panel=await (await mf.dispatchFetch('http://localhost/live/explorer/network.html')).text();
 assert.match(panel,/Detected reachable public nodes/);
 assert.equal((await mf.dispatchFetch('http://localhost/api/nodes',{method:'POST',body:'{}'})).status,404);
 const stored=JSON.parse((await db.prepare("SELECT data FROM public_state WHERE name='node_census'").first()).data);
 stored.updated-=1800001;for(const n of stored.nodes)n.checked-=1800001;
 await db.prepare("UPDATE public_state SET data=? WHERE name='node_census'").bind(JSON.stringify(stored)).run();
 census=await (await mf.dispatchFetch('http://localhost/api/nodes')).json();assert.equal(census.count,0);assert.equal(census.fresh,false);
 assert.match(await (await mf.dispatchFetch('http://localhost/live/explorer/index.html')).text(),/STALE MONITOR/);
 console.log('Workerd/D1 passed: atomic lease, bounded probes, failure removal, lease takeover, read-only API, aggregate privacy, expiry, authenticated feed/replay and both rendered panels.');
}finally{await mf.dispose();}
