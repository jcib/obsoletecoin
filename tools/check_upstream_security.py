"""Read-only alert for Bitcoin Core disclosures published after the recorded review.

This is a reminder, not a vulnerability scanner or proof that a fork is patched.
"""
import datetime
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.request
from urllib.parse import urljoin, urlparse

INDEX='https://bitcoincore.org/en/security-advisories/'


class Links(HTMLParser):
    def __init__(self):super().__init__();self.urls=set()
    def handle_starttag(self,tag,attrs):
        if tag=='a':
            href=dict(attrs).get('href','')
            url=urljoin(INDEX,href)
            if urlparse(url).netloc=='bitcoincore.org':self.urls.add(url)


def newer_advisories(html,reviewed_through):
    parser=Links();parser.feed(html)
    dated=[]
    for url in parser.urls:
        match=re.match(r'/en/(\d{4})/(\d{2})/(\d{2})/[^/]*(?:disclos|cve)[^/]*/',urlparse(url).path)
        if match:
            date=datetime.date(*map(int,match.groups()))
            if date>datetime.date.fromisoformat(reviewed_through):dated.append(url)
    return sorted(dated)


def main():
    root=Path(__file__).resolve().parents[1]
    baseline=json.loads((root/'docs/security-upstream.json').read_text())
    request=urllib.request.Request(INDEX,headers={'User-Agent':'ObsoleteCoin-security-review/1.0'})
    with urllib.request.urlopen(request,timeout=30) as response:
        html=response.read(2*1024*1024+1)
    if len(html)>2*1024*1024:raise ValueError('Advisory index exceeds expected size')
    if 'Security Advisories' not in html.decode():raise ValueError('Unexpected advisory index')
    urls=newer_advisories(html.decode(),baseline['reviewed_through'])
    print(json.dumps({'source':INDEX,'reviewed_through':baseline['reviewed_through'],
                      'needs_review':urls,'scope':'New publication dates only; no applicability claim'},indent=2))
    return 1 if urls else 0


if __name__=='__main__':raise SystemExit(main())
