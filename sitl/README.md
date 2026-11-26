# SITL: Nina in the loop

Software-in-the-loop simulation of one incarnation (home or office). It runs the **same composition, the same semantic world and the same world contracts** as the deployed Nina. Only the outside of the world contracts is simulated. See `interfaces/README.md` for the contracts.

```
 scenario.yaml ──► script events ─┐                                   ┌─► Out.Lines[m]  ─► Live.take(m, lines, by=world)
 (truth hidden)                   ├─► events.jsonl ─► semworld-step ──┼─► Out.Surprises ─► Workspace finding (kind given)
 adapters (sim) ─► receipts ──────┘    (one ordered log)  Apply/Hash  └─► edges (contract) ─► Live.take(m, edges, by=world)
       ▲                                                                                         │
       └──── command event (the world's prediction, written first) ◄── fired command rule ◄── Live.tick()
                                                                                                  │
                                    monitors (truth vs trace, scene-cited) ──► Workspace finding ◄┘
```

## The loop, one beat

1. **Script.** Emit the scenario's events due by world time `t`, in order: sensor states (`ha_state`), a person's words (`report`), strain, feed drops.
2. **Settle.** Send `{"at": t, "kind": "settle"}` to `semworld-step`. Its `Out` gives each member's level do-lines and wake, and the surprises the world raised.
3. **Edges.** Derive the one-beat edge facts each contract declares (`edges:`) from the events and level changes of this beat.
4. **Members.** For each member, `Live.take(member, lines + edges, by='world')`, then `Live.tick()` (the composition and its director, as `metis_agent.service.Live` runs them in deployment).
5. **Commands.** For each fired rule whose name is a contract `commands:` entry, write a `command` event, the world's prediction (`predicts`), **before** the adapter call. Its id becomes the correlation key.
6. **Adapters.** The simulated adapter (`mcp_sim.py`, bound by the contract's `adapter:`) applies the call to the hidden truth and schedules its receipt: an `ha_state` reading or a `report` with `ref` = the command id. It may delay it or drop it, as the scenario's truth says. A dropped receipt is not an error: the world raises its own surprise after `grace_s`.
7. **Monitors.** Each scenario monitor compares the hidden truth with what Nina did this beat. When the two diverge, it writes a finding with its scene citation.

Nothing enters a member except through step 4. Nothing leaves except through step 5. The hidden truth is read only by the adapters and the monitors, never by a member (the confound of PR #3).

## Determinism

- One ordered log, `runs/<run>/events.jsonl`: every script event, every world reply (`seq`, `hash`), every command and receipt, in order. Replaying it gives the same hashes, the same lines and the same surprises. The world never reads a clock, and every event carries `at`.
- Randomness in the simulated outside (a resident's reply, a device ignoring a command) is drawn from a generator **addressed by (scenario, seed, event id)**, never by draw order. A different number of earlier draws cannot shift a later one, so paired counterfactual runs share the outside until their histories diverge.
- The composition's own sampler seed is recorded in the run's `config.yaml`.

## Surprise producers

| producer | what it notices | kind (spec 20) |
|---|---|---|
| the semantic world | a command not confirmed within `grace_s`; a reading against the belief; strain | given by the world: probabilistic / evidential / world |
| the runtime | collisions, violations, broken rules, end of run | triage: `metis.trace kind` / MCP `trace_kind` |
| scenario monitors | the hidden truth disagrees with Nina's act (a repeat after "later", a report taken for an observation) | triage |
| a person | a marked window in the page or the REPL | confusion / triage |

All four write through `Workspace` (`RuntimeFeed.finding` / `drop_window`) under the key `<run>:<kind>:<k>` (SURPRISE-INTERFACE.md §5–§6). They then go through the metis-loop cycle: surprise → case → pack → gates → ruling (metis-loop docs/WORKSPACE.md §4). A run that produces no surprise when its scenario includes a failure is a broken producer, not a clean run.

## Scenario format

```yaml
scenario: b01-c02-ventilation-override      # cite the scene: B01-C02-S03
incarnation: home
world_map: ../world/home.map.json
seed: 7
horizon_s: 7200
beat_s: 60
truth:                                       # hidden: adapters and monitors only
  devices: {u1: {obeys: true, delay_s: 4}, u2: {obeys: false}}     # u2 ignores commands: a manual override
  residents: {host: {deferral: {later: {return_after_s: 1800}}}}
script:                                      # timed outside events, contract vocabulary only
  - {at: 0,   ha_state: {entity_id: fan.u1_supply, state: "off"}}
  - {at: 600, report: {person: host, id: call_one, var: deferral, value: later}}
monitors:
  - {id: no-repeat-before-return, scene: B01-C01-S03, when: "uttered(T) before truth.return_after_s since later(T)"}
expect:                                      # the run is invalid unless these surprises are produced
  - {producer: world, key: u2.power}
```

## Running

```sh
(cd sitl/semworld-step && go build -o semworld-step .)        # the world fold, pinned to nina-live's version
(cd workspaces/home/domains && METIS_HOME=$PWD/../../../cognition $METISC build .)   # cognition image
(cd devices && $METISC build .)                                # device image
sitl/run.sh workspaces/home/scenarios/cognition/b01-later.yaml # one scenario (metis-agent's python, CUDA libs)
python3 sitl/regress.py                                        # every scenario against sitl/baseline.json
python3 sitl/regress.py --update                               # record a reviewed change as the new baseline
```

A run writes `sitl/runs/<scenario>-s<seed>/events.jsonl` (every world input and reply, every edge, every fired rule,
every adapter call) and `summary.json`. Its findings are surprise records in the workspace (`<workspace>/.metis/surprises`)
with the trace window and the hidden truth per beat (`truth.jsonl`), so `python -m metis.trace kind RECORD` triages them.

**Regressions.** `sitl/baseline.json` holds each scenario's essence (command rules fired, findings, expectations, world
hash). `regress.py` reports NEW findings (surprises to triage), GONE ones (fixed, or a lost producer), CHANGED acts.
A scenario's `expect` states the narrative's norm; a finding against it is a real surprise, kept in the baseline
until a reviewed rule change removes it.

## Status (baseline 2026-11-26)

| scenario | top-down rules | result | triage |
|---|---|---|---|
| `cognition/b01-later` | commitments + attention (Book I) | Nina raises the call again at k=7 after "later", before the person's own return → `no-repeat-before-return` (B01-C01-S03 / C06-S01) | structural: a pack |
| `cognition/b01-completed` | commitments + attention | the person reports it done at k=4; commitments close the ledger but attention still holds the queued reminder and speaks at k=7 → `no-reminder-after-done` (B01-C08-S02) | structural: a pack (a cross-member gap) |
| `devices/b01-c02-ventilation` | devices (merged, alignment only) | the ignoring unit → the world's own surprise `u2.power` | world (probabilistic) |

The generic host (`nina_world/host.py`) serves both compositions unchanged; the person (`person_sim.py`) perceives only
Nina's `say` and answers with reports; the monitors read the truth, no member does. Reruns are byte-identical.
Not yet: monitors beyond `forbid`, contract-driven families (`project.py`'s tables), `--replay`, office.
