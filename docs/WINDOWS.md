# Mine test OBS from Windows

Use Windows with WSL2 and Debian. The home node is reached over your home LAN;
your wallet keys and CPU mining stay on the laptop. No home SSH or RPC password
is needed. The prepared server address is `192.0.2.36:19777`.

1. If WSL/Debian is not already installed, open PowerShell as administrator and
   run `wsl --install -d Debian`. Restart if Windows requests it. Open Debian once
   to create its Linux username and password. Installation requires hardware
   virtualization and a Windows version supporting WSL2.
2. Inside Debian, install the runtime dependencies:

   ```sh
   sudo apt-get update
   sudo apt-get install -y python3 python3-tk libevent-2.1-7t64 \
     libevent-core-2.1-7t64 libevent-extra-2.1-7t64 \
     libevent-pthreads-2.1-7t64 libsqlite3-0
   ```

3. Download the current `obsoletecoin-linux-experimental` artifact from private
   GitHub Actions. Extract the ZIP, then extract its `.tar.gz` with Windows tar
   (`tar -xzf obsoletecoin-linux-experimental.tar.gz`) or your archive program.
4. Connect the laptop to the same home LAN as the Dell. Open `Start-Mining.cmd`
   inside the extracted `obsoletecoin-linux` folder. It starts the local node,
   connects to the Dell, creates/loads your local wallet, and starts real RandomX
   CPU mining. It refuses a different genesis or an unreachable home node.
5. Keep that window open. To view balances, run `Start-Wallet.cmd` as well.
   The desktop requires working WSL graphical support; CLI mining does not.
   Press Ctrl-C in the mining window to stop its miner and local node cleanly.

The reference miner uses one CPU thread. Initial test difficulty is deliberately
easy; new balances are immature for 100 blocks. Test coins have no monetary value.
The default wallet is created unencrypted: use Encrypt and Backup in the wallet.
Wallet data stays in Debian at `~/.obsoletecoin/obsolete-testnet-v2/wallets`;
application updates do not delete it. Do not delete/reset the Debian distribution
without securely backing up the wallet first. v0.1 blocks/balances are incompatible.

For another server address, run PowerShell from the extracted folder:
`powershell -NoProfile -File tools/start-windows.ps1 -Server 192.168.1.X:19777`.

## If the launcher says Debian is missing

Having WSL installed is not enough: `wsl --list --verbose` must list a Debian
installation. If the list is empty, install Debian using step 1 above. If WSL
reports access denied or a service error, resolve that WSL error first; the
launcher displays the original diagnostic instead of assuming Debian is missing.

To verify setup with a bounded mining session, run from PowerShell in the
extracted folder:
`powershell -NoProfile -File tools/start-windows.ps1 -Blocks 1`.
This mines one real test block into the local wallet, then stops the local node.
The normal `Start-Mining.cmd` launcher continues until you press Ctrl-C.
