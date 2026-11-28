#!/usr/bin/env bash
# stack.sh: Nina's own install for the SITL (sitl/NINA-IN-THE-LOOP.md), apart from any machine's: her repos
# cloned under STACK (default .stack in this checkout), one go.work so the persona is built from these sources
# (a fsttm-live or acasa change is tested before it is released), built as a Pi builds her (nina-live
# scripts/persona-build.sh: metisc, the composition's image, bin/nina). The SITL's configs point into it
# (sitl/nina_proc.py). Keys are read from ~/.config (OpenRouter's for her minds; no Gemini call is made).
#   stack.sh            clone what is missing, pull the rest, build
#   stack.sh --no-pull  build the checkouts as they are (a branch under test)
#   REF_NINA_LIVE=branch stack.sh   (REF_FSTTM_LIVE, REF_ACASA, …): a repo at a branch
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
STACK=${STACK:-$ROOT/.stack}
PULL=1; [ "${1:-}" = "--no-pull" ] && PULL=0
mkdir -p "$STACK/perotheia-packages"
clone() { # url dir default-branch
  local ref_var="REF_$(echo "$2" | tr 'a-z/-' 'A-Z__' | sed 's/PEROTHEIA_PACKAGES_//')"
  local ref=${!ref_var:-$3}
  if [ ! -d "$STACK/$2/.git" ]; then
    git clone -q -b "$ref" "$1" "$STACK/$2"
  elif [ "$PULL" = 1 ]; then
    git -C "$STACK/$2" fetch -q && git -C "$STACK/$2" checkout -q "$ref" && git -C "$STACK/$2" pull -q --ff-only
  fi
  printf '%-34s %s\n' "$2" "$(git -C "$STACK/$2" log --oneline -1 | cut -c1-60)"
}
clone git@github.com:nina-ai-dev/nina-live.git nina-live main
clone git@github.com:nina-ai-dev/fsttm-live.git fsttm-live main
clone git@github.com:nina-ai-dev/nina-ha-integration.git acasa main   # the repo nina-ha-integration (was acasa), still in acasa/
clone git@github.com:nina-ai-dev/nina-narratives.git nina-narratives main   # her rules: nina-live catalog/domains links into it (the redesign's step 2)
clone git@github.com:metis-lang-dev/metis-lang.git perotheia-packages/metis-lang master
clone git@github.com:metis-lang-dev/metis-loop.git perotheia-packages/metis-loop master
clone git@github.com:metis-lang-dev/metis-agent.git perotheia-packages/metis-agent main
clone git@github.com:metis-lang-dev/metis-worlds.git perotheia-packages/metis-worlds main
cat > "$STACK/go.work" <<W
go 1.26.0
use (
	./nina-live
	./fsttm-live
	./acasa
)

replace github.com/metis-lang-dev/metis-worlds/libs/semantic-world/go v0.0.0-00010101000000-000000000000 => github.com/metis-lang-dev/metis-worlds/libs/semantic-world/go $(awk '$1=="github.com/metis-lang-dev/metis-worlds/libs/semantic-world/go" {print $2}' "$STACK/nina-live/go.mod" | head -1)
W
export GOWORK="$STACK/go.work" GOFLAGS=-mod=readonly
[ -n "${REF_METIS_LANG:-}" ] && rm -f "$STACK/perotheia-packages/metis-lang/src/metisc"   # a metis-lang branch: its own metisc
REPO_ROOT="$STACK" bash "$STACK/nina-live/scripts/persona-build.sh" | grep -v "^go: downloading"
# bin/nina: acasa's cmd/nina since the redesign's step 1 (s-b478fe59), against the stack's checkouts
[ -x "$STACK/acasa/live/build.sh" ] && REPO_ROOT="$STACK" FSTTM_LOCAL=1 bash "$STACK/acasa/live/build.sh" | grep -v "^go: downloading"
