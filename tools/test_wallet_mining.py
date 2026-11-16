import threading
import unittest
from unittest.mock import Mock, patch
from mining import MiningStats, make_work, mine, GENESIS
from wallet import network_state, maturity_text
from wallet_recovery import check_wallet_capabilities


def template(target='7fffff'+'00'*29):
    return dict(brisvia=dict(pow_version=1,header_size=80,nonce_offset=76,nonce_size=4,
                            randomx_seed_hash='11'*32),height=17,version=0x20000000,
                previousblockhash='22'*32,curtime=1794614401,bits='207fffff',
                target=target,coinbasevalue=500000000000,transactions=[])


class MiningTests(unittest.TestCase):
    def test_watch_only_copy_cannot_pass_as_spendable_backup(self):
        with self.assertRaisesRegex(ValueError,'signing capabilities'):
            check_wallet_capabilities({'private_keys_enabled':True},{'private_keys_enabled':False})
        with self.assertRaisesRegex(ValueError,'signing capabilities'):
            check_wallet_capabilities({'external_signer':True},{'external_signer':False})
        check_wallet_capabilities({'private_keys_enabled':True},{'private_keys_enabled':True})

    def test_stats_measured_not_derived_from_blocks(self):
        with patch('mining.time.monotonic',return_value=10): s=MiningStats()
        s.hashes=50;s.blocks=2
        with patch('mining.time.monotonic',return_value=20): result=s.snapshot()
        self.assertEqual(result['hps'],5)
        s.ended=20
        self.assertEqual(s.snapshot()['hps'],0)
        self.assertEqual(s.snapshot()['average_hps'],5)
        for _ in range(100):s.snapshot()
        self.assertLessEqual(len(s.samples),2)

    def test_work_unique_coinbase_and_contract(self):
        a=make_work(template(),b'\x51',b'a'*16)
        b=make_work(template(),b'\x51',b'b'*16)
        self.assertEqual(len(a[0]),76)
        self.assertNotEqual(a[0][36:68],b[0][36:68])
        t=template();t['brisvia']['nonce_offset']=0
        with self.assertRaises(ValueError):make_work(t,b'\x51',b'a'*16)

    def test_exact_hash_count_includes_winning_hash_and_does_not_retry_submission(self):
        stats=MiningStats()
        rpc=Mock()
        replies={'getblockchaininfo':dict(chain='obsolete-test',initialblockdownload=False),
                 'getblockhash':GENESIS,'validateaddress':dict(isvalid=True,scriptPubKey='51'),
                 'getconnectioncount':1,'getblocktemplate':template(),'getbestblockhash':'22'*32,'submitblock':None}
        rpc.call.side_effect=lambda name,*params:replies[name]
        engine=Mock();engine.hash.side_effect=[b'\xff'*32,b'\x00'*32]
        with patch('mining.find_library',return_value='unused'),patch('mining.RandomX',return_value=engine):
            self.assertEqual(mine(rpc,'test',max_blocks=1,stats=stats),1)
        self.assertEqual(stats.hashes,2)
        self.assertEqual(sum(c.args[0]=='submitblock' for c in rpc.call.call_args_list),1)
        engine.close.assert_called_once()

    def test_stop_and_wrong_network(self):
        rpc=Mock();rpc.call.return_value={'chain':'main'}
        with patch('mining.find_library',return_value='unused'),self.assertRaises(ValueError):mine(rpc,'test')
        self.assertEqual(rpc.call.call_count,1)

    def test_native_failure_stops_session_and_releases_vm(self):
        rpc=Mock();stats=MiningStats()
        replies={'getblockchaininfo':dict(chain='obsolete-test',initialblockdownload=False),
                 'getblockhash':GENESIS,'validateaddress':dict(isvalid=True,scriptPubKey='51'),
                 'getconnectioncount':1,'getblocktemplate':template()}
        rpc.call.side_effect=lambda name,*params:replies[name]
        engine=Mock();engine.hash.side_effect=RuntimeError('fixture hash failure')
        with patch('mining.find_library',return_value='unused'),patch('mining.RandomX',return_value=engine):
            with self.assertRaisesRegex(RuntimeError,'fixture hash failure'):mine(rpc,'test',stats=stats)
        self.assertEqual(stats.hashes,0)
        self.assertEqual(stats.state,'Error')
        engine.close.assert_called_once()

    def test_cancel_checks_between_hashes(self):
        rpc=Mock();stats=MiningStats();stop=threading.Event()
        replies={'getblockchaininfo':dict(chain='obsolete-test',initialblockdownload=False),
                 'getblockhash':GENESIS,'validateaddress':dict(isvalid=True,scriptPubKey='51'),
                 'getconnectioncount':1,'getblocktemplate':template()}
        rpc.call.side_effect=lambda name,*params:replies[name]
        engine=Mock()
        def hash_once(data):stop.set();return b'\xff'*32
        engine.hash.side_effect=hash_once
        with patch('mining.find_library',return_value='unused'),patch('mining.RandomX',return_value=engine):
            self.assertEqual(mine(rpc,'test',stop,stats=stats),0)
        self.assertEqual(stats.hashes,1)
        self.assertEqual(stats.state,'Stopped')
        engine.close.assert_called_once()

    def test_stale_work_is_not_submitted_or_counted_as_accepted(self):
        rpc=Mock();stats=MiningStats();stop=threading.Event()
        replies={'getblockchaininfo':dict(chain='obsolete-test',initialblockdownload=False),
                 'getblockhash':GENESIS,'validateaddress':dict(isvalid=True,scriptPubKey='51'),
                 'getconnectioncount':1,'getblocktemplate':template()}
        def call(name,*params):
            if name=='getbestblockhash':stop.set();return '33'*32
            return replies[name]
        rpc.call.side_effect=call
        engine=Mock();engine.hash.return_value=b'\x00'*32
        with patch('mining.find_library',return_value='unused'),patch('mining.RandomX',return_value=engine):
            self.assertEqual(mine(rpc,'test',stop,stats=stats),0)
        self.assertEqual(stats.hashes,1)
        self.assertEqual(stats.rejected,1)
        self.assertFalse(any(c.args[0]=='submitblock' for c in rpc.call.call_args_list))

    def test_network_status_never_claims_synced_without_peers(self):
        chain=dict(blocks=10,headers=10,initialblockdownload=False,verificationprogress=1)
        self.assertIn('Offline',network_state(chain,0))
        self.assertIn('connected peers',network_state(chain,1))
        chain['headers']=20
        self.assertIn('Synchronizing',network_state(chain,1))

    def test_reward_maturity_boundaries(self):
        self.assertIn('100 more blocks',maturity_text(dict(category='immature',confirmations=1)))
        self.assertIn('1 more blocks',maturity_text(dict(category='immature',confirmations=100)))
        self.assertEqual(maturity_text(dict(category='receive',confirmations=1)),'Not applicable')


if __name__=='__main__':unittest.main()
