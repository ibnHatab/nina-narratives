# Book I formalization candidates

The eight chapter packages are executable, deliberately narrow mechanism sketches. They are proposals for review, not installed household rules. The shared `mechanisms/` package tests a smaller reusable account of situations and commitments across several chapters. Read the [evaluation](../../evaluation/book-01/REVIEW.md) before interpreting a passing simulation as success.

Source fiction: `narratives/book-01-small-universe-of-home.md` at `94e2c5829e6ebefa3bd41e35e513bba943dc8e12`. The coordination update at `2420894` adds the creative director's letter and Book II; it does not change Book I. Book II was deliberately left unread as possible independent evaluation material for the creative team. None of these cases is an independent holdout.

Each chapter has a real `domain.yaml`, compiled `chapter.llp`, source/scene annotations and `cases.json`. Scene IDs `B01-Cnn-Snn` are extraction IDs, anchored by exact quotations in that chapter's README; they do not edit the canonical text. A source quote licenses the question being modeled, not every implementation assumption. READMEs name those assumptions and omissions.

## Reproduce with installed Metis

Use the Python environment containing Metis; no new installation is required. From the repository root, for the maintainer's existing layout:

```sh
export METISC=../perotheia-packages/metis-lang/src/metisc
../perotheia-packages/.venv/bin/python scripts/evaluate_book01.py
```

This compiles all nine packages with the actual OCaml compiler, validates manifests, runs the `revise` gate for each new base without `accept`, records lint, samples the fixtures with metispy, and replays every recorded trace without the environment or an LLM. It makes no paid calls. `--chapter 1` selects a chapter; `--mechanisms-only` selects the shared model. Known counterexamples remain failures in the report and do not abort the evidence run; unexpected assertion failures or any replay divergence abort it. A successful exit therefore means the evidence run completed, not that every desired property holds.

To regenerate narration as well, source your trusted private environment and export its variables before adding `--narrate`. This makes one OpenRouter call per selected package (nine for the complete run). The public `.metis.toml` contains model settings only. Original model outputs are retained under `evaluation/book-01/*/authored-seed1/narration.json`; they are not edited into compatible prose. The API's `ok` field denotes a successful request, not an evaluation verdict. On a paid narration rerun, existing output and its material are archived under `narration-history/` before replacement, preserving negative results.

For an interactive run, use tmux as the metis-loop skill requires:

```sh
export NINA_CASE="$PWD/workspaces/home/scenarios/volume-01/book-01/ch01/cases.json"
export NINA_SCENARIO=authored
tmux new-session -s nina-ch01 ./scripts/open-metis.sh \
  --plugin "$PWD/scripts/simulated_inputs.py:make" \
  workspaces/home/scenarios/volume-01/book-01/ch01/chapter.llp
# REPL:
# run 128
# narrate
# log
```

`open-metis.sh` loads and exports the private OpenRouter environment without printing it. Override `METIS_BIN` or `METIS_OPENROUTER_ENV` for another installation. This interactive example uses the authored case's initial state embedded in the LLP. Alternative initial states are prepared by the evaluation runner; merely changing `NINA_SCENARIO` does not reset those initial states.

The fixture host emits inputs at quiescence and checks the preceding phase. Inputs are recorded as `[env]` rows; they are not sampled behavior. `snapshot`/`restore` covers fixture position and checks. There are no home APIs or actuator calls. Time labels are scenario order, not elapsed-time simulation. Each run has a 128-event cap; the runner fails if the fixture did not finish.

Raw Segments witnesses are portable, with repository-relative program references. For example:

```sh
../perotheia-packages/.venv/bin/python -m metis.trace replay \
  evaluation/book-01/ch01/authored-seed1/segments ch01 \
  workspaces/home/scenarios/volume-01/book-01/ch01/chapter.llp
```

See [home mapping](HOME-MAPPING.md) for the proposed integration boundaries. No composition, intent vocabulary, weights, deployed permissions, or host implementation has been changed. The `.metis/` workspace is generated and ignored; a fresh clone recreates it using either script.
