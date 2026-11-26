"""The SITL loop: one incarnation's composition against the semantic world and simulated adapters.

    python sitl/loop.py SCENARIO.yaml [--seed N] [--out DIR]

One beat (sitl/README.md):
1. the due events (the script, the people's replies, the adapters' receipts) go into the world (device readings)
   or become contract edges (a person's words);
2. a settle gives the world's level lines, its State() for the families, and its surprises;
3. each member's host gets its lines, families and edges; the person's requests go through the intent card;
4. the composition ticks;
5. every fired rule a contract binds becomes a command (a world command event first, then the adapter);
6. the monitors compare the hidden truth with what fired, and every finding goes to the workspace feed.

Everything in and out is logged, in order, to <out>/events.jsonl; summary.json holds the acts, findings and checks.
"""
import argparse
import copy
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'sitl'))

from mcp_sim import HomeAssistantSim  # noqa: E402
from monitors import Monitors
from person_sim import Person  # noqa: E402
from project import EVENTS, OUTCOMES, OWNED, Projector  # noqa: E402

PRESETS = {'air_night': 'night', 'air_night_from_boost': 'night', 'sweep_night': 'night', 'sweep_night_boost': 'night',
           'air_boost': 'boost', 'air_boost_from_night': 'boost', 'normal_from_night': 'normal',
           'normal_from_boost': 'normal'}
SWITCHES = {'heater_up': ('heater', 'on', 'HassTurnOn'), 'heater_down': ('heater', 'off', 'HassTurnOff'),
            'winter_up': ('winter', 'on', 'HassTurnOn'), 'winter_down': ('winter', 'off', 'HassTurnOff')}
WORLD_KINDS = {'ha_state', 'feed_down', 'command', 'conclude', 'settle', 'strain'}


class World:
    """semworld-step as a subprocess: one JSON line in, one JSON line out."""

    def __init__(self, world_map, members, log):
        cmd = [str(ROOT / 'sitl/semworld-step/semworld-step'), '-map', str(world_map)]
        for name, manifest in members:
            cmd += ['-member', '%s=%s' % (name, manifest)]
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        self.log = log

    def send(self, ev):
        self.p.stdin.write(json.dumps(ev, sort_keys=True) + '\n')
        self.p.stdin.flush()
        reply = json.loads(self.p.stdout.readline())
        self.log.write(json.dumps({'world': ev, 'reply': {k: reply.get(k) for k in ('seq', 'ok', 'error', 'hash')},
                                   'surprises': (reply.get('out') or {}).get('Surprises') or []}, sort_keys=True) + '\n')
        if not reply['ok']:
            raise RuntimeError('world refused %s: %s' % (ev, reply['error']))
        return reply

    def close(self):
        self.p.stdin.close()
        self.p.wait()


def contracts(world_dir):
    """(rule -> (family, command, spec), [edge specs]) from every contract."""
    rules, edges = {}, []
    for path in sorted(world_dir.glob('*.yaml')):
        c = yaml.safe_load(path.read_text())
        for name, spec in (c.get('commands') or {}).items():
            for rule in spec.get('rules') or []:
                rules[rule] = (c['family'], name, spec)
        for e in c.get('edges') or []:
            if isinstance(e, dict) and e.get('when'):
                edges.append(dict(e, family=c['family'], consumers=c['consumers']))
    return rules, edges


def edge_of(ev, edges):
    """The contract edge a non-world event stands for, as (atom, lifetime), else None."""
    for e in edges:
        on = e['when']
        if on.get('kind') != ev.get('kind'):
            continue
        if any(ev.get(k) != v for k, v in on.items() if k != 'kind'):
            continue
        pred = e['pred'].split('(')[0]
        args = [str(ev[field]) for field in e.get('args', ['id'] if '(' in e['pred'] else [])]
        atom = pred + ('(' + ','.join(args) + ')' if args else '')
        return atom, e.get('lifetime', 'beat')
    return None


