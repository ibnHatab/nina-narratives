"""The house as Home Assistant holds it, for real Nina in the loop (sitl/real.py): every entity she reaches
and what each service call does to it, the scenario's hidden truth deciding whether a device obeys.

ha-sim (sitl/ha-sim) is the transport; this is the truth behind it. A device's command is answered by ha-sim
at once ("accepted"), and its state comes later or never, as the truth says (`truth.devices`: role ->
{obeys, delay_s}); the services (lists, calendars, the weather) answer at once, from this house's data.
Only this module and the metrics read the truth.
"""
import datetime as dt
import time

# the agenda's handles bound to the SITL's entities (no machine's: the core config's `agenda:`)
AGENDA = {'nina_cal': 'calendar.sim_nina', 'nina_local': 'calendar.sim_nina_local', 'person_cal': 'calendar.sim_person',
          'my_tasks': 'todo.sim_my_tasks', 'nina_todo': 'todo.sim_nina_local', 'shopping': 'todo.shopping_list'}
NAMES = {'calendar.sim_nina': "Nina's calendar", 'calendar.sim_nina_local': 'Nina local', 'calendar.sim_person': 'My calendar',
         'todo.sim_my_tasks': 'My Tasks', 'todo.sim_nina_local': 'Nina local list', 'todo.shopping_list': 'Shopping list'}
PLAYER = 'media_player.music_player_daemon'


def iso(t):
    return dt.datetime.fromtimestamp(t).astimezone().isoformat(timespec='seconds')


