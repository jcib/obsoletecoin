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
