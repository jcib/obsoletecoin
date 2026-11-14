"""Apply only the node UID output filter, after isolated kernel tests; no restarts."""
import base64,hashlib,hmac,ipaddress,json,os,pathlib,pwd,shlex,subprocess,sys,tempfile,time,urllib.request
P=pathlib.Path
TABLE='obsoletecoin_egress'
CONF=P('/etc/nftables.conf')
RULE=P('/etc/nftables.d/obsoletecoin-egress.nft')
BACKUP=P('/opt/obsoletecoin/lan-isolation-before')
TIMER='obsoletecoin-egress-rollback'
GENESIS='9576894f8fffa098a9b1c04c3a3edb774d9dc7f58413e0906e781ecd8f0ede98'
def run(args,**kw):return subprocess.run(args,check=True,capture_output=True,text=True,timeout=60,**kw).stdout.strip()
def states():
    return {u:run(['systemctl','show',u,'-p','MainPID','-p','NRestarts','-p','ActiveState']) for u in ('cryptobot','obsoletecoin-testnet','obsoletecoin-explorer')}
def other_tables():
    data=json.loads(run(['nft','-j','list','ruleset']))
    def scrub(x):
        if isinstance(x,list):return [scrub(y) for y in x]
        if isinstance(x,dict):return {k:scrub(v) for k,v in x.items() if k not in ('packets','bytes','handle','metainfo')}
        return x
    return scrub([x for x in data['nftables'] if 'metainfo' not in x and not any(isinstance(v,dict) and (v.get('table')==TABLE or (k=='table' and v.get('name')==TABLE)) for k,v in x.items())])
def rejected():
    data=json.loads(run(['nft','-j','list','table','inet',TABLE]))
    return sum(e['counter']['packets'] for item in data['nftables'] for r in [item.get('rule',{})] if any('reject' in x for x in r.get('expr',[])) for e in r.get('expr',[]) if 'counter' in e)
def atomic(path,data,mode=0o600):
    assert not path.is_symlink()
    with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as f:f.write(data);f.flush();os.fsync(f.fileno());name=f.name
    os.chmod(name,mode);os.chown(name,0,0);os.replace(name,path)
def usercode(code):return run(['runuser','-u','obsoletecoin','--','python3','-B','-c',code])
def cli(*args):return run(['runuser','-u','obsoletecoin','--','/opt/obsoletecoin/current/bitcoin-cli','-chain=obsolete-test','-datadir=/var/lib/obsoletecoin','-conf=/etc/obsoletecoin/obsolete.conf',*args])
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*a,**k):return None
OPENER=urllib.request.build_opener(NoRedirect)
def public_request(settings,path,post=False):
    headers={'User-Agent':'Mozilla/5.0 ObsoleteCoin-OperatorCheck'}
    if settings.get('bypass'):headers['OAI-Sites-Authorization']='Bearer '+settings['bypass']
    data=None
    if post:
        data=b'{}';stamp=str(int(time.time()));headers['X-Obsolete-Time']=stamp
        headers['X-Obsolete-Signature']=hmac.new(settings['key'].encode(),stamp.encode()+b'\n'+path.encode()+b'\n'+data,hashlib.sha256).hexdigest()
    req=urllib.request.Request('https://obsoletecoin.pages.dev'+path,data=data,headers=headers)
    with OPENER.open(req,timeout=25) as r:return json.load(r)