class House:
    def __init__(self, m, sc):
        self.m = m
        h = sc.get('house') or {}
        self.truth = (sc.get('truth') or {}).get('devices') or {}
        self.t0 = time.time()
        self.states = {}
        for d in (m.get('lights') or {}).values():
            if d.get('entity'):
                self._put(d['entity'], 'off')
        for d in (m.get('units') or {}).values():
            for f in ('supply', 'extract'):
                self._put('fan.%s_%s_fan' % (d['prefix'], f), 'off')
            for sv in ('heater', 'winter'):
                self._put('switch.%s_%s' % (d['prefix'], sv), 'off')
        for d in (m.get('tvs') or {}).values():
            if d.get('entity'):
                self._put(d['entity'], 'off')
        for r, e in (m.get('radar') or {}).items():
            if e and not r.startswith('_'):
                self._put(e, 'off')
        for r, t in (m.get('thermometers') or {}).items():
            if isinstance(t, dict):
                for k, v in (('temperature', 21.0), ('humidity', 45)):
                    if t.get(k):
                        self._put(t[k], str(v), {'unit_of_measurement': '°C' if k == 'temperature' else '%', 'device_class': k})
        self._put(m.get('sun', 'sun.sun'), 'above_horizon')
        self._put(PLAYER, 'idle', {'friendly_name': 'Music Player Daemon', 'volume_level': 0.3})
        self.lists = {e: list((h.get('lists') or {}).get(e, [])) for e in AGENDA.values() if e.startswith('todo.')}
        self.events = {e: [] for e in AGENDA.values() if e.startswith('calendar.')}
        for e, evs in (h.get('events') or {}).items():
            for ev in evs:   # {in_h: hours from the start, summary, minutes}
                s = self.t0 + float(ev['in_h']) * 3600
                self.events.setdefault(e, []).append({'start': iso(s), 'end': iso(s + 60 * ev.get('minutes', 60)), 'summary': ev['summary']})
        for e in self.lists:
            self._put(e, str(len(self.lists[e])), {'friendly_name': NAMES[e], 'supported_features': 15})
        for e in self.events:
            self._put(e, 'off', {'friendly_name': NAMES[e]})
        self.weather = h.get('weather') or {'now': 'cloudy', 'temp': 6, 'days': [['rainy', 3, 8], ['cloudy', 2, 7], ['sunny', 1, 9]]}
        self._put('weather.home', self.weather['now'], {'friendly_name': 'Home', 'temperature': self.weather['temp'], 'temperature_unit': '°C'})
        for s in h.get('states') or []:   # the scenario's own start: {entity_id, state, attributes}
            self._put(s['entity_id'], s['state'], s.get('attributes') or {})
        self.effects = []   # (at, what): what the house did, for the metrics

    def _put(self, eid, state, attrs=None):
        a = dict((self.states.get(eid) or {}).get('attributes') or {})
        a.update(attrs or {})
        self.states[eid] = {'entity_id': eid, 'state': state, 'attributes': a}
        return self.states[eid]

    def initial(self):
        return list(self.states.values())

    def responses(self):
        """What the services with return_response answer now (ha-sim serves them as set)."""
        start = time.time()
        fc = [{'datetime': iso(start + 86400 * i), 'condition': c, 'templow': lo, 'temperature': hi}
              for i, (c, lo, hi) in enumerate(self.weather['days'])]
        return {'todo.get_items': {e: {'items': [{'summary': s, 'status': 'needs_action', 'uid': '%s-%d' % (e, i)} for i, s in enumerate(l)]}
                                   for e, l in self.lists.items()},
                'calendar.get_events': {e: {'events': sorted(l, key=lambda x: x['start'])} for e, l in self.events.items()},
                'weather.get_forecasts': {'weather.home': {'forecast': fc}}}

    def role(self, eid):
        for r, l in (self.m.get('lights') or {}).items():
            if l.get('entity') == eid:
                return r
        for r, u in (self.m.get('units') or {}).items():
            if eid.split('.', 1)[-1].startswith(u['prefix']):
                return r
        for r, t in (self.m.get('tvs') or {}).items():
            if t.get('entity') == eid:
                return r
        return None

    def call(self, c, now):
        """A service call she made: [(at, state)] the house reports, and whether its services changed."""
        dom, svc, data = c['domain'], c['service'], c.get('data') or {}
        ents = data.get('entity_id') or []
        ents = ents if isinstance(ents, list) else [ents]
        out, changed = [], False
        if dom in ('light', 'fan', 'switch', 'media_player') and svc in ('turn_on', 'turn_off', 'set_preset_mode', 'toggle') and ents != [PLAYER]:
            for e in ents:
                dev = {'obeys': True, 'delay_s': 2, **(self.truth.get(self.role(e)) or {})}
                if not dev['obeys']:
                    self.effects.append((now, 'ignored %s.%s %s' % (dom, svc, e)))
                    continue
                st = dict(self.states.get(e) or {'entity_id': e, 'attributes': {}})
                if svc == 'set_preset_mode':
                    st = {'entity_id': e, 'state': 'on', 'attributes': {**st.get('attributes', {}), 'preset_mode': data.get('preset_mode')}}
                else:
                    on = svc == 'turn_on' or (svc == 'toggle' and st.get('state') != 'on')
                    st = {'entity_id': e, 'state': 'on' if on else 'off', 'attributes': st.get('attributes', {})}
                out.append((now + float(dev['delay_s']), st))
        elif dom == 'media_player':   # her music player (MPD)
            e = ents[0] if ents else PLAYER
            if svc == 'play_media':
                out.append((now + 1, self._put(e, 'playing', {'media_content_id': data.get('media_content_id')})))
            elif svc in ('media_stop', 'media_pause'):
                out.append((now + 1, self._put(e, 'idle')))
            elif svc == 'volume_set':
                out.append((now + 0.5, self._put(e, self.states.get(e, {}).get('state', 'idle'), {'volume_level': data.get('volume_level')})))
        elif dom == 'todo':
            for e in ents:
                l = self.lists.setdefault(e, [])
                if svc == 'add_item':
                    l.append(data.get('item', ''))
                elif svc == 'remove_item':
                    items = data.get('item')
                    for it in (items if isinstance(items, list) else [items]):
                        if it in l:
                            l.remove(it)
                out.append((now + 0.5, self._put(e, str(len(l)))))
                changed = True
        elif dom == 'calendar' and svc == 'create_event':
            for e in ents:
                self.events.setdefault(e, []).append({'start': data.get('start_date_time'), 'end': data.get('end_date_time'),
                                                      'summary': data.get('summary', '')})
            changed = True
        self.effects.append((now, '%s.%s %s' % (dom, svc, ' '.join(ents))))
        return out, changed

    def apply(self, st):
        self.states[st['entity_id']] = st
