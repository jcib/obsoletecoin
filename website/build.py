"""Build a portable, script-free website and a real static testnet explorer."""

import argparse,datetime,hashlib,html,json,shutil

from decimal import Decimal

from pathlib import Path

P=argparse.ArgumentParser();P.add_argument('--snapshot',type=Path,required=True);P.add_argument('--output',type=Path,required=True);P.add_argument('--live',action='store_true');P.add_argument('--public-web-only',action='store_true');a=P.parse_args()
ROOT=Path(__file__).resolve().parents[1];OUT=a.output.resolve();OUT.mkdir(parents=True,exist_ok=True)

S=json.loads(a.snapshot.read_text(encoding='utf-8'));BLOCKS=S['blocks'];BY_HEIGHT={b['height']:b for b in BLOCKS}

TX={t['txid']:(b,t) for b in BLOCKS for t in b['tx']};ADDR={}

for b,t in TX.values():

    for output in t['vout']:

        address=output['scriptPubKey'].get('address')

        if address:ADDR.setdefault(address,[]).append((b,t,output))

E=lambda x:html.escape(str(x),quote=True)

def utc(t):return datetime.datetime.fromtimestamp(t,datetime.timezone.utc).strftime('%d %b %Y, %H:%M:%S UTC')

def amount(v):return f'{Decimal(str(v)):,.8f}'

CAPTURE=datetime.datetime.fromisoformat(S['captured_at']).strftime('%d %b %Y, %H:%M:%S UTC')

ORIGIN='https://obsoletecoin.pages.dev'

GITHUB='https://github.com/jcib/obsoletecoin'

for folder in ('assets','downloads','explorer/blocks','explorer/transactions','explorer/addresses'):(OUT/folder).mkdir(parents=True,exist_ok=True)

for f in (ROOT/'website/assets').iterdir():
    if f.suffix.lower() not in ('.mp3','.wav','.ogg'):shutil.copyfile(f,OUT/'assets'/f.name)

DOWNLOADS=[('source.tar.gz',ROOT/'.local/release/ObsoleteCoin-Review-Source.tar.gz'),('windows-wsl.zip',ROOT/'.local/release/ObsoleteCoin-Windows-WSL.zip'),('linux-x64.tar.gz',ROOT/'.local/release/ObsoleteCoin-Linux-Testnet.tar.gz'),('windows-native-testnet.exe',ROOT/'.local/release/ObsoleteCoin-Testnet-Setup.exe')]

if a.public_web_only:DOWNLOADS=[(name,path) for name,path in DOWNLOADS if name!='source.tar.gz']
CHECKSUMS={}

for name,path in DOWNLOADS:

    data=path.read_bytes();CHECKSUMS[name]=hashlib.sha256(data).hexdigest();(OUT/'downloads'/name).write_bytes(data)

(OUT/'downloads/SHA256SUMS.txt').write_text(''.join(f'{v}  {k}\n' for k,v in CHECKSUMS.items()),encoding='utf-8')

(OUT/'explorer/snapshot.json').write_text(json.dumps(S,indent=2),encoding='utf-8')



