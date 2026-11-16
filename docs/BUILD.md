# Build and verify

Reference: Linux x86-64, C++20 GCC, CMake 3.22+, Python 3.10+.
Python tools use the standard library. Tk is a system package. Binary target names
retain upstream names deliberately; use the explicit Obsolete launch scripts.

```sh
sudo apt-get update
sudo apt-get install --no-install-recommends build-essential cmake pkgconf \
  python3 python3-tk xvfb xauth libevent-dev libboost-dev libsqlite3-dev ccache
git submodule update --init --recursive
cmake -S src/randomx -B src/randomx/build -DCMAKE_BUILD_TYPE=Release
cmake --build src/randomx/build --target randomx -j2
cmake -S src/randomx -B build-randomx-shared -DBUILD_SHARED_LIBS=ON -DCMAKE_BUILD_TYPE=Release -DCMAKE_SHARED_LINKER_FLAGS=-Wl,-z,noexecstack
cmake --build build-randomx-shared --target randomx -j2
python3 tools/genesis.py --library build-randomx-shared/librandomx.so --verify
cmake -B build -DBUILD_TESTS=ON -DBUILD_GUI=OFF -DBUILD_BENCH=OFF \
  -DBUILD_FUZZ_BINARY=OFF -DENABLE_IPC=OFF -DCMAKE_BUILD_TYPE=Release
cmake --build build -j2
ctest --test-dir build --output-on-failure -j1
python3 -m unittest discover -s tests -v
xvfb-run -a python3 tools/integration.py --bindir build/bin --library build-randomx-shared/librandomx.so
```

The first build takes many minutes and several GB of disk. Prefer another machine
if the Dell runs other services. Nothing here installs into an existing bot or
uses its files or credentials. RandomX is a pinned source submodule.

Actions artifacts provide experimental Linux archives with SHA256SUMS.
They are not signed production releases or reproducible-build certification.
Build locally on Debian when possible; an Ubuntu artifact may need newer system
libraries than another Linux distribution provides.

Native Windows builds are documented in `release/README.md` and
`docs/WINDOWS-NATIVE.md`. Native Linux packages and their desktop launcher are
documented in `docs/LINUX-NATIVE.md`. Both downloads use application version
0.4.0-testnet-rc1 on testnet v0.2. macOS and ARM are not validated.

Two historical upstream genesis-mining helpers are preserved in
`docs/upstream-genesis-fixtures.cpp.txt` outside the active suite; they mine a
different currency. Obsolete genesis is independently mined and checked against
fixed constants. Official RandomX vectors and remaining inherited suites run.

## Use the experimental Debian 13 archive

Download `ObsoleteCoin-0.4.0-Testnet-Linux-x64.tar.gz` and `SHA256SUMS.txt` from
the public GitHub release. Extracting the tar preserves executable permissions.
On Debian 13 x86-64, install the runtime libraries:

```sh
sudo apt-get update
sudo apt-get install --no-install-recommends python3 python3-tk \
  libevent-2.1-7t64 libevent-core-2.1-7t64 libevent-extra-2.1-7t64 \
  libevent-pthreads-2.1-7t64 libsqlite3-0
# Place the two downloaded files in a directory named artifacts:
(cd artifacts && sha256sum --ignore-missing -c SHA256SUMS.txt)
tar -xzf artifacts/ObsoleteCoin-0.4.0-Testnet-Linux-x64.tar.gz
cd obsoletecoin-linux
./Start-Wallet.sh
```

The node works without a graphical desktop. Use a separate local node on the
mining laptop for the wallet. CI repeats the real-node integration on Debian 13
using this archive; it does not test resource consumption on your actual Dell.
