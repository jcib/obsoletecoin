# Dedicated node UID outbound LAN isolation

Applied to the existing Debian Dell on 2026-11-15. This is a one-time administrative
installer, not a normal node startup command. Do not rerun it over an existing
installation. Administrative authentication was entered locally, used only in memory.

`rules.py` generates a separate nftables inet table, `obsoletecoin_egress`.
Only sockets owned by obsoletecoin (UID 987) jump into the restricted chain.
Other UIDs and packets without a matching socket owner retain existing policy.
Existing firewall tables are compared before/after, ignoring counters and handles.
No flush/reload of the production ruleset or service restart is performed.

Blocked for this UID:
- Initiated IPv4 connections to private, loopback, link-local, CGNAT, multicast,
  reserved and documentation ranges listed explicitly in the rules.
- Initiated IPv6 connections, including ULA/link-local/global addresses. This
  deployment has IPv4 public P2P and public IPv4 DNS; it has no IPv6 Internet route.
- Already-established outbound connections to those blocked destinations.

Exceptions:
- TCP 127.0.0.1:19778, required by the explorer publisher and local RPC clients.
- Replies to incoming TCP P2P connections on source port 19777, so LAN miners and
  Internet peers can initiate connections to the Dell.
- Local RPC server replies from 127.0.0.1:19778.
- Public IPv4 traffic, including current external DNS servers and HTTPS publication.

Persistence: /etc/nftables.d/obsoletecoin-egress.nft, included from
/etc/nftables.conf. nftables.service is enabled; complete config syntax was checked
using nft -c, without loading or flushing the complete host ruleset. No reboot was
performed. Router rules, input firewall, SSH, node config and mining were unchanged.

Validation: `test_namespace.py` exercises actual nftables in a disposable network
namespace, without external interfaces. Negative tests require increasing reject
counters; Debian can report a TCP timeout rather than EACCES for rejected packets.
Tests cover IPv4/IPv6, an existing outbound connection, local RPC, public IPv4,
unaffected other users, and replies to an incoming LAN peer. Production checks
verify private destination rejections, RPC, HTTPS/DNS, a new explorer publication,
and an external P2P genesis handshake. All service PIDs/restart counts are unchanged.

Before applying, the installer arms a 180-second systemd rollback timer. It cancels
that timer only after successful checks. The installed backup is root-only under
/opt/obsoletecoin/lan-isolation-before. For an explicitly requested rollback, inspect
current config first; the helper restores only its exact config version and deletes
only this dedicated table. It refuses to overwrite a subsequently edited config.
Never use a global firewall flush or restart networking as a rollback.

Limits: this is host process isolation, not a separate VLAN or VM. It does not
prevent DDoS, consensus attacks, kernel/root compromise, or access through a public
proxy/port-forwarded endpoint. It does not filter Unix-domain sockets. If LAN uses
public IPv4 addressing or DNS moves to a private resolver, review the rules. Do not
silently add broad loopback/LAN exceptions. Future IPv6 P2P requires explicit review.
