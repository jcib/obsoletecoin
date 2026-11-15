import {escape,utc} from '../live/core.mjs';
import {SESSION_MS,FORM_MS,uuid,digest,mac,verify,cookie,setCookie,sealed,openSeal,currentAdmin,formTicket,validForm,readForm,loginAllowed} from './admin-auth.mjs';
const ROOT='/forum/admin',LOGIN=ROOT+'/login';
const pageNumber=url=>/^[1-9][0-9]{0,3}$/.test(url.searchParams.get('page')||'')?Number(url.searchParams.get('page')):1;
const pager=(path,n,more)=>'<nav class="forum-pager">'+(n>1?'<a href="'+path+'?page='+(n-1)+'">Previous page</a>':'<span></span>')+(more?'<a href="'+path+'?page='+(n+1)+'">Next page</a>':'')+'</nav>';
export async function admin(req,env,template,baseHeaders){
 const url=new URL(req.url),path=url.pathname.replace(/\/$/,''),now=Date.now();
 const headers={...baseHeaders,'Cache-Control':'no-store, private','Referrer-Policy':'same-origin','X-Robots-Tag':'noindex, nofollow','X-Frame-Options':'DENY',
  'Content-Security-Policy':baseHeaders['Content-Security-Policy'].replace("frame-ancestors 'self'","frame-ancestors 'none'")};
 const respond=(html,status=200,cookies=[])=>{
  const h=new Headers({...headers,'Content-Type':'text/html; charset=utf-8'});for(const c of cookies)h.append('Set-Cookie',c);
  return new Response(req.method==='HEAD'?null:template.replace('<meta name="referrer" content="no-referrer">','<meta name="referrer" content="same-origin">').replace('<!--FORUM_CONTENT-->',html),{status,headers:h});
 };
 const redirect=(to,cookies=[])=>{const h=new Headers({...headers,Location:to});for(const c of cookies)h.append('Set-Cookie',c);return new Response(null,{status:303,headers:h});};
 if(!/^[0-9a-f]{64}$/.test(env.FORUM_ADMIN_AUTH||'')||!env.DB)return respond('<h1>Administration unavailable</h1>',503);
 // Production credentials are never accepted on deployment aliases or other hosts.
 if(url.origin!==env.SITE_ORIGIN)return respond('<h1>Use the main website</h1><p><a href="https://obsoletecoin.pages.dev/forum/admin">Open administration</a></p>',403);
 if(!['GET','HEAD','POST'].includes(req.method))return respond('<h1>Method not allowed</h1>',405);
 const loginPage=async(message='',status=200)=>{
  const token=await sealed(env.FORUM_ADMIN_AUTH,'admin-login',crypto.randomUUID(),now+FORM_MS);
  return respond('<h1 class="page-title">Forum administration</h1><p><a href="/forum">Back to forum</a></p>'+message+
   '<form class="forum-form paper" method="post" action="'+LOGIN+'"><input type="hidden" name="ticket" value="'+token+'"><label for="admin-password">Administrator password</label><input id="admin-password" name="password" type="password" maxlength="128" autocomplete="current-password" required><button type="submit">Sign in</button></form><p>Forum aliases do not grant administrator access.</p>',status,[setCookie('obca_login',token,900)]);
 };
 if(path===LOGIN){
  if(req.method!=='POST')return await loginPage();
  if(req.headers.get('Origin')!==url.origin)return respond('<h1>Form rejected</h1>',403);
  let f;try{f=await readForm(req);}catch{return respond('<h1>Invalid form</h1>',400);}
  const pre=cookie(req,'obca_login');
  if(f.get('ticket')!==pre||!await openSeal(env.FORUM_ADMIN_AUTH,'admin-login',pre,FORM_MS,now))return respond('<h1>Form expired</h1><p><a href="'+LOGIN+'">Sign in again</a></p>',403);
  if(!await loginAllowed(req,env,now))return respond('<h1>Too many sign-in attempts</h1><p>Wait 15 minutes before trying again.</p>',429);
  const password=f.get('password')||'';
  // Deployment generates a random 256-bit password, never a human-chosen password.
  const supplied=await digest(password),challenge=crypto.randomUUID();
  if(!/^[A-Za-z0-9_-]{43}$/.test(password)||!await verify(env.FORUM_ADMIN_AUTH,challenge,await mac(supplied,challenge)))return await loginPage('<p>Sign-in failed.</p>',401);
  const id=crypto.randomUUID(),expiry=now+SESSION_MS,hash=await digest(id);
  const loginNonce=pre.split('.')[0];
  try{
   await env.DB.batch([
    env.DB.prepare('DELETE FROM forum_admin_sessions WHERE expires<=?').bind(now),
    env.DB.prepare('DELETE FROM forum_admin_nonces WHERE expires<=?').bind(now),
    env.DB.prepare('INSERT INTO forum_admin_nonces(nonce,expires) VALUES(?,?)').bind(loginNonce,now+FORM_MS),
    env.DB.prepare('INSERT INTO forum_admin_sessions(id_hash,expires) VALUES(?,?)').bind(hash,expiry)
   ]);
  }catch{return respond('<h1>Form already used</h1><p><a href="'+LOGIN+'">Open a new sign-in form</a></p>',403);}
  return redirect(ROOT,[setCookie('obca',await sealed(env.FORUM_ADMIN_AUTH,'admin-session',id,expiry),3600),setCookie('obca_login','',0)]);
 }
 const user=await currentAdmin(req,env,now);
 if(!user)return req.method==='POST'?respond('<h1>Sign in required</h1>',401):redirect(LOGIN);
 const actionForm=async(actionPath,action,label)=>'<form class="admin-action" method="post" action="'+actionPath+'"><input type="hidden" name="action" value="'+action+'"><input type="hidden" name="ticket" value="'+await formTicket(env.FORUM_ADMIN_AUTH,user.id,actionPath,action,now)+'"><button type="submit">'+label+'</button></form>';
 const navigation='<nav class="admin-nav"><a href="'+ROOT+'">Topics</a> | <a href="'+ROOT+'/log">Moderation history</a> | <a href="/forum">Public forum</a></nav>'+await actionForm(ROOT+'/logout','logout','Sign out');
 const match=path.match(/^\/forum\/admin\/(thread|post)\/([0-9a-f-]{36})$/),kind=match?.[1],id=match?.[2];
 if(req.method==='POST'){
  if(req.headers.get('Origin')!==url.origin)return respond('<h1>Form rejected</h1>',403);
  let f;try{f=await readForm(req);}catch{return respond('<h1>Invalid form</h1>',400);}
  const action=f.get('action')||'';
  const allowed=path===ROOT+'/logout'?['logout']:kind==='thread'&&uuid.test(id)?['hide','restore','close','reopen']:kind==='post'&&uuid.test(id)?['hide','restore']:[];
  if(!allowed.includes(action))return respond('<h1>Unknown action</h1>',400);
  const nonce=await validForm(env.FORUM_ADMIN_AUTH,user.id,path,action,f.get('ticket')||'',now);
  if(!nonce)return respond('<h1>Form expired</h1><p>Reload the administration page.</p>',403);
  let target,sql,to=ROOT;
  if(action==='logout')sql=env.DB.prepare('DELETE FROM forum_admin_sessions WHERE id_hash=?').bind(user.hash);
  else if(kind==='thread'){
   target=await env.DB.prepare('SELECT id FROM forum_threads WHERE id=?').bind(id).first();
   if(!target)return respond('<h1>Topic not found</h1>',404);
   const statements={hide:'UPDATE forum_threads SET hidden=1 WHERE id=?',restore:'UPDATE forum_threads SET hidden=0 WHERE id=?',close:'UPDATE forum_threads SET locked=1 WHERE id=?',reopen:'UPDATE forum_threads SET locked=0 WHERE id=?'};
   sql=env.DB.prepare(statements[action]).bind(id);to=path;
  }else{
   target=await env.DB.prepare('SELECT thread_id FROM forum_posts WHERE id=?').bind(id).first();
   if(!target)return respond('<h1>Message not found</h1>',404);
   sql=env.DB.prepare('INSERT INTO forum_post_moderation(post_id,hidden,updated_at) VALUES(?,?,?) ON CONFLICT(post_id) DO UPDATE SET hidden=excluded.hidden,updated_at=excluded.updated_at').bind(id,action==='hide'?1:0,now);
   to=ROOT+'/thread/'+target.thread_id;
  }
  const batch=[env.DB.prepare('DELETE FROM forum_admin_nonces WHERE expires<=?').bind(now),env.DB.prepare('INSERT INTO forum_admin_nonces(nonce,expires) VALUES(?,?)').bind(nonce,now+FORM_MS),sql];
  if(action!=='logout')batch.push(env.DB.prepare('INSERT INTO forum_admin_audit(id,action,target_type,target_id,created_at) VALUES(?,?,?,?,?)').bind(crypto.randomUUID(),action,kind,id,now));
  try{await env.DB.batch(batch);}catch{return respond('<h1>Action not applied</h1><p>The form may already have been used. Reload the page.</p>',409);}
  return redirect(action==='logout'?LOGIN:to,action==='logout'?[setCookie('obca','',0)]:[]);
 }
 if(path===ROOT){
  const n=pageNumber(url),rows=(await env.DB.prepare('SELECT id,title,updated_at,hidden,locked,replies FROM forum_threads ORDER BY updated_at DESC,id LIMIT 21 OFFSET ?').bind((n-1)*20).all()).results;
  return respond('<h1 class="page-title">Forum administration</h1>'+navigation+'<p>Hide and restore content, or close and reopen topics. These actions preserve the original messages.</p>'+
   (rows.length?'<div class="scroll"><table><thead><tr><th>Topic</th><th>Visibility</th><th>Replies</th><th>Updated (UTC)</th></tr></thead><tbody>'+rows.slice(0,20).map(t=>'<tr><td><a href="'+ROOT+'/thread/'+t.id+'">'+escape(t.title)+'</a></td><td>'+(t.hidden?'Hidden':'Public')+' / '+(t.locked?'Closed':'Open')+'</td><td>'+Math.max(0,t.replies-1)+'</td><td>'+utc(t.updated_at)+'</td></tr>').join('')+'</tbody></table></div>':'<p>No topics yet.</p>')+pager(ROOT,n,rows.length>20));
 }
 if(kind==='thread'&&uuid.test(id)){
  const t=await env.DB.prepare('SELECT * FROM forum_threads WHERE id=?').bind(id).first();if(!t)return respond('<h1>Topic not found</h1>',404);
  const n=pageNumber(url),posts=(await env.DB.prepare('SELECT p.*,COALESCE(m.hidden,0) AS hidden FROM forum_posts p LEFT JOIN forum_post_moderation m ON m.post_id=p.id WHERE p.thread_id=? ORDER BY p.created_at,p.id LIMIT 21 OFFSET ?').bind(id,(n-1)*20).all()).results;
  let body='<h1 class="page-title">'+escape(t.title)+'</h1>'+navigation+'<div class="paper"><p>Topic: '+(t.hidden?'Hidden':'Public')+' / '+(t.locked?'Closed':'Open')+'</p><div class="admin-actions">'+await actionForm(path,t.hidden?'restore':'hide',t.hidden?'Restore topic':'Hide topic')+await actionForm(path,t.locked?'reopen':'close',t.locked?'Reopen topic':'Close topic')+'</div><p><a href="/forum/thread/'+id+'">View public topic</a></p></div>';
  for(const p of posts.slice(0,20))body+='<article class="paper forum-post"><p class="forum-meta"><strong>'+escape(p.alias)+'</strong> - '+utc(p.created_at)+' - '+(p.hidden?'Hidden message':'Public message')+'</p><div class="message">'+escape(p.body)+'</div>'+await actionForm(ROOT+'/post/'+p.id,p.hidden?'restore':'hide',p.hidden?'Restore message':'Hide message')+'</article>';
  return respond(body+pager(path,n,posts.length>20));
 }
 if(path===ROOT+'/log'){
  const n=pageNumber(url),rows=(await env.DB.prepare('SELECT action,target_type,target_id,created_at FROM forum_admin_audit ORDER BY created_at DESC,id DESC LIMIT 31 OFFSET ?').bind((n-1)*30).all()).results;
  return respond('<h1 class="page-title">Moderation history</h1>'+navigation+'<div class="scroll"><table><thead><tr><th>Time (UTC)</th><th>Action</th><th>Target</th></tr></thead><tbody>'+rows.slice(0,30).map(r=>'<tr><td>'+utc(r.created_at)+'</td><td>'+escape(r.action)+'</td><td>'+escape(r.target_type)+' <span class="hash">'+escape(r.target_id)+'</span></td></tr>').join('')+'</tbody></table></div>'+pager(path,n,rows.length>30));
 }
 return respond('<h1>Page not found</h1>',404);
}
