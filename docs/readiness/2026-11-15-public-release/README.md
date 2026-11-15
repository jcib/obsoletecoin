# Public testnet binaries - 2026-11-15

Release: https://github.com/jcib/obsoletecoin/releases/tag/v0.3.0-testnet-rc1

The release contains the native Windows installer and complete portable ZIP,
compiled Linux x86-64 package, alternative Debian/WSL package, provenance,
mainnet-readiness notes and SHA256SUMS. It is a prerelease for the existing v0.2
testnet; mainnet remains disabled and test coins have no monetary value.

Previously tested executables and libraries are unchanged. Public instructions
were refreshed, home-network references removed, Linux/WSL launchers require an
explicit peer, and Python bytecode caches were removed. Tar ownership metadata
was normalized. The archives and installer were repackaged, changing their hashes.
The release tag identifies the publishing source, not a claim that all native
binaries were rebuilt at that commit. Historical build provenance is retained.

All three archives were inspected for unsafe paths, runtime wallet/credential
filenames and the identified personal references. The packaged Windows file
manifest matches. A fresh disposable portable-wallet check started the GUI and
native node and mined two test blocks. Compiled Windows/Linux/WSL file hashes
remain identical to the previously tested candidates.

Installer compilation passed using the existing Inno Setup script. The
installation/reinstallation/uninstallation regression was attempted but refused
because it detected an existing installation. That safeguard was not bypassed.
No real installation, wallet, Dell service or consensus rule was changed.

Old draft assets, including the obsolete review-source archive, were replaced
only after their original local copies matched the GitHub digests. Published
assets were checked by GitHub digest before opening the draft. Anonymous full
downloads are verified separately in anonymous-downloads.json.
