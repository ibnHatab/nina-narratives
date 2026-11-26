# Implementation tasks for the formalizer (Codex)

Assigned by the controller for the maintainer, 2026-11-26. This file replaces GitHub issues and PRs: work on `main`, commit and push in small steps, and record the outcome here (tick the box and add one line: the commit, what passed, what is **not run**). Read `interfaces/README.md` and `sitl/README.md` first. Load the skills `$metis-language`, `$metis-loop` and `$metis-workspace`, and use the `metis` MCP tools for linting, triage and gating. Do not modify upstream repositories, nina-live or acasa.

Each task ends with its checks run. Anything not run is marked so.

## T1. Finish the Task 1 layout on the new interface split
- [ ] Move the member crossings to `interfaces/members/` (`opportunity`, `research`, and any genuine member-to-member pred). Move a person's words and the floor (`arrived`, `later`, `renewed`, `completion_report`, `floor`, `uttered`) to `interfaces/world/conversation.llp`, which exists, and delete `cognition/iface/timing`. Doing this also clears the `unknown layer 'story'` errors: contracts use the `dyn` layer.
- [ ] Update includes and `composition.yaml` `interfaces:`; set `METIS_HOME` to the repo families. `metisc build` and `metisc --interface` on `workspaces/home/domains` must be clean, and lint must be clean.
- [ ] Commit the Task 1 evidence (`workspaces/home/research/issue-4`) and write its report in `workspaces/home/REPORT.md` (issue #4's list: old→new map, results, surprises by kind, open questions).

## T2. One source of truth for routing
- [ ] `sitl/gen_director.py`: generate the director's `type domain`, `type kind`, `specialist/planner/handles` and the capacity's member type from `composition.yaml` plus the members' `shared:` (precedent: metis-worlds `alfworld/world/gen_hier.py generate_director_package`). Write it to a generated file the director instance includes.
- [ ] Add a `--check` mode that fails on drift, and run it inside `contracts.py check`.

## T3. The loop (`sitl/loop.py`)
- [ ] Implement `sitl/README.md` "The loop, one beat" over `metis_agent.service.Live`, as `workspaces/home/simulations/resident/run.py` does now, with `semworld-step` as a subprocess (JSON lines) and `RuntimeFeed` for findings.
- [ ] Edges: derive them from each contract's `edges:` (start with an explicit mapping table per contract; no free-text parsing of `from:`).
- [ ] Commands: when a fired rule's name is a contract command, write the `command` event before the adapter call. The id is `<run>:<k>:<rule>`.
- [ ] Write `runs/<run>/events.jsonl`. Add `loop.py --replay events.jsonl`, which must reproduce every hash and surprise; test this.
- [ ] Port the `later` and `completed` cards of `simulations/resident` onto the loop. The resident talks only through `report` events. Acceptance: the old card's finding is reproduced as a monitor finding, **and** a device scenario yields a world surprise.

## T4. Simulated adapters (`sitl/mcp_sim.py`)
- [ ] An MCP-shaped `tools/call(name, args)` per contract `adapter:` binding: HA tools → hidden device state → `ha_state` receipts; calendar/chat tools → `report` receipts with `ref`.
- [ ] Behaviours from the scenario truth: obey, delay, ignore, manual override, feed down, tool error. Draws are addressed by (scenario, seed, command id).
- [ ] Before the first scenario, check the tool names against the real servers' `tools/list` (HA's MCP server through nina-live `mcp`, read-only) and correct the contracts. Mark a binding unverified when its server is unreachable.

## T5. Book I scenarios and surprises
- [ ] One scenario per Book I chapter that needs the world (at least C01 appointment/kettle, C02 ventilation and manual override, C07 night ventilation, C08 missing hours/feed down and restore). Each needs a scene-cited monitor and an `expect:` with at least one world surprise.
- [ ] Triage every finding by kind (MCP `trace_kind`). Put at least two through `pack_propose`, and record which changed a domain's essence (a missing distinction, type or port) and which were noise. Proposals stay proposals.

## T6. Office (Task 2): Volume II
- [ ] `workspaces/office/`: its own composition, director instance and world map. Use the same `cognition/` units through thin instances. Office deltas follow spec 18's order (port values, type binding, inclusion, `extends`, gating, `hiding`).
- [ ] Contracts with `scope: [home]` are declared unavailable in the office (`unavailable_*`), never silently unhandled. Add the office contracts the novel needs (typed chat channels, calendar/tasks via Google MCP, music, public search) from `notes/volume-02-setting.md`.
- [ ] Reconcile with acasa `roles/secretary/catalog`. List what it does, which of it this workspace replaces, and what acasa must keep (no edits there).
- [ ] Formalize Volume II (`narratives/volume-02/`, 12 chapters) as office scenarios with scene citations, following Book I's method. No office record may read a home record.

## T7. Devices family and migration (Task 3)
- [ ] Lift nina-live `catalog/domains` specialists (lights, air, media, comfort, scenes, timers, agenda, music, habits, glow) into `devices/` as family units, with thin instances in `workspaces/home`. Keep their goldens passing (`python -m metis.catalog golden`).
- [ ] Bind every command rule in a contract: today `contracts.py check` lists 76 unbound command rules across air, glow, habits, lights, media, music, persona, scenes and timers. Split real actuations (MCP adapters) from internal bookkeeping (no adapter: mark `adapter: {internal: true}` with a reason).
- [ ] Resolve the persona boundary (issue #5): persona's preds out of the `home` namespace; `her_mood` either a member crossing or a world contract `persona_state`. Record the decision and the evidence.
- [ ] `MIGRATION.md`: every nina-live/acasa path → its new path, the refactoring nina-live (Go hosts, `mcp` client bindings) and acasa need, and what stays deployment-side.

## Proposal (document only)
- [ ] `interfaces/proposals/report-port.md`: a generic semantic-world port for reported vars (a categorical belief with freshness and source), so conversation facts gain belief like sensor readings. Address it to metis-worlds and do not implement it upstream.
