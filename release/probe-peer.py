"""Read-only P2P handshake/genesis probe from the Windows LAN client."""
import argparse,io,json,socket,struct,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'test/functional'))
from test_framework.messages import msg_version,msg_verack,msg_getheaders,msg_headers,hash256
p=argparse.ArgumentParser();p.add_argument('--peer',required=True);a=p.parse_args();host,port=a.peer.rsplit(':',1);assert port=='19777';magic=bytes.fromhex('4f425432')
genesis=json.loads((ROOT/'docs/genesis.json').read_text(encoding='utf-8'))['TEST']['hash']
def recv_exact(sock,count):
    data=b''
    while len(data)<count:
        chunk=sock.recv(count-len(data))
        if not chunk:raise RuntimeError('Peer closed connection')
        data+=chunk
    return data
def send(sock,name,payload):
    sock.sendall(magic+name.ljust(12,b'\x00')+struct.pack('<I',len(payload))+hash256(payload)[:4]+payload)
with socket.create_connection((host,19777),timeout=15) as sock:
    version=msg_version();version.nVersion=70016;version.strSubVer='/ObsoleteLanProbe:0.2/'
    version.addrTo.ip=host;version.addrTo.port=19777
    send(sock,b'version',version.serialize());requested=False;remote=None
    for _ in range(30):
        header=recv_exact(sock,24);assert header[:4]==magic
        name=header[4:16].rstrip(b'\x00');length=int.from_bytes(header[16:20],'little')
        assert length<4*1024*1024
        payload=recv_exact(sock,length);assert hash256(payload)[:4]==header[20:24]
        if name==b'version':
            remote=msg_version();remote.deserialize(io.BytesIO(payload));send(sock,b'verack',b'')
        elif name==b'verack':
            request=msg_getheaders();request.hashstop=int(genesis,16)
            send(sock,b'getheaders',request.serialize());requested=True
        elif name==b'ping':send(sock,b'pong',payload)
        elif name==b'headers' and requested:
            headers=msg_headers();headers.deserialize(io.BytesIO(payload))
            assert len(headers.headers)==1 and headers.headers[0].hash_hex==genesis
            result={'p2p_handshake':True,'server':a.peer,'genesis_verified':genesis,
                    'remote_protocol':remote.nVersion,'remote_height':remote.nStartingHeight}
            (Path.cwd()/'public-p2p-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
            print(json.dumps(result));break
    else:raise RuntimeError('No matching genesis header received')