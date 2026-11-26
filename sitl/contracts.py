"""World contracts (interfaces/world/*.yaml): load them and check a workspace against them.

    python3 sitl/contracts.py check [--workspace DIR] [--world-map MAP]

Three checks, each reported, none silently skipped:

1. schema: every contract has the keys of interfaces/README.md and its .llp compiles inside a probe member
   (metisc; a unit alone cannot be compiled, its layers are its includer's);
2. members: every member of the workspace's composition reads only ports a contract offers, as one of its
   consumers; every contract command's actuating rules exist in a member's program;
3. world: the semantic world itself accepts each member's manifest (Board.Join refuses a port the world does not
   offer), via sitl/semworld-step with the workspace's world map.

Exit status 1 when any check fails. A finding about a member is a migration item, not a contract bug.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT / 'interfaces' / 'world'
KEYS = {'family', 'version', 'owner', 'ports', 'edges', 'commands', 'receipts', 'consumers'}
OWNERS = {'world', 'host', 'person'}
RECEIPTS = {'none', 'ha_state', 'report'}


def metisc():
    return os.environ.get('METISC') or str(ROOT.parent / 'perotheia-packages/metis-lang/src/metisc')


def stepper():
    return os.environ.get('SEMWORLD_STEP') or str(ROOT / 'sitl/semworld-step/semworld-step')


def load(world=WORLD):
    contracts = {}
    for path in sorted(world.glob('*.yaml')):
        c = yaml.safe_load(path.read_text())
        c['_path'] = path
        contracts[c['family']] = c
    return contracts


def check_schema(contracts):
    bad = []
    for name, c in contracts.items():
        missing = KEYS - set(c)
        if missing:
            bad.append(f'{name}: missing keys {sorted(missing)}')
        if c.get('owner') not in OWNERS:
            bad.append(f'{name}: owner {c.get("owner")!r} not in {sorted(OWNERS)}')
        if (c.get('receipts') or {}).get('via') not in RECEIPTS:
            bad.append(f'{name}: receipts.via not in {sorted(RECEIPTS)}')
        for cmd, spec in (c.get('commands') or {}).items():
            for k in ('rules', 'args', 'predicts', 'grace_s', 'adapter'):
                if k not in spec:
                    bad.append(f'{name}: command {cmd} lacks {k}')
        if name != c['_path'].stem:
            bad.append(f'{name}: family differs from its file name {c["_path"].name}')
    return bad


def check_compile(contracts):
    """Compile every contract unit inside one probe member: their types bound to one constant each."""
    units = [c['_path'].with_suffix('.llp') for c in contracts.values() if c['_path'].with_suffix('.llp').exists()]
    types = set()
    for u in units:
        for m in re.finditer(r'^types \(([^)]*)\)\.', u.read_text(), re.M):
            types.update(m.group(1).split())
    with tempfile.TemporaryDirectory() as tmp:
        for u in units:
            Path(tmp, u.name).write_text(u.read_text())
        body = ['catalog contract_probe 1.', 'layers (dyn).', 'stages (serve).']
        body += [f'type {t} {{{t}_1}}.' for t in sorted(types)]
        body += [f'include "{u.name}".' for u in units]
        body += ['namespace contract_probe produce (dyn).', 'pred probe_seen : contract_probe.',
                 'stage serve {', '  %% the probe saw the floor.', '  probe [dyn] : floor -o probe_seen.', '}']
        Path(tmp, 'probe.llp').write_text('\n'.join(body) + '\n')
        r = subprocess.run([metisc(), 'probe.llp'], cwd=tmp, capture_output=True, text=True)
        out = (r.stdout + r.stderr).strip()
        return [] if out.startswith('ok ') else [f'compile: {out}']


def members(workspace):
    comp = yaml.safe_load((workspace / 'composition.yaml').read_text())
    found = {}
    for name in comp.get('specialists', []) + [comp.get('direct')]:
        if not name:
            continue
        manifest = workspace / name / 'domain.yaml'
        if manifest.exists():
            found[name] = (manifest, yaml.safe_load(manifest.read_text()) or {})
    return comp, found


def check_members(contracts, workspace):
    """Members read only offered ports, as consumers; every contract command's rules exist in a member's program.
    Availability is not checked here: it is the world's, after discovery (a port with no keys gives no atom)."""
    offered = {spec['world_port']: n for n, c in contracts.items() for spec in (c.get('ports') or {}).values()}
    _, ms = members(workspace)
    bad = []
    for name, (_, man) in sorted(ms.items()):
        for belief, spec in (man.get('beliefs') or {}).items():
            port = spec.get('port') if isinstance(spec, dict) else None
            if port not in offered:
                bad.append(f'{name}: reads port {port!r} (belief {belief}) that no contract offers')
            elif name not in (contracts[offered[port]].get('consumers') or []):
                bad.append(f'{name}: reads {offered[port]}.{port} but is not among its consumers')
    defined = set()
    for name, (path, _) in ms.items():
        for llp in path.parent.glob('*.llp'):
            defined |= set(re.findall(r'^\s+([a-z_][a-z0-9_]*) \[', llp.read_text(), re.M))
    for n, c in sorted(contracts.items()):
        for cmd, spec in (c.get('commands') or {}).items():
            missing = [r for r in spec.get('rules') or [] if r not in defined]
            if missing and len(missing) == len(spec.get('rules') or []):
                bad.append(f'note: {n}.{cmd} is not served by this workspace (none of {" ".join(missing)})')
            elif missing:
                bad.append(f'{n}.{cmd}: rules in no member program: {" ".join(missing)}')
    return bad


def check_world(workspace, world_map):
    """Join every member that reads ports to the semantic world; its refusal is the finding."""
    _, ms = members(workspace)
    readers = [(n, p) for n, (p, man) in sorted(ms.items()) if man.get('beliefs')]
    if not readers:
        return []
    if not Path(stepper()).exists():
        return [f'world: {stepper()} not built (cd sitl/semworld-step && go build)']
    bad = []
    for name, path in readers:
        line = json.dumps({'join': {'member': name, 'manifest': str(path)}})
        r = subprocess.run([stepper(), '-map', str(world_map)], input=line + '\n', capture_output=True, text=True)
        try:
            reply = json.loads(r.stdout.splitlines()[0])
        except (IndexError, ValueError):
            bad.append(f'world: {name}: {r.stderr.strip() or "no reply"}')
            continue
        if not reply['ok']:
            bad.append(f'world: {name}: {reply["error"]}')
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['check'])
    ap.add_argument('--workspace', type=Path, help="a composition's directory (where composition.yaml is)")
    ap.add_argument('--world-map', type=Path, help='the semantic world map (home.map.json)')
    a = ap.parse_args()
    contracts = load()
    sections = [('schema', check_schema(contracts)), ('compile', check_compile(contracts))]
    if a.workspace:
        sections.append(('members', check_members(contracts, a.workspace)))
        if a.world_map:
            sections.append(('world', check_world(a.workspace, a.world_map)))
        else:
            sections.append(('world', ['not run: no --world-map']))
    failed = False
    for title, findings in sections:
        real = [f for f in findings if not f.startswith(('note:', 'not run'))]
        status = 'ok' if not real else 'FAIL'
        if not real and any(f.startswith('not run') for f in findings):
            status = 'not run'
        failed |= status == 'FAIL'
        print(f'{title}: {status} ({len(contracts)} contracts)' if title in ('schema', 'compile') else f'{title}: {status}')
        for f in findings:
            print('  ' + f)
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
