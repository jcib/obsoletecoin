# Obsolete Coin native Windows test candidate



Experimental TESTNET only. Test coins have no monetary value. This candidate is unsigned; it is not a mainnet release. Native x64 wallet and node, no WSL or Python installation required. Windows 11 was used for local validation; the node CI uses Windows Server 2022. Other Windows versions are not yet certified.



## Start



Install ObsoleteCoin-Testnet-Setup.exe or extract the entire portable ZIP. Run ObsoleteCoin.exe. Keep the _internal directory and all DLLs next to the executable. From Network > Connect peer, enter your testnet operator's hostname or IPv4 address and P2P port. Use the current public peer and verification status at https://obsoletecoin.pages.dev/join.html. Wait for synchronization, then select Mine / Stop for one CPU mining thread.



The native wallet stores its own data in %USERPROFILE%\.obsoletecoin, and saves peer choices in native-testnet-peers.json. It does not import or move your WSL wallet. Native local RPC uses port 29778 to avoid the WSL node's default 19778. P2P is outbound-only in this desktop launcher. RPC remains on loopback with cookie authentication. Closing the wallet stops only the node it started. An already running node is left running.



## Wallet protection



Use Encrypt and then Backup; store the passphrase and backup privately. An unencrypted newly created wallet remains unencrypted until you select Encrypt. Receive shows your address. Send shows the exact transaction fee and total before signing. Activity includes local date/time and transaction details. Mining rewards require 100-block maturity, and actual block waits vary. A dominant miner can reorganize testnet; confirmations do not guarantee security.



Reinstalling/upgrading application files must preserve wallet data. Uninstall removes application files, not %USERPROFILE%\.obsoletecoin. Back up first. Never replace a newer wallet with an old backup without recovery/reconciliation planning.



## Build and verification



See release/build-wallet.ps1, release/requirements-build.txt, release/windows.iss, PROVENANCE.json and the external SHA256SUMS. Checksums detect file changes but are not a publisher signature. Official code signing and independent matching builds remain outstanding. Keep mainnet disabled.
