# Thirty days in Nina's household

This Book I package uses the catalog clock-world convention. A program declares a package-local plugin factory. At quiescence Metis calls its tick method, applies the returned input lines and samples enabled rules. The host supports snapshot and restore. The LLP includes the seven responsive-household rules from PR #2. [Upstream clock package](https://github.com/metis-lang-dev/metis-catalog/tree/7eb6e7d9382b43f38a2867f62577adb1d44bc936/domains/ports/port-proto)

Each simulated day has three speaking opportunities. At each, the resident responds to the last delivery or uses a quiet interval to cook. Evidence settles before the next opportunity, grant and receipt. Unfinished promises carry into tomorrow. A new call or dinner promise can occupy a slot only after the previous instance closes. The host tracks generations for outcome accounting. For this experiment it assumes one returning outing per morning and immediate speaker receipts. Delayed reports across recycled slots, cancellations and delivery failures would require richer identities and host behavior. The final day's last delivery can still await a reply at the horizon.

Run directly from the repository root with the installed CLI:

```sh
./scripts/open-metis.sh candidates/household-days
# In the REPL type: run 4000
```

For paired experiments use the Metis environment's Python:

```sh
../perotheia-packages/.venv/bin/python candidates/household-days/compare.py \
  --days 30 --seeds 4 --output .metis/household-days
```

The CLI host accepts NINA_SIM_DAYS, NINA_SIM_WORLD_SEED and NINA_SIM_QUIET_DAY (0 disables intervention). The runner sets these per arm. Each pair has the same initial state, sampler seed and resident seed. The counterfactual removes one morning opportunity on day 1, 15 or 30. The runner checks identical observation and delivery prefixes up to that intervention. Subsequent resident reports depend on what happened in each branch. Busy and unaided-cooking draws use an epoch/task address so different numbers of earlier draws cannot shift the resident's random stream. The policy sampler can diverge after different firings.

## Results

Four sampler seeds and two resident seeds give eight baseline histories and 24 intervention histories. Every pair differed in a delivery or resident response. Relative to its baseline, the counterfactual produced fewer repeated deliveries in 13 pairs, the same number in four and more in seven. Repeats count additional deliveries for the same task generation, including retries explicitly requested by the resident. They measure repetition, not annoyance.

For policy seed 1 and resident seed 1, silence on the first morning changed 81 deliveries to 77, repeated deliveries from 31 to 26, and reported completions from 49 to 51. Completed promises can create capacity for new promises on later days, so these totals include downstream changes in the task population. These are comparisons within an artificial resident policy. The 24 pairs reuse eight baselines and supply no population-level estimate of human preferences.

The compact evidence includes [all comparisons](../../evaluation/household-days/pairs.json) and [a paired witness](../../evaluation/household-days/example.json) with all host phases, reports, confirmed deliveries, instance numbers and ordered rule firings for both arms. The compiler accepted the include and the package manifest passed the loader. Regenerating the complete sweep in a fresh output directory produced byte-identical evidence. The existing candidate rules and the Book I baseline are inherited from PR #2.
