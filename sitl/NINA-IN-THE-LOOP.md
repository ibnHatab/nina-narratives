# SITL with Nina in the loop (design, nina-lead, 2026-11-27)

Subject `s-a3bb92db` (narratives-sitl). Branch `sitl-nina` of a fresh clone (`~/repo/nina-narratives-sitl`); Codex
keeps working on `main` in `~/repo/nina-narratives` (formalization, SIL regression, surprises).

## What the SITL is today

`sitl/loop.py` already folds every event through the **same semantic world** as nina-live (`semworld-step`,
pinned to nina-live's go.mod version) and runs the **narratives' composition** (cognition members, the
director) through `metis_agent` Live. Outside the world contracts, everything is simulated: the house
(`mcp_sim.HomeAssistantSim`, hidden truth), the people (`person_sim.Person`), the monitors.

What is **not** in the loop: nina-live's Go side, which is what people meet. Her tools and hosts (music,
timers, agenda, screen, lists, Home Assistant client), her task runner (System 2, pi, with its models) and the
way she turns a person's words into tool calls (System 1). Surprises found today are the rules' alone.

## Decisions (claudia's open questions)

1. **`cmd/nina` as a process**, not linked packages: the real binary, its real config, its real event log and
   panel. The outside it talks to is simulated at its own edges: a **fake Home Assistant** (REST + websocket,
   the endpoints `acasa/hass` uses) whose state is the scenario's hidden truth, and the panel API for words.
   Slower than linking, but it tests what runs on the Pis. Many scenarios run in parallel processes.
2. **One SITL, two roles**: the workspace (`home`, `office`) picks the role's config (acasa `live/nina.yaml`
   vs `nina-pero.yaml` shapes), map and scenarios.
3. **Live surprise drops** (Pascal, pero) feed the same workspaces later, once the SITL is real; not now.
4. **Models**: her task runner on DeepSeek Flash through OpenRouter (`tasks.fallback` / chain; the key in
   `~/.config/nina/openrouter.env`, text models only). No Gemini Live in the SITL: headless.

## Phases

### Phase 1: nina-live's own catalog, headless, against a fake Home Assistant
- **nina-live `-headless`**: no audio, no Live voice; a person's words (`POST /api/do {"action":"type"}`, or a
  new `sitl` endpoint) go to her **task runner** as the mind (System 2 with her tools), its answer is her reply
  (an event). Everything else as deployed: core, composition image, semantic world, hosts, event log.
- **`sitl/ha_sim.py`**: a fake Home Assistant on a local port: `/api/states`, `/api/services/<d>/<s>`
  (`return_response`), `/api/config`, `/api/websocket` (auth, `subscribe_events` state_changed). Backed by
  `HomeAssistantSim` (the truth); every service call is logged as the command it is, and the truth's change
  comes back as a state_changed event (with the scenario's delays and drops).
- **`sitl/nina_proc.py`**: starts `cmd/nina -headless` with a generated config (temp log dir, the fake HA's
  URL and token, the workspace's catalog root, the SITL's model chain), feeds the scenario's words and
  events by world time, reads her replies and tool calls from her event stream, runs the monitors.
- **Run**: one scenario of each volume; record the trace (`runs/<run>/`), the surprises (world's, monitors')
  and what her tools did.

### Phase 2: the narratives' composition inside cmd/nina
- nina-live's world loader takes its members from the composition (`domains/composition.yaml`), not from the
  five home packages it names today (the same blocker as acasa `roles/secretary/catalog`).
- `home.root` points at a workspace that includes nina-live's domain packages and the narratives' cognition
  members (cross-cutting: commitments, attention, conversation, …), with their interfaces.
- Then the accepted rulings move into nina-live's catalog (`image.golden` re-pinned, tests green): the
  subject's last step.

## Contracts kept

Nothing enters Nina except her edges (the fake HA, the panel). The hidden truth is read only by the fake HA
(as the house) and the monitors. Her model's answers are not deterministic: a run records them, a replay
feeds them back (the log), so a found surprise can be reproduced.