def write_page(path,title,content,active='home'):

    depth=len(Path(path).parts)-1;r='../'*depth

    nav=[('downloads','downloads.html','Downloads','download.gif'),('explorer','explorer/index.html','Block explorer','terminal.gif'),('coin','coin.html','The coin','computer.gif'),('mining','mining.html','How to mine','mining.gif'),('forum','forum','Forum','forum.gif')]

    links=''.join(f'<a href="{r}{url}"'+(' aria-current="page"' if key==active else '')+f'><img src="{r}assets/{icon}" alt="" width="80" height="80"><span>{label}</span></a>' for key,url,label,icon in nav)

    doc=f"""<!doctype html>

<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">

<title>{E(title)} | Obsolete Coin</title><meta name="description" content="Obsolete Coin (OBSC). CPU mining, testnet downloads and blockchain data.">

<meta name="robots" content="noindex,nofollow"><meta name="referrer" content="no-referrer"><meta name="theme-color" content="#000033">

<meta property="og:title" content="Obsolete Coin"><meta property="og:description" content="It's tacky, cheap, and slow."><meta property="og:url" content="{ORIGIN}/{E(path)}">

<link rel="icon" href="{r}assets/obsolete-coin.gif" type="image/gif"><link rel="stylesheet" href="{r}assets/style.css"></head>

<body><a class="skip" href="#content">Skip to content</a><div class="site">

<header class="masthead"><a class="brand" href="{r}index.html"><img src="{r}assets/obsolete-coin.gif" alt="" width="80" height="80"><span>Obsolete Coin</span></a>

<img class="redline" src="{r}assets/roughredline.gif" alt="" width="550" height="20">

<p class="slogan">It's tacky, cheap, and slow.</p>

<p class="intro">Slow life, slow money</p><p class="micro">CPU MINED &nbsp; / &nbsp; SLOW BY DESIGN &nbsp; / &nbsp; NO PREMINE</p>



<p class="notice">Experimental testnet v0.2 &mdash; <a href="{r}faq.html#mainnet">Mainnet is not live.</a><br>Test coins have no monetary value.</p></header>

<nav class="nav" aria-label="Main navigation">{links}</nav>

<div class="link-table"><a href="{r}index.html">Home</a><a href="{r}faq.html">Questions &amp; answers</a><a href="{GITHUB}">GitHub</a><a href="{r}roadmap.html">Mainnet status</a></div>

<main class="content" id="content">{content.replace('@ROOT@',r)}</main>

<footer class="footer"><img class="redline" src="{r}assets/roughredline.gif" alt="" width="550" height="20"><div class="footer-links"><a href="{r}index.html">Home</a> | <a href="{r}downloads.html">Downloads</a> | <a href="{r}explorer/index.html">Explorer</a> | <a href="{r}roadmap.html">Mainnet status</a> | <a href="{r}nodes.html">Run a node</a> | <a href="{r}forum">Forum</a> | <a href="{GITHUB}">GitHub</a></div><p>Page archive: {E(CAPTURE)}</p><div class="credits"><p>Visual inspiration: <a href="https://geocities.restorativland.org/SiliconValley/1000/">GeoCities &mdash; SiliconValley/1000</a>, archived by Restorativland.</p></div></footer></div></body></html>"""

    if a.live:

        doc=doc.replace('(private during testing).','').replace('(private repository during testing).','')

        import re

        from urllib.parse import urljoin

        doc=re.sub(r'(href|src)="([^"]+)"',lambda m:m[1]+'="'+urljoin('/'+path,m[2])+'"',doc)

        doc=doc.replace('<p>Page archive: '+E(CAPTURE)+'</p>', '<p>Experimental testnet. No monetary value. Chain resets are possible.</p>')

    if a.public_web_only:
        import re
        doc=doc.replace('>GitHub</a>','>GitHub (public)</a>').replace('>Source code</a>','>GitHub (public)</a>')
        doc=doc.replace('>jcib/obsoletecoin</a>','>jcib/obsoletecoin (public)</a>')
        doc=re.sub(r'<a href="(?:/)?downloads/source.tar.gz">Download the review source</a>', '<a href="https://github.com/jcib/obsoletecoin">Source code on GitHub</a>',doc)
    (OUT/path).write_text(doc,encoding='utf-8')



def download_cards():

    return """<div class="download-grid"><article class="download"><h3><img src="@ROOT@assets/windows.gif" alt="">Windows native</h3><p>Testnet wallet, local node and CPU miner. No WSL required.</p><a class="button" href="@ROOT@downloads/windows-native-testnet.exe" download>DOWNLOAD .EXE &darr;</a><div class="minor">x86-64 &middot; <a href="@ROOT@mining.html#windows-native">Setup instructions</a><br><a href="@ROOT@downloads/windows-wsl.zip" download>Alternative: Windows + WSL ZIP</a></div></article>

<article class="download"><h3><img src="@ROOT@assets/linux.gif" alt="">Linux</h3><p>The testnet node, command-line tools and retro desktop wallet.</p><a class="button" href="@ROOT@downloads/linux-x64.tar.gz" download>DOWNLOAD .TAR.GZ &darr;</a><div class="minor">v0.2 &middot; x86-64 &middot; <a href="@ROOT@mining.html#linux">Setup instructions</a></div></article></div>"""



latest=''.join(f'<li><a href="explorer/blocks/{b["height"]}.html">Block #{b["height"]}</a><span>{len(b["tx"])} tx</span></li>' for b in reversed(BLOCKS[-5:]))

