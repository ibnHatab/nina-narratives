"""Nina in the loop (sitl/NINA-IN-THE-LOOP.md, phase 1): nina-live's cmd/nina, headless, against ha-sim.

    nina_proc.py smoke            the radio and the shopping list on a fake house
    nina_proc.py run SCENARIO...  a scenario of words and house states (kinds say/ha_state), its truth the house

Nina runs as deployed (her core, composition image, semantic world, hosts, task runner, panel) with her edges
simulated: ha-sim is Home Assistant (its truth: this loop's), her words are typed through her panel, no
microphone (audio device none), no speakers (ALSA null). Her task runner: DeepSeek Flash through OpenRouter.
Her events come from her panel's stream (/api/events); her service calls from ha-sim's stdout: each is the
command she gave the house, and the truth (HomeAssistantSim's rule: obeys, delay) answers with a state.
"""
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
STACK = Path(os.environ.get('STACK', ROOT / '.stack'))  # Nina's own install (sitl/stack.sh), not a machine's
NINA = STACK / 'acasa/bin/nina' if (STACK / 'acasa/bin/nina').exists() else STACK / 'nina-live/bin/nina'  # acasa's since step 1
ACASA = STACK / 'acasa/live'
HA_SIM = ROOT / 'sitl/ha-sim/ha-sim'
MIND = 'openrouter:deepseek/deepseek-v4.1-flash'  # her minds on OpenRouter: no Gemini call in the SITL (the user)


CORE_SECTIONS = ('home', 'tasks', 'search', 'music')   # the core config's sections a --set may reach into


def core_template():
    return into_stack(yaml.safe_load((ACASA / 'nina.yaml').read_text()))


def into_stack(v):
    """Every ~/repo/… path of the templates, into the stack."""
    if isinstance(v, dict):
        return {k: into_stack(x) for k, x in v.items()}
    if isinstance(v, list):
        return [into_stack(x) for x in v]
    if isinstance(v, str) and v.startswith('~/repo/'):
        return str(STACK / v[len('~/repo/'):])
    return v


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


class HA:
    """ha-sim as a subprocess: control lines in, calls out (a thread collects them)."""

    def __init__(self, token, log):
        self.p = subprocess.Popen([str(HA_SIM), '-token', token], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  text=True, bufsize=1)
        self.calls, self.writes, self.log = [], [], log
        self.replies = {}
        self.cv = threading.Condition()
        self.url = json.loads(self.p.stdout.readline())['ready']
        self.n = 0
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.p.stdout:
            m = json.loads(line)
            with self.cv:
                if 'call' in m:
                    m['call']['at'] = time.time()
                    self.calls.append(m['call'])
                    self.log.write(json.dumps({'ha_call': m['call']}) + '\n')
                elif 'write' in m:
                    self.writes.append(m['write'])
                elif 'reply' in m:
                    self.replies[m['reply']] = m
                self.cv.notify_all()

    def ctl(self, obj):
        with self.cv:
            self.n += 1
            n = self.n
            self.p.stdin.write(json.dumps(obj) + '\n')
            self.p.stdin.flush()
            self.cv.wait_for(lambda: n in self.replies, timeout=5)

    def close(self):
        self.p.stdin.close()
        self.p.wait(timeout=5)


