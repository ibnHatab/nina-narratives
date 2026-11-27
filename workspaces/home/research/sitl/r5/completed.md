# Ruling: accepted

**attention**, withdraw; the program unit METIS_HOME/attention_domain.llp.

## What this record identifies: identified
- TARGET: yes. At tick 4 the candidate does something else than the record: tick 4: the record nothing, the candidate withdraw[T=call].
- SUPPORT: withdraw[T=call] is enabled on this record from tick 4, beside nothing.
- SCOPE: the record is exact to the candidate's first differing output (tick 7); past it the ticks are of a world that obeyed the old program.

The judgement's time: the baseline's replay 0.8 s, the goldens as they are 0.1 s, the link, the candidate 0.0 s, the candidate's replay 0.6 s, the goldens on the candidate 0.1 s, the cases 0.0 s.

## The receipt
Programs moved: attention, ei_key holds.

## The fired diff
- First enabled: tick 4, withdraw[T=call], beside nothing.
- First fired difference: tick 4, attention: the record [], the candidate ['withdraw[T=call]'].
- First differing output: tick 7, attention: the record ['uttered(call)'], the candidate [].
- First difference per member: attention at 4, home_director at 5.

## The cases
- case.yaml (attention, tick 4): passes in the package's harness; passes on the composition.

## The goldens
8 cases (attention 1, commitments 2, curiosity 1, home_director 0, persona 1, self_model 1, situations 1, social 1), none broken, on seeds 1 to 3.

## Lint
no lint finding on the amended unit.

## The certificate
**Open-loop:** every tick of the trace to its first differing output (tick 7), and past it only as a world that obeyed the old command.
**Closed-loop:** not run. This ruling has no world.

## The model's words
(no model was asked: the verdict and the evidence above stand alone)

A person reviews this. Spend: 0.0000 USD.