home=f"""<h1 class="home-title">Obsolete Coin (OBSC)</h1>

<section class="home-downloads"><h2>Testnet downloads</h2>{download_cards()}</section>

<div class="under-construction"><img src="assets/construction.gif" alt="" width="64" height="64"><p><strong>Native Windows test wallet.</strong><br>Installation and wallet recovery tested on Windows 11. <a href="roadmap.html">Mainnet requirements</a></p></div>

<table class="home-facts"><tbody><tr><th>Maximum issuance</th><th>Target block interval</th><th>Mining</th></tr><tr><td>1,000,000,000 OBSC</td><td>15 minutes</td><td>RandomX / CPU</td></tr></tbody></table>

<section class="node-section"><h2>First node: Dell Micro 7040 (2016)</h2><img class="server-photo" src="assets/servidor.jpeg" alt="Dell Micro 7040 used as the first Obsolete Coin testnet node"><p>Experimental testnet node. CPU mining runs on a separate computer.</p></section>

<section class="block-section"><h2>Recent blocks</h2><ul class="block-mini">{latest}</ul><p>Captured {E(CAPTURE)}. This is an archive, not a live feed.</p><p><a href="explorer/index.html">Open the block explorer</a></p></section>

<p class="network-note">The 15-minute interval is a target, not a fixed delay. Initial testnet difficulty is intentionally easy.<br><a href="coin.html">Technical specifications</a> | <a href="{GITHUB}">Source code</a> (private during testing).</p>"""

if a.live:

    start=home.index('<section class="block-section">');end=home.index('</section>',start)+len('</section>')

    home=home[:start]+'<section class="block-section"><h2>Recent blocks</h2><iframe class="live-frame compact" title="Live recent blocks" src="/live/recent"></iframe></section><p><a class="button" href="join.html">JOIN THE TESTNET</a></p>'+home[end:]

write_page('index.html','Home',home)



checks=''.join(f'<p><strong>{E(k)}</strong><br><code class="hash">{v}</code></p>' for k,v in CHECKSUMS.items())

write_page('downloads.html','Downloads',f"""<h1 class="page-title">Downloads</h1><p class="lede">Testnet packages for native Windows, Windows with WSL and Linux.</p><p><a href="https://github.com/jcib/obsoletecoin/releases/tag/v0.3.0-testnet-rc1">GitHub Release: installers, portable packages and compiled binaries</a></p>{download_cards()}<div class="under-construction">These are experimental testnet packages. Mainnet remains disabled.</div><h2 class="section-head">Package contents</h2><div class="paper"><ul><li>A full testnet node and a local wallet with send, receive, encryption and backup.</li><li>A single-threaded RandomX reference miner. Mining uses the computer running the node.</li><li>Windows launchers in the WSL ZIP. These use Debian inside WSL; they are not native Windows binaries.</li><li>Build, operation and license documentation.</li></ul><p>Use the current first-node address and connection status on the <a href="join.html">Join the testnet</a> page. No DNS seed network is supplied.</p><p><a href="mining.html">Read the setup guide before opening the package &raquo;</a></p></div><h2 class="section-head">SHA-256 verification</h2><div class="paper"><p>SHA-256 checksums identify these exact files. They are checksums, not signed releases.</p><p><a href="downloads/SHA256SUMS.txt" download>Download SHA256SUMS.txt</a></p>{checks}</div><h2 class="section-head">Other systems</h2><div class="paper"><p><strong>Native Windows:</strong> x86-64 test candidate, tested on Windows 11 build 26300. <strong>macOS and ARM:</strong> no validated packages in this release.</p><p>Source code: <a href="{GITHUB}">jcib/obsoletecoin</a> (private repository during testing).</p><p class="tiny">Compiled inputs (sanitized history): Windows node 3560329; desktop 950f6bc; Linux node 6f1d111; WSL node 5a89029. Packages include updated setup instructions. Native installer checks include mining, reinstall and wallet preservation. Official code signing and independent reproducible builds remain pending. Wallet keys, cookies and local balances are not included in any download.</p></div>""",'downloads')



