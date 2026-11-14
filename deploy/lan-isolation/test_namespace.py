"""Real nftables tests in a disposable network namespace; no production packets."""
import errno,json,os,socket,subprocess,sys,threading,time

def exercise(uid, rulefile):
    servers=[];threads=[];children=[]
    def listen(address,port,family=socket.AF_INET):
        s=socket.socket(family);s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        s.bind((address,port));s.listen();servers.append(s)
        def accept():
            while True:
                try:c,_=s.accept()
                except OSError:return
                def echo(c):
                    try:
                        with c:
                            while True:
                                b=c.recv(32)
                                if not b:break
                                c.sendall(b)
                    except OSError:pass
                threading.Thread(target=echo,args=(c,),daemon=True).start()
        threading.Thread(target=accept,daemon=True).start()
    targets=['127.0.0.1','10.23.0.2','172.16.0.2','192.168.50.2','169.254.1.2','100.64.0.2','93.184.216.34']
    for addr in targets:listen(addr,18080)
    for addr in ['::1','fd00::2','2001:db8::2']:listen(addr,18080,socket.AF_INET6)
    listen('127.0.0.1',19778)
    prefix='import os,socket,sys,json;os.setgroups([]);os.setgid('+str(uid)+');os.setuid('+str(uid)+');'
    def child(code):return subprocess.check_output([sys.executable,'-B','-c',prefix+code],text=True,timeout=8).strip()
    held=subprocess.Popen([sys.executable,'-B','-u','-c',prefix+"s=socket.create_connection(('192.168.50.2',18080),2);print('ready',flush=True);sys.stdin.readline();s.settimeout(1);\ntry:s.sendall(b'x');r=s.recv(1);print('unexpected:'+repr(r))\nexcept OSError as e:print('blocked:'+str(e.errno))"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
    children.append(held);assert held.stdout.readline().strip()=='ready'
    subprocess.run(['nft','-c','-f',rulefile],check=True)
    subprocess.run(['nft','-f',rulefile],check=True)
    def rejected():
        data=json.loads(subprocess.check_output(['nft','-j','list','table','inet','obsoletecoin_egress'],text=True))
        return sum(e['counter']['packets'] for item in data['nftables'] for r in [item.get('rule',{})] if any('reject' in x for x in r.get('expr',[])) for e in r.get('expr',[]) if 'counter' in e)
    results=[]
    try:
        for addr in targets[:-1]+['::1','fd00::2','2001:db8::2']:
            family='socket.AF_INET6' if ':' in addr else 'socket.AF_INET'
            code="s=socket.socket("+family+");s.settimeout(1);\ntry:s.connect(("+repr(addr)+",18080));print('ALLOWED')\nexcept OSError as e:print(e.errno)"
            count=rejected();value=child(code);assert value!='ALLOWED' and rejected()>count,(addr,value,rejected(),count);results.append({'blocked':addr,'reject_counter_increased':True})
        for addr,port in [('93.184.216.34',18080),('127.0.0.1',19778)]:
            value=child("s=socket.create_connection(("+repr(addr)+","+str(port)+"),2);s.sendall(b'yes');assert s.recv(3)==b'yes';print('ok')")
            assert value=='ok';results.append({'allowed':addr+':'+str(port)})
        held.stdin.write('go\n');held.stdin.flush();line=held.stdout.readline().strip();assert line.startswith('blocked:'),line
        held.wait(timeout=3);results.append({'preexisting_outbound_private_connection':'blocked'})
        # Other UIDs retain access to a private address.
        with socket.create_connection(('192.168.50.2',18080),2) as s:s.sendall(b'ok');assert s.recv(2)==b'ok'
        results.append({'other_uid':'unaffected'})
        server=subprocess.Popen([sys.executable,'-B','-u','-c',prefix+"s=socket.socket();s.bind(('192.168.50.2',19777));s.listen();print('ready',flush=True);c,_=s.accept();c.sendall(c.recv(8))"],stdout=subprocess.PIPE,text=True)
        children.append(server);assert server.stdout.readline().strip()=='ready'
        with socket.create_connection(('192.168.50.2',19777),2) as s:s.sendall(b'peer');assert s.recv(4)==b'peer'
        server.wait(timeout=3);results.append({'incoming_lan_peer_reply':'allowed'})
        print(json.dumps(results))
    finally:
        for p in children:
            if p.poll() is None:p.kill()
            p.wait(timeout=3)
        for s in servers:s.close()

if __name__=='__main__':exercise(int(sys.argv[1]),sys.argv[2])
