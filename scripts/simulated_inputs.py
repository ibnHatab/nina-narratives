"""Fiction-only Metis port plugin: explicit ordered inputs, never home I/O.

Set NINA_CASE to cases.json and NINA_SCENARIO to its case name. Each tick
checks the previous phase at quiescence before supplying the next phase.
This is an open-loop fixture, not a responsive household world.
"""
import copy
import json
import os
from pathlib import Path


class SimulatedInputs:
    name = 'book-01-fiction-fixture'

    def __init__(self, fixture):
        self.fixture = fixture
        self.index = 0
        self.checks = []

    def bind(self, registry):
        pass  # No probabilities inferred from prose; no fitted bindings.

    def on_event(self, name, args):
        pass  # Never actuate anything, including network or household devices.

    def tick(self, counts):
        phases = self.fixture['phases']
        if self.index:
            phase = phases[self.index - 1]
            missing = [a for a in phase['present'] if counts.get(a, 0) < 1]
            forbidden = [a for a in phase['absent'] if counts.get(a, 0) > 0]
            self.checks.append(dict(phase=phase['label'], counts=dict(counts),
                                    missing=missing, forbidden=forbidden,
                                    ok=not missing and not forbidden))
        if self.index >= len(phases):
            return None
        phase = phases[self.index]
        self.index += 1
        return ['+' + atom for atom in phase['inputs']]

    def snapshot(self):
        return copy.deepcopy(dict(index=self.index, checks=self.checks))

    def restore(self, snapshot):
        self.index = snapshot['index']
        self.checks = copy.deepcopy(snapshot['checks'])


def make(case):
    fixtures = json.loads(Path(os.environ['NINA_CASE']).read_text())
    name = os.environ.get('NINA_SCENARIO', 'authored')
    return SimulatedInputs(next(c for c in fixtures['cases'] if c['name'] == name))
