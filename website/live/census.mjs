import {publicPeer} from './peers.mjs';
export const INTERVAL=300000, RECENT=1800000, RETENTION=86400000, LIMIT=256, BATCH=4;
export function candidates(old,seed,now=Date.now()){
 const map=new Map();
 for(const r of old?.nodes||[])if(publicPeer(r.peer)&&now-r.seen<=RETENTION)map.set(r.peer,{...r});
 if(publicPeer(seed))map.set(seed,{peer:seed,checked:0,success:0,verified:false,...map.get(seed),seen:now});
 return [...map.values()].sort((a,b)=>Number(b.peer===seed)-Number(a.peer===seed)).slice(0,LIMIT);
}
export function selectPeers(nodes,seed){
 const first=nodes.find(r=>r.peer===seed);
 const others=nodes.filter(r=>r!==first).sort((a,b)=>(a.checked||0)-(b.checked||0)||a.peer.localeCompare(b.peer));
 return [...(first?[first]:[]),...others].slice(0,BATCH);
}
export function updateCensus(nodes,results,now=Date.now()){
 const map=new Map(nodes.map(r=>[r.peer,{...r}]));
 for(const r of results){
  const node=map.get(r.peer);if(!node)continue;
  node.checked=now;node.verified=r.verified===true;
  if(node.verified){node.success=now;node.seen=now;}
 }
 let capped=false;
 for(const r of results)if(r.verified)for(const peer of r.peers||[]){
  if(!publicPeer(peer))continue;
  const prior=map.get(peer);
  if(prior)prior.seen=now;
  else if(map.size<LIMIT)map.set(peer,{peer,seen:now,checked:0,success:0,verified:false});
  else capped=true;
 }
 return {updated:now,nodes:[...map.values()],capped};
}
export function publicCensus(record,now=Date.now()){
 if(!record)return {available:false,count:null,fresh:false,checked:null};
 const recent=r=>r.checked>0&&now-r.checked<=RECENT&&now>=r.checked;
 const verified=record.nodes.filter(r=>r.verified&&recent(r));
 return {available:true,count:verified.length,fresh:now-record.updated<=2*INTERVAL&&now>=record.updated,
  checked:record.updated,oldestVerification:verified.length?Math.min(...verified.map(r=>r.checked)):null,
  known:record.nodes.length,checkedRecently:record.nodes.filter(recent).length,
  windowMinutes:RECENT/60000,intervalMinutes:INTERVAL/60000,limit:LIMIT,capped:record.capped===true,
  scope:'Public IPv4 endpoints on TCP 19777; testnet handshake and genesis verified'};
}
const utc=n=>new Date(n).toISOString().replace('T',' ').replace(/\.\d{3}Z$/,' UTC');
export function renderCensus(c){
 let body='<section class="node-census"><h2>Detected reachable public nodes</h2>';
 if(!c?.available)body+='<p>Awaiting the first external check.</p><details><summary>What this count includes</summary>';
 else{
  body+='<p><strong class="public-node-count">'+c.count+'</strong> public endpoints verified within the last 30 minutes.</p>';
  body+='<p>'+(c.fresh?'Monitor active.':'STALE MONITOR - results may be incomplete.')+' Last check: '+utc(c.checked)+'. Checks run approximately every 5 minutes while the node feed is active.</p>';
  body+='<details><summary>What this count includes</summary><p>Discovery coverage: '+c.known+' known candidates; '+c.checkedRecently+' checked within the last 30 minutes. '+(c.capped?'Candidate limit reached. ':'')+'Up to 256 candidates retained.</p>';
 }
 body+='<p>Counts public IPv4 endpoints on TCP 19777 that answer an external testnet handshake and genesis check. Addresses are discovered from peers; discovery is gradual and incomplete. Private nodes, IPv6, Tor and other ports are outside this count. One operator may run several nodes; this is neither a total network census nor a miner count. Failed rechecks remove an endpoint immediately; unchecked results expire after 30 minutes.</p></details></section>';
 return body;
}
