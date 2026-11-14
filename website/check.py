"""Validate every generated HTML page and its local links without network access."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,unquote
import argparse,json
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();root=a.directory.resolve()
class Parser(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.ids=set();self.scripts=0
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs:self.ids.add(attrs['id'])
        if tag=='script':self.scripts+=1
        for name in ('href','src'):
            if name in attrs:self.links.append(attrs[name])
        assert not any(k.lower().startswith('on') for k in attrs),'Inline event handler'
parsers={}
for page in root.rglob('*.html'):
    text=page.read_text(encoding='utf-8');parser=Parser();parser.feed(text)
    assert parser.scripts==0,page
    assert '<html lang="en">' in text and '<h1' in text,page
    assert 'Please wait. It is still 1995.' not in text and 'Obsolete Coin 95' not in text,page
    parsers[page]=parser
count=0
for page,parser in parsers.items():
    for link in parser.links:
        url=urlsplit(link)
        if url.scheme or url.netloc:continue
        target=(page.parent/unquote(url.path)).resolve() if url.path else page
        assert target.is_relative_to(root),(page,link)
        if target.is_dir():target=target/'index.html'
        assert target.is_file(),(page,link,target)
        if url.fragment:assert target in parsers and unquote(url.fragment) in parsers[target].ids,(page,link)
        count+=1
print(json.dumps({'html_pages':len(parsers),'local_links_checked':count,'scripts':0,'broken_links':0}))
