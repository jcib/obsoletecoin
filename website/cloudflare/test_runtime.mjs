import assert from 'node:assert/strict';
import {createHmac} from 'node:crypto';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
const base=process.argv[2]||'http://127.0.0.1:8766';if(!new URL(base).hostname.match(/^(127\.0\.0\.1|localhost)$/))throw Error('Disposable local test target required');let cookie='';const report=[];
async function get(path){const r=await fetch(base+path,{headers:cookie?{Cookie:cookie}:{}});if(r.headers.get('set-cookie'))cookie=r.headers.get('set-cookie').split(';')[0];return {r,html:await r.text()};}
async function form(path){const {r,html}=await get(path);assert.equal(r.status,200);return html.match(/name="ticket" value="([^"]+)"/)[1];}
async function post(path,ticket,extra={},origin=base){return fetch(base+path,{method:'POST',redirect:'manual',headers:{Cookie:cookie,Origin:origin,'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({ticket,alias:'Test alias',body:'Test reply',...extra})});}
const page=await get('/forum');assert.equal(page.r.status,200);assert.ok(page.html.includes('No topics yet'));
const token=await form('/forum/new');assert.equal((await post('/forum/new',token,{title:'Forged'},'https://evil.example')).status,403);report.push('cross-origin rejected');
assert.equal((await post('/forum/new','bad',{title:'Bad token'})).status,403);report.push('forged form rejected');
assert.equal((await post('/forum/new',token,{title:'Spam trap',website:'spam'})).status,403);report.push('honeypot rejected');
assert.equal((await post('/forum/new',token,{title:'x',body:'bad'})).status,400);report.push('length validation');
let r=await post('/forum/new',token,{title:'Test <script>alert(1)</script>',alias:"alias' OR 1=1 --",body:'First post <img src=x onerror=alert(1)>\nSecond line'});assert.equal(r.status,303);const thread=r.headers.get('location').split('?')[0];report.push('topic created');
let detail=await get(thread);assert.equal(detail.r.status,200);assert.ok(detail.html.includes('&lt;img'));assert.ok(!detail.html.includes('<script>alert'));assert.ok(detail.html.includes("alias&#39; OR 1=1 --"));report.push('HTML and SQL payloads rendered as text');
assert.equal((await post('/forum/new',token,{title:'Duplicate'})).status,429);report.push('duplicate submission rejected');
let t=await form(thread);assert.equal((await post(thread,t)).status,429);report.push('rapid posting rejected');
await new Promise(resolve=>setTimeout(resolve,10500));r=await post(thread,t,{alias:'Reply tester',body:'Confirmed reply.'});assert.equal(r.status,303);detail=await get(thread);assert.ok(detail.html.includes('Confirmed reply.'));assert.ok(detail.html.includes('Reply tester'));report.push('reply stored and readable');
const list=await get('/forum');assert.ok(list.html.includes('Test &lt;script&gt;'));report.push('topic list updated');
const fake='/forum/thread/00000000-0000-0000-0000-000000000000';assert.equal((await get(fake)).r.status,404);
const snapshot=JSON.parse(await readFile(process.argv[3]));snapshot.observed=Date.now();
async function feed(s,key='local-test-only'){const body=JSON.stringify(s),stamp=String(Math.floor(Date.now()/1000)),sig=createHmac('sha256',key).update(stamp+'\n/api/feed\n'+body).digest('hex');return fetch(base+'/api/feed',{method:'POST',headers:{'X-Obsolete-Time':stamp,'X-Obsolete-Signature':sig},body});}
assert.equal((await feed(snapshot,'wrong')).status,401);assert.equal((await feed(snapshot)).status,200);assert.equal((await feed(snapshot)).status,409);report.push('D1 feed authentication and replay checks');
snapshot.observed=Date.now()+1;snapshot.blocks.pop();snapshot.height--;snapshot.tip=snapshot.blocks.at(-1).hash;assert.equal((await feed(snapshot)).status,200);assert.equal((await (await fetch(base+'/api/snapshot')).json()).height,snapshot.height);report.push('canonical chain reorganization replaces D1 feed');
const home=await get('/');assert.ok(!/unsigned|<audio|music\.mp3|Memories OST/i.test(home.html));assert.ok(home.html.includes('forum.gif'));
console.log(JSON.stringify({passed:true,checks:report}));