facts=[('Name / working ticker','Obsolete Coin / OBSC'),('Mining','RandomX proof of work, CPU'),('Maximum authorized issuance','1,000,000,000 OBSC'),('Decimal places','8'),('Target block interval','900 seconds / 15 minutes'),('Difficulty adjustment','ASERT, every block; six-hour half-life'),('Initial block reward','5,000 OBSC'),('Halving interval','100,000 blocks, counted from block 1'),('Genesis reward / premine','Zero / none'),('Mining reward maturity','100 blocks'),('End of subsidy','Block 3,900,000; transaction fees thereafter'),('Current network','Experimental testnet v0.2; mainnet disabled')]

write_page('coin.html','The coin',f"""<h1 class="page-title">Technical specifications</h1><p class="lede">Obsolete Coin network parameters.</p><table class="facts"><tbody>{''.join(f'<tr><th scope="row">{E(k)}</th><td>{E(v)}</td></tr>' for k,v in facts)}</tbody></table><h2 class="section-head">Slow is the target</h2><div class="paper"><p>The software does not delay your payment with a timer. Miners produce blocks, and the difficulty adjusts toward an average interval of 15 minutes. Real waits vary. Initial testnet difficulty is deliberately easy.</p><p>More hash power raises difficulty over time; it does not guarantee an exact calendar schedule. The included reference miner uses one CPU thread.</p></div><h2 class="section-head">A finite supply</h2><div class="paper"><p>The integer reward schedule authorizes exactly one billion OBSC. A one-off 0.013 OBSC rounding remainder is included at the final rewarded block. Unclaimed rewards and lost keys reduce the circulating amount.</p><p>At the target interval, halvings are roughly 2.85 years apart. The inherited timestamp format needs an upgrade before 2106, earlier than the theoretical end of the subsidy schedule.</p></div><h2 class="section-head">Where it comes from</h2><div class="paper"><p>This is a fork of Brisvia and Bitcoin Core, with pinned upstream RandomX. Original licenses are preserved. A Bitcoin-derived codebase does not give a new chain Bitcoin's hash power or security.</p><p><a href="{GITHUB}/blob/main/docs/SPEC.md">Read the full specification on GitHub &raquo;</a></p></div>""",'coin')



write_page('mining.html','How to mine',"""<h1 class="page-title">Mining instructions</h1><p class="lede">Installation and operation of the testnet node and miner.</p><div class="snapshot-note"><strong>Testnet only.</strong> Use the current peer on the <a href="join.html">Join the testnet</a> page. Test balances do not become mainnet coins.</div><div class="paper"><h2 id="windows-native">Native Windows x86-64</h2><ol><li>Download and install the testnet EXE. It needs neither WSL nor a separate Python installation.</li><li>Open Obsolete Coin. In <strong>Network &gt; Connect peer</strong>, enter the testnet address and P2P port supplied by your operator.</li><li>Wait for synchronization, then use <strong>Mine / Stop</strong>. CPU mining runs locally with one thread.</li><li>Use <strong>Encrypt</strong> and <strong>Backup</strong> to protect the wallet. The native data directory is <code>%USERPROFILE%\.obsoletecoin</code>, separate from your WSL wallet. Closing the app stops the node it started; uninstalling preserves wallet data.</li></ol><p><a href="https://github.com/jcib/obsoletecoin/blob/main/docs/WINDOWS-NATIVE.md">Native Windows guide</a></p><h2 id="windows">Windows + WSL (alternative)</h2><ol><li>Install Debian in WSL. From an administrator PowerShell:<pre class="code">wsl --install -d Debian</pre>Restart if Windows requests it, then open Debian to finish setup.</li><li>Inside Debian, install the runtime libraries:<pre class="code">sudo apt-get update

sudo apt-get install python3 python3-tk \

  libevent-2.1-7t64 libevent-core-2.1-7t64 \

  libevent-extra-2.1-7t64 libevent-pthreads-2.1-7t64 libsqlite3-0</pre></li><li><a href="downloads/windows-wsl.zip" download>Download the Windows + WSL ZIP</a> and extract it. Use the current peer address from the Join guide when starting the launcher.</li><li>Open <code>Start-Mining.cmd</code>. It starts your local node and mines into your local wallet. Keep the window open.</li><li>Open <code>Start-Wallet.cmd</code> to view the wallet. Graphical use requires WSL graphical support. Press Ctrl-C in the mining window to stop.</li></ol><h2 id="linux">Linux x86-64</h2><p>Install the same runtime libraries on Debian 13. Extract the Linux archive, enter the extracted directory and start the node with your peer:</p><pre class="code">python3 tools/node.py --peer YOUR_PEER_IP:19777

# In a second graphical terminal:

python3 tools/wallet.py</pre><p>Choose <strong>Open / Create</strong>, then <strong>Receive</strong>. Choose <strong>Mine / Stop</strong> to start the reference miner.</p><h2>Before you close the window</h2><ul><li>New mining rewards are immature until they satisfy the 100-block maturity rule.</li><li>Your wallet is initially unencrypted. Use <strong>Encrypt</strong>, then make a new private <strong>Backup</strong>. Keep its passphrase safe.</li><li>Keys live on the mining computer. Do not delete its WSL distribution or data directory without a verified wallet backup.</li><li>The current chain is v0.2. Old experimental blocks and balances are incompatible.</li></ul><p><a href="https://github.com/jcib/obsoletecoin/blob/main/docs/WINDOWS.md">Full Windows guide</a> &middot; <a href="https://learn.microsoft.com/windows/wsl/install/">Microsoft's WSL installation guide</a></p></div>""",'mining')



