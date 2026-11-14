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

Private Actions artifacts provide an experimental Linux archive with SHA256SUMS.
They are not signed production releases or reproducible-build certification.
Build locally on Debian when possible; an Ubuntu artifact may need newer system
libraries than another Linux distribution provides.

Windows node/miner: use WSL2 and Linux instructions. WSLg displays the Tk wallet.
Native Windows preview: `python tools/wallet95.py --demo`. No native Windows node
package, macOS validation or ARM validation is provided in v0.1.

Two historical upstream genesis-mining helpers are preserved in
`docs/upstream-genesis-fixtures.cpp.txt` outside the active suite; they mine a
different currency. Obsolete genesis is independently mined and checked against
fixed constants. Official RandomX vectors and remaining inherited suites run.
