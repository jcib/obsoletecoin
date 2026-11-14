"""Local-only authenticated JSON-RPC. Use an SSH tunnel for a remote node."""
import base64, http.client, ipaddress, json
from pathlib import Path
from decimal import Decimal
from urllib.parse import quote

class RPCError(RuntimeError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)

class RPC:
    def __init__(self, cookie, port=19596, wallet=None, timeout=30):
        self.cookie=Path(cookie)
        self.port=int(port)
        if not 1 <= self.port <= 65535: raise ValueError('Invalid RPC port')
        self.wallet=wallet
        self.timeout=timeout
    def for_wallet(self, name): return RPC(self.cookie,self.port,name,self.timeout)
    def call(self, method, *params):
        # Cookie refreshed for each request, including after a node restart.
        cookie=self.cookie.read_text(encoding='utf-8').strip()
        if ':' not in cookie: raise ValueError('Invalid node cookie')
        headers={'Content-Type':'application/json','Authorization':'Basic '+base64.b64encode(cookie.encode()).decode()}
        path='/' if self.wallet is None else '/wallet/'+quote(self.wallet,safe='')
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=self.timeout)
        try:
            conn.request('POST',path,json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':list(params)}),headers)
            response=conn.getresponse()
            # No redirects: authentication never leaves the loopback connection.
            if response.status not in (200,500): raise RPCError(response.status,'RPC request rejected; check node and cookie')
            data=response.read(4*1024*1024+1)
            if len(data)>4*1024*1024: raise RPCError(-1,'RPC response too large')
            value=json.loads(data,parse_float=Decimal)
            if value.get('error'):
                error=value['error'];raise RPCError(error['code'],error['message'])
            return value['result']
        finally: conn.close()

def default_data_dir():
    return Path.home()/'.obsoletecoin'

def parse_amount(text):
    from decimal import Decimal, InvalidOperation
    try: value=Decimal(text)
    except InvalidOperation: raise ValueError('Enter a valid OBS amount') from None
    if not value.is_finite() or value<=0 or value>1000000000 or value.as_tuple().exponent < -8:
        raise ValueError('Use a positive amount with at most 8 decimals')
    return format(value,'f')
