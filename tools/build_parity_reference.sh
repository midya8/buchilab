#!/usr/bin/env bash
# Optional actual external reference. No runtime dependency or vendored solver.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
python -m pip install --target "$work/cmake" 'cmake==3.31.10'
git clone https://github.com/trolando/oink "$work/oink"
git -C "$work/oink" checkout --detach db336a53e6a1b2dc12ab89b58d1871fe565d0147
test "$(git -C "$work/oink" rev-parse HEAD)" = db336a53e6a1b2dc12ab89b58d1871fe565d0147
git clone --branch v2.6.0 --depth 1 https://github.com/trolando/lace "$work/lace"
test "$(git -C "$work/lace" rev-parse HEAD)" = a091978dc4479fc3b9bc7af7dc77939ec8587c44
cmake="$work/cmake/cmake/data/bin/cmake"
# The pinned bundled cxxopts omits <cstdint>; preinclude the standard header
# for newer compilers without changing either pinned upstream source tree.
"$cmake" -S "$work/oink" -B "$work/build" -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_FLAGS=-include cstdint" -DFETCHCONTENT_SOURCE_DIR_LACE="$work/lace" -DOINK_BUILD_TESTS=OFF -DOINK_BUILD_EXAMPLES=OFF
"$cmake" --build "$work/build" --target solve -j2
cd "$root"
OINK_BIN="$work/build/oink" python tools/check_parity_reference.py
