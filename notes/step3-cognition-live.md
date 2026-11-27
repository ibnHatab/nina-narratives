# Step 3: the cognition members inside real Nina (nina-lead, 2026-11-28)

The redesign's step 3 (subject s-b478fe59, nina-live's `docs/design/channel-streamlining.md`): the narratives'
cognition members (situations, commitments, attention, social, curiosity, self_model, persona) run in cmd/nina
beside the device members, under one director, fed by the same world contracts the SITL uses
(`interfaces/world/*.yaml`). Behaviour changes, so it lands behind a switch and passes the real-Nina gate.

## What the SITL does that real Nina must do too

`sitl/loop.py` feeds each member through `nina_world.host` (a pass-through):
1. **edges**: an outside event (`{kind: report, var, value, id}`, `{kind: floor}`) matches a contract edge
   (`when:`) → an atom (`arrived(call)`) for the members that declare it in `world.out`, its lifetime `beat`
   (retracted next beat) or `consumed` (kept until a rule uses it);
2. **families**: the world's state projected per member (`sitl/project.py`, the contracts' `families:`), its
   corrections each beat; the member's `owned` preds held through the command's grace;
3. **levels**: the semantic world's do-lines for the member (`Out.Lines`);
4. **commands**: a fired rule named by a contract's `commands.*.rules` becomes a command event, then an adapter
   call (`say` → the person hears it; `message` → a chat), then its receipt as a report.

## The gap: the capacity is the scenario's, not a home's

`workspaces/home/domains/capacity.llp` names its tasks per scenario (`type task {call dinner}`). Real Nina's
commitments are open-ended words. The plan:
- **Task slots**: `type task {t1 … t8}` in the live workspace's capacity. The host keeps a **ledger**,
  slot → the person's words, as the agenda keeps an event's summary outside the rules. A slot is allocated by
  `keep`, released when the commitments member closes it (done, or forgotten after its rule).
- **Report verbs on the director's card** (claudia's P7, accepted): `KEEP(words)` → `arrived(tN)`,
  `LATER(words)` → `later(tN)`, `AGAIN(words)` → `renewed(tN)`, `DONE(words)` → `completion_report(tN)`;
  the words matched to a slot as the agenda matches a list item (`agenda.Match`). The V0 gate counts reports
  recognised and **false reports** (a verb the scenario's truth does not have).
- **Floor**: fsttm-live's floor events (`core.Floor`) → the `floor` edge.
- **Commands**: `say(tN)` → a voice NOTE with the slot's words; its receipt `uttered` from the dialogue's
  reply_done.

## The work, in order

A. **narratives**: `workspaces/live/domains`, the devices' members (links into `devices/`) and the cognition
   members under one director instance (the two handle sets merged; `scenes` the planner), its capacity with
   task slots and the home's participants and channels; the device `persona` renamed `temperament` (nina-live's
   host registration, its card `home_temperament`).
B. **nina-live `worldhost`**: the Go port of `nina_world.host` + the loop's feeding (contracts loader, edges,
   families, lifetimes, owned preds, commands), registered for every member whose host is `nina_world.host:<m>`
   and has no Go host of its own.
