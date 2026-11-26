"""A simulated person: the conversation contract's adapter on the person's side.

The person holds the hidden truth (what they intend, when they will be back, when the task is really done). They
perceive only what crosses the boundary: Nina's speech, the contract's `say` command. They answer with report events.
Neither Nina's ledger nor any member's state is visible to them (the confound of PR #3, removed).

Truth (the scenario's `truth.people.<name>`):
    hands:     [{task, at}]                      gives Nina something to keep (report arrived)
    on_first_hearing: {task: later}              the first time Nina raises the task, they defer it
    returns:   {task: s}                         s after deferring, they ask again (report renewed)
    done:      {task: at}                        they finish it themselves and say so (report done)
"""


class Person:
    def __init__(self, name, truth):
        self.name, self.t = name, truth or {}
        self.heard = []            # (at, task): what they actually heard
        self.deferred = {}         # task -> at they said later

    def scheduled(self):
        """The events the person causes regardless of Nina: handing over, finishing."""
        out = [{'at': h['at'], 'kind': 'report', 'person': self.name, 'id': h['task'], 'var': 'arrived', 'value': 'yes'}
               for h in self.t.get('hands') or []]
        out += [{'at': at, 'kind': 'report', 'person': self.name, 'id': task, 'var': 'done', 'value': 'yes'}
                for task, at in (self.t.get('done') or {}).items()]
        return out

    def hear(self, at, task):
        """Nina said something about TASK at AT: [(at, event)] the person's replies."""
        first = not any(t == task for _, t in self.heard)
        self.heard.append((at, task))
        reply = []
        if first and (self.t.get('on_first_hearing') or {}).get(task) == 'later':
            self.deferred[task] = at
            reply.append({'at': at, 'kind': 'report', 'person': self.name, 'id': task, 'var': 'deferral', 'value': 'later'})
            back = (self.t.get('returns') or {}).get(task)
            if back is not None:
                reply.append({'at': at + back, 'kind': 'report', 'person': self.name, 'id': task, 'var': 'renewed',
                              'value': 'yes'})
        return [(e['at'], e) for e in reply]

    def truth_at(self, task, at):
        """What the monitors may read: is the task done, is the person away (deferred and not yet back)."""
        done_at = (self.t.get('done') or {}).get(task)
        later_at = self.deferred.get(task)
        back = (self.t.get('returns') or {}).get(task)
        return {'done': done_at is not None and at >= done_at,
                'deferred': later_at is not None and (back is None or at < later_at + back)}
