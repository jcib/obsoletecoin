"""Measured local RandomX mining, independent of the validator's light VM."""
import hashlib
import os
import struct
import sys
import threading
import time
from pathlib import Path
from rx import RandomX
from coin_network import TESTNET

GENESIS = TESTNET.genesis
MAX_THREADS = min(4, os.cpu_count() or 1)


def find_library(explicit=None):
    if explicit:
        path = Path(explicit).resolve()
        if not path.is_file(): raise ValueError('RandomX library not found: ' + str(path))
        return path
    root = Path(__file__).resolve().parents[1]
    folders = [Path(sys.executable).resolve().parent, root, root/'build-randomx-shared',
               root/'.local/upgrade-rx-shared', root/'.local/native-node']
    names = ('librandomx.dll',) if os.name == 'nt' else (('librandomx.dylib',) if sys.platform == 'darwin' else ('librandomx.so',))
    for folder in folders:
        for name in names:
            if (folder/name).is_file(): return folder/name
    raise ValueError('Install the complete package, or supply --library for RandomX')


def sha256d(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def compact_size(n):
    if n < 253: return bytes([n])
    if n <= 65535: return b'\xfd' + struct.pack('<H', n)
    if n <= 0xffffffff: return b'\xfe' + struct.pack('<I', n)
    return b'\xff' + struct.pack('<Q', n)


def script_height(height):
    if 1 <= height <= 16: return bytes([0x50 + height])
    data = height.to_bytes(max(1, (height.bit_length()+7)//8), 'little')
    if data[-1] & 0x80: data += b'\x00'
    return bytes([len(data)]) + data


def make_work(template, payout_script, extra):
    """BIP34/141 coinbase; transaction data, fees and seed come from the node."""
    contract = template['brisvia']
    if (contract['pow_version'], contract['header_size'], contract['nonce_offset'], contract['nonce_size']) != (1, 80, 76, 4):
        raise ValueError('Unsupported mining contract')
    seed = bytes.fromhex(contract['randomx_seed_hash'])[::-1]
    if len(seed) != 32: raise ValueError('Invalid mining seed')
    script = script_height(template['height']) + bytes([len(extra)]) + extra
    if not 2 <= len(script) <= 100: raise ValueError('Invalid coinbase script length')
    txin = b'\x01' + bytes(32) + b'\xff'*4 + compact_size(len(script)) + script + b'\xff'*4
    output = struct.pack('<Q', template['coinbasevalue']) + compact_size(len(payout_script)) + payout_script
    commitment = bytes.fromhex(template.get('default_witness_commitment', ''))
    outputs = compact_size(2 if commitment else 1) + output
    if commitment: outputs += bytes(8) + compact_size(len(commitment)) + commitment
    version = struct.pack('<I', 2)
    stripped = version + txin + outputs + bytes(4)
    coinbase = version + b'\x00\x01' + txin + outputs + b'\x01\x20' + bytes(32) + bytes(4) if commitment else stripped
    transactions = template['transactions']
    hashes = [sha256d(stripped)] + [bytes.fromhex(tx['txid'])[::-1] for tx in transactions]
    while len(hashes) > 1:
        if len(hashes) % 2: hashes.append(hashes[-1])
        hashes = [sha256d(hashes[i] + hashes[i+1]) for i in range(0, len(hashes), 2)]
    header = struct.pack('<I', template['version'] & 0xffffffff) + bytes.fromhex(template['previousblockhash'])[::-1] + hashes[0]
    header += struct.pack('<II', template['curtime'], int(template['bits'], 16))
    body = compact_size(1+len(transactions)) + coinbase + b''.join(bytes.fromhex(tx['data']) for tx in transactions)
    target = int(template['target'], 16)
    if not 0 < target < 2**256: raise ValueError('Invalid mining target')
    return header, body, seed, target


class MiningStats:
    def __init__(self, threads=1, duty=100):
        self.lock = threading.Lock()
        self.started = time.monotonic()
        self.ended = None
        self.hashes = self.blocks = self.rejected = 0
        self.threads, self.duty = threads, duty
        self.state = 'Starting'
        self.samples = [(self.started, 0)]

    def snapshot(self):
        with self.lock:
            now = self.ended or time.monotonic()
            elapsed = max(0, now-self.started)
            if now > self.samples[-1][0]: self.samples.append((now, self.hashes))
            while len(self.samples) > 2 and self.samples[1][0] < now-10: self.samples.pop(0)
            start, count = self.samples[0]
            rate = (self.hashes-count)/max(.001, now-start) if not self.ended else 0
            return dict(hashes=self.hashes, blocks=self.blocks, rejected=self.rejected,
                        elapsed=elapsed, hps=rate, average_hps=self.hashes/max(.001, elapsed),
                        threads=self.threads, duty=self.duty, state=self.state)


def mine(rpc, address, stop=None, max_blocks=None, maxtries=256, *, threads=1, duty=100, library=None, stats=None, network=TESTNET):
    """ctypes releases the GIL. Duty is an active/wait ratio, not an OS CPU cap."""
    if not 1 <= threads <= MAX_THREADS: raise ValueError(f'Use 1..{MAX_THREADS} mining threads')
    if not 1 <= duty <= 100: raise ValueError('Activity must be 1..100 percent')
    if max_blocks is not None and max_blocks < 1: raise ValueError('Block count must be positive')
    if maxtries < 1: raise ValueError('Batch size must be positive')
    stop = stop or threading.Event()
    stats = stats or MiningStats(threads, duty)
    library = find_library(library)
    network.verify(rpc)
    address_info = rpc.call('validateaddress', address)
    if not address_info['isvalid']: raise ValueError(f'Invalid {network.label} payout address')
    payout = bytes.fromhex(address_info['scriptPubKey'])
    errors = []
    submission = threading.Lock()
    initialization = threading.Lock()

    def worker():
        rx = None
        current_seed = None
        try:
            while not stop.is_set():
                info = rpc.call('getblockchaininfo')
                if info['chain'] != network.chain or info['initialblockdownload'] or rpc.call('getconnectioncount') < 1:
                    raise ValueError(f'Connect a {network.label} peer and finish synchronization before mining')
                template = rpc.call('getblocktemplate', {'rules': ['segwit']})
                header, body, seed, target = make_work(template, payout, os.urandom(16))
                if seed != current_seed:
                    if rx: rx.close(); rx = None
                    with initialization:
                        if stop.is_set(): break
                        rx = RandomX(library, seed)
                    current_seed = seed
                nonce = 0
                refresh_at = time.monotonic() + 2
                with stats.lock: stats.state = 'Mining'
                while not stop.is_set() and time.monotonic() < refresh_at and nonce <= 0xffffffff:
                    started = time.monotonic()
                    for _ in range(min(maxtries, 8)):
                        if stop.is_set() or nonce > 0xffffffff: break
                        candidate = header + struct.pack('<I', nonce)
                        work = rx.hash(candidate)
                        with stats.lock: stats.hashes += 1
                        nonce += 1
                        if int.from_bytes(work, 'little') <= target:
                            with submission:
                                if stop.is_set(): break
                                # A sibling worker may have advanced the tip while this
                                # hash was running. Avoid deliberately mining a side branch.
                                result = 'stale' if rpc.call('getbestblockhash') != template['previousblockhash'] else rpc.call('submitblock', (candidate + body).hex())
                                with stats.lock:
                                    if result is None: stats.blocks += 1
                                    else: stats.rejected += 1
                                    complete = max_blocks is not None and stats.blocks >= max_blocks
                                if result is None: print('Found block', sha256d(candidate)[::-1].hex(), flush=True)
                                if complete: stop.set()
                            refresh_at = 0
                            break
                    active = time.monotonic()-started
                    if duty < 100: stop.wait(active * (100-duty)/duty)
        except Exception as error:
            with stats.lock: errors.append(error)
            stop.set()
        finally:
            if rx: rx.close()

    workers = [threading.Thread(target=worker, name=f'RandomX-{i}', daemon=True) for i in range(threads)]
    try:
        for thread in workers: thread.start()
        for thread in workers:
            while thread.is_alive(): thread.join(.2)
    finally:
        stop.set()
        for thread in workers:
            if thread.ident is not None: thread.join()
        with stats.lock:
            stats.ended = time.monotonic()
            stats.state = 'Error' if errors else 'Stopped'
    if errors: raise errors[0]
    return stats.blocks
