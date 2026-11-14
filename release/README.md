# Native Windows candidate build

This pipeline produces an unsigned TESTNET candidate. Mainnet stays disabled.

1. Check out the recorded source and RandomX submodule. Run the native workflow (.github/workflows/windows.yml). Retain the job logs, artifact digest, toolchain.txt and dependencies.txt. Download only the artifact from that exact successful run and verify the GitHub artifact SHA256.
2. Install official CPython 3.14.10 x64 in a build environment; verify its publisher signature. Create .local/build-venv314 and install with `python -m pip install --require-hashes -r release/requirements-build.lock`. The lock is Windows x64 specific.
3. Run `powershell -File release/build-wallet.ps1`. Repeat with `-Output .local/native-dist-repeat`. Compare every file hash. A same-machine match is not independent reproducibility.
4. Place the native artifact in .local/native-node, including node-provenance.json with run URL, exact commit and artifact SHA256. Include bundled runtime license notices. Run `python release/assemble-native.py`. The output must not already exist. Assembly never copies a user's data directory.
5. With verified Inno Setup 7.1.1, run `ISCC.exe release/windows.iss`. Output is .local/release/ObsoleteCoin-Testnet-Setup.exe. The default install is per user, with no autostart and no wallet-data deletion.
6. On a clean Windows test account run `python release/test-installer.py .local/release/ObsoleteCoin-Testnet-Setup.exe --output .local/readiness/installer.json`. The test refuses an existing real installation. It installs, launches the frozen UI/node, mines into a disposable wallet, reinstalls, uninstalls, verifies wallet file hashes, reinstalls and opens the same wallet.
7. Archive the entire native-package directory as ObsoleteCoin-Windows-Native-Testnet.zip. Publish SHA256SUMS and PROVENANCE.json alongside it, explicitly unsigned. Record tested OS versions and all unresolved launch gates.

When an official signing certificate becomes available, use sign-windows.ps1 on the application executable and rebuilt installer, then verify signatures and repeat installation testing. Do not publish any private key. Signing changes hashes, so regenerate the release manifest afterward. Independent source-to-binary rebuilds remain required.

## Linux adversarial checks

Use disposable loopback nodes only. Run tools/integration.py, tools/adversarial.py and tools/difficulty_simulation.py. For actual ENOSPC injection, use `sudo unshare --mount --fork sh release/test-disk-full.sh /absolute/bitcoind /absolute/result.json` from the source root. This creates a private 700 MiB tmpfs and refuses the host mount namespace. Never fill a real node filesystem for testing.

`python tools/health.py --datadir /path/to/node --rpcport 19778` is read-only and returns JSON plus exit 0 for healthy, 1 for degraded/unavailable. Native desktop RPC defaults to 29778. An old tip is an investigation signal, not proof of a fault or an attack. Alert delivery and independent hosts are not provisioned by these files.
