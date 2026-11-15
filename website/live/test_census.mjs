import assert from 'node:assert/strict';
import {publicPeer,parseAddresses} from './peers.mjs';
import {probeWith,hash} from './probe-protocol.mjs';
import {GENESIS} from './core.mjs';
import {candidates,selectPeers,updateCensus,publicCensus,renderCensus,LIMIT,RECENT} from './census.mjs';
const peer='8.8.8.8:19777',other='9.9.9.9:19777',now=Date.now();
for(const s of ['127.0.0.1','10.1.2.3','172.16.0.1','172.31.0.1','192.168.1.1','169.254.169.254','100.64.0.1','0.0.0.0','224.0.0.1','255.255.255.255','192.0.2.1','198.51.100.1','203.0.113.1','198.18.0.1','01.2.3.4','256.1.2.3','[::1]','localhost','example.com','2130706433'])assert.equal(publicPeer(s+':19777'),null,s);
for(const s of [peer,other,'172.32.0.1:19777','192.2.3.4:19777'])assert.equal(publicPeer(s),s);
assert.equal(publicPeer('8.8.8.8:19778'),null);
function addr(ip='9.9.9.9',port=19777,stamp=Math.floor(now/1000),services=1n){
 const b=new Uint8Array(31),v=new DataView(b.buffer);b[0]=1;v.setUint32(1,stamp,true);v.setBigUint64(5,services,true);b[23]=255;b[24]=255;b.set(ip.split('.').map(Number),25);v.setUint16(29,port,false);return b;
}
assert.deepEqual(parseAddresses(addr(),now),[other]);
for(const b of [addr('127.0.0.1'),addr('8.8.8.8',19778),addr('8.8.8.8',19777,1),addr('8.8.8.8',19777,Math.floor(now/1000)+601),addr('8.8.8.8',19777,Math.floor(now/1000),0n)])assert.deepEqual(parseAddresses(b,now),[]);
for(const b of [new Uint8Array(),new Uint8Array([254]),new Uint8Array([253,1,0]),new Uint8Array([253,233,3]),new Uint8Array([1])])assert.throws(()=>parseAddresses(b,now));
const header=new Uint8Array(80),hv=new DataView(header.buffer);hv.setInt32(0,1,true);
header.set(Buffer.from('b38882d6af68a402b1a665b9b4ba542b7c13750120b1401705181027329c57f3','hex').reverse(),36);
hv.setUint32(68,1794614400,true);hv.setUint32(72,0x207fffff,true);hv.setUint32(76,2,true);
assert.equal(Buffer.from(await hash(header)).reverse().toString('hex'),GENESIS);
async function message(name,payload=new Uint8Array()){
 const out=new Uint8Array(24+payload.length);out.set([79,66,84,50]);out.set(new TextEncoder().encode(name),4);new DataView(out.buffer).setUint32(16,payload.length,true);out.set((await hash(payload)).slice(0,4),20);out.set(payload,24);return out;
}
const version=new Uint8Array(86);new DataView(version.buffer).setInt32(0,70016,true);new DataView(version.buffer).setBigUint64(4,1n,true);
const headers=new Uint8Array(82);headers[0]=1;headers.set(header,1);
const normal=[await message('version',version),await message('verack'),await message('headers',headers),await message('addr',addr())];
// Simulated P2P transport only: no connection to the public fixture IPs.
function transport(messages,{fragment=false,hang=false}={}){
 let control,closed=false;const sent=[];
 const socket={opened:Promise.resolve(),closed:Promise.resolve(),
 readable:new ReadableStream({start(c){control=c;for(const m of messages){if(fragment)for(const n of m)c.enqueue(new Uint8Array([n]));else c.enqueue(m);}if(!hang){closed=true;c.close();}}}),
 writable:new WritableStream({write(m){sent.push(new TextDecoder().decode(m.slice(4,16)).replace(/\0+$/,''));}}),
 async close(){if(!closed){closed=true;control.close();}}};
 return {connect:()=>socket,sent};
}
for(const messages of [normal,[normal[0],normal[1],normal[3],normal[2]]]){
 const t=transport(messages,{fragment:true}),r=await probeWith(t.connect,peer,GENESIS,{discover:true});
 assert.equal(r.verified,true);assert.deepEqual(r.peers,[other]);assert.ok(t.sent.includes('getaddr'));assert.ok(t.sent.includes('getheaders'));
}
const noAddr=transport(normal.slice(0,3),{hang:true});
assert.equal((await probeWith(noAddr.connect,peer,GENESIS,{discover:true,timeout:30})).verified,true);
await assert.rejects(probeWith(transport([],{hang:true}).connect,peer,GENESIS,{timeout:30}),/timeout/);
await assert.rejects(probeWith(transport(normal.slice(0,2)).connect,peer,GENESIS),/closed/);
const wrongGenesis=headers.slice();wrongGenesis[77]^=1;
await assert.rejects(probeWith(transport([normal[0],normal[1],await message('headers',wrongGenesis)]).connect,peer,GENESIS),/wrong-genesis/);
const wrongMagic=normal[0].slice();wrongMagic[0]^=1;
await assert.rejects(probeWith(transport([wrongMagic]).connect,peer,GENESIS),/wrong-network/);
const wrongChecksum=normal[0].slice();wrongChecksum[20]^=1;
await assert.rejects(probeWith(transport([wrongChecksum]).connect,peer,GENESIS),/checksum/);
const oversized=normal[0].slice(0,24);new DataView(oversized.buffer).setUint32(16,65537,true);
await assert.rejects(probeWith(transport([oversized]).connect,peer,GENESIS),/oversize/);
const noServices=version.slice();new DataView(noServices.buffer).setBigUint64(4,0n,true);
await assert.rejects(probeWith(transport([await message('version',noServices)]).connect,peer,GENESIS),/not-full-node/);
await assert.rejects(probeWith(()=>{throw Error('must not connect');},'127.0.0.1:19777',GENESIS),/endpoint/);
let list=candidates(null,peer,now),r=updateCensus(list,[{peer,verified:true,peers:[other,other,'127.0.0.1:19777']}],now);
assert.equal(r.nodes.length,2);assert.equal(publicCensus(r,now).count,1);assert.equal(publicCensus(r,now).checkedRecently,1);
assert.ok(!JSON.stringify(publicCensus(r,now)).includes(peer));assert.ok(!JSON.stringify(publicCensus(r,now)).includes(other));
r=updateCensus(r.nodes,[{peer:other,verified:true}],now+1);assert.equal(publicCensus(r,now+1).count,2);
r=updateCensus(r.nodes,[{peer,verified:false}],now+2);assert.equal(publicCensus(r,now+2).count,1);
assert.equal(publicCensus(r,now+RECENT+3).count,0);assert.equal(publicCensus(r,now+RECENT+3).fresh,false);
assert.match(renderCensus(publicCensus(r,now+RECENT+3)),/STALE MONITOR/);assert.match(renderCensus(null),/Awaiting/);
const many=Array.from({length:1000},(_,i)=>'11.1.'+Math.floor(i/256)+'.'+i%256+':19777');
r=updateCensus(list,[{peer,verified:true,peers:many}],now);assert.equal(r.nodes.length,LIMIT);assert.equal(r.capped,true);
assert.equal(candidates(r,other,now)[0].peer,other);
assert.equal(selectPeers(r.nodes,peer).length,4);
const chosen=selectPeers(r.nodes,peer).slice(1);for(const n of chosen)n.checked=now;
assert.ok(selectPeers(r.nodes,peer).slice(1).every(n=>!chosen.includes(n)));
assert.equal(candidates(r,peer,now+86400001).length,1);
console.log('Public-node tests passed: address filtering, P2P handshake/genesis, fragmentation, deadlines, failures, discovery, deduplication, expiry, privacy, cap and fair rotation.');
