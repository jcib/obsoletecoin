"""Restore only the dedicated egress filter/config include; keep audit files."""
import hashlib,json,os,pathlib,subprocess,tempfile
P=pathlib.Path;backup=P('/opt/obsoletecoin/lan-isolation-before');conf=P('/etc/nftables.conf');rule=P('/etc/nftables.d/obsoletecoin-egress.nft')
assert os.geteuid()==0
manifest=json.loads((backup/'manifest.json').read_text())
assert hashlib.sha256(conf.read_bytes()).hexdigest()==manifest['installed_config_sha'],'Config changed since installation; refuse overwrite'
subprocess.run(['nft','delete','table','inet','obsoletecoin_egress'],capture_output=True)
data=(backup/'nftables.conf').read_bytes()
with tempfile.NamedTemporaryFile(dir=conf.parent,delete=False) as f:f.write(data);f.flush();os.fsync(f.fileno());name=f.name
os.chmod(name,0o644);os.chown(name,0,0);os.replace(name,conf)
if rule.exists():rule.unlink()
print('Only Obsolete Coin egress isolation reverted.')
