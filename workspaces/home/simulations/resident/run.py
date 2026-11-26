"""Two Book I household probes over the linked image. Run from the home workspace."""
import argparse
import json
from pathlib import Path
from uuid import uuid4

import yaml
from metis.catalog.workspace import Workspace
from metis_agent.runtime.feed import RuntimeFeed
from metis_agent.service import Live
from metis_agent.trace import NoModel

HOME = Path(__file__).resolve().parents[2]


def run(card, seed, days, golden):
    workspace = Workspace(HOME)
    workspace.made()
    task = 'call' if card == 'later' else 'dinner'
    # The resident determines intent before Nina sees anything. Only the utterance
    # "later", a completion report, and the eventual invitation cross the boundary.
    return_at = 13 * (days - 1) + 9
    complete_at = 4 if card == 'completed' else None
    run_id = f'{card}-{seed}-{uuid4().hex[:10]}'
    directory = workspace.path('trace', run=run_id)
    directory.mkdir(parents=True)
    config = yaml.safe_load((HOME / 'domains/service.yaml').read_text())
    config['v3']['image'] = str(HOME / 'domains')
    config['domains']['seed'] = seed
    (directory / 'config.yaml').write_text(yaml.safe_dump(config))
    config['trace'] = dict(dir=str(directory), every=0, ring=0)
    live = Live(config, NoModel())
    live.handle_due = lambda *_: None  # This headless fixture has no conversational model.
    feed = RuntimeFeed(workspace, 'home-resident', domain='home')
    feed.start()
    heard = []
    findings = []
    expired_floor = False
    exposures = []
    said_later = None
    feed.run_started(run_id, 'traces/' + run_id, dict(card=card, seed=seed, days=days))

    def tell(member, pred):
        if not live.take(member, ['+' + pred + ' 1'], by='resident'):
            raise ValueError(f'{member} refused {pred}')

    try:
        with (directory / 'truth.jsonl').open('w') as truth:
            for k in range(13 * days):
                if expired_floor:
                    if not live.take('attention', ['-floor 1'], by='clock'):
                        raise RuntimeError('could not expire the previous opening')
                    expired_floor = False
                if k == 1:
                    tell('commitments', f'arrived({task})')
                if card == 'later' and heard and said_later is None:
                    tell('commitments', f'later({task})')
                    said_later = k
                if k == complete_at:
                    for member in ('commitments', 'attention'):
                        tell(member, f'completion_report({task})')
                if card == 'later' and k == return_at:
                    tell('commitments', f'renewed({task})')
                openings = (3, 7, 11) if card == 'later' else (7,)
                opening = k % 13 in openings
                if opening:
                    tell('attention', 'floor')
                complete = complete_at is not None and k >= complete_at
                truth_row = dict(k=k, things=[dict(id=task, role=task, **{'class': 'obligation', 'as': 'task'},
                    completed=complete, available=opening,
                    intended_return=return_at if card == 'later' else None)])
                truth.write(json.dumps(truth_row) + '\n')
                start = len(live.journal.recs)
                live.tick()
                events = []
                feed.tick(k)
                # Observe the speaker's emitted event, never the resident's view of Nina's queue.
                for entry in live.journal.recs[start:]:
                    if entry['kind'] != 'dlg-trace' or entry.get('domain') != 'attention':
                        continue
                    for event in entry.get('fired', []):
                        if event.get('kind') != 'exo':
                            events.append(event['event'])
                        if f'uttered({task})' not in (event.get('produce') or []):
                            continue
                        heard.append(k)
                        if complete:
                            member, decision = 'attention', complete_at
                            words = f'B01-C08-S02: {task} was reported complete before this utterance.'
                        elif said_later is not None and k < return_at:
                            member, decision = 'commitments', said_later
                            words = f'B01-C01-S03 / C06-S01: {task} was repeated before the requested return.'
                        else:
                            continue
                        findings.append(dict(decision=decision, heard=k, member=member))
                        feed.finding(dict(kind='violation', slug=f'{card}-{k}', member=member, k=decision,
                                          k0=decision, k1=k, words=words, heard_at=k))
                if opening:
                    expired_floor = not any(name.split('[')[0] in ('speak', 'mention') for name in events)
                    exposures.append(dict(tick=k, events=events))
        live.tracer.close()
        ids = feed.run_ended(run_id, 'done')
        if any(sid is None for sid in ids):
            raise RuntimeError('a finding could not be written')
        result = dict(card=card, seed=seed, days=days, image=live.image.hash, arrival=1,
                      completion=complete_at, censored=complete_at is None, later=said_later,
                      renewed=return_at if card == 'later' else None, heard=heard,
                      openings=exposures, findings=findings)
        if golden:
            golden.write_text(json.dumps(result, indent=2) + '\n')
        return dict(card=card, heard=heard, run=run_id, surprises=ids)
    finally:
        feed.stop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--card', choices=['later', 'completed'], required=True)
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--days', type=int, default=1)
    parser.add_argument('--golden', type=Path, help='write the deterministic public event summary')
    args = parser.parse_args()
    if args.days < 1:
        parser.error('days must be positive')
    print(json.dumps(run(args.card, args.seed, args.days, args.golden)))
