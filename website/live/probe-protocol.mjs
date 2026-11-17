import {publicPeer,parseAddresses} from './peers.mjs';
const magic=new Uint8Array([0x4f,0x42,0x53,0x32]), enc=new TextEncoder();
export async function hash(b){return new Uint8Array(await crypto.subtle.digest('SHA-256',await crypto.subtle.digest('SHA-256',b)));}
export async function probeWith(connect,peer,genesis,{discover=false,timeout=10000}={}) {
 if(!publicPeer(peer) || !/^[0-9a-f]{64}$/.test(genesis))throw Error('endpoint');
 const socket=connect({hostname:peer.split(':')[0],port:19777});
 const reader=socket.readable.getReader(),writer=socket.writable.getWriter();
 let pending=new Uint8Array(),verified=false,checked=null,peers=[],seenAddresses=false,total=0;
 const result=()=>({verified:true,peer,genesis,checked,...(discover?{peers}: {})});
 let timer;
 const deadline=new Promise((_,reject)=>{timer=setTimeout(()=>{reject(Error('timeout'));socket.close().catch(()=>{});},timeout);});
 socket.closed?.catch(()=>{});
 async function read(n){
  while(pending.length<n){
   const r=await reader.read();if(r.done)throw Error('closed');
   total+=r.value.length;if(total>262144)throw Error('oversize');
   const merged=new Uint8Array(pending.length+r.value.length);merged.set(pending);merged.set(r.value,pending.length);pending=merged;
  }
  const out=pending.slice(0,n);pending=pending.slice(n);return out;
 }
 async function send(name,payload=new Uint8Array()){
  const m=new Uint8Array(24+payload.length);m.set(magic);m.set(enc.encode(name),4);
  new DataView(m.buffer).setUint32(16,payload.length,true);m.set((await hash(payload)).slice(0,4),20);m.set(payload,24);await writer.write(m);
 }
 async function exchange(){
  await socket.opened;
  const version=new Uint8Array(86),v=new DataView(version.buffer);
  v.setInt32(0,70016,true);v.setBigInt64(12,BigInt(Math.floor(Date.now()/1000)),true);
  crypto.getRandomValues(version.subarray(72,80));version[85]=0;
  await send('version',version);
  let seenVersion=false,requested=false;
  for(let i=0;i<40;i++){
   const h=await read(24);if(!magic.every((x,i)=>h[i]===x))throw Error('wrong-network');
   const size=new DataView(h.buffer,h.byteOffset,h.byteLength).getUint32(16,true);
   if(size>65536)throw Error('oversize');
   const payload=await read(size),digest=await hash(payload);
   if(!digest.slice(0,4).every((x,i)=>x===h[20+i]))throw Error('checksum');
   const name=new TextDecoder().decode(h.slice(4,16)).replace(/\0+$/,'');
   if(name==='version'){
    if(seenVersion||size<85)throw Error('version');
    const pv=new DataView(payload.buffer,payload.byteOffset,payload.byteLength);
    if(pv.getInt32(0,true)<70001 || !(pv.getBigUint64(4,true)&1025n))throw Error('not-full-node');
    seenVersion=true;await send('verack');
   } else if(name==='verack'&&seenVersion&&!requested){
    const q=new Uint8Array(37);new DataView(q.buffer).setUint32(0,70016,true);
    q.set(Uint8Array.from(genesis.match(/../g).reverse(),x=>parseInt(x,16)),5);
    await send('getheaders',q);if(discover)await send('getaddr');requested=true;
   } else if(name==='ping'&&size===8)await send('pong',payload);
   else if(name==='addr'&&requested&&discover){
    peers=[...new Set([...peers,...parseAddresses(payload)])].slice(0,1000);seenAddresses=true;
    if(verified)return result();
   } else if(name==='headers'&&requested&&!verified){
    if(size!==82||payload[0]!==1||payload[81]!==0)throw Error('headers');
    const id=Array.from(await hash(payload.slice(1,81))).reverse().map(x=>x.toString(16).padStart(2,'0')).join('');
    if(id!==genesis)throw Error('wrong-genesis');
    verified=true;checked=Date.now();if(!discover||seenAddresses)return result();
   }
  }
  if(verified)return result();throw Error('no-genesis');
 }
 try{return await Promise.race([exchange(),deadline]);}
 catch(e){
  // An otherwise verified node need not provide an address list.
  if(verified && ['timeout','closed'].includes(e.message))return result();
  throw e;
 } finally {
  clearTimeout(timer);
  try{await socket.close();}catch{}
  try{reader.releaseLock();writer.releaseLock();}catch{}
 }
}
