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
(cd devices && $METISC build .)                                # the composition image
PY=../perotheia-packages/.venv/bin/python                      # metispy; metis-agent's py on PYTHONPATH
$PY sitl/contracts.py check --workspace devices --world-map workspaces/home/world/home.map.json
PYTHONPATH=../perotheia-packages/metis-agent/py $PY sitl/loop.py workspaces/home/scenarios/devices/b01-c02-ventilation.yaml
```

A run writes `sitl/runs/<scenario>-s<seed>/events.jsonl` (every world input and reply, every adapter call) and
`summary.json` (the fired command rules, the surprises, whether each `expect` was met, the world's final hash).

## Status

| part | state |
|---|---|
| `semworld-step` | **checked**: byte-identical output over repeated runs; with a settle it also returns `State()` |
| `contracts.py check` | **checked**: 7 contracts pass schema and compile; on `devices/` every belief port resolves to a contract and the world accepts every member |
| `nina_world/host.py`, `project.py`, `mcp_sim.py`, `loop.py` | **run**: the 11 device members merged from nina-live load with the generic host. `b01-c02-ventilation` fires `air_on` twice from the person's requests; the obeying unit is confirmed, the ignoring one gives the world surprise `u2.power`; two runs give byte-identical `events.jsonl` and `summary.json` |
| not yet | scenario monitors, edges from the contracts (today `project.py`'s tables), the cognition members on the world contracts, `--replay`, office: sitl/TASKS.md |
