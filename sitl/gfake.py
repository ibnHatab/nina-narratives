"""Google's Calendar and Tasks APIs and Met.no's forecast as Nina's direct services call them (nina-live
services/google, services/weather), for real Nina in the loop with Home Assistant only through MCP (the user,
2026-11-28). The truth is the house's (sitl/house.py): a write here is reported into ha-sim's call record as the
Home Assistant service call it replaces (calendar.create_event, todo.add_item, todo.remove_item), so the house
and the metrics read it as before. The agenda's ids are the house's names (todo.shopping_list: a task list's id).
"""
import datetime as dt
import json
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from house import NAMES

MET = {'rainy': 'rain', 'cloudy': 'cloudy', 'sunny': 'clearsky_day', 'partlycloudy': 'partlycloudy_day', 'snowy': 'snow',
       'fog': 'fog', 'pouring': 'heavyrain'}


class GoogleFake:
    def __init__(self, house, ha):
        self.house, self.ha = house, ha
        fake = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, code, obj=None):
                b = json.dumps(obj if obj is not None else {}).encode()
                self.send_response(code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(b)))
                self.end_headers()
                self.wfile.write(b)

            def _body(self):
                n = int(self.headers.get('Content-Length') or 0)
                raw = self.rfile.read(n) if n else b''
                try:
                    return json.loads(raw or b'{}')
                except ValueError:
                    return dict(urllib.parse.parse_qsl(raw.decode()))

            def do_POST(self):
                fake.route(self, 'POST')

            def do_GET(self):
                fake.route(self, 'GET')

            def do_DELETE(self):
                fake.route(self, 'DELETE')

        self.srv = ThreadingHTTPServer(('127.0.0.1', 0), H)
        self.url = 'http://127.0.0.1:%d' % self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def close(self):
        self.srv.shutdown()

    def record(self, domain, service, data):
        """The write as the Home Assistant call it replaces: the loop's pump gives it to the house."""
        with self.ha.cv:
            self.ha.calls.append({'domain': domain, 'service': service, 'data': data, 'response': False,
                                  'at': time.time(), 'via': 'google'})
            self.ha.cv.notify_all()

    def route(self, h, method):
        u = urllib.parse.urlparse(h.path)
        p, q = urllib.parse.unquote(u.path), dict(urllib.parse.parse_qsl(u.query))
        parts = [x for x in p.split('/') if x]
        hs = self.house
        if p == '/token':
            h._body()
            return h._send(200, {'access_token': 'sitl', 'expires_in': 3600})
        if parts[:2] == ['calendar', 'calendars'] and len(parts) == 4 and parts[3] == 'events':
            cal = parts[2]
            if method == 'POST':
                b = h._body()
                s = (b.get('start') or {}).get('dateTime', '')
                e = (b.get('end') or {}).get('dateTime', '')
                self.record('calendar', 'create_event', {'entity_id': cal, 'summary': b.get('summary', ''),
                                                         'start_date_time': s, 'end_date_time': e})
                return h._send(200, {'id': 'e%d' % int(time.time() * 1000)})
            items = [{'summary': ev['summary'], 'start': {'dateTime': ev['start']}} for ev in hs.events.get(cal, [])]
            return h._send(200, {'items': sorted(items, key=lambda x: x['start']['dateTime'] or '')})
        if parts[:3] == ['tasks', 'users', '@me']:
            return h._send(200, {'items': [{'id': e, 'title': NAMES.get(e, e)} for e in hs.lists]})
        if parts[:2] == ['tasks', 'lists'] and len(parts) >= 4 and parts[3] == 'tasks':
            lid = parts[2]
            items = hs.lists.get(lid)
            if items is None:
                return h._send(404, {'error': {'message': 'no list ' + lid}})
            if method == 'POST':
                b = h._body()
                self.record('todo', 'add_item', {'entity_id': lid, 'item': b.get('title', '')})
                return h._send(200, {'id': 't'})
            if method == 'DELETE' and len(parts) == 5:
                i = int(parts[4][1:]) if parts[4][1:].isdigit() else -1
                if 0 <= i < len(items):
                    self.record('todo', 'remove_item', {'entity_id': lid, 'item': items[i]})
                    h.send_response(204)
                    h.end_headers()
                    return
                return h._send(404, {'error': {'message': 'no task'}})
            return h._send(200, {'items': [{'id': 't%d' % i, 'title': t, 'status': 'needsAction'} for i, t in enumerate(items)]})
        if p == '/metno':
            return h._send(200, self.metno())
        return h._send(404, {'error': {'message': 'not faked: ' + p}})

    def metno(self):
        w = self.house.weather
        start = dt.datetime.now().astimezone().replace(minute=0, second=0, microsecond=0)
        ts = []
        for i, (cond, lo, hi) in enumerate(w['days']):
            for hr in range(24):
                at = (start.replace(hour=0) + dt.timedelta(days=i, hours=hr))
                temp = lo + (hi - lo) * (1 - abs(hr - 14) / 14)
                sym = MET.get(w['now'] if i == 0 and abs(at.hour - start.hour) < 1 else cond, cond)
                ts.append({'time': at.astimezone(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                           'data': {'instant': {'details': {'air_temperature': round(temp, 1)}},
                                    'next_1_hours': {'summary': {'symbol_code': sym},
                                                     'details': {'precipitation_amount': 0.5 if 'rain' in sym else 0}}}})
        return {'properties': {'timeseries': ts}}
