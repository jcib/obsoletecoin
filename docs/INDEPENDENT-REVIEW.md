# Independent review handoff

No independent reviewer has signed off this fork. Automated checks and work by the implementing assistant are not an independent audit.

Source provenance is in UPSTREAM.md; protocol rules and exact emission are in SPEC.md. release/make-review-bundle.py exports only committed source and the pinned RandomX submodule, with a SHA256 manifest. The source archive does not contain wallets, cookies, server credentials or untracked files. Record the exact reviewed commit in the eventual report.

Review the inherited Brisvia changes as well as the Obsolete delta from upstream 59cd3d65e97348cf221662b9cdc27d4834daf7c3. Prioritize contextual RandomX header validation and branch resolution (src/pow.cpp, headerssync, randomx_seed), work accounting and seed rotation on competing chains, subsidy/UTXO conservation, network/genesis isolation, timestamp/ASERT behavior, serialization and Windows/Linux consistency. Include resource exhaustion in header synchronization and untrusted P2P messages. Existing bounded malformed-message tests do not establish a DoS budget.

Wallet/release review should examine local RPC authentication, PSBT fee confirmation, encryption/recovery, runtime dependency provenance and installer preservation of state. Repeat tests from release/README.md in an independent environment; compare complete node and GUI outputs, not just repeated GUI builds on one machine.

Required report: methodology, exact revisions/toolchains, reproduced findings, severity, remediation verification and remaining limits. A passing test suite alone cannot close the review gate. No launch date should be announced until critical/high findings and the readiness matrix are resolved.