def main():
    assert os.geteuid()==0
    bundle=json.loads(sys.stdin.readline())
    uid=pwd.getpwnam('obsoletecoin').pw_uid
    assert uid==987 and pwd.getpwnam('cryptobot').pw_uid!=uid
    before=states();others=other_tables()
    assert all('ActiveState=active' in v for v in before.values())
    assert not RULE.exists() and not BACKUP.exists(),'Already prepared or installed: inspect before retry'
    names=json.loads(run(['nft','-j','list','tables']))['nftables']
    assert not any(x.get('table',{}).get('name')==TABLE for x in names)
    assert 'include "/etc/nftables.d/obsoletecoin.nft"' in CONF.read_text()
    # This deployment intentionally uses public IPv4 DNS and no local DNS exception.
    dns=[x.split()[1] for x in P('/etc/resolv.conf').read_text().splitlines() if x.startswith('nameserver ')]
    assert dns and all(ipaddress.ip_address(x).version==4 and ipaddress.ip_address(x).is_global for x in dns)
    modules={k:base64.b64decode(v) for k,v in bundle['files'].items()}
    ns={};exec(compile(modules['rules.py'],'rules.py','exec'),ns);rules=ns['rules'](uid)
    with tempfile.TemporaryDirectory(prefix='obsolete-egress-',dir='/run') as folder:
        folder=P(folder);rf=folder/'rules.nft';rf.write_text(rules)
        tf=folder/'test.py';tf.write_bytes(modules['test_namespace.py'])
        namespace='obsolete-egress-test-'+str(os.getpid())
        run(['ip','netns','add',namespace])
        try:
            run(['ip','-n',namespace,'link','set','lo','up'])
            for addr in ['10.23.0.2/32','172.16.0.2/32','192.168.50.2/32','169.254.1.2/32','100.64.0.2/32','93.184.216.34/32','fd00::2/128','2001:db8::2/128']:
                args=['ip','-n',namespace,'addr','add',addr,'dev','lo']
                if ':' in addr:args+=['nodad']
                run(args)
            tests=json.loads(run(['ip','netns','exec',namespace,'python3','-B',str(tf),str(uid),str(rf)]))
        finally:
            subprocess.run(['ip','netns','delete',namespace],capture_output=True,timeout=10)
        assert others==other_tables() and before==states(),'Isolated tests changed host state'
        print(json.dumps({'phase':'isolated-tests-passed','tests':tests}),flush=True)
        settings=json.loads(P('/etc/obsoletecoin/explorer.json').read_text())
        first=public_request(settings,'/api/snapshot');assert first['fresh'] and first['genesis']==GENESIS
        conf_before=CONF.read_bytes();new=conf_before.rstrip()+b'\ninclude "/etc/nftables.d/obsoletecoin-egress.nft"\n'
        BACKUP.mkdir(mode=0o700)
        atomic(BACKUP/'nftables.conf',conf_before)
        atomic(BACKUP/'manifest.json',json.dumps({'installed_config_sha':hashlib.sha256(new).hexdigest(),'uid':uid,'created':int(time.time())}).encode())
        rollback=modules['rollback.py'];atomic(BACKUP/'rollback.py',rollback)
        armed=False;applied=False
        try:
            atomic(RULE,rules.encode(),0o644);atomic(CONF,new,0o644)
            run(['nft','-c','-f',str(CONF)])
            run(['systemd-run','--unit='+TIMER,'--on-active=180s','--timer-property=AccuracySec=1s','/usr/bin/python3','-B',str(BACKUP/'rollback.py')]);armed=True
            run(['nft','-f',str(rf)]);applied=True;applied_at=int(time.time()*1000)
            negatives=[]
            for address,port in [('192.168.1.1',80),('192.0.2.36',22),('127.0.0.1',22),('::1',22)]:
                family='socket.AF_INET6' if ':' in address else 'socket.AF_INET'
                code='import socket;s=socket.socket('+family+');s.settimeout(2);\ntry:s.connect(('+repr(address)+','+str(port)+'));print("allowed")\nexcept OSError as e:print(e.errno)'
                count=rejected();value=usercode(code);assert value!='allowed' and rejected()>count,(address,value);negatives.append({'destination':address+':'+str(port),'blocked':True,'reject_counter_increased':True})
            info=json.loads(cli('getblockchaininfo'));assert cli('getblockhash','0')==GENESIS
            assert info['blocks']>=first['height'] and not info['initialblockdownload']
            address=usercode("import urllib.request,ipaddress;r=urllib.request.urlopen('https://api.ipify.org',timeout=10);s=r.read(64).decode().strip();assert ipaddress.IPv4Address(s).is_global;print(s)")
            fresh=None
            for _ in range(8):
                current=public_request(settings,'/api/snapshot')
                if current['fresh'] and current['observed']>applied_at:fresh=current;break
                time.sleep(5)
            assert fresh,'Publisher did not update after isolation'
            probe=public_request(settings,'/api/probe',True);assert probe['verified'] and probe['genesis']==GENESIS
            assert before==states(),'Service PID/state changed'
            assert others==other_tables(),'Unrelated firewall rules changed'
            run(['nft','-c','-f',str(CONF)])
            result={'applied':True,'uid':uid,'tests':tests,'live_blocks':negatives,'rpc_ok':True,'public_dns_https_ok':True,'height':info['blocks'],'publisher_observed':fresh['observed'],'external_genesis_probe':probe,'service_states_unchanged':True,'unrelated_firewall_unchanged':True,'persistent_syntax_valid':True,'rules_sha256':hashlib.sha256(rules.encode()).hexdigest(),'checked_at':int(time.time())}
            atomic(BACKUP/'result.json',json.dumps(result,indent=2).encode())
            run(['systemctl','stop',TIMER+'.timer']);armed=False
            print(json.dumps({'phase':'complete',**result}),flush=True)
        except BaseException:
            # Restore only this dedicated change, never reload or flush host rules.
            subprocess.run(['python3','-B',str(BACKUP/'rollback.py')],check=True,timeout=20)
            if armed:subprocess.run(['systemctl','stop',TIMER+'.timer'],capture_output=True,timeout=10)
            raise
if __name__=='__main__':
    try:main()
    except subprocess.CalledProcessError as e:
        print('Command failed: '+str(e.cmd[0])+'; '+(e.stderr or '')[-2400:],file=sys.stderr)
        raise SystemExit(1)
