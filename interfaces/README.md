# Nina's interfaces

Nina is a composition of Metis members under a director per incarnation (home, office). Every predicate that crosses a member boundary is declared in exactly one interface package here. There are **two kinds** of crossing, and the two never share a package.

| | kind 1: member interfaces | kind 2: world contracts |
|---|---|---|
| between | member ↔ member, through the director | the composition ↔ the outside world |
| folder | `interfaces/members/` | `interfaces/world/` |
| carries | wishes, offers, signals between specialists; shared types | readings, belief levels, edge events, commands and their receipts |
| decided by | the composition (spec 15: natures, `shared: {pred: in/out}`, `handles/2`) | the semantic world (an event fold) and the adapters (MCP servers, sensors, the person) |
| deterministic | always (rules) | by event order: the world never reads a clock, every event carries `at` |
| written in | `.llp` declarations + `.yaml` natures (spec 15 I11) | `.llp` declarations + `.yaml` contract (this file's schema below) |

Cognition units (`cognition/`) and device units (`devices/`, Task 3) include the interface packages they read or write, by name. No member declares a crossing pred itself, and no director re-types one by hand (see [single source](#single-source-of-truth)).

## Kind 1: member interfaces (`interfaces/members/`)

One package per crossing family (examples: `scene` from scenes to lights/air/media/timers/music, `mood` to music/glow, `offers` as the shared type of taste handles, `opportunity`, `research`). Each package has:
- `NAME.llp`: `catalog NAME_iface 1.`, its `types (...)` imports, `namespace NAME_iface produce (dyn).`, and the preds;
- `NAME.yaml`: `nature: {pred: signal|state|...}` (spec 15 I11).

A member says which direction it uses each one in its `domain.yaml`: `shared: {pred: in|out}`. A pred with several writers or no reader fails `metisc --interface` (spec 15 §3).

**Not kind 1:** anything a person said, a sensor saw, a tool returned or a clock produced. "later", "arrived", a completion report, the speech floor and a calendar event are world inputs (kind 2), even when only one member reads them.

## Kind 2: world contracts (`interfaces/world/`)

### The principle: the semantic world is the only door

Every update from outside is an **event in the world stream**, folded by the semantic world (`metis-worlds/libs/semantic-world/go`, `home.Apply`), and the members see the result only as the board's level do-lines at a `settle`. Every action toward the outside is a **command event** written to the same stream *before* the call (the world's prediction), executed by an adapter, whose outcome comes back as a reading or a report event. So:

- perception and actuation share one ordered log. Replay gives the same world, the same member lines and the same surprises (`home.Hash()` checkpoints);
- **MCP is the uniform actuator and observer.** Home Assistant (its MCP server, through pi-core's `mcp` client in nina-live), Google Calendar/Tasks/Chat in the office, and web search are adapters. Adding a capability means declaring a world contract (ports, edges, commands bound to MCP tools, receipts) and mapping its tool results into world events. No member changes and no new orchestration is added;
- a command that never gets its receipt is a **world surprise**, raised by the world itself (`"commanded off, no reading after 15 s"`, kind probabilistic). It is not a host-side assertion;
- the person is an adapter too: speech and typed chat arrive as `report` events (`person`, `id`, `var`, `value`, `ref`) or, for edges, as host edge events logged in the same stream.

```
           ┌──────────── world stream (one ordered log: nina-live log / SITL events.jsonl) ────────────┐
 HA (MCP) ─┤ ha_state      report (person, tool)      command (prediction)      strain      settle(at) │
 person   ─┤                                                                                           │
 tools    ─┘                          semantic world: home.Apply(ev) → Out                             │
                                         Out.Lines[member]  level do-lines, one atom per known key     │
                                         Out.Wake[member]   spec 15 rule 1 (beat on change / period)   │
                                         Out.Surprises      probabilistic | evidential | world         │
 composition (director + members) ◄── level lines + edge events at the tick ──┘                        │
 composition ──► fired command rule ──► command event ──► adapter (MCP tools/call) ──► receipt event ──┘
```

### What a world contract declares

`interfaces/world/FAMILY.yaml`:

```yaml
family: ventilation            # the contract's name; one file per sensor/actuator family
version: 1
owner: world                   # who writes its readings: world (semantic world) | host | person
ports:                         # levels the semantic world offers (spec 16). A member reads them via beliefs:/levels:
  unit_on:  {world_port: on,       keys: [unit], levels: {power:   {at: [0.05, 0.95], names: ["off", unconfirmed, "on"]}}}
  out_cold: {world_port: out_cold, keys: [unit], levels: {outside: {at: [0.5],        names: [mild_out, cold_out]}}}
edges:                         # one-beat facts the host asserts on an edge, logged as world events
  - {pred: unit_missing(unit), from: "reachable(U) falls below 0.5"}
commands:                      # out: a fired rule named in `rules` → world command event → adapter call
  unit_on:
    rules: [air_on]              # the actuating rules; the person's verbs (intent.yaml) are inputs, not commands
    args: [unit]
    predicts: {var: power, value: "on"}   # the world's prediction, written before the call
    grace_s: 15                           # no confirming reading within it → world surprise
    adapter: {mcp: {server: ha, tool: HassTurnOn, args: {name: "{unit.entity}"}}}
receipts:
  via: ha_state                # the outcome returns as a reading (ha_state) | report (tool result, ref = command id)
freshness: {stale_after_s: 600, feed_down: forget}
consumers: [air, comfort]      # members allowed to read it (checked against their manifests)
```

`interfaces/world/FAMILY.llp` declares the edge and receipt preds, in namespace `world_FAMILY` (one owner, as `shared/home_world.llp` does today in nina-live). Level atoms need no declaration beyond the member's `levels:`.

### Rules for contracts

- **One door per fact.** A fact has one contract and one writer. When two members need it, they both read it, and neither re-derives it.
- **Exclusive families with an unsensed member** (as nina-live `home_world.llp`): a reading whose sensor is not wired is `unsensed`, so a rule that needs the reading does not fire. A key the world does not know holds no level atom: silence is never a level.
- **Correlation.** Each command event carries the command's id, and a receipt names it (`ref`). Pending-command expiry is the world's (`grace_s`), and so is the surprise.
- **Principal.** A contract names who may cause its commands (`consumers`). Routing a request through the director grants no authority. Each incarnation has its own world stream: no record crosses incarnations.
- **Availability is the world's, after discovery.** Contracts are incarnation-independent. What exists is what the world discovered: the initial `get_states` of each adapter (HA's entities, the MCP servers' tools). A port with no discovered keys holds no atom, so its rules cannot fire. A request naming a device the world does not have binds the standing handle (`ux`, `lx`) and the rule refuses it with a reason. The office has no ventilation because its discovery finds no unit. Nothing in a contract or a director says so.

## Incarnations: one catalog, two directories

```
cognition/                 the shared family: cross-domain character units (situations, commitments, attention,
                           social, curiosity, self_model, persona) + lifted bases (director_domain, taste_domain)
devices/                   (Task 3) the home-system family lifted from nina-live: lights, air, media, comfort,
                           scenes, timers, agenda, music, habits, glow
interfaces/members/        kind 1
interfaces/world/          kind 2
workspaces/home/           composition.yaml, the generated capacity, the director instance, thin member instances,
                           world map, scenarios/ (SITL)
workspaces/office/         the same shape, its own composition, director and world map; it includes the same units
sitl/                      the software-in-the-loop framework (see sitl/README.md)
```

A thin member instance includes the family unit by name and binds its types. Office differences are made with spec 18's tools, in order of preference: port values, abstract type binding, inclusion, `extends`, gating, `include "unit" hiding (r…)`. There is no composition inheritance (spec 15 §2.3 is flat) and no rule override (spec 18 §4, §7).

### Single source of truth

The director's `type domain`, `type kind` and `handles/2` and the capacity's member type are **generated** from `composition.yaml` and the members' `shared:` declarations. They are never written by hand. A check fails when a generated file is stale. In nina-live today these lists are written three times (`composition.yaml`, `shared/home_map.llp`, `director/director.llp`), and acasa `roles/secretary` already had to rewrite two of them.

## The catalog is independent of the runtime

The catalog (`cognition/`, `devices/`, `interfaces/`, `workspaces/*` compositions) holds rules, manifests, intents and contracts. It names one thing of the runtime: the host module, `host: nina_world.host:<member>`. Every runtime provides that module. A runtime serves this catalog when it does four things:

1. **world:** folds every outside update as an event of the world stream through the semantic world, and gives each member its level do-lines (`Out.Lines`) and the families and edges of the world contracts at its tick;
2. **commands:** when a rule named in a contract's `commands.*.rules` fires, writes the `command` event (the prediction) before the adapter call, then calls the adapter (MCP `tools/call` as the contract binds it) and folds the receipt back as an event;
3. **person:** delivers the person's requests through the member's intent card (the mapper, `AgentHost.submit`), never as host lines;
4. **discovery:** builds the world map from what its adapters report (entities, tools). The catalog never ships a deployment's map.

`sitl/` is one such runtime (Python, simulated adapters). nina-live is another (Go). Switching or updating the catalog therefore means pointing the runtime at another catalog root (`METIS_CATALOG`, `METIS_HOME`), with no fork.

## Repointing nina-live and acasa

Because the deployed runtime and the SITL share the world fold and the contracts, plugging these catalogs into Nina requires these steps (MIGRATION.md will spell out each path):
1. nina-live: its catalog host (`catalog/world/home_host.py`, a second world in Python, and the HA REST backend) is replaced by its runtime's `nina_world.host`. Its device control goes through pi-core's `mcp` client as the contracts bind it. Its catalog directory is replaced by a pointer to this catalog (see `RUNTIME.md`).
2. acasa: `domains/home` (the first-generation monolith) is retired. The deployment side stays: HA connection, `devices.json` → the world map, `live/` configs, `roles/<incarnation>` pointing at `workspaces/<incarnation>`.
3. Both set `METIS_HOME` to this repository's families and `METIS_CATALOG` to a workspace.

## Status

Design accepted by the maintainer 2026-11-26. **Runs:** the 11 device members merged from nina-live (`devices/`, from nina-live 702c428, host lines repointed to `nina_world.host`) run on the SITL. In `workspaces/home/scenarios/devices/b01-c02-ventilation.yaml`, a person's request fires `air_on`. The ventilation contract turns it into a world command and a simulated HA MCP call. A unit that ignores the call produces the world's own surprise `u2.power: commanded on, no reading after 15 s`. Two runs give byte-identical event logs. The cognition members (`workspaces/home/domains`) still take their inputs by direct injection; moving them onto the world contracts is `sitl/TASKS.md` T1/T3.

Open: conversation-level facts (utterances, completion reports, calendar arrivals) have no semantic-world port yet. They arrive as `report` events, but the home adapter offers ports only for devices and `strain`. A generic report-port (categorical belief over a reported var, with freshness) is a proposal for metis-worlds. Until then they are host edge events logged in the same stream, which keeps them deterministic but leaves them without belief.
