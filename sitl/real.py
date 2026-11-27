"""Real Nina's scenario set and its metrics: the redesign's measuring stick (subject s-b478fe59, step 0).

    real.py run [-j N] [--tag T] SCENARIO...      runs each scenario, writes runs/real/<tag>/<scenario>/
    real.py score RUN_DIR...                      the metrics of runs (one row per scenario per run)
    real.py baseline OUT.json RUN_DIR...          the baseline: per metric the median and the band (min, max)
    real.py gate BASELINE.json RUN_DIR...         a candidate's runs against it: each metric in band, better or worse

A scenario (sitl/real/<workspace>/*.yaml) is what a person says to her, the house's start and its hidden truth
(which devices obey), and what should come of it. Nina runs as deployed (sitl/nina_proc.py: cmd/nina from the
stack, ha-sim as Home Assistant, sitl/house.py the house behind it, DeepSeek Flash as her mind and her task
runner). The metrics are read afterwards from her own event log (nina.db) and the house's record, never from
what the loop saw on the way.

Turns: {say: words, want: {route, calls, no_calls, said_any, said_none}}, {wait: s}, {wait_task: s},
{set: {entity_id, state, attributes}}. Goal (after the last turn and settle_s): {states, lists, events, said_any,
said_none, calls, no_calls, task}.
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import shutil
import sqlite3
import statistics
import subprocess
import sys
import threading
import time
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nina_proc as NP  # noqa: E402
from house import AGENDA, House  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / 'sitl/runs/real'
TOKEN = 'sitl-token'


def stack_commits():
    out = {}
    for r in ('nina-live', 'fsttm-live', 'acasa', 'perotheia-packages/metis-agent', 'perotheia-packages/metis-lang'):
        p = NP.STACK / r
        if p.exists():
            out[r] = subprocess.run(['git', '-C', str(p), 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True).stdout.strip()
    return out


class Pump(threading.Thread):
    """The house answering her: each service call through the truth, the states when due, the services' data."""

    def __init__(self, ha, house):
        super().__init__(daemon=True)
        self.ha, self.house, self.due, self.seen, self.stop = ha, house, [], 0, False

    def run(self):
        while not self.stop:
            now = time.time()
            with self.ha.cv:
                calls = self.ha.calls[self.seen:]
                self.seen = len(self.ha.calls)
            changed = False
            for c in calls:
                d, ch = self.house.call(c, now)
                self.due += d
                changed |= ch
            if changed:
                self.ha.ctl({'responses': self.house.responses()})
            for at, st in [x for x in self.due if x[0] <= now]:
                self.house.apply(st)
                self.ha.ctl({'set': st})
            self.due = [x for x in self.due if x[0] > now]
            time.sleep(0.2)


def catalog_for(ws_map, run):
    cat = run / 'catalog'
    shutil.copytree(NP.STACK / 'nina-live/catalog', cat, symlinks=True, ignore=shutil.ignore_patterns('.metis'))
    shutil.copy(ws_map, cat / 'world/home.map.json')
    return cat


def tasks_finished(db):
    try:
        c = sqlite3.connect('file:%s?mode=ro' % db, uri=True, timeout=2)
        r = c.execute("select count(*) from events where stream='task' and kind in ('done','failed','stopped')").fetchone()[0]
        n = c.execute("select count(*) from events where stream='task' and kind='created'").fetchone()[0]
        c.close()
        return n, r
    except sqlite3.Error:
        return 0, 0