C. **the report verbs** (the director's card) and the slot ledger.
D. **the SITL**: `nina_proc.py` translates the cognition scenarios (report/floor/hands) into words and states
   for real Nina (phase 2 of `sitl/NINA-IN-THE-LOOP.md`); the 36 scenarios join the real-Nina set.
E. **the switch**: `home.root`'s domains link → `workspaces/live/domains` per role; gate against the baseline.

## Finding (2026-11-28): one director cannot hold both halves

metisc derives a specialist's handles from what it consumes that no specialist produces: a kind a specialist
puts out is a result, and only the planner takes results (`src/link.ml`, `handles_s`). The devices need `scenes`
as their planner (its `scene_*` wishes reach lights, air, media). The cognition needs `attention` as its planner
(`commitments` puts out `reminder_offer`, which only the planner takes). One composition has one planner:
- `scenes` the planner → `reminder_offer` is a specialist's result, routed to no one: the reminders break;
- `attention` the planner → `scene_*` are a specialist's results: the scenes break.
So step A's "one composition under one director" (P1) does not hold as planned.

The options:
1. **Two compositions in one Nina** (recommended): the devices' and the cognition's, each with its own director
   and planner, each certified by its own gates, coupled only through the world contracts (the cognition reads
   the device world's families and the conversation's edges; its `say` becomes her voice's note). This is what
   the SITL already does: the cognition runs under `home_director` with the devices as its world. The runtime
   change is metishome serving two compositions (two ticks on one beat).
2. **A director tree** (metis-lang's `director_tree_domain`): one top director over two sub-directors. Cleaner
   in Metis's terms, but a hierarchy neither catalog has been formalized or gated in.
3. Rewrite one half's routing so it needs no planner (e.g., scene wishes as person-goal kinds): a rule change
   in a gated catalog, through the loop.

## The way (the user, 2026-11-28): one board, two directors

The runtime already has the executor: the semantic world's Board (metis-worlds semworld/ports.go, spec 15's
blackboard). Ports are offered by the world's adapters; each member that joins reads its own copy of each port it
names (`Lines(member)`), wakes on its own clock or on a change it did not make (`Wake`), and every member sees
the same boundary (`Settle`, once a beat). Membership is not one composition's. So:
- the devices and the cognition keep their directors and planners (scenes, attention): each half's routing is
  its own, certified by its own gates;
- every member of both halves joins the ONE board of her one world: what they share (presence, the rooms, the
  units, and now the person's words) are ports, copied to each reader, synchronized at Settle;
- the person's words become **report ports** (interfaces/proposals/report-port.md): categorical variables with a
  finite vocabulary, keys (person, task), reporters and consumers, freshness by event time, stable report ids.
  The voice's report verbs write report events; the board settles them; the cognition members wake on them as
  the devices wake on readings. The SITL's contract edges for these become ports (a versioned migration).

The work, revised:
1. **metis-worlds**: report ports on the Board (the proposal, with its two conformance fixtures).
2. **metis-agent metishome**: several compositions on one board (each its own tick and director; one beat, one
   Settle), members of all joined before the first beat.
3. **nina-live**: the report verbs and the task-slot ledger (report events into her world), the cognition's
   commands (say → her voice's note, uttered as the receipt), and the cognition composition opened beside the
   devices'.
4. **the SITL**: the cognition scenarios through real Nina; the gate.

## Decided (the user, 2026-11-28): match the catalogs, keep the parallel ticks

Not two catalogs side by side: ONE catalog, its packages isolated and testable, assembled under ONE director.
- **One planner, `attention`.** The scenes stop routing wishes through a planner: `scenes` concludes the home's
  mode (night, away, home; the mood) into the world, offered as a board port; lights, air, media, music, glow read
  the mode level from their own copy and sweep on its change. `scenes` becomes an ordinary specialist, its card a
  person's goal (ask_scenes) like the others. A devices rule change: through the loop, the regression, the
  real-Nina gate on the scene scenarios.
- **The world on its own tick.** Today `HomeSem.Read` settles the world whenever a device view recomputes its
  readings, so the settle follows the readers (and with members on different ticks it would settle more than
  once a beat). The semantic world must settle on its own clock, independent of the rules and of the LLMs in the
  loop (their latency never delays a world update); every member reads the last settled snapshot, wakes by the
  board's change counters, on its own period (the devices every beat, the cognition slower). This is the board's
  executor: common ports copied to each member, independent ticks, synchronized updates.

The work, in this order:
W1. metis-agent: the world settled by the runtime's own ticker (metishome Settle), the members' readings keyed by
    the world's settle, not by each view's beat count.
W2. nina-live: her world ticker (home.world_beat) beside the rules' beat; the members' periods from their manifests.
W3. metis-worlds home: the mode port; devices: scenes concludes the mode, the packages sweep on its level.
W4. the merged workspace under `attention`: the cognition members, the report verbs and the task-slot ledger.

## W3 progress and design (2026-11-28)

Done: W1 (metis-agent rd-world-clock cebed18), W2 (nina-live rd-step3 ca5a59f: home.world_beat), the mode and mood
ports (metis-worlds rd-mode e2dfb38: an event set, a Metis conclusion, refused on a sensed variable), the scenes'
rules concluding them (metis-agent 063f6d0: scene_set, arrive, mood_set, mood_change → set home.mode / home.mood).

The sweeps, as a level and a latch (not an edge): a package host gives level atoms as corrected readings every
beat, so a rule that consumed the mode's atom would get it back and fire every beat. Each package keeps the mode it
last swept for and fires once when the world's mode differs:

    sweep_night [dyn] : $home_mode(yes, night) * swept(M) * other(M, night) -o swept(night) * sweep_off(l1) * sweep_off(l2).

(`#init swept(home) 1`; `other/2` and the mode's types in shared/home_world.llp; the level in each manifest:
`levels: {home_mode: {from: {belief: mode}, at: [0.5], names: [no, yes]}}`.) Idempotent, independent of the
delivery's timing: the latch is the package's own state.

Still to do in W3:
- metis-agent's home host: home_mode and home_mood among the reads of lights, air, media (homeReads);
- nina-live's own hosts (timers, music, glow) give the same level from the world (they read no board today: their
  scene_timers, scene_music, mood_music, mood_glow came forwarded by the director);
- devices: the fan files (gen_map.py SWEEPS for lights, air, media; timers, music, glow by hand) on the latch;
  scenes no longer puts out scene_* / mood_*; iface/home.llp, the director's kinds and handles without them;
- the gates: the narratives' regression, the real-Nina scene scenarios (night, away, the mood) against the baseline.
