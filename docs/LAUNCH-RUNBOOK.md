# Launch preparation runbook

These files prepare a public TESTNET rehearsal, not mainnet activation. No public servers have been provisioned. No certificate or independent reviewer is available yet.

## Operator deployment

Provision independently administered hosts in distinct networks. Review the binary and manifest before installation. Create the obsoletecoin user, /opt/obsoletecoin, /etc/obsoletecoin and state directory; install deploy/obsolete-testnet.service and adapt deploy/testnet.conf.example with actual peers. Expose P2P 19777 only; keep RPC 19778 on loopback and SSH restricted. The config is a template, not a production deployment. Never reuse the trading bot account or credentials. Enable the service only after checking its resolved paths and permissions.

Check height, tip hash, best-header progress, peer diversity, free disk, resident memory, log errors and time synchronization from each independent host. Compare tips across operators; alert on loss of peers, stalled height with known active miners, invalid work bursts or low disk. Clock and power recovery must be verified by the owner. On divergence, preserve logs and halt launch scheduling; do not restore old wallet state over newer transactions.

## Wallet and release

Build the native wallet with release/build-wallet.ps1 using the pinned requirements. Combine it with the matching native node and DLL artifact. The Inno specification installs per user and never deletes wallet data. Test installation, second installation and uninstallation in a disposable directory. Never test uninstall against a user's real wallet.

Prepare SHA256SUMS and provenance identifying node and GUI source commits independently. Compare two clean builds and record discrepancies. Equal local builds are not independent reproducibility. Once a code-signing certificate exists, use release/sign-windows.ps1; verify timestamp/signature before publishing. Unsigned test candidates must remain explicitly labelled unsigned.

## Before mainnet

Obtain independent consensus/security review and close severe findings; review ASERT simulation and initial difficulty with measured independent miner rates. Decide and publish new genesis/launch parameters and a public start procedure. Run sustained public testnet with independent operators and record partitions, restore exercises, full-disk recovery and resource limits. Mainnet guard must remain until these gates pass. No calendar date, peer count or confirmation count substitutes for hash security.