def run_one(sc_path, tag, sets=None):
    sc = yaml.safe_load(Path(sc_path).read_text())
    m_path = (Path(sc_path).parent / sc['world_map']).resolve()
    m = json.loads(m_path.read_text())
    run = RUNS / tag / sc['scenario']
    if run.exists():
        shutil.rmtree(run)
    run.mkdir(parents=True)
    house = House(m, sc)
    log = open(run / 'trace.jsonl', 'w')
    ha = NP.HA(TOKEN, log)
    ha.ctl({'states': house.initial()})
    ha.ctl({'responses': house.responses()})
    extra = {'agenda': AGENDA}
    for k, v in (sets or {}).items():   # --set home.route=director: the core config's switches
        d = extra
        ks = k.split('.')
        if ks[0] in NP.CORE_SECTIONS and ks[0] not in extra:
            extra[ks[0]] = dict(NP.core_template().get(ks[0]) or {})
        for x in ks[:-1]:
            d = d.setdefault(x, {})
        d[ks[-1]] = v
    nina = NP.Nina(ha.url, TOKEN, run, catalog=catalog_for(m_path, run), core_extra=extra)
    pump = Pump(ha, house)
    pump.start()
    turns = []
    try:
        time.sleep(float(sc.get('settle_start_s', 6)))
        for t in sc.get('turns') or []:
            if 'say' in t:
                c0 = len(ha.calls)
                t0 = time.time()
                evs = nina.say(t['say'], wait=float(t.get('timeout_s', 120)))
                time.sleep(float(t.get('after_s', 3)))
                turns.append({'say': t['say'], 'at': t0, 'want': t.get('want') or {},
                              'ha_calls': ['%s.%s %s' % (c['domain'], c['service'], ' '.join(_ents(c))) for c in ha.calls[c0:]],
                              'she_said': [x.get('said') for x in evs if x.get('ev') == 'reply_done']})
            elif 'wait' in t:
                time.sleep(float(t['wait']))
            elif 'wait_task' in t:
                end = time.time() + float(t['wait_task'])
                while time.time() < end:
                    n, r = tasks_finished(run / 'nina.db')
                    if n and r >= n:
                        break
                    time.sleep(2)
                time.sleep(3)
            elif 'set' in t:
                house.apply(t['set'])
                ha.ctl({'set': t['set']})
        time.sleep(float(sc.get('settle_s', 8)))
    finally:
        pump.stop = True
        nina.close()
        ha.close()
        log.close()
    rec = {'scenario': sc['scenario'], 'path': str(sc_path), 'goal': sc.get('goal') or {}, 'turns': turns,
           'calls': ['%s.%s %s' % (c['domain'], c['service'], ' '.join(_ents(c))) for c in ha.calls],
           'call_data': [c for c in ha.calls],
           'states': house.states, 'lists': house.lists, 'events': house.events, 'effects': house.effects,
           'stack': stack_commits(), 'sets': sets or {}}
    (run / 'run.json').write_text(json.dumps(rec, indent=1, default=str))
    return run


def _ents(c):
    e = (c.get('data') or {}).get('entity_id') or []
    return e if isinstance(e, list) else [e]


# ---------------------------------------------------------------- metrics

def _low(xs):
    return ' '.join(x or '' for x in xs).lower()


def _matches(pattern, calls):
    """A wanted call 'light.turn_on light.sim_living_lamp' (a prefix match on the service and its entity)."""
    return any(c.startswith(pattern) for c in calls)


def score(run):
    run = Path(run)
    rec = json.loads((run / 'run.json').read_text())
    db = sqlite3.connect('file:%s?mode=ro' % (run / 'nina.db'), uri=True)
    rows = [(seq, at, st, kd, json.loads(d)) for seq, at, st, kd, d in
            db.execute("select seq, at, stream, kind, data from events order by seq")]
    db.close()
    dialog = [(at, kd, d) for _, at, st, kd, d in rows if st == 'dialog']
    typed = [(at, d.get('text')) for at, kd, d in dialog if kd == 'typed']
    done = [(at, d) for at, kd, d in dialog if kd == 'reply_done']
    tools = [(at, d) for at, kd, d in dialog if kd == 'tool']
    usage = [(at, d) for at, kd, d in dialog if kd == 'mind_usage']
    tasks = [(at, kd, d) for _, at, st, kd, d in rows if st == 'task']
    out = {'scenario': rec['scenario'], 'run': str(run)}
    # per turn: the span from her typed words to the next typed words
    spans = []
    for i, (at, _) in enumerate(typed):
        end = typed[i + 1][0] if i + 1 < len(typed) else float('inf')
        spans.append((at, end))
    route_ok = route_n = 0
    turn_checks = turn_n = 0
    lat, tcalls, ptoks, ctoks, refused = [], [], [], [], 0
    attended = None   # cards: two (the redesign's step 5): the card an attended call goes to
    cards_of = {}
    for at, d in tools:
        n, a = d.get('name', ''), d.get('args') or {}
        if n == 'director' and a.get('verb') == 'route' and a.get('to'):
            attended = a['to']
        elif n == 'attended':
            attended = a.get('card') or attended
            cards_of[id(d)] = attended
    for (t0, t1), turn in zip(spans, rec['turns']):
        w = turn.get('want') or {}
        ts = [d for at, d in tools if t0 <= at < t1]
        homes = [d['name'][5:] if d.get('name', '').startswith('home_') else cards_of.get(id(d)) for d in ts
                 if d.get('name', '').startswith('home_') or (d.get('name') == 'attended' and cards_of.get(id(d)))]
        if 'route' in w:
            route_n += 1
            want = w['route']
            first = homes[0] if homes else ('delegate' if any(d.get('name') == 'delegate' for d in ts) else
                                            next((d.get('name') for d in ts), None))
            route_ok += (first == want) if want is not None else (not homes)
        ds = [at for at, _ in done if t0 <= at < t1]
        if ds:
            lat.append(ds[0] - t0)
        tcalls.append(len(ts))
        refused += sum(1 for d in ts if (d.get('result') or {}).get('status') in ('refused', 'error'))
        u = [d for at, d in usage if t0 <= at < t1]
        ptoks.append(sum(x.get('prompt_tokens', 0) for x in u))
        ctoks.append(sum(x.get('completion_tokens', 0) for x in u))
        ok, n = _checks(w, turn['ha_calls'], turn['she_said'], rec)
        turn_checks += ok
        turn_n += n
    ok, n = _checks(rec['goal'], rec['calls'], [x for t in rec['turns'] for x in t['she_said']], rec, tasks=tasks)
    out.update({
        'goal_met': int(ok == n), 'checks_ok': ok + turn_checks, 'checks_n': n + turn_n,
        'route_ok': route_ok, 'route_n': route_n,
        'tool_calls': sum(tcalls), 'refusals': refused,
        'latency_s': round(statistics.median(lat), 2) if lat else None, 'latency_max_s': round(max(lat), 2) if lat else None,
        'prompt_tokens': sum(ptoks), 'completion_tokens': sum(ctoks),
        'surprises': sum(1 for _, _, st, kd, _ in rows if st == 'surprise' and kd == 'surprise'),
        'commands': sum(1 for _, _, st, kd, _ in rows if st == 'world' and kd == 'command'),
        'ha_calls': len(rec['calls']),
        'tasks': sum(1 for _, kd, _ in tasks if kd == 'created'),
        'tasks_done': sum(1 for _, kd, _ in tasks if kd == 'done'),
        'task_tool_calls': sum(1 for _, kd, _ in tasks if kd == 'tool'),
        'mcp_uncovered': sum(1 for _, _, st, kd, _ in rows if st == 'mcp' and kd == 'uncovered'),
        'errors': sum(1 for at, kd, d in dialog if kd in ('mind_error',)),
    })
    return out