questions=[('mainnet','Is this the real mainnet?','No. This is experimental testnet v0.2. The mainnet is disabled. Test coins have no monetary value and do not automatically carry over to a future mainnet.'),('native','Where is the native Windows wallet?','A native x86-64 test candidate is available on Downloads. It includes the local node and miner and needs no WSL. Installation and wallet preservation were tested on Windows 11. Broader supported-system validation remains pending.'),('speed','Why did my block arrive so quickly?','Initial testnet difficulty is intentionally easy. Fifteen minutes is the target average, not a fixed delay for each transaction or a promise for early test blocks.'),('maturity','I mined coins. Why can I not spend them?','Block rewards must satisfy the 100-block maturity rule. The wallet lists them as immature until they become spendable.'),('security','Do four confirmations make a payment safe?','Not against a miner that dominates a small proof-of-work network. Such a miner can reorganize valid blocks and reverse its own payments. Confirmations are not absolute finality.'),('explorer','Is the explorer live?','No. It is a genuine HTML archive of public blocks and transactions, exported at the time shown on every explorer page. It does not poll a node. New blocks appear only after a new export is published.'),('github','Where is the source code?','The public GitHub repository includes the source, build instructions, test evidence and issue tracker. GitHub may require an account to report an issue.'),('keys','Can the website recover my wallet?','No. It does not request seed phrases, private keys, wallet files or RPC passwords. Protect your local wallet and keep secure backups.'),('return','Is there a promised return?','No. This is experimental software and a test network, not a promise of income, exchange listing or investment performance.')]

if a.live:

    questions=[(k,q,('Yes. Public data from the Dell node is refreshed every 15 seconds. A visible warning appears when observations are older than 60 seconds. This explorer covers at most 1024 recent blocks and only confirmed transactions; it is not a wallet balance service.' if k=='explorer' else answer)) for k,q,answer in questions]

write_page('faq.html','Questions & answers','<h1 class="page-title">Frequently asked questions</h1><p class="lede">Testnet operation and limitations.</p><div class="paper">'+''.join(f'<details id="{key}"'+(' open' if i==0 else '')+f'><summary>{E(q)}</summary><p>{E(answer)}</p></details>' for i,(key,q,answer) in enumerate(questions))+'</div>','faq')

write_page('roadmap.html','Road to mainnet',"""<h1 class="page-title">Mainnet requirements</h1><p class="lede">Mainnet activation is blocked pending security and operational validation.</p><div class="paper"><ul class="status-list"><li><b>AVAILABLE</b> Experimental CPU-mined testnet, Linux package, native Windows test installer and alternative WSL launcher.</li><li><b>REQUIRED</b> Native Windows releases, independently reproduced and tested on every supported Windows version.</li><li><b>REQUIRED</b> Independent consensus/security review, sustained public testnet and hostile-traffic testing. Local/CI adversarial and recovery regressions have passed.</li><li><b>REQUIRED</b> A public launch plan, independent miners, peer infrastructure and initial-difficulty calibration.</li><li><b>UNSCHEDULED</b> Mainnet. There is no announced release date and no automatic conversion of test coins.</li></ul><p><a href="https://github.com/jcib/obsoletecoin/blob/main/docs/MAINNET-READINESS.md">Read the current security and launch notes &raquo;</a></p></div>""",'coin')



