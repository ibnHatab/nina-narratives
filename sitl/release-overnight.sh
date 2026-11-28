#!/usr/bin/env bash
# release-overnight.sh: a release's acceptance scheduled for the night, on Gemini (the user, 2026-11-28: "schedule
# overnight and use Gemini Flash with fallbacks on other Gemini models"). It runs sitl/release.sh once, at WHEN
# (default 01:30, tonight's or the next), as a transient user timer: systemd-run, nothing kept after it ran.
#
#   sitl/release-overnight.sh TAG [ROUNDS] [WHEN]     e.g. sitl/release-overnight.sh v0.4.0 3 01:30
#   SITL_MIND=…  the chain (default google:gemini-3.8-flash,gemini-3.7-flash,gemini-3.5-flash,gemini-3.1-flash-lite)
#
# Its log: .release-TAG.log here; the certificate: sitl/certificates/TAG.json. See it: systemctl --user
# list-timers 'nina-release-*'; cancel it: systemctl --user stop nina-release-TAG.timer.
set -euo pipefail
cd "$(dirname "$0")/.."
TAG=${1:?usage: sitl/release-overnight.sh TAG [ROUNDS] [WHEN]}
ROUNDS=${2:-3}
WHEN=${3:-01:30}
MIND=${SITL_MIND:-google:gemini-3.8-flash,gemini-3.7-flash,gemini-3.5-flash,gemini-3.1-flash-lite}
P=${METIS_PY:-$HOME/repo/perotheia-packages/metis-agent/py/.venv/bin/python}
[ -e "sitl/certificates/$TAG.json" ] && { echo "release-overnight: sitl/certificates/$TAG.json exists" >&2; exit 1; }
at=$(date -d "today $WHEN" +%s)
[ "$at" -gt "$(date +%s)" ] || at=$(date -d "tomorrow $WHEN" +%s)
stamp=$(date -d "@$at" '+%Y-%m-%d %H:%M:00')
unit="nina-release-$(tr -c 'A-Za-z0-9_\n-' '_' <<<"$TAG")"
systemd-run --user --unit "$unit" --on-calendar "$stamp" --timer-property=AccuracySec=1min \
  --working-directory "$PWD" --setenv SITL_MIND="$MIND" --setenv METIS_PY="$P" --setenv PATH="$PATH" \
  ${SSH_AUTH_SOCK:+--setenv SSH_AUTH_SOCK="$SSH_AUTH_SOCK"} \
  /bin/bash -c "bash sitl/release.sh '$TAG' '$ROUNDS' > '.release-$TAG.log' 2>&1"
echo "release-overnight: $TAG at $stamp, $ROUNDS rounds, mind $MIND (log .release-$TAG.log)"
