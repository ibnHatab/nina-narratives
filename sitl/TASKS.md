# Implementation tasks for the formalizer (Codex)

Assigned by the controller for the maintainer, 2026-11-26 (rev. 00a13dc). This file replaces GitHub issues and PRs. Work on `main`, commit and push in small steps, and record each outcome here: tick the box and add one line with the commit, what passed and what is **not run**. Read `interfaces/README.md`, `sitl/README.md` and `RUNTIME.md` first. Load `$metis-language`, `$metis-loop` and `$metis-workspace`, and use the `metis` MCP tools for linting, triage and gating. Do not modify upstream repositories, nina-live or acasa.

**This repository is the reference.** Contracts, the generic host and the SITL define the interfaces. nina-live is source material to merge, not an authority. Availability is the world's, after discovery: never add per-incarnation `scope` or `unavailable` flags.

Baseline that runs (00a13dc): `devices/` (11 members merged from nina-live) on `sitl/loop.py`. Scenario `b01-c02-ventilation` produces a world surprise, with byte-identical reruns.

## T1. Cognition onto the world contracts
- [ ] Move a person's words and the floor (`arrived`, `later`, `renewed`, `completion_report`, `floor`, `uttered`) out of `cognition/iface/timing` into `interfaces/world/conversation.llp`, which exists and uses layer `dyn`. Move genuine member-to-member crossings (`opportunity`, `research`) to `interfaces/members/`. This clears the `unknown layer 'story'` errors.
- [ ] The cognition members name `host: nina_world.host:<member>` (drop `input_host.py`). `metisc build` and `metisc --interface` must be clean, and lint must be clean.
- [ ] Commit `workspaces/home/research/issue-4` and write `workspaces/home/REPORT.md` (the old→new map, results, surprises by kind, open questions).

## T2. One home composition, one source of truth
- [ ] Merge cognition and devices into **one** home composition (`workspaces/home/domains`). The device units move to `devices/` as family units, with thin instances in the workspace. Resolve name clashes: nina-live `persona` (temperament) and cognition `persona` must become one member or two distinct names. Record the decision and the evidence (issue #5: persona's preds out of the `home` namespace, and `her_mood` either a crossing or a contract).
- [ ] `sitl/gen_director.py`: generate the director's `type domain`, `type kind`, `specialist/planner/handles` and the capacity's member type from `composition.yaml` plus the members' `shared:`. Add a `--check` drift mode and run it in `contracts.py check`.
- [ ] Teach `contracts.py` to see rules in included family units, so its "not served" notes become exact.

## T3. The loop, complete
- [ ] Move `sitl/project.py`'s tables (READS, OUTCOMES, EVENTS, OWNED) and `loop.py`'s PRESETS/SWITCHES into the contracts (`families:`, `edges:`, the commands' value maps). The loop reads them from there and keeps no device knowledge.
- [ ] Person and conversation events go through the world stream: a `say` is logged as a `report` event, and the conversation contract's edges are derived from reports. The intent still goes through `AgentHost.submit`.
- [ ] Scenario `monitors:` (truth vs. trace, scene-cited) write findings through `Workspace`/`RuntimeFeed` with the key `<run>:<kind>:<k>`. World surprises are written the same way.
- [ ] `loop.py --replay events.jsonl` reproduces every hash and surprise. Add a test.

## T4. Adapters
- [ ] Extend `mcp_sim.py` to the lights, TV, calendar/tasks and chat tools the contracts bind. Behaviours: obey, delay, ignore, manual override, feed down, tool error. Draws are addressed by (scenario, seed, command id).
- [ ] Check the bound tool names against the real HA MCP server's `tools/list` (read-only, through nina-live's `mcp` client or curl with the maintainer's token file; never print or commit it). Correct the contracts, and mark any unverified binding.

## T5. Book I in the loop
- [ ] Port the `later`/`completed` resident cards onto the loop. The resident talks only through events, and the old finding comes back as a monitor finding.
- [ ] One scenario per Book I chapter that needs the world: C01 appointment/kettle, C02 override (exists: extend it with a monitor on what Nina *says*), C07 night ventilation, C08 missing hours (feed down, then restore). Each `expect:`s at least one world surprise.
- [ ] Triage all findings by kind (MCP `trace_kind`). Put at least two through `pack_propose`, and record which changed a domain's essence and which were noise.
- [ ] The devices' goldens (`devices/*/goldens`) were written with nina-live's old host. Regenerate them on `nina_world.host` and record every difference as a finding. Do not repair silently.

## T6. Office (Volume II)
- [ ] `workspaces/office/`: its own composition and director instance over the same family units, plus a fictional office world map. The office lacks ventilation and lights because its discovery finds none, not because a flag says so. Add the office's own contracts from `notes/volume-02-setting.md` (typed chat channels per participant, calendar/tasks via Google MCP, public search, music).
- [ ] Reconcile with acasa `roles/secretary/catalog`. List what it does, what this workspace replaces, and what acasa keeps (no edits there).
- [ ] Formalize Volume II (`narratives/volume-02/`, 12 chapters) as office scenarios with scene citations, following Book I's method. Check that no office event or record reads a home one.

## T7. Runtime handover
- [ ] Keep `RUNTIME.md` true. After T3, write the equivalence harness of its step 4: run one event log through the SITL and record the hashes, lines, fired rules and surprises, as the expected output a second runtime must reproduce.

## Proposal (document only)
- [ ] `interfaces/proposals/report-port.md`: a generic semantic-world port for reported vars (a categorical belief with freshness and source), addressed to metis-worlds. Do not implement it upstream.
