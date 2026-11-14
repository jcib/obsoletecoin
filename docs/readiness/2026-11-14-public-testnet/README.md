# Public testnet preparation evidence

- Node consensus and wallet binaries unchanged from the previously tested candidates.
- Public-source scan: 23 project commits, 174 distinct changed file versions, no
  matches for tested credential patterns. This is not a complete security audit.
- Explorer: core validation/authentication tests, Workerd/R2 ingest/replay/reorg and
  fixed-download hash tests passed. Python collector cache, rollback and concurrent
  tip-change tests passed with a simulated local RPC transport.
- Chrome 1440/390/360 with JavaScript disabled: navigation, iframe refresh, music
  continuity, mobile layout and installer hash. See browser.json.
- Live node deployment and an external fresh-node synchronization must be recorded
  separately before claiming public readiness. The draft forum post has not been sent.

## Applied node preparation and live data

The owner completed local administrator authentication. The Dell now has the
specific public P2P allowance, full block retention and an enabled explorer publisher.
Node and publisher were active with zero automatic restarts at verification;
the unrelated bot retained PID 845 and zero restarts. See node-deployment.json.
Two fresh explorer observations differed by 15,000 ms at height 305, covering
blocks 0?305. There were zero connected peers at that moment. See live-feed.json.

Public connectivity remains BLOCKED: the cloud website probe failed, and GitHub
run 43650047516 timed out during TCP connection to the public peer before any P2P
handshake. The same probe succeeded on the LAN. The first GitHub rehearsal,
43649892357, stopped earlier because the read-only job token could not list the
unpublished draft release; that attempt did not test the network.
No independent full synchronization or anonymous-download check has passed yet.
Repository, draft release and website remain private pending explicit owner approval.
