import unittest
from wallet import transaction_time, transaction_state
class HistoryTests(unittest.TestCase):
    def test_times(self):
        self.assertEqual(transaction_time({}), 'Unavailable')
        self.assertEqual(transaction_time({'time':'bad'}), 'Unavailable')
        self.assertEqual(transaction_time({'time':100}),transaction_time({'timereceived':100}))
        self.assertNotEqual(transaction_time({'time':100}),transaction_time({'time':200}))
        self.assertEqual(transaction_time({'time':100},'blocktime'),'Unavailable')
        self.assertIn('(',transaction_time({'time':100}))
    def test_states(self):
        for tx,state in [({},'Pending'),({'confirmations':2},'Confirmed'),({'confirmations':-1},'Conflicted'),({'category':'orphan'},'Orphaned reward'),({'category':'immature','confirmations':2},'Immature reward'),({'abandoned':True},'Abandoned')]:
            self.assertEqual(transaction_state(tx),state)
if __name__=='__main__':unittest.main()
