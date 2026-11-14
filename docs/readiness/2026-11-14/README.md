# Evidence index

All tests use disposable data and loopback peers. No production Dell services, live miner or existing wallet was used. Tests are evidence of these scenarios only, not an independent audit.

- ci.json: exact successful core/expanded Linux workflow revisions and links. The native package's node is from 46beda6; its source is unchanged by the desktop/tooling commits.
- integration-context.json / integration-windows.json: real Debian/Windows mining, wallet, invalid-header and recovery traversal.
- adversarial-linux.json / adversarial-windows.json: partition/double-spend, bounded malformed P2P, unauthenticated RPC, abrupt process termination and peer recovery.
- disk-full.json: actual ENOSPC in a private tmpfs, recovery after space is restored.
- difficulty.json: production C++ ASERT routine, five seeded simulation scenarios and limits.
- native-frozen.json / installer.json: autonomous frozen GUI/node, RandomX mining and installer lifecycle on Windows 11 build 26300.
- wallet-reproducibility.json: two clean GUI builds on one machine, not independent whole-release reproducibility.
- gui-mining.json / health.json: GUI start/stop/refusal without peers and read-only health transitions. Corresponding helper scripts are included; run them from the repo root after following release/README.md (native node in .local/native-node and configured Tcl/Tk).
- windows-hardening.json: ASLR/NX/high-entropy VA and absence of writable executable PE sections. Runtime/JIT behavior is outside this check.

The installer and portable package remain unsigned. Mainnet remains disabled. See ../../MAINNET-READINESS.md for unclosed launch gates.
