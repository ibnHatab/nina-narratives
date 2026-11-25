"""Render saved evidence only. No environment or policy is rerun."""
import argparse
import json
from collections import defaultdict

from metis.loop import llm
from metis.loop.narrate import options

from experiment import OUT, save

EVENT = {
    'due': 'Nina marked the reminder ready',
    'select': 'Nina used the available interruption to queue the reminder',
    'commit': 'Nina committed to giving the reminder',
    'deliver': 'The simulated speaker confirmed delivery of the reminder',
    'postpone': 'Nina made the reminder eligible again',
    'close': 'Nina closed the promise on the available report',
}
SUBJECT = {'call_one': 'the first call', 'dinner': 'dinner', 'appointment': 'the appointment outing'}
SYSTEM = ('Render the supplied synthetic witness faithfully. Epochs order observations. Independent '
          'events need not be simultaneous. Attribute actions and reports separately. Consumed '
          'markers represent lifecycle transitions. Preserve uncertainty. Do not infer dialogue.')


def projection(trace):
    epochs = defaultdict(list)
    for phase in trace['phases']:
        lines = epochs[phase['epoch']]
        for obs in phase['evidence']:
            lines.append(f"{obs['source']} reported {obs['kind']} concerning {SUBJECT[obs['subject']]} "
                         f"(observation {obs['identity']}, occurrence epoch {obs['at']}).")
        for row in phase['fired']:
            if row['kind'] == 'clause':
                rule, args = row['name'].split('[', 1)
                task = args.split('=', 1)[1].rstrip(']').split(',')[0]
                lines.append(f"{EVENT[rule]} for {SUBJECT[task]}.")
        if phase['phase'] == 'delivery' and not phase['inputs']:
            lines.append('No reminder was delivered during this decision.')
    return {str(epoch): lines for epoch, lines in epochs.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', action='store_true')
    args = parser.parse_args()
    for seed in (1, 19):
        trace = json.loads((OUT / f'witness-{seed}.json').read_text())
        epochs = projection(trace)
        save(f'epochs-{seed}.json', epochs)
    if args.model:
        endpoint, _ = llm.seat('narrate')
        foata = json.loads((OUT / 'foata.json').read_text())['prompt']
        prompts = {'full': foata + '\nObservation chronology\n' + json.dumps(epochs)}
        prompts.update({f'epoch-{e}': json.dumps({e: lines}) for e, lines in epochs.items()})
        results = {}
        for name, prompt in prompts.items():
            try:
                results[name] = {'text': llm.complete(endpoint, prompt, system=SYSTEM,
                                                      options=options(), timeout=25)}
            except RuntimeError as exc:
                # Keep the network diagnostic, never response bodies or credentials.
                if 'openrouter not reachable:' not in str(exc):
                    raise
                results[name] = {'error': str(exc)}
        save('model-attempts.json', dict(endpoint=endpoint, results=results))


if __name__ == '__main__':
    main()
