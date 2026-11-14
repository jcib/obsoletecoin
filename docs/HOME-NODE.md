# Home testnet node ? public preparation

The public preparation was applied after local administrator authentication:
TCP 19777 is allowed by the Dell firewall, the node retains full block history
(pruning disabled), and the explorer publisher starts automatically with systemd.
The node permits up to 32 connections and targets at most 1024 MiB upload per day.
RPC remains loopback-only and the server wallet remains disabled. Existing CPU
and memory limits remain. The unrelated trading service retained its process.

The live explorer received two fresh observations 15 seconds apart at height 305.
At that check there were zero peers. A local P2P handshake verified the expected
genesis. An external probe did NOT connect: public reachability is still pending.
Router NAT was reported configured by the operator; it has not yet passed an
external end-to-end check. Website/repository access remains private pending an
explicit owner decision. Do not announce the network as publicly reachable yet.

Current peer and data freshness are shown on the join page once access is granted.
Node service: `obsoletecoin-testnet.service`; exporter: `obsoletecoin-explorer.service`.
Do not run the one-time installation scripts again against these existing services.

## Initial LAN installation (historical)


The v0.2 node was installed and verified on the home Debian 13 server on
2026-11-14. Its LAN endpoint is **192.0.2.36:19777**.

- Service: `obsoletecoin-testnet.service`, enabled at boot and restarted
  successfully during installation. The physical server was not rebooted.
- Dedicated unprivileged account: `obsoletecoin`.
- Binaries: `/opt/obsoletecoin/current`; data: `/var/lib/obsoletecoin`.
- Configuration: `/etc/obsoletecoin/obsolete.conf`.
- RPC: localhost only, `127.0.0.1:19778`; cookie authentication.
- P2P: accepts only the home IPv4 LAN through its dedicated firewall allowance.
- CPU limit: half of one logical CPU; memory ceiling: 1536 MiB; pruning: 1000 MiB
  of block files (total storage may be higher).
- Server wallets and mining are disabled. The laptop holds its own wallet and
  runs its own local node and miner; see [WINDOWS.md](WINDOWS.md).

The installed binary is from commit
`46584f64ec0a582e83479371aefe39d3b2700342`, validated in
[GitHub Actions](https://github.com/jcib/obsoletecoin/actions/runs/43544745891).
A Windows LAN probe completed the P2P handshake and retrieved the expected v0.2
genesis header. The RPC port was unreachable from that LAN client. The existing
trading bot retained its process and restart count throughout installation.

Useful commands on the Dell:

```sh
systemctl status obsoletecoin-testnet.service
sudo journalctl -u obsoletecoin-testnet.service -n 50 --no-pager
sudo systemctl restart obsoletecoin-testnet.service
sudo systemctl stop obsoletecoin-testnet.service
```

To keep it stopped after a reboot, use
`sudo systemctl disable --now obsoletecoin-testnet.service`. This changes only
the Obsolete service. Avoid running the initial installer again or deleting data
to resolve a startup problem. Keep node maintenance separate from trading-bot
maintenance. No router port forwarding or public network was configured.
