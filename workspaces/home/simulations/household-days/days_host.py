"""Synthetic household. One decision per simulated morning, afternoon and evening."""
import os
from hashlib import sha256


TASKS = ('call_one', 'dinner')


def setting(name, default):
    return int(os.environ.get('NINA_SIM_' + name, default))


class Days:
    def __init__(self, days, seed, quiet_day):
        if days < 1 or quiet_day not in range(days + 1):
            raise ValueError('need positive days and quiet day in 0..days')
        self.days, self.seed, self.quiet_day = days, seed, quiet_day
        self.tick_index = 0
        self.generation = dict.fromkeys(TASKS, 0)
        self.last_heard = None
        self.last_row = None

    def bind(self, registry):
        pass

    def on_event(self, name, args):
        pass

    def snapshot(self):
        return [self.tick_index, dict(self.generation), self.last_heard, self.last_row]

    def restore(self, snapshot):
        self.tick_index, generations, self.last_heard, self.last_row = snapshot
        self.generation = dict(generations)

    def draw(self, epoch, task, purpose):
        # Address randomness by exogenous epoch, independent of branch call count.
        key = f'{self.seed}/{epoch}/{task}/{purpose}'.encode()
        return int.from_bytes(sha256(key).digest()[:4], 'big')

    def tick(self, counts):
        epoch, phase = divmod(self.tick_index, 5)
        if epoch == self.days * 3:
            return None
        day, slot = divmod(epoch, 3)
        day += 1
        ops = []
        report = None
        heard = None
        def status(task, state):
            return counts.get(f'state({task},{state})', 0)
        if phase == 0:  # Respond to the previous delivery before considering a new one.
            task = self.last_heard
            if task:
                if self.draw(epoch, task, 'busy') % 3 == 0:
                    ops.append(f'+retry({task})')
                    report = ['later', task, self.generation[task]]
                else:
                    ops.append(f'+reconcile({task})')
                    report = ['done', task, self.generation[task]]
            elif epoch and status('dinner', 'ready') and self.draw(epoch, 'dinner', 'cook') % 2 == 0:
                ops.append('+reconcile(dinner)')
                report = ['done unaided', 'dinner', self.generation['dinner']]
            self.last_heard = None
            if slot == 0 and counts.get('returned(appointment)'):
                ops.append('-returned(appointment)')
        elif phase == 1 and slot == 0:
            # Unresolved tasks carry into tomorrow. Reuse a finite slot only
            # after closure; observations in this world never outlive that slot.
            for task in TASKS:
                if not self.generation[task] or status(task, 'closed'):
                    if self.generation[task]:
                        ops.append(f'-state({task},closed)')
                    else:
                        ops.append(f'+promise({task},appointment)')
                    self.generation[task] += 1
                    ops.append(f'+state({task},waiting)')
            ops.append('+returned(appointment)')
        elif phase == 2:
            if slot or day != self.quiet_day:
                ops.append('+attention')
        elif phase == 3:
            if counts.get('attention'):
                ops.append('-attention')
            if any(status(t, 'queued') for t in TASKS):
                ops.append('+authorize')
        elif phase == 4:
            committed = [t for t in TASKS if status(t, 'committed')]
            assert len(committed) <= 1
            if committed:
                task, = committed
                ops.append(f'+receipt({task})')
                self.last_heard = task
                heard = [task, self.generation[task]]
        self.last_row = dict(day=day, slot=slot, phase=phase, inputs=ops,
                              report=report, heard=heard)
        self.tick_index += 1
        return ops


def make(case):
    return Days(setting('DAYS', 30), setting('WORLD_SEED', 1), setting('QUIET_DAY', 0))
