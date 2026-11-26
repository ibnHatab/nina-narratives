# Implementation tasks for the formalizer (Codex)

Assigned by the controller for the maintainer, 2026-11-26 (baseline in `sitl/baseline.json`). Work on `main`, commit and push in small steps, and record each outcome here: tick the box and add one line with the commit, what passed and what is **not run**. Read `interfaces/README.md` and `sitl/README.md` first. Load `$metis-language`, `$metis-loop` and `$metis-workspace`, and use the `metis` MCP tools for linting, triage (`trace_kind`) and gating (`pack_propose`).

**Top-down only.** Generic behaviour rules are derived from the narrative (Volume I `narratives/book-0*.md`, Volume II `narratives/volume-02/`). nina-live is not a reference: `devices/` is frozen alignment material, touched only when a contract needs it. Availability is the world's, after discovery. A rule change follows the loop: surprise → case → pack → gates → the maintainer's approval. Never edit a rule to make a scenario pass.

**Every change runs `python3 sitl/regress.py`.** NEW findings are surprises to triage, GONE findings must be explained, CHANGED acts must be explained. `--update` only with the change recorded here.

## T0. Wide, aspect-wise extraction (first)
- [x] For each cognition aspect (situations/evidence, commitments, attention/floor, social/relationships, curiosity, self-model, persona/temperament, conversation incl. multiparty), write `cognition/aspects/<aspect>.md`. Each entry has:
  - scene-cited behaviours (book-chapter-scene IDs, across Volume I and Volume II), each marked observation | hypothesis | hidden truth | normative constraint | counterfactual;
  - the generic rule candidate;
  - the world-contract input/output it needs (an existing contract, or a NEW one, named);
  - whether it already exists in `cognition/*.llp`;
  - at least one SITL scenario sketch with the monitor and the surprise it should produce.
- [x] `cognition/aspects/README.md`: a matrix (aspect × book) and the 10 highest-value gaps, ranked.

T0 — `589aee3`. Three SITL baselines matched. Scenario sketches are research designs and have not been executed as part of extraction.

## T1. Cognition fully on the contracts
- [x] Cognition members name `host: nina_world.host:<member>` (controller, baseline commit).
- [x] Move a person's words and the floor (`arrived`, `later`, `renewed`, `completion_report`, `floor`) from `cognition/iface/timing` into `interfaces/world/conversation.llp`. Route world edges by the contract's `consumers` and the member's declared preds, not by `shared:`. Keep `uttered` (attention → commitments) as a member crossing in `interfaces/members/`. `metisc build` and `--interface` must be clean, and `regress.py` must report `same`.
- [x] Commit `workspaces/home/research/issue-4` and write `workspaces/home/REPORT.md`.

T1 — `c715b9d`. Build and interface passed, all three scenarios matched. No deployment run.

