const enc=new TextEncoder();
export const SESSION_MS=3600000, FORM_MS=900000;
export const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const hex=b=>Array.from(new Uint8Array(b),x=>x.toString(16).padStart(2,'0')).join('');
export const digest=async s=>hex(await crypto.subtle.digest('SHA-256',enc.encode(s)));
export async function mac(secret,text){
 const key=await crypto.subtle.importKey('raw',enc.encode(secret),{name:'HMAC',hash:'SHA-256'},false,['sign']);
 return hex(await crypto.subtle.sign('HMAC',key,enc.encode(text)));
}
export async function verify(secret,text,sig){
 if(!/^[0-9a-f]{64}$/.test(sig||''))return false;
 const key=await crypto.subtle.importKey('raw',enc.encode(secret),{name:'HMAC',hash:'SHA-256'},false,['verify']);
 return crypto.subtle.verify('HMAC',key,Uint8Array.from(sig.match(/../g),x=>parseInt(x,16)),enc.encode(text));
}
export const cookie=(req,name)=>(req.headers.get('Cookie')||'').split(';').map(x=>x.trim()).find(x=>x.startsWith(name+'='))?.slice(name.length+1)||'';
export const setCookie=(name,value,age)=>name+'='+value+'; Path=/forum/admin; Max-Age='+age+'; HttpOnly; Secure; SameSite=Strict';
export async function sealed(secret,purpose,id,expiry){
 const value=id+'.'+expiry;return value+'.'+await mac(secret,purpose+'|'+value);
}
export async function openSeal(secret,purpose,value,lifetime,now=Date.now()){
 const parts=value.split('.');if(parts.length!==3)return null;
 const [id,exp,sig]=parts;
 if(!uuid.test(id)||!/^\d{13}$/.test(exp)||Number(exp)<=now||Number(exp)>now+lifetime)return null;
 return await verify(secret,purpose+'|'+id+'.'+exp,sig)?{id,expiry:Number(exp)}:null;
}
export async function currentAdmin(req,env,now=Date.now()){
 const parsed=await openSeal(env.FORUM_ADMIN_AUTH,'admin-session',cookie(req,'obca'),SESSION_MS,now);
 if(!parsed)return null;
 const hash=await digest(parsed.id),row=await env.DB.prepare('SELECT expires FROM forum_admin_sessions WHERE id_hash=? AND expires>?').bind(hash,now).first();
 return row&&row.expires===parsed.expiry?{...parsed,hash}:null;
}
export async function formTicket(secret,sid,path,action,now=Date.now()){
 const data=crypto.randomUUID()+'.'+(now+FORM_MS);
 return data+'.'+await mac(secret,'admin-form|'+sid+'|'+path+'|'+action+'|'+data);
}
export async function validForm(secret,sid,path,action,value,now=Date.now()){
 const parts=value.split('.');if(parts.length!==3)return null;
 const [nonce,expiry,sig]=parts;
 if(!uuid.test(nonce)||!/^\d{13}$/.test(expiry)||Number(expiry)<=now||Number(expiry)>now+FORM_MS)return null;
 return await verify(secret,'admin-form|'+sid+'|'+path+'|'+action+'|'+nonce+'.'+expiry,sig)?nonce:null;
}
export async function readForm(req,max=4096){
 if(!(req.headers.get('Content-Type')||'').startsWith('application/x-www-form-urlencoded'))throw Error('form-type');
 const reader=req.body?.getReader();if(!reader)throw Error('form-empty');
 let size=0;const chunks=[];
 while(true){const {value,done}=await reader.read();if(done)break;size+=value.length;if(size>max){await reader.cancel();throw Error('form-size');}chunks.push(value);}
 const bytes=new Uint8Array(size);let offset=0;for(const c of chunks){bytes.set(c,offset);offset+=c.length;}
 const f=new URLSearchParams(new TextDecoder().decode(bytes));
 if([...f.keys()].some(k=>f.getAll(k).length!==1))throw Error('form-duplicate');
 return f;
}
export async function loginAllowed(req,env,now){
 const bucket=Math.floor(now/900000),ip=req.headers.get('CF-Connecting-IP')||'local-preview';
 const tag=await mac(env.FORUM_ADMIN_AUTH,'admin-login-rate|'+Math.floor(now/86400000)+'|'+ip);
 const rate=(tag,cap)=>env.DB.prepare('INSERT INTO forum_admin_limits(tag,bucket,count,cap,last_at) VALUES(?,?,1,?,?) ON CONFLICT(tag) DO UPDATE SET count=CASE WHEN bucket<>? THEN 1 ELSE count+1 END,bucket=?,last_at=?').bind(tag,bucket,cap,now,bucket,bucket,now);
 try{
  await env.DB.batch([env.DB.prepare('DELETE FROM forum_admin_limits WHERE last_at<?').bind(now-172800000),rate(tag,10),rate('site',100)]);
  return true;
 }catch{return false;}
}
