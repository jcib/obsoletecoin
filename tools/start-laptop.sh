#!/usr/bin/env bash
set -euo pipefail
package_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
server="${1:-}"
mode="${2:-mine}"
blocks="${3:-0}"
if [ "$mode" != wallet ] && [ -z "$server" ]; then echo "Supply the current peer from https://obsoletecoin.pages.dev/join.html" >&2; exit 2; fi
if ! [[ "$blocks" =~ ^[0-9]+$ ]]; then echo "Invalid block count" >&2; exit 2; fi
if ! command -v python3 >/dev/null || ! ldd "$package_root/bitcoind" 2>/dev/null | awk '/not found/{missing=1} END {exit missing}'; then
  echo 'Install the Debian runtime dependencies listed in docs/WINDOWS.md first.' >&2
  exit 1
fi
# Copy only application files into the Linux filesystem, never wallet data.
install_dir="$HOME/.local/share/obsoletecoin-v0.2"
mkdir -p "$install_dir"
if [ "$package_root" != "$install_dir" ]; then
  cp "$package_root/bitcoind" "$install_dir/bitcoind.new"
  chmod 755 "$install_dir/bitcoind.new"
  mv "$install_dir/bitcoind.new" "$install_dir/bitcoind"
  cp -R "$package_root/tools" "$package_root/docs" "$install_dir/"
fi
cd "$install_dir"
if [ "$mode" = wallet ]; then
  exec python3 tools/wallet.py
fi
if [ "$blocks" -gt 0 ]; then
  exec python3 tools/laptop.py --server "$server" --blocks "$blocks"
fi
exec python3 tools/laptop.py --server "$server"
