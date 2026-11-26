#!/usr/bin/env python3
"""Compile, gate, simulate, replay and optionally REPL-narrate Book I.

Run with the Metis environment's Python. --narrate makes eight paid calls
through the project's configured REPL endpoint; no API keys are written.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from metis.catalog.workspace import workspace
from metis.catalog.manifests import check_manifest
from metis.lang.repl import Repl
from metis.loop.wire import dispatch
from metis.session_trace import SessionTrace
from metis.trace import replay


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str) + '\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--narrate', action='store_true')
    ap.add_argument('--chapter', type=int)
    ap.add_argument('--mechanisms-only', action='store_true')
    ap.add_argument('--metisc', default=os.environ.get('METISC') or shutil.which('metisc'))
    args = ap.parse_args()
    if not args.metisc:
        ap.error('set METISC or pass --metisc pointing to the actual compiler')
    os.chdir(ROOT)
    workspace(ROOT).made()
    output = ROOT / 'evaluation/book-01'
    summary = []
    for directory in sorted((ROOT / 'candidates/book-01').glob('*')):
        if not directory.is_dir():
            continue
        if args.mechanisms_only and directory.name != 'mechanisms':
            continue
        if args.chapter and directory.name != f'ch{args.chapter:02d}':
            continue
        source = directory / 'chapter.llp'
        fixtures = json.loads((directory / 'cases.json').read_text())
        chapter_output = output / directory.name
        chapter_output.mkdir(parents=True, exist_ok=True)
        compilation = subprocess.run([args.metisc, str(source)], capture_output=True, text=True)
        write_json(chapter_output / 'compiler.json', dict(returncode=compilation.returncode,
                   stdout=compilation.stdout, stderr=compilation.stderr,
                   sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
        if compilation.returncode:
            raise RuntimeError(compilation.stdout + compilation.stderr)
        check_manifest(directory / 'domain.yaml', root=ROOT)
        # New standalone bases: revise runs the harness; accept is never called.
        blank = ROOT / '.metis/empty.llp'
        blank.write_text('catalog empty 1.\nlayers (story).\nstages (live).\nstage live {}\n')
        gate_shell = Repl(blank, stdout=io.StringIO())
        dispatch(gate_shell, 'text', directory.joinpath('README.md').read_text())
        dispatch(gate_shell, 'llp', source.read_text())
        first_case = fixtures['cases'][0]
        gate_initial = first_case['initial'] + first_case['phases'][0]['inputs']
        dispatch(gate_shell, 'init', ','.join(gate_initial))
        dispatch(gate_shell, 'steps', '16')
        gate = dispatch(gate_shell, 'revise', '')
        write_json(chapter_output / 'gate.json', gate)
        if not gate.get('ok'):
            raise RuntimeError(f'{directory.name} gate refused: {gate}')
        lint = subprocess.run([sys.executable, '-m', 'metis.lint', str(source),
                               '--manifest', str(directory / 'domain.yaml')], capture_output=True, text=True)
        (chapter_output / 'lint.txt').write_text(lint.stdout + lint.stderr)
        if lint.returncode:
            raise RuntimeError('lint could not run: ' + lint.stderr)
        for case in fixtures['cases']:
            for seed in fixtures['seeds']:
                name = f'{case["name"]}-seed{seed}'
                run_dir = chapter_output / name
                run_dir.mkdir(parents=True, exist_ok=True)
                scratch = ROOT / '.metis/scenarios' / directory.name / (name + '.llp')
                scratch.parent.mkdir(parents=True, exist_ok=True)
                text = '\n'.join(l for l in source.read_text().splitlines() if not l.startswith('#init'))
                scratch.write_text(text + '\n' + ''.join(f'#init {a} 1\n' for a in case['initial']))
                os.environ['NINA_CASE'] = str(directory / 'cases.json')
                os.environ['NINA_SCENARIO'] = case['name']
                shell = Repl(scratch, seed=seed, terminal=True,
                             plugin=str(ROOT / 'scripts/simulated_inputs.py') + ':make', stdout=io.StringIO())
                trace_dir = ROOT / '.metis/traces/book01' / directory.name / name
                if trace_dir.exists():
                    shutil.rmtree(trace_dir)
                recorder = SessionTrace(trace_dir, shell, directory.name, program=source)
                recorder.before(shell)
                result = dispatch(shell, 'run', '128')
                recorder.after(shell, 'run 128')
                recorder.close()
                checks = shell.plugin.checks
                complete = len(checks) == len(case['phases']) and shell.plugin.index == len(case['phases'])
                passed = result.get('ok') and complete and all(c['ok'] for c in checks)
                from dataclasses import asdict
                replay_result = asdict(replay(trace_dir, directory.name, source))
                if replay_result.get('divergence'):
                    passed = False
                write_json(run_dir / 'replay.json', replay_result)
                # Raw Segments witness, with portable program paths and no private logs.
                target = run_dir / 'segments'
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(trace_dir, target)
                for p in target.rglob('*.json'):
                    p.write_text(p.read_text().replace(str(ROOT) + '/', ''))
                for p in target.rglob('*.jsonl'):
                    p.write_text(p.read_text().replace(str(ROOT) + '/', ''))
                if case['name'] == 'competing-reminders':
                    counts = shell.counts
                    notified = sum(counts.get(f'notified({t})', 0) for t in ('call', 'secondary_call'))
                    ready = sum(counts.get(f'ready({t})', 0) for t in ('call', 'secondary_call'))
                    if (notified, ready, counts.get('interruption_budget', 0)) != (1, 1, 0):
                        passed = False
                write_json(run_dir / 'trace.json', dict(source_revision=fixtures['source_revision'],
                           program=str(source.relative_to(ROOT)), key=shell.key, seed=seed,
                           case=case['name'], initial=case['initial'], inputs=case['phases'],
                           result=result, checks=checks, complete=complete, passed=bool(passed)))
                if case['name'] == 'authored' and seed == 1:
                    existing = run_dir / 'narration.json'
                    if args.narrate and existing.exists():
                        digest = hashlib.sha256(existing.read_bytes()).hexdigest()[:16]
                        archive = run_dir / 'narration-history' / digest
                        archive.mkdir(parents=True, exist_ok=True)
                        for old in ('narration.json', 'narration-material.json'):
                            if (run_dir / old).exists():
                                shutil.copy2(run_dir / old, archive / old)
                    prompt = dispatch(shell, 'narrate', 'user')
                    write_json(run_dir / 'narration-material.json', prompt)
                    if args.narrate:
                        narration = dispatch(shell, 'narrate', '')
                        narration.update(trace_seed=seed, program_key=shell.key,
                            assessment='See evaluation/book-01/REVIEW.md; ok means API success, not semantic acceptance.')
                        write_json(run_dir / 'narration.json', narration)
                        if not narration.get('ok'):
                            raise RuntimeError(f'narration failed: {narration}')
                summary.append(dict(chapter=directory.name, case=case['name'], seed=seed,
                                    passed=bool(passed), known_limitation=case.get('known_limitation'), replay=replay_result))
                print(f'{directory.name} {name}: {"PASS" if passed else "FAIL"}', flush=True)
                if replay_result.get('divergence') or not complete or (not passed and not case.get('known_limitation')):
                    raise RuntimeError(f'phase assertion failed: {checks}')
        # Corpus artifacts contain only synthetic fixtures; no household data is read.
    write_json(output / ('summary-mechanisms.json' if args.mechanisms_only else 'summary.json' if not args.chapter else f'summary-ch{args.chapter:02d}.json'), summary)


if __name__ == '__main__':
    main()
