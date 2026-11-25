"""Synthetic resident, observation adapter and offline Metis experiment."""
import argparse
import copy
from dataclasses import asdict, dataclass
import io
import json
from pathlib import Path
import random
import subprocess
import tempfile

from metis.catalog.manifests import check_manifest
from metis.lang.repl import Repl
from metis.loop.wire import dispatch
from metis.session_trace import SessionTrace
from metis.trace import replay, restore_session, session_state
from semantic_world.ports import sync_diff

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = HERE / 'household.llp'
OUT = ROOT / 'evaluation/responsive-household'
TASKS = ('call_one', 'dinner')


def save(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


@dataclass(frozen=True)
class Observation:
    identity: str
    at: int
    source: str
    kind: str
    subject: str


def project(history):
    """Fold one incarnation's journal. Each decision uses only its delivered prefix."""
    seen = {}
    trips = set()
    cancelled = set()
    reports = {}
    for obs in history:
        if obs.identity in seen:
            if seen[obs.identity] != obs:
                raise ValueError('identity reused with different payload')
            continue
        seen[obs.identity] = obs
        if obs.kind == 'cancel':
            cancelled.add(obs.subject)
        if obs.kind == 'return' and obs.at >= 1 and obs.subject not in cancelled:
            trips.add(obs.subject)
        if obs.kind in ('done', 'pending'):
            reports.setdefault(obs.subject, {})[obs.source] = obs.kind
        if obs.kind == 'confirm' and obs.source == 'resident':
            reports[obs.subject] = {'resident': 'done'}
    beliefs = {}
    for task, claims in reports.items():
        if len(set(claims.values())) > 1:
            beliefs[task] = 'question'
        elif claims.get('resident') == 'pending':
            beliefs[task] = 'question'
        elif claims.get('resident') == 'done':
            beliefs[task] = 'reconcile'
    return trips, beliefs


class Resident:
    def __init__(self, seed):
        self.busy = random.Random(seed).choice(TASKS)
        self.deferred = False
        self.completed = set()

    def respond(self, heard, epoch):
        if heard is None:
            if 'dinner' in self.completed:
                return []
            task = 'dinner'  # With a quiet interval the resident finishes dinner unaided.
        elif heard == self.busy and not self.deferred:
            self.deferred = True
            return [Observation(f'reply-{epoch}', epoch, 'resident', 'later', heard)]
        else:
            task = heard
        self.completed.add(task)
        return [Observation(f'reply-{epoch}', epoch, 'resident', 'done', task)]


class InputBatch:
    """Supply a single atomic input at quiescence and let policy rules settle."""
    pending = None

    def tick(self, counts):
        batch, self.pending = self.pending, None
        return batch

    def on_event(self, name, args):
        pass

    def snapshot(self):
        return self.pending

    def restore(self, value):
        self.pending = copy.deepcopy(value)


class Trial:
    def __init__(self, seed, trace):
        self.shell = Repl(SOURCE, seed=seed, stdout=io.StringIO())
        self.shell.plugin = InputBatch()
        self.recorder = SessionTrace(trace, self.shell, 'household', program=SOURCE)
        self.history = []
        self.phases = []

    def phase(self, epoch, phase, changes, observations=()):
        self.shell.plugin.pending = changes
        self.recorder.before(self.shell)
        result = dispatch(self.shell, 'run', '64')
        self.recorder.after(self.shell, 'run 64')
        assert result['ok'] and len(result['fired']) < 64, result
        self.phases.append(dict(epoch=epoch, phase=phase, inputs=changes,
                                evidence=[asdict(o) for o in observations],
                                fired=result['fired'], after=dict(self.shell.counts)))

    def observe(self, epoch, events):
        _, before = project(self.history)
        unique = {o.identity for o in self.history}
        changes = []
        for o in events:
            if o.kind == 'later' and o.identity not in unique:
                changes.append(f'+retry({o.subject})')
            unique.add(o.identity)
        self.history.extend(events)
        trips, beliefs = project(self.history)
        reading = {f'returned({trip})': 1 for trip in trips}
        changes.extend(sync_diff(reading, self.shell.counts, {'returned'}))
        for task, verdict in sorted(beliefs.items()):
            if before.get(task) != verdict:
                changes.append(f'+{verdict}({task})')
        self.phase(epoch, 'observe', changes, events)
        self.phases[-1]['hypotheses'] = {
            task: ['completion report may refer to another instance', 'checklist may lag']
            for task, verdict in beliefs.items() if verdict == 'question'
        }

    def task_in(self, status):
        return [t for t in TASKS if self.shell.counts.get(f'state({t},{status})')]

    def decide(self, epoch, correct_queue=False, available=True):
        self.phase(epoch, 'deliberate', ['+attention'] if available else [])
        events = []
        if correct_queue:
            selected, = self.task_in('queued')
            events.append(Observation('last-minute', epoch, 'resident', 'done', selected))
        self.observe(epoch, events)
        changes = ['-attention'] if self.shell.counts.get('attention') else []
        if self.task_in('queued'):
            changes.append('+authorize')
        self.phase(epoch, 'commit', changes)
        commands = self.task_in('committed')
        assert len(commands) <= 1
        self.phase(epoch, 'delivery', [f'+receipt({t})' for t in commands])
        return next(iter(commands), None)


RETURN = Observation('return-1', 1, 'door_adapter', 'return', 'appointment')
DONE = Observation('completion-1', 1, 'resident', 'done', 'call_one')
PENDING = Observation('checklist-1', 1, 'checklist', 'pending', 'call_one')


def run(case, seed, world_seed):
    with tempfile.TemporaryDirectory() as temp:
        trace = Path(temp)
        trial = Trial(seed, trace)
        person = Resident(world_seed)
        inputs = [RETURN]
        if case == 'repeat':
            trial.phase(0, 'second instance', ['+promise(call_two,errand)', '+state(call_two,waiting)'])
        if case == 'restart_gap':
            inputs = []
        elif case == 'old':
            inputs = [Observation('past', 0, 'door_adapter', 'return', 'appointment')]
        elif case == 'unrelated':
            inputs = [Observation('other', 1, 'door_adapter', 'return', 'errand')]
        elif case == 'cancelled':
            inputs.insert(0, Observation('cancel', 0, 'resident', 'cancel', 'appointment'))
        elif case == 'repeat':
            inputs.append(Observation('other-task', 1, 'resident', 'done', 'call_two'))
        elif case in ('early', 'conflict', 'reverse', 'duplicate', 'revision'):
            inputs += {'revision': [DONE], 'early': [DONE], 'conflict': [DONE, PENDING],
                       'reverse': [PENDING, DONE], 'duplicate': [RETURN, DONE, DONE]}[case]
        trial.observe(1, inputs)
        if case in ('restart', 'restart_gap'):
            checkpoint = json.loads(json.dumps(session_state(trial.shell)))
            trial.shell = Repl(SOURCE, seed=seed, stdout=io.StringIO())
            restore_session(trial.shell, checkpoint)
            trial.shell.plugin = InputBatch()
            # Simulate reloading the durable prefix and redelivering its last envelope.
            trial.history = [Observation(**o) for o in json.loads(json.dumps(
                [asdict(o) for o in trial.history]))]
            trial.observe(1, inputs[-1:])
            assert trial.phases[-1]['inputs'] == []
        spoken = [trial.decide(1, correct_queue=case == 'queued', available=case != 'quiet')]
        if case == 'queued':
            assert spoken == [None] and len(trial.task_in('closed')) == 1
        if case in ('responsive', 'quiet'):
            for epoch in (2, 3, 4):
                trial.observe(epoch, person.respond(spoken[-1], epoch))
                spoken.append(trial.decide(epoch))
            trial.observe(5, person.respond(spoken[-1], 5))
        if case in ('responsive', 'quiet'):
            assert set(trial.task_in('closed')) == set(TASKS)
        if case == 'quiet':
            assert spoken[0] is None and 'dinner' not in spoken
        if case == 'repeat':
            assert trial.shell.counts.get('state(call_two,closed)')
        if case == 'revision':
            assert 'call_one' in trial.task_in('closed')
            trial.observe(2, [PENDING])
            assert 'call_one' in trial.task_in('disputed')
        if case in ('conflict', 'reverse', 'revision'):
            assert trial.task_in('disputed') == ['call_one']
            trial.observe(3, [Observation('clarification', 3, 'resident', 'confirm', 'call_one')])
            assert 'call_one' in trial.task_in('closed')
        if case == 'late':
            task = spoken[0]
            trial.observe(2, [Observation('late-report', 1, 'resident', 'done', task)])
            assert task in trial.task_in('closed')
        if case in ('early', 'conflict', 'reverse', 'duplicate'):
            assert spoken == ['dinner']
        if case in ('old', 'unrelated', 'cancelled', 'restart_gap'):
            assert spoken == [None] and len(trial.task_in('waiting')) == 2
        if case in ('repeat', 'restart'):
            assert spoken[0] and len(trial.task_in('ready')) == 1
        trial.recorder.close()
        replayed = asdict(replay(trace, 'household', SOURCE))
        assert not replayed['divergence'], replayed
        if case == 'responsive' and seed == 19 and world_seed == 1:
            save('foata.json', dispatch(trial.shell, 'narrate', 'user'))
        return dict(case=case, seed=seed, world_seed=world_seed, key=trial.shell.key,
                    spoken=spoken, latent_busy_task=person.busy,
                    replay=replayed, phases=trial.phases)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--metisc', type=Path, required=True)
    args = parser.parse_args()
    check_manifest(HERE / 'domain.yaml', root=ROOT)
    subprocess.run([args.metisc, SOURCE], check=True)
    with tempfile.TemporaryDirectory() as temp:
        blank = Path(temp) / 'base.llp'
        blank.write_text('catalog empty 1.\nlayers (story).\nstages (live).\nstage live {}\n')
        shell = Repl(blank, stdout=io.StringIO())
        dispatch(shell, 'text', 'Scoped reminders share one optional interruption. Reconcile before speech.')
        dispatch(shell, 'llp', SOURCE.read_text())
        dispatch(shell, 'init', 'promise(call_one,appointment),state(call_one,waiting),returned(appointment),attention')
        gate = dispatch(shell, 'revise', '')
        save('gate.json', gate)
        assert gate['ok'], gate
    summary = []
    for case in ('responsive', 'quiet', 'old', 'unrelated', 'cancelled', 'repeat', 'restart',
                 'restart_gap', 'revision', 'early', 'duplicate', 'queued', 'late', 'conflict', 'reverse'):
        for seed in (1, 7, 19):
            for world_seed in ((1, 7) if case == 'responsive' else (1,)):
                witness = run(case, seed, world_seed)
                if case == 'responsive' and seed in (1, 19) and world_seed == 1:
                    save(f'witness-{seed}.json', witness)
                immediate_retry = any(first is not None and first == second
                                      for first, second in zip(witness['spoken'], witness['spoken'][1:]))
                summary.append(dict(case=case, policy_seed=seed, resident_seed=world_seed,
                                    spoken=witness['spoken'], consecutive_repeat=immediate_retry,
                                    replay_divergence=witness['replay']['divergence']))
    save('runs.json', summary)


if __name__ == '__main__':
    main()