def _checks(g, calls, said, rec, tasks=None):
    ok = n = 0
    low = _low(said)

    def check(c):
        nonlocal ok, n
        n += 1
        ok += bool(c)
    for p in g.get('calls') or []:
        check(_matches(p, calls))
    for p in g.get('no_calls') or []:
        check(not _matches(p, calls))
    if g.get('said_any'):
        check(any(re.search(x.lower(), low) for x in g['said_any']))
    for x in g.get('said_none') or []:
        check(not re.search(x.lower(), low))
    for e, s in (g.get('states') or {}).items():
        st = rec['states'].get(e) or {}
        if isinstance(s, dict):
            check(all(str((st.get('attributes') or {}).get(k)) == str(v) if k != 'state' else st.get('state') == v for k, v in s.items()))
        else:
            check(st.get('state') == s)
    for e, want in (g.get('lists') or {}).items():
        items = [x.lower() for x in rec['lists'].get(e, [])]
        for x in want.get('has') or []:
            check(any(x.lower() in i for i in items))
        for x in want.get('not') or []:
            check(not any(x.lower() in i for i in items))
    for e, want in (g.get('events') or {}).items():
        sums = [x['summary'].lower() for x in rec['events'].get(e, [])]
        for x in want.get('has') or []:
            check(any(x.lower() in s for s in sums))
        if want.get('none'):
            check(not sums or all(any(o.lower() in s for o in want.get('keep', [])) for s in sums))
    if 'task' in g and tasks is not None:
        if g['task'].get('created'):
            check(any(kd == 'created' for _, kd, _ in tasks))
        if g['task'].get('done'):
            check(any(kd == 'done' for _, kd, _ in tasks))
        if g['task'].get('none'):
            check(not any(kd == 'created' for _, kd, _ in tasks))
    return ok, n


# Each metric's direction: +1 higher is better, -1 lower is better, 0 watched only.
METRICS = {'goal_met': 1, 'checks_ok': 1, 'route_ok': 1, 'tool_calls': -1, 'refusals': 0, 'latency_s': -1,
           'latency_max_s': -1, 'prompt_tokens': -1, 'completion_tokens': -1, 'surprises': 0, 'commands': 0,
           'ha_calls': 0, 'tasks': 0, 'tasks_done': 1, 'task_tool_calls': -1, 'mcp_uncovered': -1, 'errors': -1}
