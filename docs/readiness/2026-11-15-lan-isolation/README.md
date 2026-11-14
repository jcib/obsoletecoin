# LAN isolation applied - 2026-11-15

Owner requested preventing the node user from initiating connections to domestic
devices. Implemented only that first measure, not a router/VLAN redesign.

- Installed dedicated UID 987 nftables output filter; persisted include, enabled
  nftables service, full configuration validated without reload/reboot.
- 14 isolated cases passed: nine blocked address cases, public IPv4 and local RPC,
  established outbound connection blocked, another UID unaffected, LAN peer replies.
- Four production negative probes incremented rejection counters: router HTTP,
  Dell SSH, IPv4 loopback SSH and IPv6 loopback SSH. No login or application data sent.
- A real Windows LAN client also completed the P2P handshake and genesis check
  at height 342 after the change (lan-peer.json).
- RPC/genesis and public HTTPS/DNS passed; explorer observed fresh height 342 after
  applying; external Cloudflare genesis handshake passed. See verification.json.
- Node PID257843, publisher PID257948 and cryptobot PID845 unchanged, all active
  with NRestarts0. No trading edits, ledger access, orders or restarts.
- Other nftables tables structurally identical before/after. Automatic rollback
  timer cancelled after success and subsequently verified inactive.
- Initial namespace-only assertion expected EACCES; Debian returned timeout despite
  rejection. Test was corrected to require counter evidence, then all cases passed.
  That initial failure occurred before any production firewall change.

Rules SHA256: 51ab357d845a70b13a95ccea63b9627c1fbcfe05417474b62e31b3f7653d2a66.
Implementation and operating limits: ../../../deploy/lan-isolation/README.md.
No password was saved. Mainnet readiness is unchanged.
