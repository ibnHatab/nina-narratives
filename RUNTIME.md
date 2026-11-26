# Serving this catalog from a runtime

This is a brief for the agent maintaining nina-live/acasa. It describes the intermediate step that lets one runtime switch between its own catalog (`nina-live/catalog/domains`) and this one, then retire its own. The reference is this repository: `interfaces/README.md` (the contracts and the four runtime duties) and `sitl/` (a working runtime in Python that serves this catalog against simulated adapters).

## What the catalog expects

| duty | the SITL does it in | nina-live does it today in | the change |
|---|---|---|---|
| host module `nina_world.host:<member>` | `sitl/nina_world/host.py` (a generic host: lines in, fired rules out) | `catalog/world/home_host.py`, per-member factories, a second world in Python | provide `nina_world.host` in the runtime, the same generic host fed by the Go world (metis-home), and drop `home_host.py` from the catalog |
| world: events → semantic world → `Out.Lines`, families, edges | `sitl/semworld-step` (the Go world, pinned to nina-live's go.mod), `sitl/project.py` (State → families) | `world/world.go` + metis-home's families over `Home.State()` | none for the fold. Take the families and edges from the contracts (`interfaces/world/*.yaml`) instead of the host's tables |
| commands: contract rule fired → `command` event first → adapter → receipt event | `sitl/loop.py` + `sitl/mcp_sim.py` | the host's `ACTS` table → HA REST | route the contracts' `commands.*.rules` to pi-core's `mcp` client (HA's MCP server tools as bound in the contract). Write the `command` event before the call and fold the HA state back as `ha_state` |
| person: intents through the member's card | `AgentHost.submit` | the mapper (already) | none |
| discovery: the world map from the adapters | a fictional map (`workspaces/home/world/home.map.json`) | `catalog/world/home.map.json` + `gen_map.py` | keep the map deployment-side (private; it never enters this repo). Generate it from HA discovery through MCP (`ha_find`, `GetLiveContext`) |

## The step, in order

1. **Configuration switch.** Make the catalog root a configuration value: `METIS_CATALOG` points at a workspace's composition (here `devices/` today, `workspaces/home/domains` after T7), and `METIS_HOME` at this repository's families. The old catalog stays the default until the new one passes step 4.
2. **Generic host.** Implement `nina_world.host` in the runtime, keeping the old per-member hosts behind the switch. Its behaviour is `sitl/nina_world/host.py`'s: retract one-beat tokens, correct families to the world's projection (with the program-owned grace), hand over level lines and edges, report fired rules.
3. **Commands through MCP.** Resolve every fired rule against the contracts' `commands.*.rules`. Write the `command` event and call the MCP tool. A tool error is a `report` event, not an exception. The world's grace then produces its own surprise when no reading confirms the command.
4. **Equivalence.** Run the SITL scenarios under `workspaces/home/scenarios/` through both runtimes on the same event log. The world hashes, the member lines, the fired rules and the surprises must match. Differences are findings, kept, not repaired silently.
5. **Retire.** When step 4 holds, delete `catalog/domains` and `catalog/world/home_host.py` from nina-live. acasa keeps its deployment side: the HA connection, `devices.json` → the world map, `live/`, and `roles/<incarnation>` pointing at `workspaces/<incarnation>`. acasa `domains/home` (the first-generation single domain) is retired.

No step changes a rule. When a rule must change for the new runtime, that is a finding about the catalog, and it goes through this repository's loop (surprise → pack → gates).

## Status

Steps 1–5 not started (2026-11-26). The SITL side runs the 11 device members merged from nina-live 702c428.