TOTALS = ('goal_met', 'checks_ok', 'checks_n', 'route_ok', 'route_n', 'tool_calls', 'refusals', 'prompt_tokens',
          'completion_tokens', 'surprises', 'tasks', 'tasks_done', 'task_tool_calls', 'mcp_uncovered', 'errors')


def table(run_dirs):
    rows = []
    for rd in run_dirs:
        for r in sorted(Path(rd).iterdir()):
            if (r / 'run.json').exists():
                rows.append(score(r))
    return rows


def totals(rows):
    """Per run tag: the sums (and the latency median) over its scenarios."""
    by = {}
    for r in rows:
        by.setdefault(str(Path(r['run']).parent), []).append(r)
    out = {}
    for tag, rs in by.items():
        t = {k: sum(r[k] or 0 for r in rs) for k in TOTALS}
        lats = [r['latency_s'] for r in rs if r['latency_s'] is not None]
        t['latency_s'] = round(statistics.median(lats), 2) if lats else None
        t['scenarios'] = len(rs)
        out[tag] = t
    return out


def baseline(out, run_dirs):
    rows = table(run_dirs)
    tot = totals(rows)
    per = {}
    for r in rows:
        per.setdefault(r['scenario'], []).append(r)
    band = {}
    for k in list(TOTALS) + ['latency_s']:
        vs = [t[k] for t in tot.values() if t[k] is not None]
        if vs:
            band[k] = {'median': statistics.median(vs), 'min': min(vs), 'max': max(vs)}
    scen = {s: {k: {'median': statistics.median([r[k] for r in rs if r[k] is not None] or [0]),
                    'min': min([r[k] for r in rs if r[k] is not None] or [0]),
                    'max': max([r[k] for r in rs if r[k] is not None] or [0])} for k in METRICS}
            for s, rs in per.items()}
    stack = {}
    for rd in run_dirs:
        for r in Path(rd).iterdir():
            if (r / 'run.json').exists():
                stack = json.loads((r / 'run.json').read_text()).get('stack', {})
                break
    Path(out).write_text(json.dumps({'runs': list(tot), 'stack': stack, 'totals': tot, 'band': band, 'scenarios': scen}, indent=1))
    print(json.dumps({'band': band}, indent=1))


def gate(base, run_dirs):
    b = json.loads(Path(base).read_text())
    tot = totals(table(run_dirs))
    verdict = 'pass'
    lines = []
    for k, d in sorted(METRICS.items()):
        if k not in b['band']:
            continue
        lo, hi, med = b['band'][k]['min'], b['band'][k]['max'], b['band'][k]['median']
        vs = [t[k] for t in tot.values() if t.get(k) is not None]
        if not vs:
            continue
        v = statistics.median(vs)
        if lo <= v <= hi:
            s = 'in band'
        elif (v > hi and d > 0) or (v < lo and d < 0):
            s = 'better'
        elif d == 0:
            s = 'moved (watched)'
        else:
            s = 'WORSE'
            verdict = 'fail'
        lines.append('%-18s %8s  baseline %s [%s, %s]  %s' % (k, v, med, lo, hi, s))
    print('\n'.join(lines))
    print('verdict:', verdict)
    return verdict


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run')
    r.add_argument('-j', type=int, default=4)
    r.add_argument('--tag', default=time.strftime('%Y%m%d-%H%M%S'))
    r.add_argument('--set', action='append', default=[], help='a core config switch: home.route=director, cards=two')
    r.add_argument('scenarios', nargs='+')
    s = sub.add_parser('score')
    s.add_argument('runs', nargs='+')
    b = sub.add_parser('baseline')
    b.add_argument('out')
    b.add_argument('runs', nargs='+')
    g = sub.add_parser('gate')
    g.add_argument('base')
    g.add_argument('runs', nargs='+')
    a = ap.parse_args()
    if a.cmd == 'run':
        with cf.ThreadPoolExecutor(a.j) as ex:
            sets = dict(x.split('=', 1) for x in a.set)
            futs = {ex.submit(run_one, p, a.tag, sets): p for p in a.scenarios}
            for f in cf.as_completed(futs):
                try:
                    print(json.dumps(score(f.result())), flush=True)
                except Exception as e:  # a scenario that could not run is a finding, not a crash of the set
                    print(json.dumps({'scenario': futs[f], 'error': repr(e)}), flush=True)
    elif a.cmd == 'score':
        rows = table(a.runs)
        for r in rows:
            print(json.dumps(r))
        print(json.dumps(totals(rows), indent=1))
    elif a.cmd == 'baseline':
        baseline(a.out, a.runs)
    elif a.cmd == 'gate':
        sys.exit(0 if gate(a.base, a.runs) == 'pass' else 1)


if __name__ == '__main__':
    main()