if not a.live:

    NOTICE=f'<div class="snapshot-note"><strong>STATIC TESTNET ARCHIVE</strong><br>Captured {E(CAPTURE)}. Blocks {S["first_height"]}&ndash;{S["height"]}. Newer blocks are not shown until the next export. <a href="@ROOT@explorer/snapshot.json" download>Download public snapshot JSON</a>.</div>'

    rows=''.join(f'<tr><td class="table-number"><a href="blocks/{b["height"]}.html">#{b["height"]}</a></td><td class="mono"><a href="blocks/{b["height"]}.html">{b["hash"][:16]}&hellip;</a></td><td class="table-number">{len(b["tx"])}</td><td>{E(utc(b["time"]))}</td></tr>' for b in reversed(BLOCKS))

    write_page('explorer/index.html','Block explorer',f'<h1 class="page-title">Block explorer</h1><p class="lede">Public testnet blocks and transactions.</p>{NOTICE}<div class="stats"><div><strong>{S["height"]}</strong><span>CAPTURED HEIGHT</span></div><div><strong>{len(TX)}</strong><span>ARCHIVED TRANSACTIONS</span></div><div><strong>{len(ADDR)}</strong><span>OUTPUT ADDRESSES</span></div></div><p><a href="addresses/index.html">Browse address activity &raquo;</a> <span class="tiny dim">Use your browser\'s Find command to locate a block height on this page.</span></p><div class="scroll"><table><thead><tr><th scope="col">Height</th><th scope="col">Block hash</th><th scope="col">Tx</th><th scope="col">Block time</th></tr></thead><tbody>{rows}</tbody></table></div>','explorer')

    for b in BLOCKS:

        height=b['height'];prev=f'<a href="{height-1}.html">&laquo; Block {height-1}</a>' if height-1 in BY_HEIGHT else 'Start of archive'

        nxt=f'<a href="{height+1}.html">Block {height+1} &raquo;</a>' if height+1 in BY_HEIGHT else 'End of archive'

        facts=[('Block hash',f'<span class="mono hash">{E(b["hash"])}</span>'),('Block time',E(utc(b['time']))),('Confirmations at capture',str(S['height']-height+1)),('Transactions',str(len(b['tx']))),('Size',f'{b["size"]:,} bytes'),('Weight',f'{b["weight"]:,}'),('Difficulty',E(b['difficulty'])),('Target bits',E(b['bits'])),('Nonce',str(b['nonce'])),('Merkle root',f'<span class="mono hash">{E(b["merkleroot"])}</span>')]

        table=''.join(f'<tr><th scope="row">{key}</th><td>{value}</td></tr>' for key,value in facts)

        txrows=''.join(f'<tr><td><a class="mono hash" href="../transactions/{t["txid"]}.html">{t["txid"]}</a></td><td>{"Block reward" if "coinbase" in t["vin"][0] else "Transfer"}</td><td>{len(t["vout"])}</td></tr>' for t in b['tx'])

        write_page(f'explorer/blocks/{height}.html',f'Block {height}',f'<p class="crumb"><a href="../index.html">Explorer</a> / Block {height}</p><h1 class="page-title">Block #{height}</h1>{NOTICE}<p>{prev} &nbsp; | &nbsp; {nxt}</p><table class="facts"><tbody>{table}</tbody></table><h2 class="section-head">Transactions</h2><table><thead><tr><th>Transaction ID</th><th>Type</th><th>Outputs</th></tr></thead><tbody>{txrows}</tbody></table>','explorer')

    for txid,(b,t) in TX.items():

        outs=[]

        for v in t['vout']:

            addr=v['scriptPubKey'].get('address');target=f'<a class="mono hash" href="../addresses/{E(addr)}.html">{E(addr)}</a>' if addr else '<span class="mono">'+E(v['scriptPubKey']['type'])+'</span>'

            outs.append(f'<tr><td>{v["n"]}</td><td>{target}</td><td class="table-number">{amount(v["value"])} OBSC</td></tr>')

        inputs=[]

        for vin in t['vin']:

            if 'coinbase' in vin:inputs.append('<li>Coinbase input: block reward, created according to the subsidy rules.</li>')

            else:

                source=vin['txid'];label=f'{source}:{vin["vout"]}'

                inputs.append('<li class="mono hash">'+(f'<a href="{source}.html">{label}</a>' if source in TX else E(label)+' (outside this archive)')+'</li>')

        write_page(f'explorer/transactions/{txid}.html','Transaction',f'<p class="crumb"><a href="../index.html">Explorer</a> / <a href="../blocks/{b["height"]}.html">Block {b["height"]}</a> / Transaction</p><h1 class="page-title">Transaction record</h1>{NOTICE}<div class="paper"><p class="mono hash">{txid}</p><p>Included in <a href="../blocks/{b["height"]}.html">block #{b["height"]}</a>. {S["height"]-b["height"]+1} confirmations at capture.</p><h2>Inputs</h2><ul>{"".join(inputs)}</ul></div><h2 class="section-head">Outputs</h2><div class="scroll"><table><thead><tr><th>Index</th><th>Address / script type</th><th>Amount</th></tr></thead><tbody>{"".join(outs)}</tbody></table></div>','explorer')

    address_items=''.join(f'<li><a class="mono hash" href="{E(addr)}.html">{E(addr)}</a> &mdash; {len(outputs)} recorded outputs</li>' for addr,outputs in sorted(ADDR.items()))

    write_page('explorer/addresses/index.html','Address index',f'<p class="crumb"><a href="../index.html">Explorer</a> / Addresses</p><h1 class="page-title">Address index</h1>{NOTICE}<div class="paper"><p>Public output addresses found in this archive. These records do not identify people and are not wallet balances.</p><ul class="address-index">{address_items}</ul></div>','explorer')

    for addr,records in ADDR.items():

        rows=''.join(f'<tr><td><a href="../blocks/{b["height"]}.html">#{b["height"]}</a></td><td><a class="mono hash" href="../transactions/{t["txid"]}.html">{t["txid"][:20]}&hellip;</a></td><td class="table-number">{amount(v["value"])} OBSC</td></tr>' for b,t,v in reversed(records))

        write_page(f'explorer/addresses/{addr}.html','Address activity',f'<p class="crumb"><a href="../index.html">Explorer</a> / <a href="index.html">Addresses</a></p><h1 class="page-title">Address activity</h1>{NOTICE}<div class="paper"><p class="mono hash">{E(addr)}</p><p>{len(records)} outputs recorded in this archive. This is an output history, <strong>not a current spendable balance</strong>.</p></div><h2 class="section-head">Recorded outputs</h2><div class="scroll"><table><thead><tr><th>Block</th><th>Transaction</th><th>Output amount</th></tr></thead><tbody>{rows}</tbody></table></div>','explorer')

