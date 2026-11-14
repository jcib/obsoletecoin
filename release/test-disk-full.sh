#!/bin/sh
# Run via: sudo unshare --mount --fork sh release/test-disk-full.sh /absolute/bitcoind /absolute/result.json
set -eu
if [ "$(readlink /proc/self/ns/mnt)" = "$(readlink /proc/1/ns/mnt)" ]; then
  echo 'Refusing the host mount namespace' >&2; exit 1
fi
mount --make-rprivate /
fixture=$(mktemp -d /tmp/obsolete-disk-XXXXXX)
trap 'umount "$fixture"; rmdir "$fixture"' EXIT
mount -t tmpfs -o size=700m tmpfs "$fixture"
python3 -B tools/disk_full_test.py --root "$fixture" --binary "$1" --output "$2"
