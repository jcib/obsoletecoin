"""Obsolete Coin: local desktop wallet backed by Core descriptor wallets."""
import datetime
import argparse, queue, threading, tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from pathlib import Path
from decimal import Decimal
from rpc import RPC, RPCError, default_data_dir, parse_amount
from mine import mine

def transaction_time(tx, field=None):
    value = tx.get(field) if field else tx.get('time', tx.get('timereceived'))
    try:
        if value is None: return 'Unavailable'
        return datetime.datetime.fromtimestamp(value, datetime.timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M:%S %Z (%z)')
    except (ValueError, TypeError, OSError, OverflowError): return 'Unavailable'

def transaction_state(tx):
    confirmations = tx.get('confirmations', 0)
    if tx.get('category') == 'orphan': return 'Orphaned reward'
    if confirmations < 0 or tx.get('walletconflicts'): return 'Conflicted'
    if tx.get('abandoned'): return 'Abandoned'
    if tx.get('category') == 'immature': return 'Immature reward'
    return 'Confirmed' if confirmations > 0 else 'Pending'

BG='#000033'; NAVY='#000033'; TEAL='#000033'
YELLOW='#ffff00'; CYAN='#00ffff'; BLACK='#000000'
class Wallet:
    def __init__(self,root,rpc,demo=False):
        self.root=root;self.rpc=rpc;self.demo=demo;self.queue=queue.Queue();self.busy=False
        self.mining=threading.Event();self.miner=None;self.snapshot=None;self.history_count=20;self.transactions={}
        root.title('Obsolete Coin');root.geometry('980x820');root.minsize(940,780);root.configure(bg=TEAL)
        root.option_add('*Font',('Times New Roman',11));root.option_add('*Background',BG)
        for key,value in [('*Foreground',YELLOW),('*Button.Background',BLACK),('*Button.Foreground',CYAN),('*activeBackground',BLACK),('*activeForeground','#ffffff'),('*Entry.Background',BLACK),('*Entry.Foreground',CYAN),('*Entry.readonlyBackground',BLACK),('*Entry.insertBackground',CYAN),('*selectBackground','#000080'),('*selectForeground','#ffffff')]:root.option_add(key,value)
        self.art=[]
        asset_dir=Path(__file__).resolve().parent/'assets'
        backdrop=tk.Canvas(root,highlightthickness=0,bg=BG);backdrop.place(x=0,y=0,relwidth=1,relheight=1)
        try:
            tile=tk.PhotoImage(file=str(asset_dir/'mazes.png'));self.art.append(tile)
            def paint(event):
                backdrop.delete('tile')
                for x in range(0,event.width,tile.width()):
                    for y in range(0,event.height,tile.height()):backdrop.create_image(x,y,image=tile,anchor='nw',tags='tile')
            backdrop.bind('<Configure>',paint)
        except tk.TclError:pass
        style=ttk.Style();style.theme_use('clam');style.configure('Treeview',background=BLACK,fieldbackground=BLACK,foreground=YELLOW,rowheight=27,bordercolor=YELLOW,font=('Courier New',10))
        style.configure('Treeview.Heading',background=BLACK,foreground=CYAN,font=('Times New Roman',11,'bold'))
        style.map('Treeview',background=[('selected','#000080')],foreground=[('selected','#ffffff')])
        style.map('Treeview.Heading',background=[('active',NAVY)],foreground=[('active','#ffffff')])
        shell=tk.Frame(root,bd=1,relief='solid',bg=BG,highlightbackground=YELLOW,highlightthickness=1);shell.pack(fill='both',expand=True,padx=24,pady=24)
        title=tk.Frame(shell,bg=NAVY);title.pack(fill='x',padx=3,pady=3)
        try:
            logo=tk.PhotoImage(file=str(asset_dir/'obsolete-coin.gif'))
            scale=max(1,(max(logo.width(),logo.height())+55)//56);logo=logo.subsample(scale,scale);self.art.append(logo);root.iconphoto(True,logo)
            tk.Label(title,image=logo,bg=BG).pack(side='left',padx=14,pady=6)
        except tk.TclError:pass
        tk.Label(title,text='Obsolete Coin',bg=NAVY,fg=YELLOW,font=('Times New Roman',28,'bold italic')).pack(side='left',pady=8)
        menus=tk.Frame(shell,bd=1,relief='raised');menus.pack(fill='x',padx=3)
        for label,commands in [('File',[('Refresh',self.refresh),('Exit',self.close)]),
                               ('Wallet',[('Open / Create',self.open_wallet),('Receive',self.receive),('Send',self.send),('Backup',self.backup)]),
                               ('Mining',[('Start / Stop',self.toggle_mine)]),
                               ('Help',[('About',lambda:messagebox.showinfo('Obsolete Coin','Experimental testnet v0.2\nTest coins have no value. Blocks target 15 minutes.\nA dominant miner can reorganize this network.'))])]:
            button=tk.Menubutton(menus,text=label,relief='flat');button.pack(side='left')
            menu=tk.Menu(button,tearoff=0)
            for title,command in commands:menu.add_command(label=title,command=command)
            button.configure(menu=menu)
        tk.Frame(shell,height=3,bg='#ff0000').pack(fill='x',padx=22,pady=(12,10))
        tk.Label(shell,text='DEMO PREVIEW - no blockchain connection' if demo else 'EXPERIMENTAL TESTNET - test coins have no monetary value',fg=YELLOW,anchor='w').pack(fill='x',padx=22)
        panel=tk.Frame(shell,bd=1,relief='solid',bg=BLACK,highlightbackground=YELLOW,highlightthickness=1);panel.pack(fill='x',padx=22,pady=18)
        self.balance=tk.StringVar(value='-- OBSC');self.detail=tk.StringVar(value='Waiting for your local node...')
        tk.Label(panel,text='Available balance',bg=BLACK,anchor='w').pack(fill='x',padx=14,pady=(12,0))
        tk.Label(panel,textvariable=self.balance,bg=BLACK,font=('Courier New',26,'bold'),anchor='w').pack(fill='x',padx=14)
        tk.Label(panel,textvariable=self.detail,bg=BLACK,anchor='w').pack(fill='x',padx=14,pady=(0,12))
        row=tk.Frame(shell);row.pack(fill='x',padx=22)
        for label,command in [('Open / Create',self.open_wallet),('Receive',self.receive),('Send...',self.send),('Backup...',self.backup),('Mine / Stop',self.toggle_mine)]:
            tk.Button(row,text=label,command=command,bd=2,relief='raised',padx=8,pady=5).pack(side='left',padx=(0,6))
        row2=tk.Frame(shell);row2.pack(fill='x',padx=22,pady=(8,0))
        for label,command in [('Encrypt...',self.encrypt),('Unlock...',self.unlock),('Lock',self.lock),('Refresh',self.refresh)]:
            tk.Button(row2,text=label,command=command,bd=2).pack(side='left',padx=(0,7))
        tk.Label(shell,text='Recent activity',anchor='w',font=('Tahoma',10,'bold')).pack(fill='x',padx=22,pady=(18,5))
        self.table=ttk.Treeview(shell,columns=('date','type','amount','conf'),show='headings',height=5)
        for key,name,width in [('date','Date / time (local)',340),('type','Status',180),('amount','Amount (OBSC)',180),('conf','Confirmations',100)]:
            self.table.heading(key,text=name);self.table.column(key,width=width)
        self.table.pack(fill='both',expand=True,padx=22)
        self.table.bind('<Double-1>',lambda event:self.transaction_details())
        history_buttons=tk.Frame(shell);history_buttons.pack(fill='x',padx=22,pady=4)
        tk.Button(history_buttons,text='Transaction details',command=self.transaction_details).pack(side='left')
        self.more_button=tk.Button(history_buttons,text='Load 20 more',command=self.more_history)
        self.more_button.pack(side='left',padx=8)
        tk.Label(shell,text='Target block time: 15 minutes. Actual waits vary. Confirmations are not a security guarantee.',anchor='w',wraplength=760).pack(fill='x',padx=22,pady=12)
        self.status=tk.StringVar(value='Starting...')
        statusbar=tk.Label(shell,textvariable=self.status,anchor='w',bd=2,relief='sunken')
        statusbar.pack(side='bottom',fill='x',padx=3,pady=3,before=self.table)
        root.protocol('WM_DELETE_WINDOW',self.close);root.after(100,self.drain)
        if demo:
            self.balance.set('12,345.00000000 OBSC');self.detail.set('Immature: 5,000.00000000 OBSC | Pending: 0.00000000 OBSC')
            self.status.set('DEMO | 120 blocks | 2 peers | No real funds')
            for v in [('Received','12,345.00000000','8'),('Mined (immature)','5,000.00000000','1')]:self.table.insert('',tk.END,values=('2026-11-14 10:00:00 UTC (+0000)',)+v)
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
            return chain,peers,self.wallet_call('getbalances'),self.wallet_call('listtransactions','*',self.history_count+1)
        def done(data):
            chain,peers,bal,txs=data;self.snapshot=data;m=bal['mine']
            self.balance.set(f"{Decimal(str(m['trusted'])):,.8f} OBSC")
            self.detail.set(f"Immature: {m['immature']:.8f} OBSC | Pending: {m['untrusted_pending']:.8f} OBSC")
            self.status.set(f"TESTNET | {chain['blocks']} blocks | {peers} peers | Wallet: {self.rpc.wallet}")
            for item in self.table.get_children():self.table.delete(item)
            self.transactions={}
            self.more_button.configure(state='normal' if len(txs)>self.history_count else 'disabled')
            for tx in reversed(txs[-self.history_count:]):
                item=self.table.insert('',tk.END,values=(transaction_time(tx),transaction_state(tx),f"{tx['amount']:.8f}",tx.get('confirmations',0)))
                self.transactions[item]=tx
        self.work(job,done)
    def more_history(self):
        if self.busy:return
        self.history_count+=20
        self.refresh()
    def transaction_details(self):
        selection=self.table.selection()
        if not selection or selection[0] not in self.transactions:return
        tx=dict(self.transactions[selection[0]])
        def done(detail):
            merged={**tx,**detail}
            win=tk.Toplevel(self.root);win.title('Transaction details');win.geometry('760x440')
            fields=[('Transaction ID',merged.get('txid','Unavailable')),('Address',tx.get('address','Unavailable')),
                    ('Amount (OBSC)',str(tx.get('amount','Unavailable'))),('Fee (OBSC)',str(abs(Decimal(str(merged['fee'])))) if 'fee' in merged else 'Not applicable'),
                    ('Status',transaction_state(merged)),('Confirmations',str(merged.get('confirmations',0))),
                    ('Date / time (local)',transaction_time(merged)),('Block date / time',transaction_time(merged,'blocktime'))]
            for label,value in fields:
                row=tk.Frame(win);row.pack(fill='x',padx=12,pady=5)
                tk.Label(row,text=label,width=22,anchor='w').pack(side='left')
                entry=tk.Entry(row);entry.pack(side='left',fill='x',expand=True);entry.insert(0,value);entry.configure(state='readonly')
            def copy_id():win.clipboard_clear();win.clipboard_append(merged.get('txid',''))
            tk.Button(win,text='Copy transaction ID',command=copy_id).pack(pady=8)
        self.work(lambda:self.wallet_call('gettransaction',tx['txid']),done)
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
        address=simpledialog.askstring('Send OBSC','Recipient testnet address:',parent=self.root)
        if not address:return
        amount=simpledialog.askstring('Send OBSC','Amount in OBSC:',parent=self.root)
        if amount is None:return
        try:amount=parse_amount(amount)
        except ValueError as e:messagebox.showerror('Invalid amount',str(e));return
        if not address.startswith('tobs1'):messagebox.showerror('Wrong address','Use an Obsolete testnet address (tobs1...).');return
        if not messagebox.askyesno('Confirm transfer',f'Send {amount} TEST OBSC to\n{address}\n\nA network fee will also be charged. The transfer cannot be cancelled here.'):return
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
        if not messagebox.askyesno('CPU mining','Use this computer to mine TEST OBSC?\n\nThe node must run on this computer. One CPU thread and about 256 MiB of memory will be used.'):return
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
    p.add_argument('--cookie',type=Path,default=default_data_dir()/'obsolete-testnet-v2/.cookie');p.add_argument('--rpcport',type=int,default=19778)
    a=p.parse_args();root=tk.Tk();Wallet(root,RPC(a.cookie,a.rpcport,a.wallet),a.demo);root.mainloop()
if __name__=='__main__':main()
