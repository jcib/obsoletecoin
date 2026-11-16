# Native Linux 0.4.0 publication

Published 2026-11-16 alongside the existing Windows 0.4.0-testnet-rc1 binaries.
Linux source/packaging commit: `698b3d148e048aa818a28f44c89b8e8cbdf83243`.
The existing release tag and Windows binary assets were preserved.

- Release: https://github.com/jcib/obsoletecoin/releases/tag/v0.4.0-testnet-rc1
- Website: https://obsoletecoin.pages.dev/downloads.html
- Verified Pages deployment: https://1f1d33bd.obsoletecoin.pages.dev
- Native Linux archive SHA-256: `c539c352383d2adf8ad272f2f968c56175ca3b026e56411621312a9b9c5fabd9`.
- GitHub and website files were downloaded anonymously and their hashes checked;
  see `linux-publication.json` for exact URLs and results.
- Desktop and mobile browser checks passed for version parity, links, archive
  hash, the top marquee and absence of horizontal overflow.
- The WSL release asset was deleted. Its GitHub URL returns 404; the website URL
  explicitly returns 410. Old checksums/source history remain historical records.
- Linux package, extracted-launcher and adversarial evidence is recorded in the
  adjacent `linux-*.json` files. The launcher mined with two threads and checked
  encrypted backup recovery in isolated test nodes.

The native Linux reference environment is Debian 13 x86-64 with Python 3 and Tk.
The chain remains experimental testnet v0.2; mainnet is disabled.
