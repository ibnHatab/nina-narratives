#!/usr/bin/env bash
# Start the installed Metis in this workspace; secrets stay in the child environment.
set -euo pipefail
set +x
cd "$(dirname "$0")/.."
metis_env="${METIS_OPENROUTER_ENV:-$HOME/.config/metis/openrouter.env}"
if [[ -f "$metis_env" ]]; then
  set -a
  source "$metis_env"
  set +a
fi
if [[ -n "${OPENROUTER_API_KEY:-}" ]]; then export OPENROUTER_API_KEY; fi
metis_bin="${METIS_BIN:-}"
if [[ -z "$metis_bin" ]]; then metis_bin="$(command -v metis || true)"; fi
if [[ -z "$metis_bin" && -x ../perotheia-packages/.venv/bin/metis ]]; then
  metis_bin="../perotheia-packages/.venv/bin/metis"
fi
if [[ -z "$metis_bin" ]]; then
  echo 'Set METIS_BIN to your installed metis executable.' >&2
  exit 1
fi
mkdir -p .metis
exec "$metis_bin" "$@"
