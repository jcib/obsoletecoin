import {renderCensus} from './census.mjs';
// Public testnet read model. No wallet RPC or arbitrary proxy route exists.
export const GENESIS='9576894f8fffa098a9b1c04c3a3edb774d9dc7f58413e0906e781ecd8f0ede98';
const hex=/^[0-9a-f]{64}$/;const address=/^[a-zA-Z0-9]{0,100}$/;
const enc=new TextEncoder();
export const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const integer=(v,max=Number.MAX_SAFE_INTEGER)=>Number.isSafeInteger(v)&&v>=0&&v<=max;
const check=(v)=>{if(!v)throw new Error('invalid-feed');};
export function validate(s,now=Date.now()){
 check(s&&s.network==='obsolete-test'&&s.genesis===GENESIS&&integer(s.observed)&&Math.abs(now-s.observed)<=120000);
 check(integer(s.height)&&integer(s.first)&&hex.test(s.tip)&&Array.isArray(s.blocks)&&s.blocks.length>0&&s.blocks.length<=1024);
 check(s.blocks.length===s.height-s.first+1&&integer(s.connections,100000)&&integer(s.mempool,10000000));
 check(typeof s.peer==='string'&&/^(\d{1,3}\.){3}\d{1,3}:19777$/.test(s.peer));
 const ip=s.peer.split(':')[0].split('.').map(Number);check(ip.every(n=>n<=255)&&![0,10,127,169,172,192].includes(ip[0])&&ip[0]<224&&!(ip[0]===100&&ip[1]>=64&&ip[1]<=127));
 let prior;let txCount=0;
 const blocks=s.blocks.map((b,i)=>{
  check(b.height===s.first+i&&hex.test(b.hash)&&hex.test(b.previous)&&integer(b.time,4294967295)&&/^[0-9a-f]{8}$/.test(b.bits)&&integer(b.size,4000000));
  check(!prior||b.previous===prior);prior=b.hash;
  if(b.height===0)check(b.hash===GENESIS);
  check(Array.isArray(b.tx)&&b.tx.length>0&&b.tx.length<=20000);txCount+=b.tx.length;check(txCount<=30000);
  const tx=b.tx.map(t=>{
   check(hex.test(t.txid)&&Array.isArray(t.vin)&&t.vin.length>0&&t.vin.length<=20000&&Array.isArray(t.vout)&&t.vout.length<=20000);
   return {txid:t.txid,vin:t.vin.map(v=>{if(v.coinbase===true)return {coinbase:true};check(hex.test(v.txid)&&integer(v.vout,4294967295));return {txid:v.txid,vout:v.vout};}),vout:t.vout.map((v,n)=>{
    check(v.n===n&&typeof v.atoms==='string'&&/^(0|[1-9][0-9]{0,17})$/.test(v.atoms)&&BigInt(v.atoms)<=100000000000000000n&&typeof v.address==='string'&&address.test(v.address)&&/^[a-z0-9_]{1,40}$/.test(v.type));
    return {n,atoms:v.atoms,address:v.address,type:v.type};
   })};
  });return {height:b.height,hash:b.hash,previous:b.previous,time:b.time,bits:b.bits,size:b.size,tx};
 });check(prior===s.tip);
 return {network:s.network,genesis:GENESIS,observed:s.observed,height:s.height,tip:s.tip,first:s.first,connections:s.connections,mempool:s.mempool,peer:s.peer,blocks};
}
export const amount=s=>{const n=BigInt(s);return (n/100000000n).toLocaleString('en-US')+'.'+(n%100000000n).toString().padStart(8,'0');};
export const utc=n=>new Date(n).toISOString().replace('T',' ').replace(/\.\d{3}Z$/,' UTC');
export async function authorized(req,key,body,now=Date.now()){
 if(!key)return false;const stamp=req.headers.get('X-Obsolete-Time')||'',sig=req.headers.get('X-Obsolete-Signature')||'';
 if(!/^\d{10}$/.test(stamp)||Math.abs(now/1000-Number(stamp))>120||!hex.test(sig))return false;
 const k=await crypto.subtle.importKey('raw',enc.encode(key),{name:'HMAC',hash:'SHA-256'},false,['verify']);
 const data=enc.encode(stamp+'\n'+new URL(req.url).pathname+'\n');const full=new Uint8Array(data.length+body.length);full.set(data);full.set(body,data.length);
 return crypto.subtle.verify('HMAC',k,Uint8Array.from(sig.match(/../g),x=>parseInt(x,16)),full);
}
const link=(path,label)=>`<a target="_top" href="${escape(path)}">${escape(label)}</a>`;
const bl=b=>link('/explorer/blocks/'+b.height+'.html','#'+b.height);
const tl=t=>link('/explorer/transactions/'+t.txid+'.html',t.txid);
export function render(s,path,now=Date.now(),probe=null,census=null){
 let body='',status=200;const age=s?Math.max(0,Math.floor((now-s.observed)/1000)):null;
 const fresh=s&&age<=60;
 const note=s?`<div class="snapshot-note"><strong>${fresh?'LIVE TESTNET DATA':'STALE DATA — NODE FEED UNAVAILABLE'}</strong><br>Last node observation: ${utc(s.observed)} (${age}s ago). Refresh: 15 seconds.<br>Coverage: blocks ${s.first}–${s.height}. Confirmations refer to this observation.</div>`:'<div class="snapshot-note"><strong>NODE FEED UNAVAILABLE</strong><p>No live data received yet. Retrying in 15 seconds.</p></div>';
 const peer=s&&probe&&probe.peer===s.peer&&probe.verified===true&&now-probe.checked<1800000;
 if(!s)body=note;
 else if(path==='/live/peer')body=note+`<h2>First node: Dell Micro 7040 (2016)</h2><p>${peer&&fresh?'Public P2P connection verified':'Public connection awaiting verification'}</p><p>Current peer: <code>${escape(s.peer)}</code></p><p>Enter this in Network → Connect peer. The home connection has a dynamic IP; check this page again if it changes.</p>`;
 else if(path==='/live/recent')body=note+`<ul class="block-mini">${s.blocks.slice(-5).reverse().map(b=>`<li>${bl(b)} <span>${b.tx.length} tx</span></li>`).join('')}</ul><p>${link('/explorer/index.html','Open block explorer')}</p>`;
 else {
  body=note+`<p>${link('/explorer/index.html','Blocks')} | ${link('/explorer/network.html','Network observations')} | ${link('/explorer/addresses/index.html','Addresses')} | ${link('/api/snapshot','Public JSON')}</p>`;
  if(path==='/live/explorer/index.html')body+=`<h1>Block explorer</h1><div class="stats"><div><strong>${s.height}</strong><span>HEIGHT</span></div><div><strong>${s.connections}</strong><span>FIRST-NODE CONNECTIONS</span></div><div><strong>${s.mempool}</strong><span>PENDING TRANSACTIONS</span></div></div>${renderCensus(census)}<form method="get" action="/explorer/search" target="_top"><label>Block height, transaction ID or address <input name="q" maxlength="100" required></label> <button>Find</button></form><div class="scroll"><table><thead><tr><th>Height</th><th>Hash</th><th>Tx</th><th>Block time (UTC)</th></tr></thead><tbody>${s.blocks.slice().reverse().map(b=>`<tr><td>${bl(b)}</td><td class="hash">${link('/explorer/blocks/'+b.height+'.html',b.hash.slice(0,16)+'…')}</td><td>${b.tx.length}</td><td>${utc(b.time*1000)}</td></tr>`).join('')}</tbody></table></div>`;
  else if(/^\/live\/explorer\/blocks\/\d+\.html$/.test(path)){
   const h=Number(path.split('/').at(-1).slice(0,-5)),b=s.blocks.find(b=>b.height===h);
   if(!b){status=404;body+='<h1>Block outside current coverage</h1>';}
   else body+=`<h1>Block #${h}</h1><p class="hash">${b.hash}</p><p>${utc(b.time*1000)} · ${s.height-h+1} confirmations · ${b.size} bytes · bits ${b.bits}</p><p>${h>s.first?link('/explorer/blocks/'+(h-1)+'.html','Previous'):''} | ${h<s.height?link('/explorer/blocks/'+(h+1)+'.html','Next'):''}</p><h2>Transactions</h2><ul>${b.tx.map(t=>'<li class="hash">'+tl(t)+'</li>').join('')}</ul>`;
  }else if(/^\/live\/explorer\/transactions\/[0-9a-f]{64}\.html$/.test(path)){
   const id=path.split('/').at(-1).slice(0,-5),b=s.blocks.find(b=>b.tx.some(t=>t.txid===id)),t=b?.tx.find(t=>t.txid===id);
   if(!t){status=404;body+='<h1>Transaction not in current canonical coverage</h1><p>It may be pending, outside the displayed range, or removed by a reorganization.</p>';}
   else body+=`<h1>Transaction</h1><p class="hash">${id}</p><p>${bl(b)} · ${utc(b.time*1000)} · ${s.height-b.height+1} confirmations</p><h2>Inputs</h2><ul>${t.vin.map(v=>'<li class="hash">'+(v.coinbase?'Mining reward; subject to 100-block maturity':link('/explorer/transactions/'+v.txid+'.html',v.txid+':'+v.vout))+'</li>').join('')}</ul><h2>Outputs</h2><div class="scroll"><table><thead><tr><th>Index</th><th>Address / script</th><th>OBSC</th></tr></thead><tbody>${t.vout.map(v=>`<tr><td>${v.n}</td><td class="hash">${v.address?link('/explorer/addresses/'+v.address+'.html',v.address):escape(v.type)}</td><td>${amount(v.atoms)}</td></tr>`).join('')}</tbody></table></div>`;
  }else if(path.startsWith('/live/explorer/addresses/')){
   const a=path.split('/').at(-1).slice(0,-5);const records=[];
   for(const b of s.blocks)for(const t of b.tx)for(const v of t.vout)if(v.address&&(a==='index'||v.address===a))records.push({b,t,v});
   body+='<h1>Address activity</h1><p>Output history within the displayed range, not a spendable balance.</p>';
   if(a==='index')body+='<ul>'+[...new Set(records.map(r=>r.v.address))].sort().map(a=>'<li class="hash">'+link('/explorer/addresses/'+a+'.html',a)+'</li>').join('')+'</ul>';
   else {if(!records.length)status=404;body+=`<p class="hash">${escape(a)}</p><ul>${records.reverse().map(({b,t,v})=>'<li class="hash">'+bl(b)+' · '+tl(t)+' · '+amount(v.atoms)+' OBSC</li>').join('')}</ul>`;}
  }else{status=404;body+='<h1>Page not found</h1>';}
 }
 return {status,html:`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="15"><title>Obsolete Coin testnet</title><link rel="icon" href="/assets/obsolete-coin.gif" type="image/gif"><link rel="stylesheet" href="/assets/style.css"></head><body class="live-body"><main class="live-content">${body}</main></body></html>`};
}
