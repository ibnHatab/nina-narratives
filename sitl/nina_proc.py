"""Nina in the loop (sitl/NINA-IN-THE-LOOP.md, phase 1): nina-live's cmd/nina, headless, against ha-sim.

    nina_proc.py smoke            the house's lights from nina-live's map, "turn on the living room light"

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
NINA = HOME / 'repo/nina-live/bin/nina'
ACASA = HOME / 'repo/acasa/live'
HA_SIM = ROOT / 'sitl/ha-sim/ha-sim'


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

    def __init__(self, ha_url, token, workdir, catalog=None, model='deepseek/deepseek-v4.1-flash'):
        self.dir = Path(workdir)
        (self.dir / 'token').write_text(token)
        os.chmod(self.dir / 'token', 0o600)
        self.port = free_port()
        core = yaml.safe_load((ACASA / 'nina.yaml').read_text())
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
        (self.dir / 'nina.yaml').write_text(yaml.safe_dump(core, sort_keys=False))
        dia = yaml.safe_load((ACASA / 'pascal.yaml').read_text())
        dia['audio'].update({'device': 'none', 'channels': 1, 'speech': 0, 'ref': -1, 'out': 'null'})
        dia['dialog']['wake'] = {'mode': 'cloud'}
        dia['dialog']['start_asleep'] = False
        dia['sources'] = {'metis': {'enabled': False}}
        dia['prefs'].update({'mic': True, 'voice': True})
        dia['plugins']['web'].update({'addr': '127.0.0.1:%d' % self.port, 'remote': ''})
        dia['plugins']['gpio'] = {'enabled': False}
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


if __name__ == '__main__':
    {'smoke': smoke}[sys.argv[1] if len(sys.argv) > 1 else 'smoke']()