else:

    write_page('explorer/index.html','Block explorer','<h1 class="page-title">Live testnet explorer</h1><p>Automatic refresh every 15 seconds. <a href="/explorer/network.html">Network power, history and reward distribution</a></p><iframe class="live-frame" title="Live testnet explorer" src="/live/explorer/index.html"></iframe>','explorer')

    write_page('join.html','Join the testnet',"""<h1 class="page-title">Join the Obsolete Coin testnet</h1><p class="lede">Experimental v0.2 network. Test coins have no monetary value. Resets may erase all test balances; they will not convert into mainnet coins.</p><iframe class="live-frame compact" title="Current first-node address" src="/live/peer"></iframe><h2>Windows</h2><ol><li><a href="downloads.html">Download the native x64 installer</a> and compare its SHA-256 with the published checksum. Tested on Windows 11.</li><li>Open Obsolete Coin. In <strong>Network ? Connect peer</strong>, enter the current public peer shown above.</li><li>Wait for synchronization and a connected peer. Compare your block height and hash with the explorer.</li><li>Select <strong>Open / Create</strong>, then <strong>Receive</strong>. Select <strong>Mine / Stop</strong> to run the one-thread CPU reference miner.</li></ol><h2>Linux</h2><p>Extract the Linux archive and open a terminal in its directory. Replace PUBLIC_PEER with the address shown above.</p><pre>python3 tools/node.py --peer PUBLIC_PEER

# In a second terminal:

python3 tools/wallet.py</pre><h2>What to test</h2><ul><li>Fresh synchronization, mining and confirmation of rewards.</li><li>Transfers between two independently created wallets, including exact fees and timestamps.</li><li>Restarting your own wallet, reconnecting and making an encrypted backup.</li><li>Report reproducible errors with operating system, package version, block height and redacted logs in <a href="https://github.com/jcib/obsoletecoin/issues/new/choose">GitHub Issues</a> or the announcement thread.</li></ul><p>Mining rewards require 100-block maturity. Fifteen minutes is an average target; initial test difficulty is easy and real waits vary. Do not interpret a mined reward as immediately spendable.</p><p>The first node is a Dell Micro 7040 from 2016 on a home connection. Availability is best effort; independent node operators are welcome. A dominant miner can reorganize this small network.</p><p>Never post a wallet file, seed, private key, passphrase or RPC cookie. Do not open RPC ports to the Internet. Outbound-only mining computers do not need router port forwarding.</p><p><a href="downloads/source.tar.gz">Download the review source</a> ? <a href="explorer/index.html">Explorer</a> ? <a href="downloads.html">Downloads and checksums</a></p>""")