def device_command(rule, family, spec, role, m):
    """The world's prediction (var, value) and the HA tool call for a fired device rule on ROLE."""
    pred, mcp = dict(spec['predicts']), dict(spec['adapter']['mcp'])
    if family == 'lights':
        return pred, mcp['tool'], {'name': m['lights'][role]['entity']}
    pre = m['units'][role]['prefix']
    fans = ['fan.%s_supply_fan' % pre, 'fan.%s_extract_fan' % pre]
    if rule in PRESETS:
        pred['value'] = PRESETS[rule]
        return pred, mcp['tool'], {'name': fans[0], 'preset_mode': PRESETS[rule]}
    if rule in SWITCHES:
        var, state, tool = SWITCHES[rule]
        return {'var': var, 'value': state}, tool, {'name': 'switch.%s_%s' % (pre, var)}
    return pred, mcp['tool'], {'name': fans}


def discovery(m, at):
    """The initial get_states: every entity the map names, as discovered. Devices off, rooms empty."""
    out = []
    for d in (m.get('lights') or {}).values():
        if d.get('entity'):
            out.append({'entity_id': d['entity'], 'state': 'off', 'attributes': {}})
    for d in (m.get('units') or {}).values():
        for f in ('supply', 'extract'):
            out.append({'entity_id': 'fan.%s_%s_fan' % (d['prefix'], f), 'state': 'off', 'attributes': {}})
        for sv in ('heater', 'winter'):
            out.append({'entity_id': 'switch.%s_%s' % (d['prefix'], sv), 'state': 'off', 'attributes': {}})
    for d in (m.get('tvs') or {}).values():
        if d.get('entity'):
            out.append({'entity_id': d['entity'], 'state': 'off', 'attributes': {}})
    for r, e in (m.get('radar') or {}).items():
        if e and not r.startswith('_'):
            out.append({'entity_id': e, 'state': 'off', 'attributes': {}})
    out.append({'entity_id': m.get('sun', 'sun.sun'), 'state': 'above_horizon', 'attributes': {}})
    return [{'at': at, 'kind': 'ha_state', 'ha': s} for s in out]


