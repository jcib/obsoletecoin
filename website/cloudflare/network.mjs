import {renderCensus} from '../live/census.mjs';
import {escape,utc} from '../live/core.mjs';
export const RETAIN=4097;
const header=b=>({height:b.height,hash:b.hash,previous:b.previous,time:b.time,bits:b.bits});
export function target(bits){
 if(!/^[0-9a-f]{8}$/.test(bits))return null;
 const n=parseInt(bits,16),size=n>>>24,word=n&0x007fffff;
 if(!word||(n&0x00800000)||size>34)return null;
 const t=size<=3?BigInt(word)>>BigInt(8*(3-size)):BigInt(word)<<BigInt(8*(size-3));
 return t>0n&&t<(1n<<256n)?t:null;
}
export function work(bits){const t=target(bits);return t===null?null:(1n<<256n)/(t+1n);}
export function difficulty(bits){const t=target(bits);return t===null?null:Number(target('1d00ffff'))/Number(t);}
export function mergeHistory(old,s){
 const incoming=s.blocks.map(header);
 if(old?.headers?.at(-1)?.hash===s.tip)return old;
 const prior=old?.headers||[],map=new Map(incoming.map(b=>[b.height,b]));let common=null;
 for(let i=prior.length-1;i>=0;i--)if(map.get(prior[i].height)?.hash===prior[i].hash){common=prior[i];break;}
 if(!common&&prior.length&&incoming[0].height===prior.at(-1).height+1&&incoming[0].previous===prior.at(-1).hash)common=prior.at(-1);
 const events=[...(old?.events||[])];let merged;
 if(!prior.length)merged=incoming;
 else if(common){
  const depth=prior.at(-1).height-common.height;
  if(depth>0)events.push({observed:s.observed,kind:'reorganization',depth,from:prior.at(-1).height,to:s.height});
  merged=[...prior.filter(b=>b.height<=common.height),...incoming.filter(b=>b.height>common.height)];
 }else{
  const known=new Map(prior.map(b=>[b.height,b.hash]));
  const conflict=incoming.some(b=>known.has(b.height)&&known.get(b.height)!==b.hash);
  events.push({observed:s.observed,kind:conflict?'chain-change-unresolved':'coverage-gap',depth:null,from:prior.at(-1).height,to:s.height});
  merged=incoming;
 }
 return {started:old?.started||s.observed,updated:s.observed,headers:merged.slice(-RETAIN),events:events.slice(-100)};
}
export function estimate(headers,n){
 const list=headers.slice(-(n+1)),actual=Math.max(0,list.length-1);
 const empty={requested:n,blocks:actual,hashrate:null,seconds:null,from:null,to:null};
 if(!actual)return empty;
 let total=0n;for(const b of list.slice(1)){const w=work(b.bits);if(w===null)return empty;total+=w;}
 const lo=Math.min(...list.map(b=>b.time)),hi=Math.max(...list.map(b=>b.time)),seconds=hi-lo;
 return {requested:n,blocks:actual,hashrate:seconds>0?Number(total)/seconds:null,seconds,from:lo,to:hi};
}
export function summarize(s,h,now=Date.now()){
 if(!s)return null;
 const headers=h?.headers?.at(-1)?.hash===s.tip?h.headers:s.blocks.map(header);
 const tip=headers.at(-1),since=Math.floor(now/1000)-tip.time;
 const selected=s.blocks.filter(b=>b.height>0).slice(-672),rewards=new Map();let unassigned=0n;
 for(const b of selected){
  const seen=new Set(),coinbase=b.tx.find(t=>t.vin.some(v=>v.coinbase));
  for(const v of coinbase?.vout||[]){
   const atoms=BigInt(v.atoms);if(atoms===0n)continue;
   if(!v.address){unassigned+=atoms;continue;}
   const r=rewards.get(v.address)||{address:v.address,blocks:0,atoms:0n};
   if(!seen.has(v.address)){r.blocks++;seen.add(v.address);}r.atoms+=atoms;rewards.set(v.address,r);
  }
 }
 const rows=[...rewards.values()].sort((a,b)=>b.blocks-a.blocks||a.address.localeCompare(b.address)),days=new Map();
 for(let i=0;i<headers.length;i++){
  const b=headers[i];if(b.height===0)continue;
  const day=new Date(b.time*1000).toISOString().slice(0,10),r=days.get(day)||{day,blocks:0,diff:0,count:0,work:0n,valid:true,times:[]};
  r.blocks++;const d=difficulty(b.bits);if(d!==null){r.diff+=d;r.count++;}
  if(i>0){const w=work(b.bits);if(w===null)r.valid=false;else r.work+=w;r.times.push(headers[i-1].time,b.time);}
  days.set(day,r);
 }
 const daily=[...days.values()].sort((a,b)=>a.day.localeCompare(b.day)).map(r=>{
  const span=r.times.length?Math.max(...r.times)-Math.min(...r.times):0;
  return {day:r.day,blocks:r.blocks,difficulty:r.count?r.diff/r.count:null,hashrate:r.valid&&span>0?Number(r.work)/span:null};
 });
 return {observed:s.observed,fresh:now-s.observed<=60000,height:s.height,difficulty:difficulty(tip.bits),connections:s.connections,mempool:s.mempool,
  lastBlock:tip.time,sinceBlock:since,noBlockWarning:now-s.observed<=60000&&since>5400,
  windows:[24,96,672].map(n=>estimate(headers,n)),coverage:{first:headers[0].height,last:tip.height,retained:headers.length,limit:RETAIN},
  rewards:{blocks:selected.length,first:selected[0]?.height??null,last:selected.at(-1)?.height??null,addresses:rows.length,rows:rows.slice(0,50).map(r=>({...r,atoms:String(r.atoms)})),omitted:Math.max(0,rows.length-50),unassignedAtoms:String(unassigned)},
  daily,events:h?.events||[],monitoringSince:h?.started??null};
}
const num=v=>v===null||!Number.isFinite(v)?'Unavailable':v.toLocaleString('en-US',{maximumSignificantDigits:5});
const rate=v=>v===null?'Unavailable':num(v)+' H/s';
const date=v=>v===null?'Unavailable':utc(v*1000);
const table=(heads,rows)=>'<div class="scroll"><table><thead><tr>'+heads.map(x=>'<th>'+x+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(x=>'<td>'+x+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';
export function renderNetwork(m,now=Date.now()){
 let body='<h1>Network observations</h1><p><a target="_top" href="/explorer/index.html">Blocks</a> | <a target="_top" href="/api/network">Network JSON</a></p>';
 if(!m)body+='<div class="snapshot-note">NODE FEED UNAVAILABLE</div>';
 else{
  const age=Math.max(0,Math.floor((now-m.observed)/1000)),peak=Math.max(1,...m.daily.map(r=>r.hashrate||0));
  body+='<div class="snapshot-note"><strong>'+(m.fresh?'LIVE MAINNET DATA':'STALE DATA - NODE FEED UNAVAILABLE')+'</strong><br>Observation: '+utc(m.observed)+' ('+age+'s ago). Refresh: 15 seconds.</div>';
  body+=table(['Height','First-node connections','Current difficulty','Pending transactions'],[[m.height,m.connections,num(m.difficulty),m.mempool]]);
  body+=renderCensus(m.publicNodes);
  body+='<p>Last block timestamp: '+date(m.lastBlock)+'. '+(m.sinceBlock<0?'Timestamp is ahead of this clock.':num(m.sinceBlock)+' seconds ago.')+'</p>';
  if(m.noBlockWarning)body+='<div class="snapshot-note"><strong>BLOCK DELAY NOTICE</strong><p>No block timestamp within the last 90 minutes (six target intervals). This alone does not prove an outage or attack.</p></div>';
  body+='<h2>Estimated network power</h2><p>Historical accepted chain work divided by elapsed block time. Not live miner telemetry. Timestamps, withheld blocks and reorganizations affect estimates. A fresh feed does not make an old mining sample current.</p>';
  body+=table(['Requested window','Actual intervals','Estimated power','Time span (UTC)'],m.windows.map(w=>[w.requested+' blocks',w.blocks+(w.blocks<w.requested?' (partial)':''),rate(w.hashrate),date(w.from)+'<br>'+date(w.to)]));
  body+='<h2>Canonical history</h2><p>Retained blocks '+m.coverage.first+' - '+m.coverage.last+'; up to '+m.coverage.limit+' headers. Earlier data is not reconstructed. Daily rows follow miner-provided UTC timestamps; boundary days and gaps may be incomplete. Difficulty uses the conventional difficulty-1 reference.</p>';
  body+=table(['UTC day','Observed blocks','Mean difficulty','Estimated power','Power history'],m.daily.slice().reverse().map(d=>[d.day,d.blocks,num(d.difficulty),rate(d.hashrate),d.hashrate===null?'Unavailable':'<meter min="0" max="'+peak+'" value="'+d.hashrate+'" aria-label="Estimated power on '+d.day+'">'+rate(d.hashrate)+'</meter>']));
  body+='<h2>Reward destinations</h2><p>'+m.rewards.addresses+' distinct addresses received coinbase outputs in '+m.rewards.blocks+' covered blocks (#'+m.rewards.first+' - #'+m.rewards.last+'). One operator may use many addresses; one address may represent a pool. Shares count blocks paying each address and may sum above 100% for split payouts. This is not a miner count or proof of independent ownership.</p>';
  body+=table(['Address','Blocks paying address','Share of covered blocks'],m.rewards.rows.map(r=>['<span class="hash"><a target="_top" href="/explorer/addresses/'+escape(r.address)+'.html">'+escape(r.address)+'</a></span>',r.blocks,num(100*r.blocks/m.rewards.blocks)+'%']));
  body+='<p>Top 50 addresses shown; '+m.rewards.omitted+' omitted. Outputs without a decoded address: '+escape(m.rewards.unassignedAtoms)+' atomic units. Outputs can include fees and may still be immature.</p>';
  body+='<h2>Observed chain changes</h2><p>Monitoring started: '+(m.monitoringSince?utc(m.monitoringSince):'awaiting first archive')+'. Up to 100 events retained. Changes between observations can be missed; no events does not prove no attack.</p>';
  body+=m.events.length?table(['Observed (UTC)','Event','Removed blocks','Old / new height'],m.events.slice().reverse().map(e=>[utc(e.observed),escape(e.kind),e.depth===null?'Unknown':e.depth,e.from+' / '+e.to])):'<p>No chain changes recorded by this monitor.</p>';
 }
 return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="15"><title>Obsolete Coin network</title><link rel="icon" href="/assets/obsolete-coin.gif" type="image/gif"><link rel="stylesheet" href="/assets/style.css"></head><body class="live-body"><main class="live-content">'+body+'</main></body></html>';
}
