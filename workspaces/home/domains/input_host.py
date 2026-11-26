"""Input-only host following metis-catalog kitchen_pot/pass_host at 7eb6e7d.
The director relays and resident observations enter through the same tick host.
"""


class PassHost:
    def __init__(self):
        self.beat, self.due, self.script, self.last, self.queue = 0, (), {}, None, []

    def bind(self, reg):
        pass

    def tick(self, counts):
        self.beat += 1
        dos, self.queue = self.queue, []
        return dos

    def on_event(self, name, args):
        pass

    def observe(self, counts):
        return {}

    def reading(self):
        return {}

    def sync(self, counts):
        return []

    def pending(self):
        return False

    def world(self, lines):
        self.queue += [l.strip() for l in lines if l.strip()]

    def deliver(self, domain, goal, tokens):
        return ["+" + goal + " 1"]

    def instance(self, domain, goal, tokens):
        return False

    def snapshot(self):
        return {"beat": self.beat, "queue": list(self.queue)}

    def restore(self, snap):
        self.beat, self.queue = snap["beat"], list(snap.get("queue", ()))


def make(case=None):
    return PassHost()
