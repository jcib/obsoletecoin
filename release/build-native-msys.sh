#!/usr/bin/env bash
# Run from the repository root in MSYS2 UCRT64 with the packages from windows.yml.
set -euo pipefail
test "${MSYSTEM:-}" = UCRT64
output=${1:-.local/windows-upgrade}
jobs=${BUILD_JOBS:-4}
mkdir -p "$output"
output=$(cd "$output" && pwd)
cmake -S src/randomx -B "$output/rx-static" -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build "$output/rx-static" -j "$jobs"
cmake -S src/randomx -B "$output/rx-shared" -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON
cmake --build "$output/rx-shared" -j "$jobs"
cmake -S . -B "$output/core" -G Ninja -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_TESTS=ON -DBUILD_GUI=OFF -DBUILD_BENCH=OFF -DBUILD_FUZZ_BINARY=OFF \
    -DENABLE_IPC=OFF -DBRISVIA_RANDOMX_LIB="$output/rx-static/librandomx.a"
cmake --build "$output/core" -j "$jobs"
ctest --test-dir "$output/core" --output-on-failure -j 1 --output-junit "$output/ctest.xml"
mkdir -p "$output/node"
cp "$output/core/bin/bitcoind.exe" "$output/core/bin/bitcoin-cli.exe" \
   "$output/core/bin/bitcoin-wallet.exe" "$output/node/"
cp "$output/rx-shared/"*randomx.dll "$output/node/"
for binary in "$output/node/"*.exe "$output/node/"*.dll; do ldd "$binary"; done > "$output/node/dependencies.txt"
while IFS= read -r dll; do cp "$dll" "$output/node/"; done < <(awk '/ucrt64.*dll/{print $3}' "$output/node/dependencies.txt" | sort -u)
pacman -Q > "$output/node/toolchain.txt"
cp -r /ucrt64/share/licenses "$output/node/licenses"
echo 'Native Windows build and CTest completed.'
