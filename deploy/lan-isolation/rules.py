"""Outbound isolation for the dedicated Obsolete Coin UID, IPv4 node deployment."""
TABLE = "obsoletecoin_egress"
def rules(uid):
    assert isinstance(uid, int) and uid > 0
    return f"""table inet {TABLE} {{
 set private_v4 {{
  type ipv4_addr; flags interval;
  elements = {{ 0.0.0.0/8, 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8,
   169.254.0.0/16, 172.16.0.0/12, 192.0.0.0/24, 192.0.2.0/24,
   192.168.0.0/16, 198.18.0.0/15, 198.51.100.0/24, 203.0.113.0/24,
   224.0.0.0/4, 240.0.0.0/4 }}
 }}
 chain output {{
  type filter hook output priority 10; policy accept;
  meta skuid {uid} jump node_only
 }}
 chain node_only {{
  ct direction reply tcp sport 19777 counter accept comment "P2P replies to incoming peers"
  ct direction reply ip saddr 127.0.0.1 tcp sport 19778 counter accept comment "Local RPC replies"
  ip daddr 127.0.0.1 tcp dport 19778 counter accept comment "Explorer local RPC only"
  meta nfproto ipv6 counter reject with icmpx type admin-prohibited comment "No initiated IPv6 from node UID"
  ip daddr @private_v4 counter reject with icmpx type admin-prohibited comment "No initiated LAN or other loopback access"
  counter accept comment "Public IPv4 DNS HTTPS and P2P"
 }}
}}
"""
