# Ruling: accepted

**commitments**, postpone; the program unit METIS_HOME/commitments_domain.llp.

## What this record identifies: identified
- TARGET: yes. At tick 4 the candidate does something else than the record: tick 4: the record heard[T=call], postpone[T=call], offer[T=call], the candidate heard[T=call], postpone[T=call].
- SUPPORT: postpone[T=call] is enabled on this record from tick 4, beside nothing.
- SCOPE: the record is exact to the candidate's first differing output (tick 4); past it the ticks are of a world that obeyed the old program.

The judgement's time: the baseline's replay 0.8 s, the goldens as they are 0.1 s, the link, the candidate 0.0 s, the candidate's replay 0.6 s, the goldens on the candidate 0.1 s, the cases 0.0 s.

## The receipt
Programs moved: commitments, ei_key holds.

## The fired diff
- First enabled: tick 4, postpone[T=call], beside nothing.
- First fired difference: tick 4, commitments: the record ['heard[T=call]', 'postpone[T=call]', 'offer[T=call]'], the candidate ['heard[T=call]', 'postpone[T=call]'].
- First differing output: tick 4, commitments: the record ['reminder_offer(call)'], the candidate [].
- First difference per member: commitments at 4, home_director at 4, attention at 5.

## The cases
- case.yaml (commitments, tick 4): passes in the package's harness; passes on the composition.

## The goldens
8 cases (attention 1, commitments 2, curiosity 1, home_director 0, persona 1, self_model 1, situations 1, social 1), none broken, on seeds 1 to 3.

## Lint
no lint finding on the amended unit.

## The certificate
**Open-loop:** every tick of the trace to its first differing output (tick 4), and past it only as a world that obeyed the old command.
**Closed-loop:** not run. This ruling has no world.

## The model's words
(no model was asked: the verdict and the evidence above stand alone)

A person reviews this. Spend: 0.0000 USD.
