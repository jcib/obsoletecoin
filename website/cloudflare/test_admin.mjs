import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {resolve} from 'node:path';
import {readFile} from 'node:fs/promises';
import {digest,sealed,formTicket} from './admin-auth.mjs';
const require=createRequire(resolve(process.argv[2],'package.json'));
const {Miniflare,convertV4MiniflareOptions}=require('miniflare');
const password='A'.repeat(43),secret=await digest(password),base='http://localhost';
const mf=new Miniflare(convertV4MiniflareOptions({modules:true,scriptPath:resolve(process.argv[3]||'.local/pages-dist/_worker.js'),compatibilityDate:'2026-11-10',d1Databases:['DB'],
 bindings:{SITE_ORIGIN:base,FORUM_SECRET:'test-forum-only',FORUM_ADMIN_AUTH:secret,NODE_CENSUS_ENABLED:'false'},port:0,host:'127.0.0.1'}));
const req=(path,options)=>mf.dispatchFetch(base+path,{redirect:'manual',...options});
const cookies=r=>r.headers.getSetCookie().map(c=>c.split(';')[0]).join('; ');
const ticket=html=>html.match(/name="ticket" value="([^"]+)"/)?.[1];
const post=(path,body,cookie='',extra={})=>req(path,{method:'POST',headers:{Origin:base,'Content-Type':'application/x-www-form-urlencoded',Cookie:cookie,...extra},body:new URLSearchParams(body)});
const thread=crypto.randomUUID(),postId=crypto.randomUUID(),second=crypto.randomUUID(),t2=crypto.randomUUID();
let db,adminCookie,loginCookie,loginTicket;
async function action(path,label,custom={}){
 const r=await req(path.startsWith('/forum/admin/post/')?'/forum/admin/thread/'+thread:path,{headers:{Cookie:adminCookie}});
 const html=await r.text();
 const forms=[...html.matchAll(/<form class="admin-action"[\s\S]*?<\/form>/g)].map(x=>x[0]);
 const f=forms.find(f=>f.includes('>'+label+'</button>'));assert.ok(f,label);
 const target=f.match(/action="([^"]+)"/)[1],value=f.match(/name="action" value="([^"]+)"/)[1];
 return {response:await post(target,{action:value,ticket:ticket(f),...custom},adminCookie),target,value,token:ticket(f)};
}
try{
 await mf.ready;db=await mf.getD1Database('DB');
 const schema=await readFile('website/cloudflare/schema.sql','utf8');
 let trigger=[];
 for(const line of schema.split(/\\r?\\n/)){
  if(!line.trim())continue;
  if(line.startsWith('CREATE TRIGGER')||trigger.length){
   trigger.push(line);
   if(line.trim()==='END;'){await db.prepare(trigger.join(' ')).run();trigger=[];}
  }else await db.prepare(line).run();
 }
 const now=Date.now();
 await db.prepare('INSERT INTO forum_threads(id,title,created_at,updated_at) VALUES(?,?,?,?)').bind(thread,'Example <script>alert(1)</script>',now,now).run();
 await db.prepare('INSERT INTO forum_posts(id,thread_id,alias,body,created_at) VALUES(?,?,?,?,?)').bind(postId,thread,'OriginalAliasUnique','OriginalBodyUnique <img src=x onerror=evil>',now).run();
 await db.prepare('INSERT INTO forum_posts(id,thread_id,alias,body,created_at) VALUES(?,?,?,?,?)').bind(second,thread,'ReplyAliasUnique','ReplyBodyUnique',now+1).run();
 await db.prepare('INSERT INTO forum_threads(id,title,created_at,updated_at) VALUES(?,?,?,?)').bind(t2,'Another topic',now,now).run();
 assert.equal((await req('/forum/admin')).status,303);
 assert.equal((await post('/forum/admin/thread/'+thread,{action:'hide'},'obcf=admin')).status,401);
 assert.equal((await mf.dispatchFetch('https://untrusted.example/forum/admin/login')).status,403);
 let r=await req('/forum/admin/login');loginCookie=cookies(r);const html=await r.text();loginTicket=ticket(html);
 assert.ok(r.headers.get('cache-control').includes('no-store'));assert.equal(r.headers.get('x-frame-options'),'DENY');assert.equal(r.headers.get('referrer-policy'),'same-origin');
 assert.match(r.headers.get('set-cookie'),/HttpOnly; Secure; SameSite=Strict/);
 assert.equal((await post('/forum/admin/login',{ticket:loginTicket,password},loginCookie,{Origin:'https://evil.example'})).status,403);
 assert.equal((await post('/forum/admin/login',{ticket:'forged',password},loginCookie)).status,403);
 assert.equal((await post('/forum/admin/login',{ticket:loginTicket,password:'wrong'},loginCookie)).status,401);
 r=await post('/forum/admin/login',{ticket:loginTicket,password},loginCookie);assert.equal(r.status,303);adminCookie=cookies(r).split('; ').find(x=>x.startsWith('obca='));
 assert.equal((await post('/forum/admin/login',{ticket:loginTicket,password},loginCookie)).status,403);
 assert.equal((await req('/forum/admin',{headers:{Cookie:adminCookie}})).status,200);
 assert.equal((await req('/forum/admin',{headers:{Cookie:adminCookie+'x'}})).status,303);
 r=await req('/forum/admin/thread/'+thread,{headers:{Cookie:adminCookie}});
 assert.ok((await r.text()).includes('&lt;script&gt;'));
 const initialPublic=await req('/forum/thread/'+thread),publicCookie=cookies(initialPublic),publicTicket=ticket(await initialPublic.text());
 assert.equal((await action('/forum/admin/thread/'+thread,'Close topic')).response.status,303);
 assert.match(await (await req('/forum/thread/'+thread)).text(),/This topic is closed/);
 assert.equal((await post('/forum/thread/'+thread,{ticket:publicTicket,alias:'reader',body:'Cannot post here'},publicCookie)).status,429);
 assert.equal((await action('/forum/admin/thread/'+thread,'Reopen topic')).response.status,303);
 assert.ok(!(await (await req('/forum/thread/'+thread)).text()).includes('This topic is closed'));
 const hidden=await action('/forum/admin/post/'+postId,'Hide message');
 assert.equal(hidden.response.status,303);
 let body=await (await req('/forum/thread/'+thread)).text();
 assert.ok(!body.includes('OriginalBodyUnique'));assert.ok(!body.includes('OriginalAliasUnique'));assert.ok(body.includes('hidden by a moderator'));
 assert.ok(!(await (await req('/forum')).text()).includes('OriginalAliasUnique'));
 assert.ok((await (await req('/forum/admin/thread/'+thread,{headers:{Cookie:adminCookie}})).text()).includes('OriginalBodyUnique'));
 assert.equal((await post(hidden.target,{ticket:hidden.token,action:hidden.value},adminCookie)).status,409);
 assert.equal((await post(hidden.target,{ticket:hidden.token,action:'restore'},adminCookie)).status,403);
 assert.equal((await action('/forum/admin/post/'+postId,'Restore message')).response.status,303);
 assert.ok((await (await req('/forum/thread/'+thread)).text()).includes('OriginalBodyUnique'));
 assert.equal((await action('/forum/admin/thread/'+thread,'Hide topic')).response.status,303);
 assert.equal((await req('/forum/thread/'+thread)).status,404);
 assert.ok(!(await (await req('/forum')).text()).includes('Example &lt;script'));
 assert.equal((await action('/forum/admin/thread/'+thread,'Restore topic')).response.status,303);
 assert.equal((await req('/forum/thread/'+thread)).status,200);
 assert.equal((await req('/forum/admin/thread/'+thread+'?action=hide',{headers:{Cookie:adminCookie}})).status,200);
 assert.equal((await req('/forum/thread/'+thread)).status,200);
 const adminPage=await req('/forum/admin',{headers:{Cookie:adminCookie}});
 const logoutForm=(await adminPage.text()).match(/<form class="admin-action"[\s\S]*?<\/form>/)[0];
 const logout={action:'logout',ticket:ticket(logoutForm)};
 assert.equal((await post('/forum/admin/logout',logout,adminCookie,{Origin:'https://evil.example'})).status,403);
 assert.equal((await post('/forum/admin/logout',logout,adminCookie)).status,303);
 assert.equal((await req('/forum/admin',{headers:{Cookie:adminCookie}})).status,303);
 assert.equal((await db.prepare('SELECT COUNT(*) AS n FROM forum_admin_audit').first()).n,6);
 assert.equal((await db.prepare('SELECT COUNT(*) AS n FROM forum_posts').first()).n,2);
 // Expired sessions remain invalid even if a stale row exists in storage.
 const sid=crypto.randomUUID(),expires=Date.now()-1000;
 await db.prepare('INSERT INTO forum_admin_sessions VALUES(?,?)').bind(await digest(sid),expires).run();
 const stale='obca='+await sealed(secret,'admin-session',sid,expires);
 assert.equal((await req('/forum/admin',{headers:{Cookie:stale}})).status,303);
 // Concurrent failed logins cannot bypass the per-network attempt cap.
 r=await req('/forum/admin/login');const cc=cookies(r),tt=ticket(await r.text());
 const attempts=await Promise.all(Array.from({length:15},()=>post('/forum/admin/login',{ticket:tt,password:'incorrect'},cc,{'CF-Connecting-IP':'198.51.100.99'})));
 assert.equal(attempts.filter(r=>r.status===401).length,10);assert.equal(attempts.filter(r=>r.status===429).length,5);
 const limits=await db.prepare('SELECT tag FROM forum_admin_limits').all();assert.ok(!JSON.stringify(limits).includes('198.51.100.99'));
 r=await post('/forum/admin/login',{ticket:tt,password:'A'.repeat(5000)},cc);assert.equal(r.status,400);
 console.log('Admin Workerd/D1 tests passed: authentication, origin/host checks, secure cookies, one-use forms, XSS escaping, hide/restore, close/reopen, public-content privacy, audit, logout revocation, expiry and concurrent login limits.');
}finally{await mf.dispose();}
