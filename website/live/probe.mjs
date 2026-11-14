import { connect } from 'cloudflare:sockets';
const magic=new Uint8Array([0x4f,0x42,0x54,0x32]);
const enc=new TextEncoder();
async function hash(b){return new Uint8Array(await crypto.subtle.digest('SHA-256',await crypto.subtle.digest('SHA-256',b)));}
export async function probePeer(peer,genesis){
 const [host,port]=peer.split(':');if(port!=='19777')throw Error('port');
 const socket=connect({hostname:host,port:19777});const reader=socket.readable.getReader(),writer=socket.writable.getWriter();let pending=new Uint8Array();
 const timer=setTimeout(()=>{socket.close().catch(()=>{});},12000);
 async function read(n){while(pending.length<n){const r=await reader.read();if(r.done)throw Error('closed');const merged=new Uint8Array(pending.length+r.value.length);merged.set(pending);merged.set(r.value,pending.length);pending=merged;if(pending.length>4194328)throw Error('oversize');}const out=pending.slice(0,n);pending=pending.slice(n);return out;}
 async function send(name,payload=new Uint8Array()) {const m=new Uint8Array(24+payload.length);m.set(magic);m.set(enc.encode(name),4);new DataView(m.buffer).setUint32(16,payload.length,true);m.set((await hash(payload)).slice(0,4),20);m.set(payload,24);await writer.write(m);}
 try{
  await socket.opened;const version=new Uint8Array(86),v=new DataView(version.buffer);v.setInt32(0,70016,true);v.setBigInt64(12,BigInt(Math.floor(Date.now()/1000)),true);crypto.getRandomValues(version.subarray(72,80));version[80]=0;v.setInt32(81,0,true);version[85]=0;
  await send('version',version);let seenVersion=false,requested=false;
  for(let i=0;i<40;i++){
   const h=await read(24);if(!magic.every((x,i)=>h[i]===x))throw Error('wrong-network');const size=new DataView(h.buffer,h.byteOffset,h.byteLength).getUint32(16,true);if(size>4194304)throw Error('oversize');
   const payload=await read(size),digest=await hash(payload);if(!digest.slice(0,4).every((x,i)=>x===h[20+i]))throw Error('checksum');const name=new TextDecoder().decode(h.slice(4,16)).replace(/\0+$/,'');
   if(name==='version'){seenVersion=true;await send('verack');}
   else if(name==='verack'&&seenVersion){const q=new Uint8Array(37);new DataView(q.buffer).setUint32(0,70016,true);q[4]=0;q.set(Uint8Array.from(genesis.match(/../g).reverse(),x=>parseInt(x,16)),5);await send('getheaders',q);requested=true;}
   else if(name==='ping'&&size===8)await send('pong',payload);
   else if(name==='headers'&&requested){if(size!==82||payload[0]!==1||payload[81]!==0)throw Error('headers');const id=Array.from(await hash(payload.slice(1,81))).reverse().map(x=>x.toString(16).padStart(2,'0')).join('');if(id!==genesis)throw Error('wrong-genesis');return {verified:true,peer,genesis:id,checked:Date.now()};}
  }throw Error('no-genesis');
 }finally{clearTimeout(timer);try{reader.releaseLock();writer.releaseLock();await socket.close();}catch{}}
}
