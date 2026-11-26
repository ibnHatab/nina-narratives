"""nina_world.host: the SITL runtime's world host, the one host every member gets (interfaces/README.md).

A catalog member names `host: nina_world.host:<member>` and nothing of the runtime. Each runtime provides a
module of that name: this one is the SITL's, and nina-live provides its own. The host does no world reasoning.
The loop (sitl/loop.py) gives it, for each beat, the member's world lines (the semantic world's level do-lines,
the families projected from the world's state, the contract edges). The host hands them over on its next tick
and reports every fired rule back to the loop, which turns a contract's command into a command event and an
adapter call.

    nina_world.host.REGISTRY[member]   the member's host, once Live has built it
"""
REGISTRY = {}


class WorldHost:
    """The host protocol metis-agent's AgentHost wraps (bind/tick/sync/on_event/world/observe/reading/pending)."""

    def __init__(self, member, case=None):
        self.member, self.case, self.beat = member, case, 0
        self.want = {}             # atom -> bool: the families this member reads, as the world projects them now
        self.levels = []           # the semantic world's do-lines for this beat (Board.Lines: already +/- lines)
        self.edges = []            # one-beat facts for this beat
        self.retract = ()          # preds whose tokens a beat leaves and the next retracts (outcomes, edges)
        self.hold = {}             # role -> world time its grace ends: the program owns that belief until then
        self.owned = ()            # preds the program switches itself (read back only after the grace)
        self.fired = []            # (beat, rule, args) fired since the loop last drained them
        self.taken = []            # the composition's own lines (the director's forwards), for the next tick
        self.now = 0.0
        self.due, self.script, self.last = (), {}, None    # AgentHost's faces (a hosted script: none here)
        REGISTRY[member] = self

    # the loop's face
    def give(self, now, want, levels, edges):
        self.changed = dict(want) != self.want
        self.now, self.want, self.levels, self.edges = now, dict(want), list(levels), list(edges)

    def drain(self):
        fired, self.fired = self.fired, []
        return fired

    # the runtime's face
    def bind(self, reg):
        pass

    def _corrections(self, counts):
        dos = []
        for atom, want in sorted(self.want.items()):
            pred, _, args = atom.partition('(')
            role = args.rstrip(')').split(',')[0] if args else ''
            if pred in self.owned and self.hold.get(role, -1) >= self.now:
                continue
            have = counts.get(atom, 0)
            if want and not have:
                dos.append('+' + atom)
            elif not want and have:
                dos.append('-%s %d' % (atom, have))
        return dos

    def tick(self, counts):
        self.beat += 1
        dos = ['-%s %d' % (a, n) for a, n in sorted(counts.items())
               if n and a.split('(')[0] in self.retract]
        dos += self._corrections(counts)
        dos += self.levels + ['+' + e for e in self.edges] + self.taken
        self.levels, self.edges, self.taken, self.changed = [], [], [], False
        return dos

    def sync(self, counts):
        return self._corrections(counts)

    def on_event(self, name, args):
        self.fired.append((self.beat, name.split('[')[0].split('-')[0], tuple(args)))

    def world(self, lines):
        """The composition's own lines (Live.take: the director's forwards and relays), for the next tick. Not a door
        for the outside: the outside comes through the loop's give() from the world and the contracts."""
        self.taken += [l.strip() for l in lines if l.strip()]

    def observe(self, counts):
        return {}

    def reading(self):
        return {}

    def pending(self):
        """Input waiting for the next tick: a member without a clock period beats only then (spec 15 rule 1)."""
        return bool(self.edges or self.levels or self.taken or getattr(self, 'changed', False))

    # a director's faces (metis-agent Live: the director forwards a goal to a member)
    def deliver(self, domain, goal, tokens):
        return ['+' + goal + ' 1']

    def instance(self, domain, goal, tokens):
        return False

    def snapshot(self):
        return (self.beat, sorted(self.hold.items()))

    def restore(self, snap):
        self.beat, hold = snap
        self.hold = dict(hold)


def make(case=None):
    raise ValueError('name the member: host: nina_world.host:<member>')


def flips(atom):
    """A refusal's blocker's complement (the consult): the contracts' exclusive families, not yet wired."""
    return None


def words(atom, names=None):
    return None


def __getattr__(name):
    """nina_world.host:<member>: a factory for any member's name (lower case; the runtime's probes, ANSWERS,
    PAIRS, WAITS..., are not members)."""
    if name.startswith('_') or not name.islower():
        raise AttributeError(name)
    return lambda case=None: WorldHost(name, case)
