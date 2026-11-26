"""Run every SITL scenario and compare it with the recorded baseline: the regressions and the new surprises.

    sitl/run.sh is the loop; this is the suite:
    METIS_PY=... python sitl/regress.py [--update] [SCENARIO ...]

A scenario's essence is what the rules did and what the world and the monitors noticed: the command rules fired
(member, rule, args, beat), the findings (monitor or world key, beat), whether each `expect` was met, and the
world's final hash. The baseline (sitl/baseline.json) records the essence of every scenario at a known commit.
A change is reported as NEW (a finding the baseline lacks: a surprise to triage), GONE (a finding that went away:
fixed, or a lost producer), or CHANGED (the same findings, different acts). `--update` records the current
essences as the new baseline; do it only with the change reviewed.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / 'sitl/baseline.json'


def scenarios(args):
    if args:
        return [Path(a).resolve() for a in args]
    found = (p.resolve() for p in (ROOT / 'workspaces').glob('*/scenarios/**/*.yaml'))
    return sorted(p for p in found if p.read_text().lstrip().startswith(('scenario:', '#')) and
                  any(line.startswith('scenario:') for line in p.read_text().splitlines()))


def essence(summary):
    return {'commands': [[c['k'], c['member'], c['rule'], c['args']] for c in summary['commands']],
            'findings': sorted([f.get('monitor') or f['slug'].rsplit('-', 1)[0], f['k1']] for f in summary['findings']),
            'expect': [[e.get('monitor') or e.get('key'), e['met']] for e in summary['expect']],
            'world_hash': summary['world_hash']}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('scenario', nargs='*')
    ap.add_argument('--update', action='store_true')
    a = ap.parse_args()
    base = json.loads(BASELINE.read_text()) if BASELINE.exists() else {}
    now, report, failed, errors = {}, [], False, False
    for sc in scenarios(a.scenario):
        rel = str(sc.relative_to(ROOT))
        r = subprocess.run([str(ROOT / 'sitl/run.sh'), str(sc)], capture_output=True, text=True)
        out = Path(json.loads(r.stdout[:r.stdout.rindex('}') + 1])['run']) if r.stdout.strip().startswith('{') else None
        summ = ROOT / 'sitl/runs' / out / 'summary.json' if out else None
        if summ is None or not summ.exists():
            report.append('ERROR  %s\n  %s' % (rel, (r.stderr or r.stdout).strip().splitlines()[-1:]))
            failed = errors = True
            continue
        e = essence(json.loads(summ.read_text()))
        now[rel] = e
        b = base.get(rel)
        if b is None:
            report.append('FIRST  %s  findings=%s' % (rel, [f[0] for f in e['findings']]))
            continue
        new = [f for f in e['findings'] if f not in b['findings']]
        gone = [f for f in b['findings'] if f not in e['findings']]
        if new:
            report.append('NEW    %s  %s' % (rel, new))
            failed = True
        if gone:
            report.append('GONE   %s  %s' % (rel, gone))
            failed = True
        if not new and not gone and (e['commands'] != b['commands'] or e['world_hash'] != b['world_hash']):
            report.append('CHANGED %s  acts or world differ, same findings' % rel)
            failed = True
        if not new and not gone and e['expect'] != b['expect']:
            report.append('CHANGED %s  narrative expectation differs' % rel)
            failed = True
        if not new and not gone and e == b:
            report.append('same   %s' % rel)
    print('\n'.join(report))
    if a.update and not errors:
        merged = {**base, **now} if a.scenario else now
        BASELINE.write_text(json.dumps(merged, indent=1, sort_keys=True) + '\n')
        print('baseline updated: %d scenarios' % len(now))
    sys.exit(1 if errors or (failed and not a.update) else 0)


if __name__ == '__main__':
    main()
