// Only literal public IPv4 mainnet endpoints; no DNS, redirects or arbitrary ports.
export function publicPeer(value) {
 if (typeof value !== 'string' || !/^(\d{1,3}\.){3}\d{1,3}:19777$/.test(value)) return null;
 const [host] = value.split(':'), p = host.split('.').map(Number);
 if (p.some((n,i) => n>255 || String(n)!==host.split('.')[i])) return null;
 const [a,b,c] = p;
 if (a===0 || a===10 || a===127 || a>=224 || (a===100 && b>=64 && b<=127) ||
     (a===169 && b===254) || (a===172 && b>=16 && b<=31) ||
     (a===192 && (b===168 || b===0 || (b===88 && c===99))) ||
     (a===198 && (b===18 || b===19 || (b===51 && c===100))) ||
     (a===203 && b===0 && c===113)) return null;
 return value;
}
export function parseAddresses(payload, now=Date.now()) {
 // Legacy addr (we do not request addrv2): CompactSize followed by 30-byte records.
 if (!payload.length) throw Error('addr-size');
 let count=payload[0], offset=1;
 if (count===253) {
  if(payload.length<3)throw Error('addr-size');
  count=payload[1]+256*payload[2];offset=3;
  if(count<253)throw Error('addr-size');
 } else if(count>253)throw Error('addr-size');
 if(count>1000 || payload.length!==offset+30*count)throw Error('addr-size');
 const peers=new Set(), v=new DataView(payload.buffer,payload.byteOffset,payload.byteLength);
 for(let i=0;i<count;i++) {
  const k=offset+i*30, stamp=v.getUint32(k,true)*1000, services=v.getBigUint64(k+4,true);
  if(stamp<now-30*86400000 || stamp>now+600000 || !(services&1025n))continue;
  if(!payload.slice(k+12,k+22).every(n=>n===0) || payload[k+22]!==255 || payload[k+23]!==255)continue;
  const peer=publicPeer(Array.from(payload.slice(k+24,k+28)).join('.')+':'+v.getUint16(k+28,false));
  if(peer)peers.add(peer);
 }
 return [...peers];
}
