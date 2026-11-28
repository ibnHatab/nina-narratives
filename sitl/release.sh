#!/usr/bin/env bash
# release.sh: a release's certificate (the user, 2026-11-28). Real Nina in the loop costs model tokens, so it
# runs only here, at a release tag, on Pascal (the keys stay off GitHub); every push is certified for
# nothing by CI (the catalog: sitl/certify.sh; the runtime: nina-live's Go tests).
#
#   sitl/release.sh TAG [ROUNDS]    e.g. sitl/release.sh v0.3.0 3
#
#   1. her stack built at the release's refs (STACK=.stack-release; REF_NINA_LIVE=… as sitl/stack.sh takes);
#   2. what can be spent, checked first: the OpenRouter key's limit AND the account's credit (BUDGET, $);
#   3. the catalog's certification (level 1, sitl/certify.sh);
#   4. the acceptance (level 3): sitl/real/{home,live,w5} with real Nina, ROUNDS rounds (default 3), against
#      the previous release's band (sitl/certificates/*.json, the newest); the first release sets the band;
#   5. the certificate: sitl/certificates/TAG.json (the refs, the images, the catalog's verdicts, the
#      acceptance's metrics and band, the per-scenario checks, the money spent). Exit 0: certified.
#
# Uploading it to the GitHub release is the person's step (gh release upload TAG sitl/certificates/TAG.json).
set -euo pipefail
cd "$(dirname "$0")/.."
TAG=${1:?usage: sitl/release.sh TAG [ROUNDS]}
ROUNDS=${2:-3}
BUDGET=${BUDGET:-3}
STACK=${STACK:-$PWD/.stack-release}
export STACK
P=${METIS_PY:-$PWD/../perotheia-packages/metis-agent/py/.venv/bin/python}
CERTS=sitl/certificates
mkdir -p "$CERTS"
[ -e "$CERTS/$TAG.json" ] && { echo "release: $CERTS/$TAG.json exists" >&2; exit 1; }