def run(scenario_path, seed=None, out_dir=None, *, scenario=None, storage=None):
    sc = scenario if scenario is not None else yaml.safe_load(Path(scenario_path).read_text())
    base = Path(scenario_path).parent
    ws = (base / sc['workspace']).resolve()                     # the composition's directory
    home = (base / sc['metis_workspace']).resolve() if sc.get('metis_workspace') else ws
    home = Path(storage or home)
    comparisons = {}
    for monitor in sc.get('monitors') or []:
        if 'never_reads' not in monitor:
            continue
        spec = monitor['never_reads']
        other = copy.deepcopy(sc)
        other['scenario'] += '-' + monitor['id'] + '-control'
        other['monitors'], other['expect'] = [], []
        person = other['truth']['people'][spec['person']]
        if person[spec['field']] == spec['alternative']:
            raise ValueError('noninterference control must change the private fact')
        person[spec['field']] = spec['alternative']
        control = run(scenario_path, seed, out_dir, scenario=other, storage=home)
        comparisons[monitor['id']] = control['acts']
    m = json.loads((base / sc['world_map']).read_text())
    seed = sc.get('seed', 1) if seed is None else seed
    run_id = '%s-s%d' % (sc['scenario'], seed)
    out = Path(out_dir or ROOT / 'sitl/runs') / run_id
    out.mkdir(parents=True, exist_ok=True)
    comp = yaml.safe_load((ws / 'composition.yaml').read_text())
    names = list(comp['specialists']) + [comp['direct']]
    mans = {n: yaml.safe_load((ws / n / 'domain.yaml').read_text()) or {} for n in names}
    readers = [(n, ws / n / 'domain.yaml') for n in comp['specialists'] if mans[n].get('beliefs')]

    os.environ['METIS_CATALOG'] = str(ws)                       # the workspace is the catalog root: its packages only
    if sc.get('metis_home'):
        os.environ['METIS_HOME'] = str((base / sc['metis_home']).resolve())
    import nina_world.host as nh
    nh.REGISTRY.clear()
    from metis.catalog.workspace import Workspace
    from metis_agent.runtime.feed import RuntimeFeed
    from metis_agent.service import Live
    from metis_agent.trace import NoModel
    workspace = Workspace(home)
    workspace.made()
    trace_dir = workspace.path('trace', run=run_id)
    trace_dir.mkdir(parents=True, exist_ok=True)
    cfg = {'v3': {'catalog': [], 'loaded': names, 'image': str(ws), 'prompt': ['../go/grammar/v3-orchestrator.txt']},
           'domains': {'tick': True, 'consult': False, 'seed': seed, 'records': None}}
    (trace_dir / 'config.yaml').write_text(yaml.safe_dump(dict(cfg, scenario=sc['scenario'])))
    cfg['trace'] = dict(dir=str(trace_dir), every=0, ring=0)
    live = Live(cfg, NoModel())
    live.handle_due = lambda *_: None
    hosts = dict(nh.REGISTRY)
    rules, edge_specs = contracts(ROOT / 'interfaces/world')
    edge_preds = {e['pred'].split('(')[0]: e.get('lifetime', 'beat') for e in edge_specs}
    takes = {n: set((mans[n].get('world') or {}).get('out') or []) for n in names}
    for name, preds in takes.items():
        allowed = {e['pred'].split('(')[0] for e in edge_specs if name in e['consumers']}
        if preds - allowed:
            raise ValueError(f'{name} declares unauthorized world edges {sorted(preds - allowed)}')
    for n, h in hosts.items():
        h.retract = (set(OUTCOMES.get(n, ())) | set(EVENTS.get(n, ()))
                     | {p for p in takes.get(n, ()) if edge_preds.get(p) == 'beat'})
        h.owned = OWNED.get(n, ())

    truth = sc.get('truth') or {}
    ha = HomeAssistantSim(truth.get('devices'))
    people = {name: Person(name, t) for name, t in (truth.get('people') or {}).items()}
    monitors = Monitors(sc.get('monitors'), people)
    proj = Projector(m)
    beat_s, horizon = float(sc.get('beat_s', 5)), float(sc['horizon_s'])
    script = discovery(m, 0.0) + [dict(e) for e in sc.get('script') or []]
    for p in people.values():
        script += p.scheduled()
    script = sorted(script, key=lambda e: e['at'])
    pending = []                                   # (at, event): replies and receipts not yet due
    acts, surprises, findings, says = [], [], [], []
    feed = RuntimeFeed(workspace, 'sitl', domain=comp.get('name', 'home'))
    feed.start()
    feed.run_started(run_id, 'traces/' + run_id, dict(scenario=sc['scenario'], seed=seed))
    k = 0
    channel = 'hall'
    tasks = sorted({h['task'] for p in people.values() for h in p.t.get('hands') or []})
    truth_log = (trace_dir / 'truth.jsonl').open('w')     # the hidden truth per beat, for the triage (spec 20 §4)
    with (out / 'events.jsonl').open('w') as log:
        world = World(base / sc['world_map'], readers, log)
        try:
            t = 0.0
            while t <= horizon:
                due = [e for e in script if e['at'] <= t]
                script = [e for e in script if e['at'] > t]
                due += [e for a, e in sorted(pending, key=lambda x: x[0]) if a <= t]
                pending = [(a, e) for a, e in pending if a > t]
                person_cmds, beat_edges = [], {}
                for ev in due:
                    if ev.get('kind') in WORLD_KINDS:
                        rep = world.send({x: v for x, v in ev.items() if x != 'note'})
                        surprises += [dict(s, k=k) for s in (rep.get('out') or {}).get('Surprises') or []]
                        continue
                    log.write(json.dumps({'event': ev, 'k': k}, sort_keys=True) + '\n')
                    if ev.get('kind') == 'say':                 # a person's request through the member's card
                        person_cmds.append(ev)
                        continue
                    if ev.get('kind') == 'report':
                        monitors.report(ev, k)
                    if ev['kind'] == 'floor':
                        channel = ev.get('channel', 'hall')
                    hit = edge_of(ev, edge_specs)
                    if hit is None:
                        raise ValueError('event %s matches no contract edge' % ev)
                    atom, _ = hit
                    for n in names:
                        if atom.split('(')[0] in takes.get(n, ()):
                            beat_edges.setdefault(n, []).append(atom)
                reply = world.send({'at': t, 'kind': 'settle'})
                surprises += [dict(s, k=k) for s in (reply.get('out') or {}).get('Surprises') or []]
                fams, dev_edges = proj.project(reply['state'], t)
                lines = (reply.get('out') or {}).get('Lines') or {}
                for n, h in hosts.items():
                    want, evs = Projector.for_member(n, fams, dev_edges)
                    h.give(t, want, lines.get(n) or [], evs + beat_edges.get(n, []))
                for i, p in enumerate(person_cmds):
                    live.agents.agents[p['member']].host.submit('%s:%d:say%d' % (run_id, k, i), p['atom'])
                says += [dict(p, k=k) for p in person_cmds]
                things = []
                for task in tasks:
                    tr = {}
                    for p in people.values():
                        for key, v in p.truth_at(task, t).items():
                            tr[key] = tr.get(key) or v
                    things.append({'id': task, 'role': task, 'class': 'obligation', 'as': 'task',
                                   'completed': tr.get('done', False), 'deferred': tr.get('deferred', False),
                                   'available': any(a.startswith('floor') for e in beat_edges.values() for a in e)})
                truth_log.write(json.dumps({'k': k, 'things': things}, sort_keys=True) + '\n')
                live.tick()
                feed.tick(k)
                for n, h in sorted(hosts.items()):
                    for _, rule, args in h.drain():
                        args = list(args)
                        acts.append({'at': t, 'k': k, 'member': n, 'rule': rule, 'args': args, 'channel': channel})
                        log.write(json.dumps({'fired': rule, 'member': n, 'args': args, 'k': k}) + '\n')
                        for f in monitors.check(acts[-1]):
                            findings.append(f)
                            feed.finding(f)
                        if rule not in rules:
                            continue
                        family, cmd, spec = rules[rule]
                        cid = '%s:%d:%s:%s' % (run_id, k, rule, ','.join(args))
                        adapter = spec['adapter']
                        if 'person' in adapter:                 # Nina speaks: the people hear it
                            for p in people.values():
                                if p.listens(channel, t):
                                    pending += p.hear(t, args[0] if args else None)
                            log.write(json.dumps({'adapter': 'person', 'cid': cid, 'heard': args}) + '\n')
                            continue
                        role = args[0]
                        pred, tool, targs = device_command(rule, family, spec, role, m)
                        ev = {'at': t, 'kind': 'command', 'id': role, 'var': pred['var'], 'value': pred['value'],
                              'ref': cid}
                        surprises += [dict(s, k=k) for s in (world.send(ev).get('out') or {}).get('Surprises') or []]
                        h.hold[role] = t + float(spec['grace_s'])
                        answer, receipts = ha.call(tool, targs, t, cid, role)
                        log.write(json.dumps({'adapter': 'ha', 'cid': cid, 'tool': tool, 'args': targs,
                                              'answer': answer}, sort_keys=True) + '\n')
                        pending += [(a, {'at': a, 'kind': 'ha_state', 'ha': s}) for a, s in receipts]
                t += beat_s
                k += 1
            for finding in monitors.finish(t - beat_s, k - 1, comparisons):
                findings.append(finding)
                feed.finding(finding)
            final = world.send({'hash': True})['hash']
        finally:
            world.close()
    for s in surprises:                                # the world's own surprises, as the workspace's records
        findings.append({'kind': 'violation', 'slug': 'world-%s-%d' % (s['key'], s['k']), 'k': s['k'], 'k0': s['k'],
                         'k1': s['k'], 'words': 'world (%s): %s %s' % (s['kind'], s['key'], s['why']), 'world': s})
        feed.finding(findings[-1])
    truth_log.close()
    live.tracer.close()
    ids = feed.run_ended(run_id, 'done')
    feed.stop()
    summary = {'run': run_id, 'scenario': sc['scenario'], 'seed': seed, 'image': getattr(live.image, 'hash', None),
               'acts': acts, 'commands': [a for a in acts if a['rule'] in rules], 'fired': len(acts), 'says': says,
               'surprises': surprises, 'findings': [{k_: v for k_, v in f.items() if k_ != 'world'} for f in findings],
               'records': [i for i in ids if i], 'world_hash': final}
    checks = []
    for e in sc.get('expect') or []:
        if e.get('producer') == 'world':
            met = any(s['key'] == e['key'] for s in surprises)
        else:
            met = any(f.get('monitor') == e.get('monitor') for f in findings)
        checks.append(dict(e, met=met if not e.get('absent') else not met))
    summary['expect'] = checks
    (out / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    return summary


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('scenario')
    ap.add_argument('--seed', type=int)
    ap.add_argument('--out')
    a = ap.parse_args()
    t0 = time.time()
    s = run(a.scenario, a.seed, a.out)
    print(json.dumps({k: s[k] for k in ('run', 'commands', 'findings', 'expect', 'world_hash')}, indent=1))
    print('%.1fs' % (time.time() - t0), file=sys.stderr)
    sys.exit(0 if all(e['met'] for e in s['expect']) else 1)
