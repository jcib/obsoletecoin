import sys, unittest, tempfile, threading, json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from rpc import RPC, RPCError, parse_amount

class AmountTests(unittest.TestCase):
    def test_exact_amounts(self):
        self.assertEqual(parse_amount('0.00000001'),'0.00000001')
        self.assertEqual(parse_amount('1000000000'),'1000000000')
        self.assertEqual(parse_amount('12.34000000'),'12.34000000')
    def test_reject_nonfinite_negative_and_extra_precision(self):
        for text in ['NaN','Infinity','-1','0','0.000000001','1000000001','oops']:
            with self.subTest(text=text),self.assertRaises(ValueError):parse_amount(text)

class RPCTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.cookie=Path(self.temp.name)/'.cookie';self.cookie.write_text('user:test')
        outer=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                outer.path=self.path;outer.auth=self.headers['Authorization']
                request=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                if request['method']=='redirect':
                    self.send_response(302);self.send_header('Location','http://example.invalid/');self.end_headers();return
                self.send_response(200);self.end_headers()
                response={'result':request['params'],'error':None,'id':1}
                if request['method']=='fail':response={'error':{'code':-6,'message':'Insufficient funds'},'id':1}
                self.wfile.write(json.dumps(response).encode())
        self.server=HTTPServer(('127.0.0.1',0),Handler);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.rpc=RPC(self.cookie,self.server.server_port,'wallet/with space')
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()
    def test_wallet_routing_and_exact_amount(self):
        self.assertEqual(self.rpc.call('send','0.00000001'),['0.00000001'])
        self.assertEqual(self.path,'/wallet/wallet%2Fwith%20space')
    def test_credentials_refresh_after_restart(self):
        self.rpc.call('ok');before=self.auth;self.cookie.write_text('new:cookie');self.rpc.call('ok');self.assertNotEqual(before,self.auth)
    def test_no_authentication_redirect(self):
        with self.assertRaises(RPCError) as cm:self.rpc.call('redirect')
        self.assertEqual(cm.exception.code,302)
    def test_structured_rpc_error(self):
        with self.assertRaises(RPCError) as cm:self.rpc.call('fail')
        self.assertEqual(cm.exception.code,-6)
if __name__=='__main__':unittest.main()
