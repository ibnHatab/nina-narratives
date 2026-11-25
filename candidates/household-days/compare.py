"""Paired code runs. No household I/O, model calls or calibrated weights."""
import argparse
import io
import json
import os
from pathlib import Path
from metis.lang.repl import Repl

HERE = Path(__file__).resolve().parent


def run(days, seed, world, silence):
    os.environ.update(NINA_SIM_DAYS=str(days), NINA_SIM_WORLD_SEED=str(world),
                      NINA_SIM_QUIET_DAY=str(silence))
    shell = Repl(HERE / 'days.llp', terminal=True, seed=seed, stdout=io.StringIO())
    rows = []
    for _ in range(days * 100 + 100):
        result = shell.run_steps(1)
        if shell.plugin.tick_index > len(rows):
            rows.append(shell.plugin.last_row)
        if result["done"]:
            break
    else:
        raise RuntimeError("simulation exceeded its firing budget")
    assert len(rows) == days * 15 and shell.plugin.tick_index == len(rows)
    firings = [r[2].name for r in shell.fired_rows if r[0] == "clause"]
    return rows, firings


def metrics(rows):
    spoken = [tuple(r['heard']) for r in rows if r['heard']]
    return dict(deliveries=len(spoken), repeats=len(spoken) - len(set(spoken)),
                completed=sum(bool(r['report'] and r['report'][0].startswith('done')) for r in rows))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--days', type=int, default=30)
    ap.add_argument('--seeds', type=int, default=4)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.days < 1 or args.seeds < 1:
        ap.error('days and seeds must be positive')
    args.output.mkdir(parents=True, exist_ok=True)
    summary = []
    example = False
    for seed in range(1, args.seeds + 1):
        for world in (1, 7):
            baseline, base_firings = run(args.days, seed, world, 0)
            for day in sorted({1, (args.days + 1)//2, args.days}):
                alternate, alt_firings = run(args.days, seed, world, day)
                cut = (day - 1) * 15 + 2
                assert baseline[:cut] == alternate[:cut]
                assert baseline[cut]['inputs'] == ['+attention'] and alternate[cut]['inputs'] == []
                facts = metrics(baseline)
                alt = metrics(alternate)
                different = [i for i,(x,y) in enumerate(zip(baseline, alternate))
                             if (x['heard'], x['report']) != (y['heard'], y['report'])]
                summary.append(dict(policy_seed=seed, world_seed=world, quiet_day=day,
                                    days=args.days, baseline=facts, alternate=alt,
                                    differing_response_or_delivery_ticks=len(different)))
                if different and not example:
                    example = True
                    path = args.output / 'example.json'
                    path.write_text(json.dumps(dict(pair=summary[-1], baseline=baseline, alternate=alternate,
                                               baseline_rules=base_firings, alternate_rules=alt_firings),
                                               separators=(',', ':'))+'\n')
    (args.output / 'pairs.json').write_text(json.dumps(summary, indent=2)+'\n')


if __name__ == '__main__':
    main()