write_page('404.html','Page not found','<h1 class="page-title">Page not found</h1><div class="paper"><p>The page you are looking for is not in this archive.</p><p><a href="index.html">Return to the homepage &raquo;</a></p></div>')

(OUT/'robots.txt').write_text('User-agent: *\nDisallow: /\n',encoding='utf-8')

print(json.dumps({'html_pages':len(list(OUT.rglob('*.html'))),'blocks':len(BLOCKS),'transactions':len(TX),'addresses':len(ADDR),'captured_at':CAPTURE,'downloads':CHECKSUMS}))


write_page('forum-template.html','Forum','<!--FORUM_CONTENT-->','forum')
write_page('nodes.html','Run a node',"""<h1 class="page-title">Run an Obsolete Coin node</h1><p class="lede">A full node verifies blocks and transactions and relays them to other peers. Mining is optional.</p><div class="paper"><h2>What a node contributes</h2><ul><li>Independent verification of proof of work, signatures and issuance rules.</li><li>Another source of blocks for new users synchronizing the testnet.</li><li>More connection paths when another node goes offline.</li></ul><p>A node does not earn rewards just for being online. Mining adds proof of work and can earn test coins; extra nodes alone do not prevent majority-hash-power attacks.</p><h2>Windows</h2><p>Install the native wallet, open it and connect to the current peer on the <a href="/join.html">Join guide</a>. Leave the application running to keep its node online. You can receive and relay blocks without starting the miner. The current Windows desktop app makes outbound connections only; use the Linux/WSL dedicated-node command below to accept incoming peers.</p><h2>Linux: dedicated node</h2><p>Use the Debian 13 x86-64 package and install the runtime dependencies listed in <a href="/mining.html#linux">the Linux guide</a>. Extract it, open a terminal in its directory, create a separate data directory and run the included daemon. Replace PUBLIC_PEER with the current address on the Join guide.</p><pre class="code">mkdir -p "$HOME/.obsoletecoin-node"
./bitcoind -chain=obsolete-test -datadir="$HOME/.obsoletecoin-node" -server=1 -disablewallet=1 -listen=1 -port=19777 -rpcbind=127.0.0.1 -rpcallowip=127.0.0.1 -addnode=PUBLIC_PEER -maxconnections=32 -maxuploadtarget=1024</pre><p>Keep the process running. For unattended operation, configure a service under a dedicated unprivileged account. Monitor disk space, RAM, traffic and software updates. The upload target is not a hard network bandwidth cap.</p><h2>Accepting incoming peers</h2><p>The dedicated-node command above enables listening. Forwarding a router port alone does not enable listening in the Windows desktop app.</p><ol><li>Allow TCP 19777 in the host firewall.</li><li>If behind a router, forward TCP 19777 to this node. CGNAT may prevent inbound connections.</li><li>Keep RPC 19778 local. Never forward it or use the router's DMZ-host option.</li><li>Check synchronization against the <a href="/explorer/index.html">explorer</a> and test reachability from another Internet connection.</li><li>Share your public peer address in the <a href="/forum">forum</a> if you want others to connect. That makes your public IP visible.</li></ol><p>Nodes behind NAT can still validate and connect outward. A reachable node is more useful for accepting new participants. Verify peer information yourself; forum aliases are not authenticated.</p></div>""",'coin')
