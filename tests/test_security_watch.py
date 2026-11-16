import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from check_upstream_security import newer_advisories


class AdvisoryTests(unittest.TestCase):
    def test_only_new_official_dated_disclosures(self):
        html='''<a href="/en/2026/11/10/disclose-cve-1/">old</a>
        <a href="/en/2026/11/17/disclose-cve-2/">new</a>
        <a href="/en/2026/11/17/disclose-cve-2/">duplicate</a>
        <a href="https://untrusted.invalid/en/2026/11/18/disclose-cve-3/">external</a>
        <a href="/en/2026/11/18/release/">release</a>'''
        self.assertEqual(newer_advisories(html,'2026-11-16'),
                         ['https://bitcoincore.org/en/2026/11/17/disclose-cve-2/'])


if __name__=='__main__':unittest.main()
