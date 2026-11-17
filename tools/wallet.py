"""Obsolete Coin: local desktop wallet backed by Core descriptor wallets."""
import datetime
import argparse, queue, threading, time, sys, tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from pathlib import Path
from decimal import Decimal
from rpc import RPC, RPCError, default_data_dir, parse_amount
from mine import mine
from mining import MiningStats, MAX_THREADS, GENESIS
from wallet_recovery import verify_backup
from functools import wraps

def user_action(method):
    """Keep automatic polling out of modal user flows (Tk runs a nested loop)."""
    @wraps(method)
    def wrapped(self,*args,**kwargs):
        if getattr(self,'busy',False):return
        self.interacting=True
        try:return method(self,*args,**kwargs)
        finally:self.interacting=False
    return wrapped

def verify_testnet(rpc):
    chain = rpc.call('getblockchaininfo')
    if chain['chain'] != 'obsolete-test':
        raise ValueError('Only Obsolete testnet is supported')
    if rpc.call('getblockhash', 0) != GENESIS:
        raise ValueError('Wrong testnet genesis')
    return chain

def network_state(chain, peers):
    blocks, headers = chain['blocks'], chain['headers']
    if not peers: return f'Offline - 0 peers | Local height {blocks:,}; network tip unknown'
    if chain['initialblockdownload'] or blocks < headers:
        percent = min(100, max(0, float(chain.get('verificationprogress', 0))*100))
        return f'Synchronizing {percent:.1f}% | {blocks:,} / {headers:,} known headers | {peers} peers'
    return f'Up to date with connected peers | Height {blocks:,} | {peers} peers'

