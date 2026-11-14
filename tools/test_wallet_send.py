import unittest
from unittest.mock import patch,Mock
from wallet import Wallet
class SendTests(unittest.TestCase):
 def app(self):
  a=Wallet.__new__(Wallet);a.root=object();a.status=Mock()
  replies={'validateaddress':{'isvalid':True},'walletcreatefundedpsbt':{'psbt':'unsigned','fee':'0.00000200'},'walletprocesspsbt':{'complete':True,'psbt':'signed'},'finalizepsbt':{'complete':True,'hex':'raw'},'sendrawtransaction':'txid'}
  a.wallet_call=Mock(side_effect=lambda name,*args:replies[name])
  a.work=lambda job,done:done(job())
  return a
 def run_send(self,a,approve):
  with patch('wallet.simpledialog.askstring',side_effect=['tobs1test','1.25']),patch('wallet.messagebox.askyesno',return_value=approve) as confirm,patch('wallet.messagebox.showinfo'):
   a.send();return confirm.call_args.args[1]
 def test_cancel_does_not_sign_or_broadcast(self):
  a=self.app();text=self.run_send(a,False)
  self.assertIn('0.00000200 OBSC',text);self.assertIn('1.25000200 OBSC',text)
  self.assertEqual([c.args[0] for c in a.wallet_call.call_args_list],['validateaddress','walletcreatefundedpsbt'])
 def test_approved_transaction_is_signed_and_sent_once(self):
  a=self.app();self.run_send(a,True)
  names=[c.args[0] for c in a.wallet_call.call_args_list]
  self.assertEqual(names,['validateaddress','walletcreatefundedpsbt','walletprocesspsbt','finalizepsbt','sendrawtransaction'])
  a.status.set.assert_called_once_with('Transfer submitted: txid')
if __name__=='__main__':unittest.main()
