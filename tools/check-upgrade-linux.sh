#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "${1:-}" != "--postbuild" ]]; then
cmake -S src/randomx -B .local/upgrade-rx -DCMAKE_BUILD_TYPE=Release
cmake --build .local/upgrade-rx --target randomx -j2
cmake -S src/randomx -B .local/upgrade-rx-shared -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON
cmake --build .local/upgrade-rx-shared --target randomx -j2
cmake -S . -B .local/upgrade-build -DBUILD_TESTS=ON -DBUILD_GUI=OFF -DBUILD_BENCH=OFF -DBUILD_FUZZ_BINARY=OFF -DENABLE_IPC=OFF -DCMAKE_BUILD_TYPE=Release -DBRISVIA_RANDOMX_LIB="$PWD/.local/upgrade-rx/librandomx.a"
cmake --build .local/upgrade-build -j2
ctest --test-dir .local/upgrade-build --output-on-failure -j2
fi
python3 tools/check_select_backend.py --build .local/upgrade-build
python3 -B -m unittest discover -s tests -v
python3 -B -m unittest discover -s tools -p 'test_wallet*.py' -v
xvfb-run -a python3 tools/integration.py --bindir .local/upgrade-build/bin --library .local/upgrade-rx-shared/librandomx.so
python3 tools/adversarial.py --binary .local/upgrade-build/bin/bitcoind --output .local/readiness/upgrade-adversarial.json
python3 tools/difficulty_simulation.py --output .local/readiness/upgrade-difficulty.json
