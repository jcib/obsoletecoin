"""Obsolete Coin 95: local desktop wallet backed by Core descriptor wallets."""
import argparse, queue, threading, tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from pathlib import Path
from decimal import Decimal
from rpc import RPC, RPCError, default_data_dir, parse_amount
from mine import mine

BG='#c0c0c0'; NAVY='#000080'; TEAL='#008080'
class Wallet95:
    def __init__(self,root,rpc,demo=False):
        self.root=root;self.rpc=rpc;self.demo=demo;self.queue=queue.Queue();self.busy=False
        self.mining=threading.Event();self.miner=None;self.snapshot=None
        root.title('Obsolete Coin 95');root.geometry('900x760');root.minsize(840,700);root.configure(bg=TEAL)
        root.option_add('*Font',('Tahoma',10));root.option_add('*Background',BG)
        style=ttk.Style();style.theme_use('clam');style.configure('Treeview',background='white',fieldbackground='white',rowheight=25)
        shell=tk.Frame(root,bd=3,relief='raised',bg=BG);shell.pack(fill='both',expand=True,padx=24,pady=24)
        title=tk.Frame(shell,bg=NAVY);title.pack(fill='x',padx=3,pady=3)
        tk.Label(title,text='  [O]  Obsolete Coin 95',bg=NAVY,fg='white',font=('Tahoma',12,'bold')).pack(side='left',pady=5)
        tk.Label(title,text='_  []  X ',bg=NAVY,fg='white').pack(side='right')
        menus=tk.Frame(shell,bd=1,relief='raised');menus.pack(fill='x',padx=3)
        for label,commands in [('File',[('Refresh',self.refresh),('Exit',self.close)]),
                               ('Wallet',[('Open / Create',self.open_wallet),('Receive',self.receive),('Send',self.send),('Backup',self.backup)]),
                               ('Mining',[('Start / Stop',self.toggle_mine)]),
                               ('Help',[('About',lambda:messagebox.showinfo('Obsolete Coin 95','Experimental testnet v0.1\nPlease wait. It is still 1995.\n\nTest coins have no value. Blocks target 15 minutes.\nA dominant miner can reorganize this network.'))])]:
            button=tk.Menubutton(menus,text=label,relief='flat');button.pack(side='left')
            menu=tk.Menu(button,tearoff=0)
            for title,command in commands:menu.add_command(label=title,command=command)
            button.configure(menu=menu)
        tk.Label(shell,text='Please wait. It is still 1995.',font=('Tahoma',22,'bold'),anchor='w').pack(fill='x',padx=22,pady=(20,4))
        tk.Label(shell,text='DEMO PREVIEW - no blockchain connection' if demo else 'EXPERIMENTAL TESTNET - test coins have no monetary value',fg='#800000',anchor='w').pack(fill='x',padx=22)
        panel=tk.Frame(shell,bd=2,relief='sunken',bg='white');panel.pack(fill='x',padx=22,pady=18)
        self.balance=tk.StringVar(value='-- OBS');self.detail=tk.StringVar(value='Waiting for your local node...')
        tk.Label(panel,text='Available balance',bg='white',anchor='w').pack(fill='x',padx=14,pady=(12,0))
        tk.Label(panel,textvariable=self.balance,bg='white',font=('Courier New',26,'bold'),anchor='w').pack(fill='x',padx=14)
        tk.Label(panel,textvariable=self.detail,bg='white',anchor='w').pack(fill='x',padx=14,pady=(0,12))
        row=tk.Frame(shell);row.pack(fill='x',padx=22)
        for label,command in [('Open / Create',self.open_wallet),('Receive',self.receive),('Send...',self.send),('Backup...',self.backup),('Mine / Stop',self.toggle_mine)]:
            tk.Button(row,text=label,command=command,bd=2,relief='raised',padx=8,pady=5).pack(side='left',padx=(0,6))
        row2=tk.Frame(shell);row2.pack(fill='x',padx=22,pady=(8,0))
        for label,command in [('Encrypt...',self.encrypt),('Unlock...',self.unlock),('Lock',self.lock),('Refresh',self.refresh)]:
            tk.Button(row2,text=label,command=command,bd=2).pack(side='left',padx=(0,7))
        tk.Label(shell,text='Recent activity',anchor='w',font=('Tahoma',10,'bold')).pack(fill='x',padx=22,pady=(18,5))
        self.table=ttk.Treeview(shell,columns=('type','amount','conf'),show='headings',height=5)
        for key,name,width in [('type','Type',160),('amount','Amount (OBS)',220),('conf','Confirmations',150)]:
            self.table.heading(key,text=name);self.table.column(key,width=width)
        self.table.pack(fill='both',expand=True,padx=22)
        tk.Label(shell,text='Target block time: 15 minutes. Actual waits vary. Confirmations are not a security guarantee.',anchor='w',wraplength=760).pack(fill='x',padx=22,pady=12)
        self.status=tk.StringVar(value='Starting...')
        statusbar=tk.Label(shell,textvariable=self.status,anchor='w',bd=2,relief='sunken')
        statusbar.pack(side='bottom',fill='x',padx=3,pady=3,before=self.table)
        root.protocol('WM_DELETE_WINDOW',self.close);root.after(100,self.drain)
        if demo:
            self.balance.set('12,345.00000000 OBS');self.detail.set('Immature: 5,000.00000000 OBS | Pending: 0.00000000 OBS')
            self.status.set('DEMO | 95 blocks | 2 peers | No real funds')
            for v in [('Received','12,345.00000000','8'),('Mined (immature)','5,000.00000000','1')]:self.table.insert('',tk.END,values=v)
        else:self.refresh()
    def wallet_call(self,method,*params):
        # Guard every operation, including backup/encryption, if a user selects
        # the wrong local port or a different node restarts on the same port.
        chain=self.rpc.call('getblockchaininfo')
        if chain['chain']!='obsolete-test':raise ValueError('Only Obsolete testnet is supported')
        if method=='getblockchaininfo':return chain
        return self.rpc.call(method,*params)
    def work(self,job,done):
        if self.demo:messagebox.showinfo('Demo','Preview only. Start without --demo to use a local node.');return
        if self.busy: return
        self.busy=True;self.status.set('Please wait...')
        def runner():
            try:self.queue.put((done,job(),None))
            except Exception as e:self.queue.put((done,None,str(e)))
        threading.Thread(target=runner,daemon=True).start()
    def drain(self):
        try:
            while True:
                done,value,error=self.queue.get_nowait();self.busy=False
                if error:self.status.set('Not ready: '+error[:140])
                else:done(value)
        except queue.Empty:pass
        self.root.after(100,self.drain)
    def refresh(self):
        def job():
            chain=self.wallet_call('getblockchaininfo')
            if chain['chain']!='obsolete-test':raise ValueError('Only Obsolete testnet is supported')
            peers=self.wallet_call('getconnectioncount')
            return chain,peers,self.wallet_call('getbalances'),self.wallet_call('listtransactions','*',10)
        def done(data):
            chain,peers,bal,txs=data;self.snapshot=data;m=bal['mine']
            self.balance.set(f"{Decimal(str(m['trusted'])):,.8f} OBS")
            self.detail.set(f"Immature: {m['immature']:.8f} OBS | Pending: {m['untrusted_pending']:.8f} OBS")
            self.status.set(f"TESTNET | {chain['blocks']} blocks | {peers} peers | Wallet: {self.rpc.wallet}")
            for item in self.table.get_children():self.table.delete(item)
            for tx in reversed(txs):self.table.insert('',tk.END,values=(tx['category'],f"{tx['amount']:.8f}",tx.get('confirmations',0)))
        self.work(job,done)
    def open_wallet(self):
        def job():
            base=RPC(self.rpc.cookie,self.rpc.port)
            if base.call('getblockchaininfo')['chain']!='obsolete-test':raise ValueError('Wrong network')
            name=self.rpc.wallet
            if name not in base.call('listwallets'):
                known=[w['name'] for w in base.call('listwalletdir')['wallets']]
                base.call('loadwallet' if name in known else 'createwallet',name)
            return name
        self.work(job,lambda name:(self.status.set('Wallet open: '+name),self.refresh()))
    def receive(self):
        def done(address):
            win=tk.Toplevel(self.root);win.title('Receive obsolete money');win.geometry('620x150')
            tk.Label(win,text='Your TESTNET receive address').pack(pady=10)
            entry=tk.Entry(win,width=76);entry.pack(padx=10);entry.insert(0,address);entry.configure(state='readonly')
            tk.Button(win,text='Copy address',command=lambda:(win.clipboard_clear(),win.clipboard_append(address))).pack(pady=10)
            self.status.set('Receive address ready')
        self.work(lambda:self.wallet_call('getnewaddress','', 'bech32'),done)
    def send(self):
        address=simpledialog.askstring('Send OBS','Recipient testnet address:',parent=self.root)
        if not address:return
        amount=simpledialog.askstring('Send OBS','Amount in OBS:',parent=self.root)
        if amount is None:return
        try:amount=parse_amount(amount)
        except ValueError as e:messagebox.showerror('Invalid amount',str(e));return
        if not address.startswith('tobs1'):messagebox.showerror('Wrong address','Use an Obsolete testnet address (tobs1...).');return
        if not messagebox.askyesno('Confirm transfer',f'Send {amount} TEST OBS to\n{address}\n\nA network fee will also be charged. The transfer cannot be cancelled here.'):return
        def job():
            if self.wallet_call('getblockchaininfo')['chain']!='obsolete-test':raise ValueError('Wrong network')
            # Fixed 1 atom/vB fee for experimental testnet; no floating-point amount.
            return self.wallet_call('sendtoaddress',address,amount,'','',False,True,None,None,False,1)
        self.work(job,lambda tx:(self.status.set('Transfer submitted: '+tx),messagebox.showinfo('Submitted','Transaction ID:\n'+tx+'\n\nWait for miners to confirm it.')))
    def backup(self):
        path=filedialog.asksaveasfilename(title='Backup local wallet',defaultextension='.dat')
        if path:self.work(lambda:self.wallet_call('backupwallet',str(Path(path).resolve())),lambda _:self.status.set('Backup saved. Store it privately.'))
    def encrypt(self):
        pw=simpledialog.askstring('Encrypt wallet','New passphrase (cannot be recovered):',show='*')
        if not pw:return
        again=simpledialog.askstring('Encrypt wallet','Repeat passphrase:',show='*')
        if again!=pw:messagebox.showerror('Mismatch','Passphrases differ.');return
        self.work(lambda:self.wallet_call('encryptwallet',pw),lambda _:self.status.set('Wallet encrypted. Make a new backup.'))
    def unlock(self):
        pw=simpledialog.askstring('Unlock wallet','Passphrase (unlocks for 60 seconds):',show='*')
        if pw:self.work(lambda:self.wallet_call('walletpassphrase',pw,60),lambda _:self.status.set('Unlocked for 60 seconds'))
    def lock(self):self.work(lambda:self.wallet_call('walletlock'),lambda _:self.status.set('Wallet locked'))
    def toggle_mine(self):
        if self.demo:return
        if self.miner and self.miner.is_alive():self.mining.set();self.status.set('Stopping miner after current batch...');return
        if not messagebox.askyesno('CPU mining','Use this computer to mine TEST OBS?\n\nThe node must run on this computer. One CPU thread and about 256 MiB of memory will be used.'):return
        self.mining.clear()
        def job():
            try:
                address=self.wallet_call('getnewaddress','mining','bech32')
                mine(RPC(self.rpc.cookie,self.rpc.port,timeout=120),address,self.mining)
            except Exception as e:self.queue.put((lambda _:None,None,'Mining: '+str(e)))
        self.miner=threading.Thread(target=job,daemon=True);self.miner.start();self.status.set('CPU mining started. Refresh to see rewards.')
    def close(self):self.mining.set();self.root.destroy()

def main():
    p=argparse.ArgumentParser();p.add_argument('--demo',action='store_true');p.add_argument('--wallet',default='obsolete')
    p.add_argument('--cookie',type=Path,default=default_data_dir()/'obsolete-testnet/.cookie');p.add_argument('--rpcport',type=int,default=19596)
    a=p.parse_args();root=tk.Tk();Wallet95(root,RPC(a.cookie,a.rpcport,a.wallet),a.demo);root.mainloop()
if __name__=='__main__':main()
