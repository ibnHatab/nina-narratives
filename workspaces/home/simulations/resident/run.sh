#!/usr/bin/env bash
set -eu
runner_python="$1"
shift
cd "$(dirname "$0")/../.."
export METIS_CATALOG="$PWD" METIS_HOME="$PWD/../../cognition"
if [[ -d "${CUDA_LIB:-$HOME/.local/cuda-12.9/lib64}" ]]; then
  export LD_LIBRARY_PATH="${CUDA_LIB:-$HOME/.local/cuda-12.9/lib64}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi
exec "$runner_python" simulations/resident/run.py "$@"
