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
