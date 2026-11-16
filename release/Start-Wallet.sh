#!/bin/sh
set -eu
package_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 -B "$package_root/tools/linux_wallet.py" "$@"
