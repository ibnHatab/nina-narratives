"""The SITL loop: one incarnation's composition against the semantic world and simulated MCP adapters.

    python sitl/loop.py SCENARIO.yaml [--seed N] [--out DIR]

One beat (sitl/README.md): the script's and the adapters' due events into the world, a settle, the world's
lines and the projected families to each member's host, the composition's tick, every fired command rule to a
command event (the world's prediction, written first) and an adapter call. Every input and every world reply
goes to runs/<run>/events.jsonl, in order.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'sitl'))

from mcp_sim import HomeAssistantSim  # noqa: E402
from project import EVENTS, OUTCOMES, OWNED, Projector  # noqa: E402

PRESETS = {'air_night': 'night', 'air_night_from_boost': 'night', 'sweep_night': 'night', 'sweep_night_boost': 'night',
           'air_boost': 'boost', 'air_boost_from_night': 'boost', 'normal_from_night': 'normal',
           'normal_from_boost': 'normal'}
SWITCHES = {'heater_up': ('heater', 'on', 'HassTurnOn'), 'heater_down': ('heater', 'off', 'HassTurnOff'),
            'winter_up': ('winter', 'on', 'HassTurnOn'), 'winter_down': ('winter', 'off', 'HassTurnOff')}


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
        self.log.write(json.dumps({'in': ev, 'reply': {k: reply.get(k) for k in ('seq', 'ok', 'error', 'hash')},
                                   'surprises': (reply.get('out') or {}).get('Surprises') or []}, sort_keys=True) + '\n')
        if not reply['ok']:
            raise RuntimeError('world refused %s: %s' % (ev, reply['error']))
        return reply

    def close(self):
        self.p.stdin.close()
        self.p.wait()


def bindings(world_dir):
    """rule name -> (family, command, spec) from every contract's commands."""
    out = {}
    for path in sorted(world_dir.glob('*.yaml')):
        c = yaml.safe_load(path.read_text())
        for name, spec in (c.get('commands') or {}).items():
            for rule in spec.get('rules') or []:
                out[rule] = (c['family'], name, spec)
    return out


def entities(m, family, role):
    if family == 'lights':
        return {'entity': m['lights'][role]['entity']}
    pre = m['units'][role]['prefix']
    fans = ['fan.%s_supply_fan' % pre, 'fan.%s_extract_fan' % pre]
    return {'fans': fans, 'supply': fans[0], 'switch': None, 'prefix': pre}


def resolve(rule, family, spec, role, m):
    """The world's prediction (var, value) and the adapter's tool call for a fired rule on ROLE."""
    ent = entities(m, family, role)
    pred = dict(spec['predicts'])
    mcp = dict(spec['adapter']['mcp'])
    args = {}
    if rule in PRESETS:
        pred['value'] = PRESETS[rule]
        args = {'name': ent['supply'], 'preset_mode': PRESETS[rule]}
    elif rule in SWITCHES:
        var, state, tool = SWITCHES[rule]
        pred = {'var': var, 'value': state}
        mcp['tool'] = tool
        args = {'name': 'switch.%s_%s' % (ent['prefix'], var)}
    else:
        key = 'fans' if family == 'ventilation' else 'entity'
        args = {'name': ent[key]}
    return pred, mcp['tool'], args


def discovery(m, at):
    """The initial get_states: every entity the map names, as discovered. Devices off, rooms empty."""
    out = []
    for l, d in m['lights'].items():
        if d.get('entity'):
            out.append({'entity_id': d['entity'], 'state': 'off', 'attributes': {}})
    for u, d in m['units'].items():
        for f in ('supply', 'extract'):
            out.append({'entity_id': 'fan.%s_%s_fan' % (d['prefix'], f), 'state': 'off', 'attributes': {}})
        for sv in ('heater', 'winter'):
            out.append({'entity_id': 'switch.%s_%s' % (d['prefix'], sv), 'state': 'off', 'attributes': {}})
    for t, d in m['tvs'].items():
        if d.get('entity'):
            out.append({'entity_id': d['entity'], 'state': 'off', 'attributes': {}})
    for r, e in (m.get('radar') or {}).items():
        if e and not r.startswith('_'):
            out.append({'entity_id': e, 'state': 'off', 'attributes': {}})
    out.append({'entity_id': m.get('sun', 'sun.sun'), 'state': 'above_horizon', 'attributes': {}})
    return [{'at': at, 'kind': 'ha_state', 'ha': s} for s in out]