class Nina:
    """cmd/nina, headless, its configs generated from the acasa templates."""

    def __init__(self, ha_url, token, workdir, catalog=None, model='deepseek/deepseek-v4.1-flash', core_extra=None, dia_extra=None):
        self.dir = Path(workdir)
        (self.dir / 'token').write_text(token)
        os.chmod(self.dir / 'token', 0o600)
        self.port = free_port()
        core = into_stack(yaml.safe_load((ACASA / 'nina.yaml').read_text()))
        core['log'] = str(self.dir / 'nina.db')
        if catalog:
            core['home']['root'] = str(catalog)
        core['hass'] = {'url': ha_url, 'token': str(self.dir / 'token')}
        core['dialogue'] = str(self.dir / 'dialogue.yaml')
        core['tasks'].update({'provider': 'openrouter', 'model': model, 'key': str(HOME / '.config/nina/openrouter.env'),
                              'fallback': []})
        core['search'] = {'enabled': False}
        core['whatsapp'] = {'enabled': False}
        core['radar'] = False
        core['mcp'] = []
        core.update(core_extra or {})
        (self.dir / 'nina.yaml').write_text(yaml.safe_dump(core, sort_keys=False))
        dia = into_stack(yaml.safe_load((ACASA / 'pascal.yaml').read_text()))
        dia['models']['mind'] = MIND
        dia['models']['mind_key'] = str(HOME / '.config/nina/openrouter.env')
        dia['audio'].update({'device': 'none', 'channels': 1, 'speech': 0, 'ref': -1, 'out': 'null'})
        dia['dialog']['wake'] = {'mode': 'cloud'}
        dia['dialog']['start_asleep'] = False
        dia['sources'] = {'metis': {'enabled': False}}
        dia['prefs'].update({'mic': True, 'voice': True})
        dia['plugins']['web'].update({'addr': '127.0.0.1:%d' % self.port, 'remote': ''})
        dia['plugins']['gpio'] = {'enabled': False}
        for k, v in (dia_extra or {}).items():
            dia[k] = {**dia.get(k, {}), **v} if isinstance(v, dict) else v
        (self.dir / 'dialogue.yaml').write_text(yaml.safe_dump(dia, sort_keys=False))
        self.out = open(self.dir / 'nina.log', 'w')
        self.p = subprocess.Popen([str(NINA), '-config', str(self.dir / 'nina.yaml')], stdout=self.out, stderr=subprocess.STDOUT)
        self.panel = 'http://127.0.0.1:%d' % self.port
        self.events = []
        self.cv = threading.Condition()
        self._wait_up()
        threading.Thread(target=self._stream, daemon=True).start()

    def _wait_up(self, limit=90):
        end = time.time() + limit
        while time.time() < end:
            if self.p.poll() is not None:
                raise RuntimeError('cmd/nina exited: see %s' % (self.dir / 'nina.log'))
            try:
                urllib.request.urlopen(self.panel + '/api/state', timeout=2).read()
                return
            except Exception:
                time.sleep(1)
        raise RuntimeError('cmd/nina did not come up in %ds: see %s' % (limit, self.dir / 'nina.log'))

    def _stream(self):
        r = urllib.request.urlopen(self.panel + '/api/events', timeout=3600)
        kind = None
        for raw in r:
            line = raw.decode().rstrip('\n')
            if line.startswith('event:'):
                kind = line[6:].strip()
            elif line.startswith('data:') and kind == 'ev':
                e = json.loads(line[5:])
                with self.cv:
                    self.events.append((time.time(), e))
                    self.cv.notify_all()

    def do(self, action, arg=''):
        req = urllib.request.Request(self.panel + '/api/do', data=json.dumps({'action': action, 'arg': arg}).encode(),
                                     headers={'Content-Type': 'application/json'})
        return json.load(urllib.request.urlopen(req, timeout=10))

    def say(self, text, wait=90):
        """Types the person's words; returns her events until her reply is done."""
        with self.cv:
            n0 = len(self.events)
        self.do('type', text)
        end = time.time() + wait
        with self.cv:
            while time.time() < end:
                if any(e.get('ev') == 'reply_done' for _, e in self.events[n0:]):
                    break
                self.cv.wait(timeout=1)
            return [e for _, e in self.events[n0:]]

    def close(self):
        self.p.terminate()
        try:
            self.p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.p.kill()
        self.out.close()


def lights_of_map(path):
    """The house's lights (nina-live's map): their entity ids, all off at the start."""
    m = json.loads(Path(path).read_text())
    out = []
    for role, d in (m.get('lights') or {}).items():
        ent = d.get('entity') if isinstance(d, dict) else d
        if ent:
            out.append({'entity_id': ent, 'state': 'off', 'attributes': {'friendly_name': (d.get('name') if isinstance(d, dict) else None) or ent}})
    return out


HOUSE = [  # the entities Pascal's Nina reaches (her music host, her lists, the weather)
    {'entity_id': 'media_player.music_player_daemon', 'state': 'idle', 'attributes': {'friendly_name': 'Music Player Daemon', 'volume_level': 0.3}},
    {'entity_id': 'todo.shopping_list', 'state': '0', 'attributes': {'friendly_name': 'Shopping list'}},
    {'entity_id': 'weather.home', 'state': 'cloudy', 'attributes': {'friendly_name': 'Home', 'temperature': 6}},
]


def smoke():
    run = Path(tempfile.mkdtemp(prefix='nina-sitl-'))
    log = open(run / 'trace.jsonl', 'w')
    ha = HA('sitl-token', log)
    ha.ctl({'states': HOUSE})
    nina = Nina(ha.url, 'sitl-token', run)
    out = {'run': str(run), 'turns': []}
    try:
        time.sleep(5)  # her world settles on the house's states
        for words in ('Nina, play some jazz on the radio.', 'Add milk to the shopping list.'):
            c0 = len(ha.calls)
            evs = nina.say(words)
            out['turns'].append({'said': words,
                                 'tools': [(e.get('name'), e.get('args')) for e in evs if e.get('ev') == 'tool'],
                                 'ha_calls': [(c['domain'], c['service'], c['data']) for c in ha.calls[c0:]],
                                 'she_said': [e.get('said') for e in evs if e.get('ev') == 'reply_done']})
        print(json.dumps(out, indent=1, default=str))
    finally:
        nina.close()
        ha.close()
        log.close()


SUPPORTED = {'say', 'ha_state'}   # a scenario of the cognition atoms (report, floor, hands) waits for phase 2