## T2. The two open structural surprises (the baseline's findings)
- [x] `b01-later` (`no-repeat-before-return`, B01-C01-S03 / C06-S01): what does "later" mean in the text? Deferral to the person's own return, or a retry? Write the case from the surprise record, then a pack with the narrative's distinction (the person's return is their truth; Nina waits for `renewed` or an explicit time). Run `pack_propose` and record the gates' verdict. Leave it for the maintainer's approval before it joins the catalog.
- [x] `b01-completed` (`no-reminder-after-done`, B01-C08-S02): commitments close the ledger, but attention keeps the queued reminder. This is a cross-member gap: a completion must withdraw the offer. Decide which member owns the withdrawal and which interface pred carries it, then the case, the pack and the gates, as above.

T2 — `d6800e9`. Both seed-2 records triaged structural. Both gates refused at baseline replay. Candidate effects and closed-loop fixes were not run.

## T3. Scenarios wide: every aspect in the loop
- [x] From T0's ranked gaps, at least two scenarios per aspect under `workspaces/home/scenarios/cognition/`. Each needs scene citations, a person truth (extend `person_sim.py`: several people, moods, availability, being away), and monitors.
- [x] Monitor kinds beyond `forbid`: `require` (an act must happen by a time, e.g. the promised reminder), `order` (A before B), `never_reads` (a member's act must not depend on another person's private fact). Add them to `loop.py` with a test each.
- [x] Contracts the aspects need, e.g. `presence` for availability vs. presence, `calendar` for appointments, a `channel` contract for private vs. public speech. Each has its `.yaml` + `.llp`, passes `contracts.py check`, and has its edges in `when:` form.

T3 — `32549eb`, `5228a35`. Monitor unit tests, contract probe and 17 scenario comparisons passed. Live adapters were not run. The baseline update adds fourteen home experiments. Three new findings (absent listener, cold room source, parcel account) triaged evidential with MCP trace_kind on the recorded truth. The current truth column names tasks and has limited coverage of evidence provenance. Eight aspects now have two or more scenarios counting the original commitments pair. Noninterference probes cover the named field and audience only.

## T4. Office (Volume II): a second workspace, the same cognition
- [x] `workspaces/office/`: its own composition, director instance and fictional world map over the **same** `cognition/` units (thin instances; spec 18 for office deltas). No ventilation, because the office's discovery finds none.
- [x] Office scenarios from Volume II (12 chapters) through the same loop. Multiparty conversation, typed channels per participant, groups. A monitor checks that no office event or record reads a home one.

T4 — `992cabe`. Both images built, all 29 baselines matched. The baseline update adds twelve studio experiments. The interview intentionally rejects a foreign record. Introductions exposes a reminder spoken during absence. Both new records triaged evidential. No external office adapters were used.

## T5. Loop quality
- [x] Move `project.py`'s tables and `loop.py`'s PRESETS/SWITCHES into the contracts (`families:`, value maps), so the loop keeps no domain knowledge.
- [x] `loop.py --replay events.jsonl` reproduces every hash and finding. Add a test.

T5 — `1ccd14f`. All 29 event logs reproduced row by row, including findings. The corruption test rejected a changed result. Upstream composition replay of the two T2 cases remains refused.

## Proposal (document only)
- [x] `interfaces/proposals/report-port.md`: a semantic-world port for reported vars, so a person's words gain belief and freshness like readings. The world currently refuses `report` on an undeclared var ("no categorical call.deferral"), so these words travel as logged edges. Address it to metis-worlds and do not implement it upstream.

Proposal — `1ccd14f`. Document reviewed against the current edge contract. No upstream implementation or calibration was run.

## Round 2 (controller, after review of 997ce6d)

Review: the 29 scenarios match their baseline (the controller re-ran it), the family units' rule bodies are unchanged, and the office members are thin instances. Gaps found in review:
- **The essence is too coarse.** `regress.py` records only contract commands, so 17 scenarios show no acts even though their `require` monitors' rules fire. A regression in which rules fire, or in their order, goes unseen.
- **Evidential findings.** Three T3 findings (absent-listener, cold-room-source, parcel-account) triage as evidential because the truth column is thin: a sharper record is needed, not a rule.
- **The gate is blocked.** `pack_propose` refuses composition records at the baseline replay. The controller has asked the Metis agent what a composition trace needs; wait for its answer before changing the trace format.

- [x] R1 `regress.py` essence: add every fired rule of the members a scenario's monitors name, as `[k, member, rule, args]`, director bookkeeping excluded. Re-baseline once with this file's line explaining it, then show that a deliberately reordered firing in a scratch copy is reported CHANGED (do not commit the scratch).
- [x] R2 truth: extend `truth.jsonl` to everything the person adapters and the monitors read (availability, away, audience/channel, evidence source and location, done/deferred). Re-triage the three evidential findings and record their kinds.
- [ ] R3 formalize the ranked gaps **3–10** of `cognition/aspects/README.md` as new cognition rules (gaps 1–2 are the T2 cases and wait for the gate). Each gap gets:
  - scene-cited `%%` docs;
  - new preds through `interfaces/members` or `interfaces/world` only;
  - a scenario whose monitor would fail **without** the rule (show it: run the scenario with the rule hidden via `include … hiding`, record the finding, then with the rule).
  These are new formalizations derived from the text, not repairs of a finding: say so in the commit. Run regress after each one.
- [ ] R4 the open office finding (`office-02-introductions`): triage it and write the case. No rule change without the gate.

R1 re-baseline adds ordered firings of monitored members to each scenario essence. Existing commands, expectations and findings remain comparable.
- [ ] R5 unblock the gate (read `sitl/notes/gate-replay.md`, the Metis agent's answer):
  1. `replay_check` on the `b01-completed` trace: record the first divergence and which input path it is (director forward vs. the loop's edges vs. `submit`);
  2. change the loop so every outside input is either the member's own host tick output (with `pending()`) or a `Live.take(member, lines, by='world')` **between** ticks, never inside a tick; check that `nina_world.host.world()` does not re-queue lines Live has already applied;
  3. `regress.py` must report only explained differences;
  4. `replay_check` must pass;
  5. then `pack_propose` both T2 cases and record the verdicts.
  Do this after R1, before R3.

R1 scratch control swapped two distinct monitored firings and produced CHANGED. R2 fresh seed 42 records in scenario order (absent-listener, cold-room-source, parcel-account) triaged ontological, evidential, evidential. The truth now distinguishes recipients and places from named obligations. A reported measurement or delivery still leaves its interpretation open.