def maturity_text(tx):
    if tx.get('category') != 'immature': return 'Not applicable'
    # Core GetBlocksToMaturity uses COINBASE_MATURITY + 1 - depth.
    remaining = max(0, 101-int(tx.get('confirmations', 0)))
    return f'{remaining} more blocks (~{remaining/4:.1f} h at target; actual wait varies)'

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
        self.mining_stats=None;self.mining_events=queue.Queue();self.closing=False;self.interacting=False;self.wallet_info={};self.last_backup=None
        root.title('Obsolete Coin');root.geometry('1020x940');root.minsize(940,640);root.configure(bg=TEAL)
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
        self.viewport=tk.Canvas(root,highlightthickness=0,bg=BG)
        scrollbar=tk.Scrollbar(root,orient='vertical',command=self.viewport.yview)
        scrollbar.pack(side='right',fill='y',pady=16)
        self.viewport.configure(yscrollcommand=scrollbar.set)
        self.viewport.pack(fill='both',expand=True,padx=16,pady=16)
        shell=tk.Frame(self.viewport,bd=1,relief='solid',bg=BG,highlightbackground=YELLOW,highlightthickness=1)
        content=self.viewport.create_window(0,0,window=shell,anchor='nw')
        def fit_content(event=None):
            width=self.viewport.winfo_width()
            height=max(shell.winfo_reqheight(),self.viewport.winfo_height())
            self.viewport.itemconfigure(content,width=width,height=height)
            self.viewport.configure(scrollregion=(0,0,width,height))
        shell.bind('<Configure>',fit_content);self.viewport.bind('<Configure>',fit_content)
        def scroll_content(event):
            if getattr(self,'table',None) is event.widget:return
            delta=(-1 if event.num==4 else 1) if getattr(event,'num',None) in (4,5) else -int(event.delta/120)
            self.viewport.yview_scroll(delta,'units')
        root.bind('<MouseWheel>',scroll_content);root.bind('<Button-4>',scroll_content);root.bind('<Button-5>',scroll_content)
        title=tk.Frame(shell,bg=NAVY);title.pack(fill='x',padx=3,pady=3)
        try:
            logo=tk.PhotoImage(file=str(asset_dir/'obsolete-coin.gif'))
            scale=max(1,(max(logo.width(),logo.height())+55)//56);logo=logo.subsample(scale,scale);self.art.append(logo);root.iconphoto(True,logo)
            tk.Label(title,image=logo,bg=BG).pack(side='left',padx=14,pady=6)
        except tk.TclError:pass
        tk.Label(title,text='Obsolete Coin',bg=NAVY,fg=YELLOW,font=('Times New Roman',28,'bold italic')).pack(side='left',pady=8)
        menus=tk.Frame(shell,bd=1,relief='raised');menus.pack(fill='x',padx=3)
        for label,commands in [('File',[('Refresh',self.refresh),('Exit',self.close)]),
                               ('Wallet',[('Open / Create',self.open_wallet),('Receive',self.receive),('Send',self.send),('Backup',self.backup),('Protect / check recovery',self.recovery_guide)]),
                               ('Network',[('Connect peer...',self.connect_peer)]),
                               ('Mining',[('Start / Stop',self.toggle_mine)]),
                               ('Help',[('About',lambda:messagebox.showinfo('Obsolete Coin','Experimental testnet v0.2\nTest coins have no value. Blocks target 15 minutes.\nA dominant miner can reorganize this network.'))])]:
            button=tk.Menubutton(menus,text=label,relief='flat');button.pack(side='left')
            menu=tk.Menu(button,tearoff=0)
            for title,command in commands:menu.add_command(label=title,command=command)
            button.configure(menu=menu)
        tk.Frame(shell,height=3,bg='#ff0000').pack(fill='x',padx=22,pady=(12,10))
        tk.Label(shell,text='DEMO PREVIEW - no blockchain connection' if demo else 'EXPERIMENTAL TESTNET - test coins have no monetary value',fg=YELLOW,anchor='w').pack(fill='x',padx=22)
        self.network=tk.StringVar(value='Connecting to local node...')
        tk.Label(shell,textvariable=self.network,fg=CYAN,anchor='w',wraplength=850).pack(fill='x',padx=22,pady=(6,0))
        panel=tk.Frame(shell,bd=1,relief='solid',bg=BLACK,highlightbackground=YELLOW,highlightthickness=1);panel.pack(fill='x',padx=22,pady=10)
        self.balance=tk.StringVar(value='-- OBSC');self.detail=tk.StringVar(value='Waiting for your local node...')
        tk.Label(panel,text='Available balance',bg=BLACK,anchor='w').pack(fill='x',padx=14,pady=(12,0))
        tk.Label(panel,textvariable=self.balance,bg=BLACK,font=('Courier New',26,'bold'),anchor='w').pack(fill='x',padx=14)
        tk.Label(panel,textvariable=self.detail,bg=BLACK,anchor='w').pack(fill='x',padx=14,pady=(0,12))
        tk.Label(panel,text='Mined rewards mature after 100 additional blocks (~25 h at target). Actual waits vary.',bg=BLACK,anchor='w',wraplength=850).pack(fill='x',padx=14,pady=(0,8))
        self.protection=tk.StringVar(value='Wallet protection: checking...')
        tk.Label(panel,textvariable=self.protection,bg=BLACK,anchor='w').pack(fill='x',padx=14,pady=(0,8))
        row=tk.Frame(shell);row.pack(fill='x',padx=22)
        for label,command in [('Open / Create',self.open_wallet),('Receive',self.receive),('Send...',self.send),('Backup...',self.backup),('Mine / Stop',self.toggle_mine)]:
            tk.Button(row,text=label,command=command,bd=2,relief='raised',padx=8,pady=5).pack(side='left',padx=(0,6))
        row2=tk.Frame(shell);row2.pack(fill='x',padx=22,pady=(8,0))
        for label,command in [('Encrypt...',self.encrypt),('Unlock...',self.unlock),('Lock',self.lock),('Protect / check recovery...',self.recovery_guide),('Refresh',self.refresh)]:
            tk.Button(row2,text=label,command=command,bd=2).pack(side='left',padx=(0,7))
        mining_panel=tk.LabelFrame(shell,text='CPU mining');mining_panel.pack(fill='x',padx=22,pady=(12,0))
        settings=tk.Frame(mining_panel);settings.pack(fill='x',padx=8)
        self.threads=tk.IntVar(value=1);self.activity=tk.IntVar(value=50)
        tk.Label(settings,text='Threads').pack(side='left')
        self.thread_control=tk.Spinbox(settings,from_=1,to=MAX_THREADS,textvariable=self.threads,width=3,state='readonly');self.thread_control.pack(side='left',padx=8)
        tk.Label(settings,text='Activity per thread (%)').pack(side='left')
        self.activity_control=tk.Spinbox(settings,values=(25,50,75,100),textvariable=self.activity,width=4,state='readonly');self.activity_control.pack(side='left',padx=8)
        self.activity.set(50)
        tk.Label(settings,text='~256 MiB per thread; activity is approximate',fg=CYAN).pack(side='left')
        self.mining_detail=tk.StringVar(value='Stopped | 0 hashes | 0 accepted blocks')
        tk.Label(mining_panel,textvariable=self.mining_detail,anchor='w').pack(fill='x',padx=8,pady=5)
        tk.Label(shell,text='Recent activity',anchor='w',font=('Tahoma',10,'bold')).pack(fill='x',padx=22,pady=(10,5))
        self.table=ttk.Treeview(shell,columns=('date','type','amount','conf'),show='headings',height=3)
        for key,name,width in [('date','Date / time (local)',340),('type','Status',180),('amount','Amount (OBSC)',180),('conf','Confirmations',100)]:
            self.table.heading(key,text=name);self.table.column(key,width=width)
        self.table.pack(fill='both',expand=True,padx=22)
        self.table.bind('<Double-1>',lambda event:self.transaction_details())
        history_buttons=tk.Frame(shell);history_buttons.pack(fill='x',padx=22,pady=4)
        tk.Button(history_buttons,text='Transaction details',command=self.transaction_details).pack(side='left')
        self.more_button=tk.Button(history_buttons,text='Load 20 more',command=self.more_history)
        self.more_button.pack(side='left',padx=8)
        tk.Label(shell,text='Target block time: 15 minutes. Actual waits vary. Confirmations are not a security guarantee.',anchor='w',wraplength=760).pack(fill='x',padx=22,pady=6)
        self.status=tk.StringVar(value='Starting...')
        statusbar=tk.Label(shell,textvariable=self.status,anchor='w',bd=2,relief='sunken')
        statusbar.pack(side='bottom',fill='x',padx=3,pady=3,before=self.table)
        root.protocol('WM_DELETE_WINDOW',self.close);root.after(100,self.drain);root.after(1000,self.mining_tick);root.after(5000,self.auto_refresh)
        if demo:
            self.balance.set('12,345.00000000 OBSC');self.detail.set('Immature: 5,000.00000000 OBSC | Pending: 0.00000000 OBSC')
            self.status.set('DEMO | 120 blocks | 2 peers | No real funds')
            self.network.set('DEMO | Up to date with connected peers | Height 120 | 2 peers')
            self.protection.set('DEMO | Encrypted and locked | Backup verification available')
            for v in [('Received','12,345.00000000','8'),('Mined (immature)','5,000.00000000','1')]:self.table.insert('',tk.END,values=('2026-11-14 10:00:00 UTC (+0000)',)+v)
        else:self.refresh()
    def wallet_call(self,method,*params):
        # Guard every operation, including backup/encryption, if a user selects
        # the wrong local port or a different node restarts on the same port.
        chain=verify_testnet(self.rpc)
        if method=='getblockchaininfo':return chain
        return self.rpc.call(method,*params)
    def work(self,job,done,on_error=None):
        if self.demo:messagebox.showinfo('Demo','Preview only. Start without --demo to use a local node.');return
        if self.busy: return
        self.busy=True;self.status.set('Please wait...')
        def runner():
            try:self.queue.put((done,job(),None,on_error))
            except Exception as e:self.queue.put((done,None,str(e),on_error))
        threading.Thread(target=runner,daemon=True).start()
    def drain(self):
        try:
            while True:
                done,value,error,on_error=self.queue.get_nowait();self.busy=False
                if error:
                    self.status.set('Not ready: '+error[:140])
                    if on_error:on_error(error)
                else:done(value)
        except queue.Empty:pass
        self.root.after(100,self.drain)
    def auto_refresh(self):
        if self.closing:return
        if not self.demo and not self.busy and not self.interacting:self.refresh(automatic=True)
        self.root.after(5000,self.auto_refresh)
    def refresh(self,automatic=False):
        def job():
            chain=self.wallet_call('getblockchaininfo')
            if chain['chain']!='obsolete-test':raise ValueError('Only Obsolete testnet is supported')
            peers=self.wallet_call('getconnectioncount')
            info=self.wallet_call('getwalletinfo')
            return chain,peers,self.wallet_call('getbalances'),self.wallet_call('listtransactions','*',self.history_count+1),info
        def done(data):
            chain,peers,bal,txs,info=data;self.snapshot=data;m=bal['mine'];self.wallet_info=info
            self.network.set(network_state(chain,peers))
            protection='Not encrypted - use Protect / check recovery' if 'unlocked_until' not in info else ('Encrypted / unlocked temporarily' if info['unlocked_until']>time.time() else 'Encrypted / locked')
            self.protection.set(protection)
            self.balance.set(f"{Decimal(str(m['trusted'])):,.8f} OBSC")
            self.detail.set(f"Immature: {m['immature']:.8f} OBSC | Pending: {m['untrusted_pending']:.8f} OBSC")
            self.status.set(previous_status if automatic else f"TESTNET | {chain['blocks']} blocks | {peers} peers | Wallet: {self.rpc.wallet}")
            for item in self.table.get_children():self.table.delete(item)
            self.transactions={}
            self.more_button.configure(state='normal' if len(txs)>self.history_count else 'disabled')
            for tx in reversed(txs[-self.history_count:]):
                item=self.table.insert('',tk.END,values=(transaction_time(tx),transaction_state(tx),f"{tx['amount']:.8f}",tx.get('confirmations',0)))
                self.transactions[item]=tx
        previous_status=self.status.get()
        def failed(error):
            self.network.set('Status unavailable - displayed balances may be stale. Check local node / wallet.')
            self.protection.set('Protection status unavailable')
        self.work(job,done,failed)
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
            win=tk.Toplevel(self.root);win.title('Transaction details');win.geometry('820x490')
            fields=[('Transaction ID',merged.get('txid','Unavailable')),('Address',tx.get('address','Unavailable')),
                    ('Amount (OBSC)',str(tx.get('amount','Unavailable'))),('Fee (OBSC)',str(abs(Decimal(str(merged['fee'])))) if 'fee' in merged else 'Not applicable'),
                    ('Status',transaction_state(merged)),('Confirmations',str(merged.get('confirmations',0))),
                    ('Reward maturity',maturity_text(merged)),
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
            verify_testnet(base)
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
    @user_action
    def send(self):
        address=simpledialog.askstring('Send OBSC','Recipient testnet address:',parent=self.root)
        if not address:return
        amount=simpledialog.askstring('Send OBSC','Amount in OBSC:',parent=self.root)
        if amount is None:return
        try:amount=parse_amount(amount)
        except ValueError as e:messagebox.showerror('Invalid amount',str(e));return
        if not address.startswith('tobs1'):messagebox.showerror('Wrong address','Use an Obsolete testnet address (tobs1...).');return
        def prepare():
            if not self.wallet_call('validateaddress',address)['isvalid']:raise ValueError('Invalid testnet address')
            return self.wallet_call('walletcreatefundedpsbt',[],[{address:amount}],0,{'fee_rate':1,'replaceable':True},True)
        def confirm(funded):
            fee=Decimal(str(funded['fee']));total=Decimal(amount)+fee
            self.interacting=True
            try:approved=messagebox.askyesno('Confirm transfer',f'Send {amount} TEST OBSC to\n{address}\n\nNetwork fee: {fee:.8f} OBSC\nTotal debit: {total:.8f} OBSC\n\nBroadcast this transaction?')
            finally:self.interacting=False
            if not approved:return
            def broadcast():
                signed=self.wallet_call('walletprocesspsbt',funded['psbt'])
                if not signed['complete']:raise ValueError('Transaction signing incomplete; unlock the wallet if needed')
                final=self.wallet_call('finalizepsbt',signed['psbt'])
                if not final['complete']:raise ValueError('Transaction finalization incomplete')
                return self.wallet_call('sendrawtransaction',final['hex'])
            self.work(broadcast,lambda tx:(self.status.set('Transfer submitted: '+tx),messagebox.showinfo('Submitted','Transaction ID:\n'+tx+'\n\nWait for miners to confirm it.')))
        self.work(prepare,confirm)
    @user_action
    def backup(self):
        if self.busy:return
        path=filedialog.asksaveasfilename(title='Backup local wallet',defaultextension='.dat')
        def saved(_):
            self.last_backup=Path(path).resolve()
            self.status.set('Backup saved. Keep it privately, separately from the passphrase. Use Check recovery to verify it.')
        if path:self.work(lambda:self.wallet_call('backupwallet',str(Path(path).resolve())),saved)
    def recovery_guide(self):
        win=tk.Toplevel(self.root);win.title('Protect your wallet');win.geometry('700x390')
        text=('1. Encrypt the wallet with a unique passphrase. Keep the passphrase separately.\n\n'
              '2. Save a fresh backup after encryption. Keep a private copy on another device.\n\n'
              '3. Check recovery: restore a selected backup into a temporary offline node, '
              'check its passphrase and compare its public descriptors with this wallet.\n\n'
              'This checks database/key recovery. It does not rescan balances or verify that '
              'you can recover after losing this computer. The open wallet is not replaced.')
        tk.Label(win,text=text,justify='left',wraplength=650).pack(fill='x',padx=20,pady=20)
        for label,command in [('1. Encrypt...',self.encrypt),('2. Save backup...',self.backup),('3. Check recovery...',self.check_recovery)]:
            tk.Button(win,text=label,command=command).pack(pady=4)
    @user_action
    def check_recovery(self):
        if self.busy:return
        path=filedialog.askopenfilename(title='Select private wallet backup to verify')
        if not path:return
        phrase=simpledialog.askstring('Backup passphrase','Passphrase for this backup (leave empty only if unencrypted):',show='*',parent=self.root)
        if phrase is None:return
        binary=getattr(self,'node_binary',None)
        if not binary:
            base=Path(__file__).resolve().parents[1]
            binary=next((p for p in [Path(sys.executable).parent/'bitcoind.exe',base/'bitcoind',base/'build/bin/bitcoind',base/'.local/native-node/bitcoind.exe',base/'.local/upgrade-build/bin/bitcoind'] if p.is_file()),None)
        if not binary:messagebox.showerror('Node missing','Use the complete package to check recovery.');return
        def checked(result):
            self.status.set('Backup restored offline; descriptors match'+('; passphrase verified.' if result['encrypted'] else '. Backup is unencrypted.'))
            messagebox.showinfo('Recovery check passed','Temporary restore succeeded and public descriptors match.\n'+('The backup passphrase works.\n' if result['encrypted'] else 'This backup is not encrypted.\n')+'Balances were not rescanned. Keep the backup and passphrase separately.')
        self.work(lambda:verify_backup(self.rpc,path,binary,phrase),checked)
    @user_action
    def encrypt(self):
        pw=simpledialog.askstring('Encrypt wallet','New passphrase (cannot be recovered):',show='*')
        if not pw:return
        again=simpledialog.askstring('Encrypt wallet','Repeat passphrase:',show='*')
        if again!=pw:messagebox.showerror('Mismatch','Passphrases differ.');return
        self.work(lambda:self.wallet_call('encryptwallet',pw),lambda _:self.status.set('Wallet encrypted. Make a new backup.'))
    @user_action
    def unlock(self):
        pw=simpledialog.askstring('Unlock wallet','Passphrase (unlocks for 60 seconds):',show='*')
        if pw:self.work(lambda:self.wallet_call('walletpassphrase',pw,60),lambda _:self.status.set('Unlocked for 60 seconds'))
    def lock(self):self.work(lambda:self.wallet_call('walletlock'),lambda _:self.status.set('Wallet locked'))
    @user_action
    def connect_peer(self):
        peer=simpledialog.askstring('Connect testnet peer','Peer hostname or IPv4 address and port (host:19777):',parent=self.root)
        if not peer:return
        import re
        if not re.fullmatch(r'[A-Za-z0-9.-]+:[0-9]{1,5}',peer) or not 1<=int(peer.rsplit(':',1)[1])<=65535:
            messagebox.showerror('Invalid peer','Use host:port, supplied by a testnet operator.');return
        def connected(_):
            save=getattr(self,'peer_added',None)
            if save:save(peer)
            self.status.set(('Peer saved: ' if save else 'Peer configured for this session: ')+peer)
        self.work(lambda:self.wallet_call('addnode',peer,'add'),connected)
    def toggle_mine(self):
        if self.demo:return
        if self.miner and self.miner.is_alive():self.mining.set();self.status.set('Stopping miner...');return
        if self.busy:return
        threads,duty=self.threads.get(),self.activity.get()
        self.interacting=True
        try:approved=messagebox.askyesno('CPU mining',f'Mine TEST OBSC with {threads} thread(s), {duty}% activity per thread?\n\nAbout {256*threads} MiB of mining memory, plus the node.\nActivity uses short work/rest cycles; it is not an exact total CPU limit.')
        finally:self.interacting=False
        if not approved:return
        self.mining.clear()
        self.mining_stats=MiningStats(threads,duty)
        self.thread_control.configure(state='disabled');self.activity_control.configure(state='disabled')
        def job():
            try:
                if self.wallet_call('getblockchaininfo')['initialblockdownload'] or self.wallet_call('getconnectioncount')<1:raise ValueError('Connect a testnet peer and finish synchronization before mining')
                address=self.wallet_call('getnewaddress','mining','bech32')
                mine(RPC(self.rpc.cookie,self.rpc.port,timeout=30),address,self.mining,threads=threads,duty=duty,library=getattr(self,'mining_library',None),stats=self.mining_stats)
            except Exception as e:
                with self.mining_stats.lock:
                    self.mining_stats.state='Error';self.mining_stats.ended=time.monotonic()
                self.mining_events.put('Mining: '+str(e))
        self.miner=threading.Thread(target=job,daemon=True);self.miner.start();self.status.set('CPU mining started. Refresh to see rewards.')
    def mining_tick(self):
        if self.closing:return
        if self.mining_stats:
            s=self.mining_stats.snapshot();seconds=int(s['elapsed'])
            state='Stopping' if self.mining.is_set() and self.miner and self.miner.is_alive() else s['state']
            self.mining_detail.set(f"{state} | {s['hps']:.2f} H/s | {seconds//3600:02}:{seconds//60%60:02}:{seconds%60:02} | {s['hashes']:,} hashes | {s['blocks']} accepted | {s['rejected']} stale/rejected")
            if self.miner and not self.miner.is_alive():
                self.thread_control.configure(state='readonly');self.activity_control.configure(state='readonly')
        try:
            while True:self.status.set(self.mining_events.get_nowait())
        except queue.Empty:pass
        self.root.after(1000,self.mining_tick)
    def close(self):
        self.closing=True;self.mining.set()
        def finish():
            if self.busy or (self.miner and self.miner.is_alive()):
                self.status.set('Finishing local work before closing...');self.root.after(100,finish)
            else:self.root.destroy()
        finish()

def main():
    p=argparse.ArgumentParser();p.add_argument('--demo',action='store_true');p.add_argument('--wallet',default='obsolete')
    p.add_argument('--cookie',type=Path,default=default_data_dir()/'obsolete-testnet-v2/.cookie');p.add_argument('--rpcport',type=int,default=19778)
    a=p.parse_args();root=tk.Tk();Wallet(root,RPC(a.cookie,a.rpcport,a.wallet),a.demo);root.mainloop()
if __name__=='__main__':main()