def catalog_for(sc_path, sc, run):
    """nina-live's catalog (the stack's), its home map the scenario's: her domains and image as deployed."""
    import shutil
    cat = run / 'catalog'
    shutil.copytree(STACK / 'nina-live/catalog', cat, symlinks=True, ignore=shutil.ignore_patterns('.metis'))
    shutil.copy(Path(sc_path).parent / sc['world_map'], cat / 'world/home.map.json')
    return cat


def bridge(call, m):
    """A service call as HomeAssistantSim's tool: (tool, args, role) or None (no device of the map)."""
    svc = (call['domain'], call['service'])
    ents = (call.get('data') or {}).get('entity_id') or []
    ents = ents if isinstance(ents, list) else [ents]
    tool = {'turn_on': 'HassTurnOn', 'turn_off': 'HassTurnOff', 'set_preset_mode': 'HassFanSetPresetMode'}.get(svc[1])
    if not tool or not ents:
        return None
    role = None
    for r, u in (m.get('units') or {}).items():
        if any(e.split('.', 1)[-1].startswith(u['prefix']) for e in ents):
            role = r
    for r, l in (m.get('lights') or {}).items():
        if l.get('entity') in ents:
            role = r
    args = {'name': ents}
    if tool == 'HassFanSetPresetMode':
        args['preset_mode'] = call['data'].get('preset_mode')
    return tool, args, role


def run_scenario(sc_path):
    from mcp_sim import HomeAssistantSim, discovery
    sc = yaml.safe_load(Path(sc_path).read_text())
    kinds = {e['kind'] for e in sc.get('script') or []}
    if kinds - SUPPORTED or (sc.get('truth') or {}).get('people'):
        return {'scenario': sc['scenario'], 'skipped': 'cognition atoms %s: phase 2 (the narratives\' members in cmd/nina)' % sorted(kinds - SUPPORTED or {'people'})}
    run = Path(tempfile.mkdtemp(prefix='nina-sitl-%s-' % sc['scenario']))
    m = json.loads((Path(sc_path).parent / sc['world_map']).read_text())
    truth = HomeAssistantSim((sc.get('truth') or {}).get('devices'))
    log = open(run / 'trace.jsonl', 'w')
    ha = HA('sitl-token', log)
    ha.ctl({'states': [e['ha'] for e in discovery(m, 0.0)]})
    nina = Nina(ha.url, 'sitl-token', run, catalog=catalog_for(sc_path, sc, run))
    out = {'scenario': sc['scenario'], 'run': str(run), 'turns': [], 'receipts': []}
    due = []                                       # (at, state): the house's replies, by scenario time
    seen = 0
    try:
        time.sleep(5)
        t0 = time.time()
        script = sorted(sc.get('script') or [], key=lambda e: e['at'])
        horizon = float(sc.get('horizon_s', 60))
        while True:
            now = time.time() - t0
            with ha.cv:
                calls = ha.calls[seen:]
                seen = len(ha.calls)
            for c in calls:                        # what she told the house: the truth answers
                b = bridge(c, m)
                if b:
                    _, receipts = truth.call(b[0], b[1], now, 'sitl', b[2])
                    due += receipts
                    out['receipts'].append({'at': round(now, 1), 'call': '%s.%s' % (c['domain'], c['service']),
                                            'entities': b[1]['name'], 'role': b[2], 'moves': bool(receipts)})
            for at, st in [x for x in due if x[0] <= now]:
                ha.ctl({'set': st})
            due = [x for x in due if x[0] > now]
            if script and script[0]['at'] <= now:
                e = script.pop(0)
                if e['kind'] == 'ha_state':
                    ha.ctl({'set': e['ha']})
                elif e['kind'] == 'say':
                    c0 = len(ha.calls)
                    evs = nina.say(e['words'])
                    out['turns'].append({'at': e['at'], 'said': e['words'],
                                         'tools': [(x.get('name'), x.get('args')) for x in evs if x.get('ev') == 'tool'],
                                         'ha_calls': ['%s.%s %s' % (c['domain'], c['service'], (c.get('data') or {}).get('entity_id'))
                                                      for c in ha.calls[c0:]],
                                         'she_said': [x.get('said') for x in evs if x.get('ev') == 'reply_done']})
                continue
            if not script and now >= horizon:
                break
            time.sleep(0.2)
        evs = nina.say('Is the living room ventilation running?') if sc['scenario'] == 'b01-c02-ventilation' else []
        if evs:
            out['probe'] = {'said': 'Is the living room ventilation running?',
                            'she_said': [x.get('said') for x in evs if x.get('ev') == 'reply_done']}
        out['surprises'] = [e for _, e in nina.events if 'surpris' in json.dumps(e).lower()][:10]
    finally:
        nina.close()
        ha.close()
        log.close()
    return out


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'smoke'
    if cmd == 'run':
        for p in sys.argv[2:]:
            print(json.dumps(run_scenario(p), indent=1, default=str), flush=True)
    else:
        {'smoke': smoke}[cmd]()
