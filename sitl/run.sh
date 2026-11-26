#!/usr/bin/env bash
# Run a SITL scenario with metis-agent's own Python (metispy, metis-agent and the feed's aiohttp), from the
# maintainer's sibling checkouts. METIS_PY and CUDA_LIB override the defaults.
#   sitl/run.sh workspaces/home/scenarios/cognition/b01-later.yaml [--seed N]
set -eu
here="$(cd "$(dirname "$0")/.." && pwd)"
py="${METIS_PY:-$here/../perotheia-packages/metis-agent/py/.venv/bin/python}"
cuda="${CUDA_LIB:-$HOME/.local/cuda-12.9/lib64}"
if [[ -d "$cuda" ]]; then export LD_LIBRARY_PATH="$cuda${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"; fi
export METISC="${METISC:-$here/../perotheia-packages/metis-lang/src/metisc}"
exec "$py" "$here/sitl/loop.py" "$@"
