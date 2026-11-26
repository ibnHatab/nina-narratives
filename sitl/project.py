"""The families and edges a member reads, projected from the semantic world's State() (semworld-step's settle).

Merged from nina-live catalog/world/home_host.py at 702c428, without its second world. nina-live's host
re-estimated presence, temperature and power in Python. Here the semantic world is the only estimator: this
module turns its likeliest values (home.State) into the exclusive families of interfaces/world (one member true
per role, `unsensed`/`untracked` when the world does not know) and the one-beat edges. It keeps the
classification's own state, the vacant timer and the hysteresis, which the rules expect.

Projection membership and edge ownership come from interfaces/world/*.yaml.
"""


def hysteresis(prev, value, enter, leave, above):
    if value is None:
        return None
    if above:
        return value >= enter if not prev else value > leave
    return value <= enter if not prev else value < leave


class Projector:
    def __init__(self, world_map, families):
        self.families = families
        self.m = world_map
        self.th = world_map.get('thresholds') or {}
        self.empty_since = {}      # room -> world time it was first seen empty
        self.prev = {}

    def _th(self, name, default):
        return self.th.get(name) or default

    def project(self, state, now):
        """(families: atom -> bool, edges: [atom]) for this settle."""
        r, ev, prev = {}, [], self.prev
        lights = state.get('Lights') or {}
        for l, d in lights.items():
            r['light_lit(%s)' % l], r['light_dark(%s)' % l] = d['Lit'], not d['Lit']
            r['light_ok(%s)' % l], r['light_missing(%s)' % l] = d['OK'], not d['OK']
        vacant_s = self._th('vacant_after_s', [600])[0]
        presence = state.get('Presence') or {}
        for room in sorted(k for k in self.m['rooms'] if not k.startswith('_')):
            lit = any(d['Lit'] for l, d in lights.items() if self.m['lights'].get(l, {}).get('room') == room)
            r['room_lit(%s)' % room], r['room_unlit(%s)' % room] = lit, not lit
            p = presence.get(room, '')
            if p == 'empty':
                self.empty_since.setdefault(room, now)
            else:
                self.empty_since.pop(room, None)
            cls = ('unsensed' if not p else 'occupied' if p == 'occupied'
                   else 'vacant' if now - self.empty_since[room] >= vacant_s else 'empty')
            for c in ('occupied', 'empty', 'vacant', 'unsensed'):
                r['%s(%s)' % (c, room)] = c == cls
            if cls == 'occupied' and prev.get('cls_' + room) not in (None, 'occupied', 'unsensed'):
                ev.append('entered(%s)' % room)
            prev['cls_' + room] = cls
            clim = (state.get('Climate') or {}).get(room)
            t = clim['C'] if clim else None
            cold = hysteresis(prev.get('cold_' + room), t, *self._th('room_cold_c', [19, 20]), above=False)
            warm = hysteresis(prev.get('warm_' + room), t, *self._th('room_warm_c', [26, 25]), above=True)
            tcls = 'untracked' if t is None else 'cold_room' if cold else 'warm_room' if warm else 'comfy_room'
            for c in ('cold_room', 'comfy_room', 'warm_room', 'untracked'):
                r['%s(%s)' % (c, room)] = c == tcls
            for c, name, k in ((cold, 'got_cold', 'cold_'), (warm, 'got_warm', 'warm_')):
                if c and prev.get(k + room) is False:
                    ev.append('%s(%s)' % (name, room))
                prev[k + room] = c
            rh = clim.get('RH') if clim else None
            humid = hysteresis(prev.get('humid_' + room), rh, *self._th('humid_pct', [65, 60]), above=True)
            hcls = 'humidity_unknown' if rh is None else 'humid_room' if humid else 'fresh_room'
            for c in ('humid_room', 'fresh_room', 'humidity_unknown'):
                r['%s(%s)' % (c, room)] = c == hcls
            if humid and prev.get('humid_' + room) is False:
                ev.append('got_humid(%s)' % room)
            prev['humid_' + room] = humid
        sensed = [p for p in presence.values() if p]
        home = None if not sensed else any(p == 'occupied' for p in sensed)
        r['someone_home'], r['nobody_home'], r['home_unsensed'] = home is True, home is False, home is None
        if prev.get('home') is True and home is False:
            ev.append('left_home')
        if prev.get('home') is False and home is True:
            ev.append('came_home')
        prev['home'] = home
        sun = bool(state.get('SunUp'))
        r['day'], r['night'] = sun, not sun
        if sun and prev.get('sun') is False:
            ev.append('dawn')
        prev['sun'] = sun
        for u, d in (state.get('Units') or {}).items():
            for k, v in (('running', d['Running']), ('stopped', not d['Running']), ('heater_on', d['Heater']),
                         ('heater_off', not d['Heater']), ('winter_on', d['Winter']), ('winter_off', not d['Winter']),
                         ('unit_ok', d['OK']), ('unit_missing', not d['OK'])):
                r['%s(%s)' % (k, u)] = v
            for mode in ('normal', 'night', 'boost'):
                r['%s_mode(%s)' % (mode, u)] = (d.get('Preset') or 'normal') == mode
            out = d.get('Outside')
            cold = hysteresis(prev.get('out_' + u), out, *self._th('outside_cold_c', [8, 10]), above=False)
            ocls = 'out_unknown' if cold is None else 'cold_out' if cold else 'mild_out'
            for c in ('cold_out', 'mild_out', 'out_unknown'):
                r['%s(%s)' % (c, u)] = c == ocls
            if cold and prev.get('out_' + u) is False:
                ev.append('chilled(%s)' % u)
            prev['out_' + u] = cold
        for t, d in (state.get('TVs') or {}).items():
            r['tv_on(%s)' % t], r['tv_off(%s)' % t] = d['On'], not d['On']
            r['tv_ok(%s)' % t], r['tv_missing(%s)' % t] = d['OK'], not d['OK']
        ir = bool(state.get('IRReady'))
        r['ir_ready'], r['ir_absent'] = ir, not ir
        return r, ev

    def for_member(self, member, families, edges):
        reads = self.families.get(member, {}).get('reads', ())
        want = {a: v for a, v in families.items() if a.split('(')[0] in reads}
        evs = [e for e in edges if e.split('(')[0] in self.families.get(member, {}).get('events', ())]
        return want, evs
