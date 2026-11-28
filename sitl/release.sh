#!/usr/bin/env bash
# release.sh: a release's certificate (the user, 2026-11-28). Real Nina in the loop costs model tokens, so it
# runs only here, at a release tag, on Pascal (the keys stay off GitHub); every push is certified for
# nothing by CI (the catalog: sitl/certify.sh; the runtime: nina-live's Go tests).
#
#   sitl/release.sh TAG [ROUNDS]    e.g. sitl/release.sh v0.3.0 3
#   SITL_MIND=google:gemini-3.8-flash,gemini-3.7-flash,gemini-3.5-flash,gemini-3.1-flash-lite sitl/release.sh TAG   (her minds on Gemini)
#   sitl/release-overnight.sh TAG [ROUNDS]   the same, scheduled for the night (01:30), on Gemini
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
case "${SITL_MIND:-openrouter:}" in
  google:*) left() { echo 999; }; BUDGET=0                 # Gemini: the AI Studio key's quota, not OpenRouter's money
            echo "release: mind $SITL_MIND (Gemini; OpenRouter not spent)";;
esac
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

# unreached: a run whose mind could not be reached (the network, the provider, the credit: "no such host",
# "requires more credits") tested the infrastructure, not her (Pascal's DNS, 2026-11-28 18:2x)
unreached() { find "sitl/runs/real/$1" -name nina.db -exec sqlite3 {} "select data from events where kind='mind_error'" \; 2>/dev/null |
  grep -ciE 'no such host|connection refused|network is unreachable|i/o timeout|tls handshake|requires more credits|502 bad gateway' || true; }
# suite TAG ARGS…: one suite of a round, run again once (its runs set aside) when its mind was not reached
suite() { local tag=$1; shift
  "$P" sitl/real.py run --tag "$tag" "$@" > /dev/null 2>&1
  local n; n=$(unreached "$tag")
  if [ "${n:-0}" -gt 0 ]; then
    echo "  $tag: her mind unreached $n times (the network or the provider): run again" | tee -a "$STACK.reruns"
    mv "sitl/runs/real/$tag" "sitl/runs/real/$tag.unreached-$(date +%H%M%S)"
    "$P" sitl/real.py run --tag "$tag" "$@" > /dev/null 2>&1
  fi; }
: > "$STACK.reruns"

echo "== 3. the acceptance (level 3): $ROUNDS rounds"
dirs=()
need=1.0   # a round's cost, learnt from the last one (x1.25): no round starts that the money would cut short
for i in $(seq 1 "$ROUNDS"); do
  l=$(left)
  python3 -c "import sys; sys.exit(0 if float('$l') >= float('$need') else 1)" || { echo "release: stopped before round $i, \$$l left, a round needs \$$need" >&2; exit 2; }
  suite "rel-$TAG-$i" -j 4 sitl/real/home/*.yaml
  suite "rel-$TAG-times-$i" -j 3 sitl/real/w5/*.yaml
  suite "rel-$TAG-live-$i" -j 3 --live --set home.world_beat=300ms sitl/real/live/*.yaml
  dirs+=("sitl/runs/real/rel-$TAG-$i")
  e=$(left); c=$(python3 -c "print(round(float('$l') - float('$e'), 2))")
  need=$(python3 -c "print(round(max(1.0, 1.25 * $c), 2))")
  echo "round $i done $(date +%H:%M), \$$e left (it cost \$$c)"
done
after=$(left)

MIND=$("$P" -c "import sys; sys.path.insert(0, 'sitl'); import nina_proc; print(nina_proc.MIND)")
# the band to meet: the newest certificate made with the same mind (another model's band says nothing of this one's)
prev=$("$P" - "$CERTS" "$MIND" <<'PY'
import json, sys
from pathlib import Path
cs = sorted(Path(sys.argv[1]).glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
ok = lambda c: c.get('certified') and c.get('mind', 'openrouter:deepseek/deepseek-v4.1-flash') == sys.argv[2]
print(next((str(p) for p in cs if ok(json.load(open(p)))), ''))   # a certified one only: a failed run sets no band
PY
)
"$P" - "$TAG" "$ROUNDS" "$CAT" "${prev:-}" "$before" "$after" "$STACK" "$CERTS/$TAG.json" "$MIND" <<'PY'
import json, statistics, subprocess, sys
from pathlib import Path
sys.path.insert(0, 'sitl')
import real
tag, rounds, cat, prev, before, after, stack, out, mind = sys.argv[1:]
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
# what Nina is built from in Go: nina-live's module pins (metis-agent is the pin, not the stack's checkout)
for l in open(Path(stack) / 'nina-live' / 'go.mod'):
    f = l.split()
    if len(f) >= 2 and f[0].startswith('github.com/metis-lang-dev/'):
        refs['go.mod ' + f[0].split('/', 2)[2]] = f[1]
catalog = json.load(open(cat))
cert = {'tag': tag, 'certified': catalog['certified'] and verdict == 'pass', 'mind': mind, 'refs': refs, 'catalog': catalog,
        'acceptance': {'rounds': rounds, 'band': band, 'against': Path(prev).stem if prev else None,
                       'gate': rows, 'verdict': verdict, 'scenarios': {k: {'checks': '%d/%d' % (v[0], v[1]), 'runs_all_pass': '%d/%d' % (v[2], rounds)} for k, v in sorted(per.items())}},
        'spent_usd': round(float(before) - float(after), 2),
        'reruns': [l.strip() for l in open(stack + '.reruns')] if Path(stack + '.reruns').exists() else []}
json.dump(cert, open(out, 'w'), indent=1)
print('\n'.join(rows) or '(the first release: its band is the next one\'s)')
for k, v in sorted(per.items()):
    print('%-22s checks %d/%d  runs all-pass %d/%d' % (k, v[0], v[1], v[2], rounds))
if not cert['certified']:                # kept apart: the tag may be run again once mended, and sets no band
    import time
    Path(out).parent.joinpath('failed').mkdir(exist_ok=True)
    out = str(Path(out).parent / 'failed' / ('%s.%s.json' % (tag, time.strftime('%Y%m%dT%H%M'))))
    json.dump(cert, open(out, 'w'), indent=1)
    Path(sys.argv[8]).unlink()
print('certificate:', out, 'CERTIFIED' if cert['certified'] else 'NOT certified', '(spent $%.2f)' % cert['spent_usd'])
sys.exit(0 if cert['certified'] else 1)
PY