# what can be spent: the key's limit left and the account's credit left (a raised limit over an empty
# account spends nothing: every call "requires more credits", 2026-11-28)
left() { ( set -a; . ~/.config/metis/openrouter.env; h="Authorization: Bearer $OPENROUTER_API_KEY"
  k=$(curl -s https://openrouter.ai/api/v1/key -H "$h"); c=$(curl -s https://openrouter.ai/api/v1/credits -H "$h")
  python3 -c "import json,sys; k=json.loads(sys.argv[1])['data']; c=json.loads(sys.argv[2])['data']; l=k.get('limit_remaining'); a=c['total_credits']-c['total_usage']; print(round(min(a, l if l is not None else a), 2))" "$k" "$c" ); }
before=$(left)
python3 -c "import sys; sys.exit(0 if float('$before') >= float('$BUDGET') else 1)" ||
  { echo "release: \$$before can be spent, under the budget \$$BUDGET: add OpenRouter credit (or BUDGET=…)" >&2; exit 2; }
echo "release $TAG: \$$before can be spent"

echo "== 1. her stack at the release's refs ($STACK)"
bash sitl/stack.sh > "$STACK.build.log" 2>&1 || { tail -5 "$STACK.build.log"; exit 1; }

echo "== 2. the catalog (level 1)"
CAT=$(mktemp)
OUT=$CAT METISC="$STACK/perotheia-packages/metis-lang/src/metisc" METIS_PY="$P" bash "$STACK/nina-narratives/sitl/certify.sh" > "$CAT.log" 2>&1 || {
  tail -5 "$CAT.log"; echo "release: the catalog is not certified" >&2; exit 1; }

echo "== 3. the acceptance (level 3): $ROUNDS rounds"
dirs=()
for i in $(seq 1 "$ROUNDS"); do
  l=$(left)
  python3 -c "import sys; sys.exit(0 if float('$l') >= 1.0 else 1)" || { echo "release: stopped before round $i, \$$l left" >&2; exit 2; }
  "$P" sitl/real.py run -j 4 --tag "rel-$TAG-$i" sitl/real/home/*.yaml > /dev/null 2>&1
  "$P" sitl/real.py run -j 3 --tag "rel-$TAG-times-$i" sitl/real/w5/*.yaml > /dev/null 2>&1
  "$P" sitl/real.py run -j 3 --tag "rel-$TAG-live-$i" --live --set home.world_beat=300ms sitl/real/live/*.yaml > /dev/null 2>&1
  dirs+=("sitl/runs/real/rel-$TAG-$i")
  echo "round $i done $(date +%H:%M), \$$(left) left"
done
after=$(left)

prev=$(ls -t "$CERTS"/*.json 2>/dev/null | head -1 || true)
"$P" - "$TAG" "$ROUNDS" "$CAT" "${prev:-}" "$before" "$after" "$STACK" "$CERTS/$TAG.json" <<'PY'
import json, statistics, subprocess, sys
from pathlib import Path
sys.path.insert(0, 'sitl')
import real
tag, rounds, cat, prev, before, after, stack, out = sys.argv[1:]
rounds = int(rounds)
home = ['sitl/runs/real/rel-%s-%d' % (tag, i) for i in range(1, rounds + 1)]
tot = real.totals(real.table(home))
band, verdict, rows = {}, 'pass', []
for k in list(real.TOTALS) + ['latency_s']:
    vs = [t[k] for t in tot.values() if t.get(k) is not None]
    if vs:
        band[k] = {'median': statistics.median(vs), 'min': min(vs), 'max': max(vs)}
old = json.load(open(prev))['acceptance']['band'] if prev else None
if old:                                  # the gate's rule: the median against the previous release's band
    for k, d in real.METRICS.items():
        if k not in band or k not in old:
            continue
        v, lo, hi = band[k]['median'], old[k]['min'], old[k]['max']
        s = 'in band' if lo <= v <= hi else ('better' if (v > hi and d > 0) or (v < lo and d < 0) else ('moved' if d == 0 else 'WORSE'))
        verdict = 'fail' if s == 'WORSE' else verdict
        rows.append('%-18s %10s  previous [%s, %s]  %s' % (k, v, lo, hi, s))
per = {}
for kind in ('times', 'live'):
    for i in range(1, rounds + 1):
        d = Path('sitl/runs/real/rel-%s-%s-%d' % (tag, kind, i))
        for r in sorted(d.iterdir()) if d.exists() else []:
            if (r / 'run.json').exists():
                s = real.score(r)
                p = per.setdefault(s['scenario'], [0, 0, 0])
                p[0] += s['checks_ok']; p[1] += s['checks_n']; p[2] += int(s['checks_ok'] == s['checks_n'])
        # a scenario not every run of which passed fails the release (its checks are the acceptance's)
for k, (ok, n, full) in per.items():
    if full < rounds:
        verdict = 'fail'
refs = {}
for d in sorted(Path(stack).glob('*/.git')) + sorted(Path(stack).glob('perotheia-packages/*/.git')):
    repo = d.parent
    refs[str(repo.relative_to(stack))] = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
catalog = json.load(open(cat))
cert = {'tag': tag, 'certified': catalog['certified'] and verdict == 'pass', 'refs': refs, 'catalog': catalog,
        'acceptance': {'rounds': rounds, 'band': band, 'against': Path(prev).stem if prev else None,
                       'gate': rows, 'verdict': verdict, 'scenarios': {k: {'checks': '%d/%d' % (v[0], v[1]), 'runs_all_pass': '%d/%d' % (v[2], rounds)} for k, v in sorted(per.items())}},
        'spent_usd': round(float(before) - float(after), 2)}
json.dump(cert, open(out, 'w'), indent=1)
print('\n'.join(rows) or '(the first release: its band is the next one\'s)')
for k, v in sorted(per.items()):
    print('%-22s checks %d/%d  runs all-pass %d/%d' % (k, v[0], v[1], v[2], rounds))
print('certificate:', out, 'CERTIFIED' if cert['certified'] else 'NOT certified', '(spent $%.2f)' % cert['spent_usd'])
sys.exit(0 if cert['certified'] else 1)
PY
