import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {validate,render,amount,authorized} from './core.mjs';
const fixture={height:0,hash:'39edafd04ad371911d1d17c38c40d16878b550489bc3df92530a7c813b0de133',previous:'0'.repeat(64),time:1794960000,bits:'1f014000',size:219,tx:[{txid:'a'.repeat(64),vin:[{coinbase:true}],vout:[{n:0,atoms:'0',address:'',type:'nulldata'}]}]}; const feed={network:'obsolete',genesis:fixture.hash,observed:Date.now(),height:1,first:0,tip:'1'.repeat(64),connections:1,mempool:0,peer:'83.45.159.127:19777',blocks:[fixture,{...structuredClone(fixture),height:1,hash:'1'.repeat(64),previous:fixture.hash}]};
assert.equal(validate(feed).height,1);assert.equal(amount('100000000000000000'),'1,000,000,000.00000000');
for(const mutate of [s=>s.genesis='0'.repeat(64),s=>s.blocks[1].previous='0'.repeat(64),s=>s.tip='0'.repeat(64),s=>s.height++,s=>s.observed-=121000,s=>s.peer='127.0.0.1:19777',s=>s.blocks[0].tx[0].vout[0].atoms='1e10',s=>s.blocks[0].tx[0].vout[0].address='<script>']){
 const bad=structuredClone(feed);mutate(bad);assert.throws(()=>validate(bad));
}
const extra=structuredClone(feed);extra.rpcpassword='private';extra.blocks[0].tx[0].privateKey='private';assert.ok(!JSON.stringify(validate(extra)).includes('private'));
assert.match(render(feed,'/live/recent').html,/LIVE MAINNET DATA/);assert.match(render(feed,'/live/recent',feed.observed+61000).html,/STALE DATA/);
assert.match(render(null,'/live/recent').html,/UNAVAILABLE/);assert.equal(render(feed,'/live/explorer/blocks/99999.html').status,404);
const shorter=structuredClone(feed);shorter.blocks.pop();shorter.height--;shorter.tip=shorter.blocks.at(-1).hash;assert.equal(validate(shorter).height,0);
const key='test-only-key';const body=new TextEncoder().encode(JSON.stringify(feed));const stamp=String(Math.floor(Date.now()/1000));
const k=await crypto.subtle.importKey('raw',new TextEncoder().encode(key),{name:'HMAC',hash:'SHA-256'},false,['sign']);
const bytes=new TextEncoder().encode(stamp+'\n/api/feed\n'+new TextDecoder().decode(body));
const sig=Buffer.from(await crypto.subtle.sign('HMAC',k,bytes)).toString('hex');const req=new Request('https://example.test/api/feed',{headers:{'X-Obsolete-Time':stamp,'X-Obsolete-Signature':sig}});
assert.ok(await authorized(req,key,body));assert.ok(!await authorized(req,'wrong',body));assert.ok(!await authorized(req,key,body,Date.now()+121000));
assert.ok(!await authorized(new Request('https://example.test/api/probe',{headers:req.headers}),key,body));
console.log('Core validation, reorg, amounts, stale data, escaping and authentication checks passed.');