def run(scenario_path, seed=None, out_dir=None):
    sc = yaml.safe_load(Path(scenario_path).read_text())
    base = Path(scenario_path).parent
    ws = (base / sc['workspace']).resolve()
    m = json.loads((base / sc['world_map']).read_text())
    seed = sc.get('seed', 1) if seed is None else seed
    run_id = '%s-s%d' % (sc['scenario'], seed)
    out = Path(out_dir or ROOT / 'sitl/runs') / run_id
    out.mkdir(parents=True, exist_ok=True)
    comp = yaml.safe_load((ws / 'composition.yaml').read_text())
    names = list(comp['specialists']) + [comp['direct']]
    readers = [(n, ws / n / 'domain.yaml') for n in comp['specialists']
               if (yaml.safe_load((ws / n / 'domain.yaml').read_text()) or {}).get('beliefs')]

    import os
    os.environ['METIS_CATALOG'] = str(ws)       # the workspace is the catalog root: its packages, no other
    sys.path.insert(0, str(ROOT / 'sitl'))
    import nina_world.host as nh
    from metis_agent.service import Live
    from metis_agent.trace import NoModel
    cfg = {'v3': {'catalog': [], 'loaded': names, 'image': str(ws), 'prompt': ['../go/grammar/v3-orchestrator.txt']},
           'domains': {'tick': True, 'consult': False, 'seed': seed, 'records': None}, 'trace': None}
    live = Live(cfg, NoModel())
    live.handle_due = lambda *_: None
    hosts = dict(nh.REGISTRY)
    for n, h in hosts.items():
        h.retract = set(OUTCOMES.get(n, ())) | set(EVENTS.get(n, ()))
        h.owned = OWNED.get(n, ())

    rules = bindings(ROOT / 'interfaces/world')
    ha = HomeAssistantSim((sc.get('truth') or {}).get('devices'))
    proj = Projector(m)
    beat_s, horizon = float(sc.get('beat_s', 5)), float(sc['horizon_s'])
    script = sorted(discovery(m, 0.0) + [dict(e) for e in sc.get('script') or []], key=lambda e: e['at'])
    pending = []                                   # (at, event): the adapters' receipts
    acts, surprises, says = [], [], []
    with (out / 'events.jsonl').open('w') as log:
        world = World(base / sc['world_map'], readers, log)
        try:
            t = 0.0
            while t <= horizon:
                due = [e for e in script if e['at'] <= t]
                script = [e for e in script if e['at'] > t]
                due += [e for a, e in sorted(pending, key=lambda x: x[0]) if a <= t]
                pending = [(a, e) for a, e in pending if a > t]
                person = []
                for ev in due:
                    if ev.get('kind') == 'say':                 # a person's request, mapped to the member's atom
                        person.append(ev)
                        log.write(json.dumps({'in': ev}) + '\n')
                        continue
                    ev = {k: v for k, v in ev.items() if k != 'note'}
                    surprises += [dict(s, beat=t) for s in (world.send(ev).get('out') or {}).get('Surprises') or []]
                reply = world.send({'at': t, 'kind': 'settle'})
                surprises += [dict(s, beat=t) for s in (reply.get('out') or {}).get('Surprises') or []]
                fams, edges = proj.project(reply['state'], t)
                lines = (reply.get('out') or {}).get('Lines') or {}
                for n, h in hosts.items():
                    want, evs = Projector.for_member(n, fams, edges)
                    h.give(t, want, lines.get(n) or [], evs)
                for i, p in enumerate(person):                  # the mapper's door: AgentHost.submit, as an intent
                    live.agents.agents[p['member']].host.submit('%s:%g:say%d' % (run_id, t, i), p['atom'])
                says += [dict(p, beat=t) for p in person]
                live.tick()
                for n, h in sorted(hosts.items()):
                    for _, rule, args in h.drain():
                        acts.append({'at': t, 'member': n, 'rule': rule, 'args': list(args)})
                        if rule not in rules:
                            continue
                        family, cmd, spec = rules[rule]
                        role = args[0]
                        cid = '%s:%g:%s:%s' % (run_id, t, rule, role)
                        pred, tool, targs = resolve(rule, family, spec, role, m)
                        ev = {'at': t, 'kind': 'command', 'id': role, 'var': pred['var'], 'value': pred['value'],
                              'ref': cid}
                        surprises += [dict(s, beat=t) for s in (world.send(ev).get('out') or {}).get('Surprises') or []]
                        h.hold[role] = t + float(spec['grace_s'])
                        answer, receipts = ha.call(tool, targs, t, cid, role)
                        log.write(json.dumps({'adapter': 'ha', 'cid': cid, 'tool': tool, 'args': targs,
                                              'answer': answer}, sort_keys=True) + '\n')
                        pending += [(a, {'at': a, 'kind': 'ha_state', 'ha': s}) for a, s in receipts]
                t += beat_s
            final = world.send({'hash': True})['hash']
        finally:
            world.close()
    summary = {'run': run_id, 'scenario': sc['scenario'], 'seed': seed, 'image': getattr(live.image, 'hash', None),
               'acts': [a for a in acts if a['rule'] in rules], 'fired': len(acts), 'says': says,
               'surprises': surprises, 'world_hash': final}
    expect = sc.get('expect') or []
    summary['expect'] = [{**e, 'met': any(s['key'] == e['key'] for s in surprises)} for e in expect]
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
    print(json.dumps({k: s[k] for k in ('run', 'acts', 'surprises', 'expect', 'world_hash')}, indent=1))
    print('%.1fs' % (time.time() - t0), file=sys.stderr)
