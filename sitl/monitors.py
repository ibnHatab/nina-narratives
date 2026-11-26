"""Scene monitors see observed acts and independent person truth. Times use scenario seconds."""


class Monitors:
    def __init__(self, specs, people):
        self.specs, self.people = specs or [], people
        self.reports, self.history = {}, []

    def report(self, ev, k):
        self.reports[(ev.get('person'), ev.get('var'), ev.get('value'), ev.get('id'))] = k

    @staticmethod
    def finding(m, start, end):
        return dict(kind='violation', slug=f"{m['id']}-{end}", member=m['member'], k=start,
                    k0=start, k1=end, words=f"{m['scene']}: {m['words']}", monitor=m['id'])

    @staticmethod
    def matches(act, spec):
        return (act['rule'] == spec['rule'] and
                all(act.get(key) == spec[key] for key in ('member', 'channel') if key in spec) and
                ('arg' not in spec or spec['arg'] in act['args']))

    def check(self, act):
        out = []
        k = act['k']
        for m in self.specs:
            if 'order' in m:
                order = m['order']
                if self.matches(act, order['second']) and not any(
                        self.matches(a, order['first']) for a in self.history):
                    out.append(self.finding(m, 0, k))
            if 'forbid' not in m or not self.matches(act, m['forbid']):
                continue
            f = m['forbid']
            task = f.get('arg') or next(iter(act['args']), None)
            after = f.get('after') or ({'var': 'done', 'value': 'yes'} if f.get('while') == 'done' else {})
            for who, person in self.people.items():
                if f.get('person', who) != who:
                    continue
                start = self.reports.get((who, after.get('var'), after.get('value'), task)) if after else 0
                if start is None or (f.get('while') and not person.truth_at(task, act['at']).get(f['while'])):
                    continue
                out.append(self.finding(m, start, k))
                break
        self.history.append(act)
        return out

    def finish(self, at, k, comparisons):
        out = []
        for m in self.specs:
            if 'require' in m:
                spec = m['require']
                if spec['by'] > at:
                    raise ValueError(f"deadline beyond scenario horizon: {m['id']}")
                if not any(self.matches(a, spec) and spec.get('from', 0) <= a['at'] <= spec['by']
                           for a in self.history):
                    out.append(self.finding(m, 0, k))
            if 'never_reads' in m:
                spec = m['never_reads']
                def visible(acts):
                    return [(a['k'], a['rule'], a['args'], a['channel']) for a in acts
                            if a['member'] == spec['member'] and a['channel'] == spec['channel']]
                if visible(self.history) != visible(comparisons[m['id']]):
                    out.append(self.finding(m, 0, k))
        return out
