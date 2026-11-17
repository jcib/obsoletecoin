"""Restore a backup on an isolated, temporary node; never replace the user's wallet."""
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from rpc import RPC, RPCError
from coin_network import TESTNET


def descriptor_identity(rpc):
    return sorted((d['desc'], d.get('active', False), d.get('internal', False))
                  for d in rpc.call('listdescriptors')['descriptors'])


def check_wallet_capabilities(source, restored):
    for field in ('private_keys_enabled', 'external_signer'):
        if bool(source.get(field, False)) != bool(restored.get(field, False)):
            raise ValueError('Backup signing capabilities do not match the open wallet')


def verify_backup(source_rpc, backup, binary, passphrase=None, *, network=TESTNET):
    backup, binary = Path(backup).resolve(), Path(binary).resolve()
    if not backup.is_file() or not binary.is_file(): raise ValueError('Backup or node executable is missing')
    network.verify(source_rpc)
    identity = descriptor_identity(source_rpc)
    source_info = source_rpc.call('getwalletinfo')
    if not identity: raise ValueError('Source wallet has no descriptors to compare')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix='obsolete-backup-check-') as folder:
        data = Path(folder)
        rpc = RPC(data/network.directory/'.cookie', port, timeout=30)
        with (data/'check.log').open('w') as log:
            process = subprocess.Popen([str(binary), f'-chain={network.chain}', f'-datadir={data}',
                f'-rpcport={port}', '-rpcbind=127.0.0.1', '-rpcallowip=127.0.0.1', '-server=1',
                '-listen=0', '-connect=0', '-dnsseed=0', '-fixedseeds=0', '-discover=0',
                '-networkactive=0', '-dbcache=32', '-printtoconsole=0'], stdout=log, stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            try:
                deadline = time.monotonic()+60
                while True:
                    if process.poll() is not None: raise RuntimeError('Temporary verification node failed to start')
                    try:
                        network.verify(rpc)
                        break
                    except (OSError, RPCError):
                        if time.monotonic() >= deadline: raise RuntimeError('Verification startup timed out')
                        time.sleep(.2)
                rpc.call('restorewallet', 'backup-check', str(backup))
                recovered = rpc.for_wallet('backup-check')
                info = recovered.call('getwalletinfo')
                check_wallet_capabilities(source_info, info)
                if 'unlocked_until' in info:
                    if not passphrase: raise ValueError('Enter the backup passphrase to verify recovery')
                    recovered.call('walletpassphrase', passphrase, 30)
                if descriptor_identity(recovered) != identity:
                    raise ValueError('This backup does not match all descriptors in the open wallet')
                if 'unlocked_until' in info: recovered.call('walletlock')
                return {'matched': True, 'encrypted': 'unlocked_until' in info,
                        'descriptors': len(identity), 'balances_rescanned': False}
            finally:
                if process.poll() is None:
                    try: rpc.call('stop')
                    except (OSError, RPCError): pass
                    try: process.wait(timeout=30)
                    except subprocess.TimeoutExpired: process.kill(); process.wait()
