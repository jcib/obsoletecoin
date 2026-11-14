"""Enable only the requested Obsolete public P2P service and public-data exporter."""
import hashlib,json,os,pwd,subprocess,sys,tempfile,time
from pathlib import Path
UNIT='obsoletecoin-testnet.service';CONF=Path('/etc/obsoletecoin/obsolete.conf');BASE=Path('/opt/obsoletecoin');FW=Path('/etc/nftables.d/obsoletecoin.nft')
STAGE=Path('/home/NODE_USER/.local/share/obsoletecoin-public-stage')
def run(args,**kw):return subprocess.run(args,check=True,text=True,capture_output=True,**kw).stdout.strip()
def state(unit):return dict(x.split('=',1) for x in run(['systemctl','show',unit,'-p','MainPID','-p','NRestarts','-p','ActiveState']).splitlines())
def write(path,data,mode=0o644,gid=0):
 with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as f:f.write(data);f.flush();os.fsync(f.fileno());name=f.name
 os.chmod(name,mode);os.chown(name,0,gid);os.replace(name,path)
def cli(*args):return run(['runuser','-u','obsoletecoin','--',str(BASE/'current/bitcoin-cli'),'-chain=obsolete-test','-datadir=/var/lib/obsoletecoin','-conf='+str(CONF),*args])
assert os.geteuid()==0
settings=json.loads(sys.stdin.readline());assert len(settings['key'])==64 and settings['origin']=='https://obsoletecoin.pages.dev'
before=state('cryptobot');assert before['ActiveState']=='active'
info=json.loads(cli('getblockchaininfo'));assert info['chain']=='obsolete-test'
assert cli('getblockhash','0')=='9576894f8fffa098a9b1c04c3a3edb774d9dc7f58413e0906e781ecd8f0ede98'
assert info.get('pruneheight',0)==0,'Historical blocks have already been pruned; do not change mode without recovery planning'
conf_before=CONF.read_bytes();fw_before=FW.read_bytes()
assert b'rpcbind=127.0.0.1' in conf_before and b'disablewallet=1' in conf_before
assert 'ObsoleteCoin testnet public' not in run(['nft','list','chain','inet','heimweh','input']),'Already configured; inspect rather than repeat'
backup=BASE/'public-testnet-before';backup.mkdir(mode=0o700)
(backup/'obsolete.conf').write_bytes(conf_before);(backup/'obsoletecoin.nft').write_bytes(fw_before)
new=conf_before.replace(b'prune=1000',b'prune=0').replace(b'maxuploadtarget=256',b'maxuploadtarget=1024').replace(b'maxconnections=16',b'maxconnections=32')
# Keep established-connection handling and all existing rules. Never reload/flush nftables.
rule='add rule inet heimweh input tcp dport 19777 ct state new limit rate 20/second burst 40 packets counter accept comment "ObsoleteCoin testnet public"\n'
rulepath=STAGE/'public-rule.nft';write(rulepath,rule.encode());run(['nft','-c','-f',str(rulepath)])
# Install reviewed public-data code, with no arbitrary RPC forwarding.
gid=pwd.getpwnam('obsoletecoin').pw_gid
app=BASE/'public-web';(app/'website/live').mkdir(parents=True,exist_ok=True);(app/'tools').mkdir(exist_ok=True)
for rel in ('website/live/publisher.py','tools/rpc.py'):
 data=(STAGE/rel).read_bytes();expected=settings['files'][rel];assert hashlib.sha256(data).hexdigest()==expected;write(app/rel,data)
private=Path('/etc/obsoletecoin/explorer.json');write(private,json.dumps({k:settings[k] for k in ('origin','key','bypass')}).encode(),0o640,gid)
service=Path('/etc/systemd/system/obsoletecoin-explorer.service')
assert not service.exists(),'Exporter already exists'
service_text='''[Unit]
Description=Obsolete Coin public testnet explorer publisher
Wants=network-online.target
After=network-online.target obsoletecoin-testnet.service
[Service]
Type=simple
User=obsoletecoin
Group=obsoletecoin
ExecStart=/usr/bin/python3 -B /opt/obsoletecoin/public-web/website/live/publisher.py --config /etc/obsoletecoin/explorer.json
Restart=always
RestartSec=15
Nice=15
CPUQuota=10%
MemoryMax=128M
TasksMax=16
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
CapabilityBoundingSet=
[Install]
WantedBy=multi-user.target
'''
write(service,service_text.encode());run(['systemd-analyze','verify',str(service)])
write(CONF,new)
try:
 run(['systemctl','restart',UNIT])
 for _ in range(60):
  try:
   current=json.loads(cli('getblockchaininfo'))
   if current['chain']=='obsolete-test' and current['blocks']>=info['blocks'] and not current['pruned']:break
  except subprocess.CalledProcessError:pass
  time.sleep(1)
 else:raise RuntimeError('Node restart failed')
except Exception:
 write(CONF,conf_before);run(['systemctl','restart',UNIT]);raise
write(FW,fw_before.rstrip()+b'\n'+rule.encode());run(['nft','-c','-f','/etc/nftables.conf']);run(['nft','-f',str(rulepath)])
run(['systemctl','daemon-reload']);run(['systemctl','enable','--now','obsoletecoin-explorer.service'])
after=state('cryptobot');assert after==before,'Unrelated bot changed during setup; investigate'
print(json.dumps({'public_p2p_firewall':True,'port':19777,'rpc_loopback':True,'wallet_disabled':True,'full_history':not current['pruned'],'height':current['blocks'],'node':state(UNIT),'publisher':state('obsoletecoin-explorer.service'),'unrelated_bot_unchanged':after==before}),flush=True)
