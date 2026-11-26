# Book I: formalization and semantic review

**Review disposition: executable research candidates; not ready for integration.** The mechanical checks succeed for the authored abstractions, but full-trace narration is semantically unreliable and the shared abstraction has reproducible counterexamples. These negative results are part of the deliverable.

The fiction remains unchanged at source revision `94e2c5829e6ebefa3bd41e35e513bba943dc8e12`. After pulling `2420894`, I read the creative director's letter and updated AGENTS.md. The maintainer's explicit chapter-by-chapter assignment authorizes this implementation beyond the bootstrap planning task. Book II was left unread so the creative team can use it for independent evaluation. This report is the formalizer's self-review, **not** an independent evaluator's verdict.

## What was run

- Workspace created through Metis under `.metis/`, ignored by Git. OpenRouter credentials sourced/exported only into the execution environment. Model settings are public; credentials are not.
- Installed `love_triangle` smoke test: six sampled firings, live workspace trace, successful REPL `narrate` call. Transcript: [smoke](love-triangle-smoke.txt). Its source was not copied into this repository.
- Eight chapter candidates, plus one reusable situations/commitments candidate, compile with the actual `metisc`. Manifest validation and the REPL `revise` admission harness pass for all nine. No `accept`, deployment, calibrated weight change or upstream source modification occurred.
- Authored chapter fixtures and derived controls: **66 runs** across seeds 1, 7 and 19, all phase assertions pass. The shared candidate adds **21 passing runs** and **six deliberately retained failing runs** (two counterexamples × three seeds). These counts are finite sampled checks, not proofs of all reachable behavior.
- All **93 runs replay with zero divergence**, including the failing runs. Replay proves reproducibility of the bad behavior too; it does not make it acceptable. [Summary](summary.json) records each outcome.
- Nine paid REPL narration calls (one authored trace per package), plus the smoke narration. Raw results and the actual narration material are preserved. No model output was rewritten to resemble the fiction.

Tool revisions and narrator settings: [toolchain.json](toolchain.json). Reproduction commands: [candidate README](../../candidates/book-01/README.md). Every run records initial state, ordered simulated inputs, seed, canonical program key, fired rows, per-phase counts, assertions and a raw Segments witness. Narration's API `seed: 0` denotes the live-session rendering; `trace_seed: 1` and the adjacent trace identify the sampler seed.

The admission gate uses each package's first fixture/first input to ensure a nonempty transition check. Its exact scenario comparison is not a replay of every chapter phase. The additional simulation/replay harness supplies that evidence. The gate's class-F classification is a static admission result, not evidence of empirically calibrated likelihoods or composition safety.

## What the chapter abstractions preserve

| Chapter | Represented mechanism and successful boundary probes | Important omission |
|---|---|---|
| I | Tentative greeting withdrawn; hallway plus kettle licenses greeting; promise rebound to return; discovery deferred. Kettle alone does not greet; return releases the reminder in a separate derived case. | No duration model, specific event identity, or rule to resume deferred discovery. |
| II | Missing/contradictory reports leave explanation open; human remote-control report revises it; quiet scene needs consent and explicit activation. Presence alone and an unconsented word do not activate it. | No automatic work recognition or implemented quiet-scene device policy. |
| III | Visitor-scoped tentative preference; corrected inventory; private question handed back; qualified self-description and relationship memory. | Guest data permission/retention and richer reciprocal relationship state are undefined. |
| IV | Two coexisting hypotheses; restrained action before certainty; cancellation/design reports change explanation while observations persist. | Other hypotheses, source reliability and independent social effects remain outside this sketch. |
| V | Permission and budget constrain initiative; arrival alone does not prompt; critique can preserve a useful idea while abandoning its implementation. | Budget magnitude, interruption by urgent duties and research cancellation are not modeled. |
| VI | Competing options offered; explicit consent simplifies dinner; guest delay does not restore the original plan; reaffirmed choice survives. | Scheduling arithmetic, actual parallel timers, ingredients and other-person notification. |
| VII | Quiet expression does not consume commitments or identity; moon knowledge is indirect; voice ends while persistent state survives. | Synthetic temperament dynamics and physical actuator outcomes. Night authorization is an assumption. |
| VIII | Checkpoint recovery preserves an unknown interval; completed/relevant reminders reconciled separately; restore waits for a reliable connection and report. | Actual process restart, durable exactly-once semantics, epochs and host failures. |

`cases.json` inputs are authored fixture assumptions, including source identity, consent and observation availability. They are not sensor capabilities established by compilation. Outputs are symbolic receipts; a predicate such as `settings_restored` is only reached after a supplied report, not a measurement performed here. Prohibitions on unrepresented actions (e.g. private-log disclosure) are coverage limits, not meaningful proofs of runtime safety.

The chapter packages are still relatively specific extractions. They should not become eight production specialists. Their value is exposing distinctions and testing the abstraction; the shared experiment below asks whether fewer rules can span chapters.

## Narration compatibility: failed full-sequence acceptance

All nine calls returned text successfully. None is accepted as a faithful complete retelling without qualification. The following are observations from the saved output, not suggested edits to it.

| Trace | Assessment against the fiction and fired trace |
|---|---|
| [I](ch01/authored-seed1/narration.json) | **Fail, actor/agency.** “Nina stirred in the bedroom” invents bodily action. The resident's promised call becomes Nina calling Elena and briefing herself; discovery deferral is confused with the call's trigger. |
| [II](ch02/authored-seed1/narration.json) | **Fail, evidence meaning.** `human_reports_remote` becomes “reported remote work” instead of using a remote control. “the lab remained present” misreads presence. Consent/manual activation/proposal-pending constraints are retained, but reports are compressed ahead of the events they followed. |
| [III](ch03/authored-seed1/narration.json) | **Fail, identity and relations.** “Simone remarked on Elena” reverses a music preference into a speaker relation. The resident is described as deferring their own private answer. Some final visitor-scoped state is correctly retained. |
| [IV](ch04/authored-seed1/narration.json) | **Partial content, fail full chronology.** Observations survive explanation revision and the unread channel is acknowledged. The two distinct hypotheses are rendered ambiguously as “an upset, working hypothesis”; later reports arrive in the opening bundle. |
| [V](ch05/authored-seed1/narration.json) | **Partial content, fail causal order.** Permission, budget, critique and useful revision survive. Return, invitation and objections are placed before investigation; discussion and revision are incorrectly described as simultaneous. |
| [VI](ch06/authored-seed1/narration.json) | **Fail, time and agency.** “Another ten minutes” becomes “only ten more minutes to spare.” The guest delay and consent arrive before the corresponding deliberation. The final simple plan is correctly retained. |
| [VII](ch07/authored-seed1/narration.json) | **Partial character continuity, fail chronology.** Identity and duties persist, bodily knowledge stays indirect, and ventilation is a request. “human moon” is a lexical error; reflection is moved after voice-session ending. |
| [VIII](ch08/authored-seed1/narration.json) | **Fail, token semantics.** Consuming restart/checkpoint markers becomes “the restart and the checkpoint were lost,” contrary to recovery. The persistent recovered checkpoint and unknown interval appear correctly in the final inventory, exposing the contradiction. |
| [Shared](mechanisms/authored-seed1/narration.json) | **Improved agency, still fail causal order.** Explanatory rule docs correctly distinguish Nina reminding the resident from the resident completing the call. But making the reminder ready is described as simultaneous with rebinding its trigger even though the former consumes the latter's promise. |

There are two distinct findings. First, terse quotation-only `%%` docs and opaque predicate names underspecify actor roles for the model. The shared candidate's explanatory docs help, but do not guarantee correctness. Second, the full-run narrator uses a Foata causal partial order: independent environment inputs can be grouped into the same beat even though the fixture delivered them at different times. That is visible in `narration-material.json`; it is not just a prose hallucination. Causal independence does not establish simultaneity of household observations. Some narrated simultaneities also violate the supplied causal order itself.

Do **not** add household rules merely to force the narrator into chapter order. Candidate follow-up: preserve observation epochs/temporal constraints in the host/trace narration contract, distinguish them from causal independence, and review phase-local narration against the same unmodified trace. No upstream toolchain changes were authorized or made. This is a representation/narration finding, not a demonstrated missing household rule to approve through the structural loop.

## Shared mechanisms and useful counterexamples

The same `consider`/`accept_report` rules handle ventilation override, appointment cancellation and a pantry transfer case, with issue-specific alternatives supplied as data. Observations are retained, tentative candidates are distinct from accepted sourced reports, and no report is asserted to be hidden truth. An explicit clarification opportunity permits action before certainty. This is a useful unification, but only two hypotheses per issue and no reopen lifecycle are modeled.

Promises use scheduled → ready → notified → fulfilled states; notification is not fulfillment. Human instructions rebind triggers. Human consent changes plans; changed circumstances only offer reconsideration. One interruption token arbitrates reminders and clarification.

- **Generative result:** with two due reminders and one interruption token, seed 7 notifies `call`, while seeds 1 and 19 notify `secondary_call`; the other stays ready. The resource is spent once. These outcomes expose unresolved scheduling policy, not a calibrated preference or a satisfactory social priority.
- **Stale-trigger counterexample:** all three seeds make `call` ready after rebinding it to an old `return` token. Desired `promise(call,return)` is missing and forbidden `ready(call)` is present. A future event needs identity/freshness; a persistent class is insufficient. The failing desired expectation is retained.
- **Completion-race counterexample:** all three seeds spend the interruption token before reconciling an already supplied completion report. The final task is fulfilled, but the unwanted notification already occurred. The desired unspent interruption is missing. Checking only the final `fulfilled` atom would have concealed the error. Reconciliation needs an explicit priority or epoch contract.

The last two are candidate structural/representation deficiencies requiring architectural input, not occasions to fit weights from fiction. Both replay exactly. Their cases are marked `known_limitation`; the harness retains `passed: false`, rather than changing the desired outcome to bless the bug.

## Lint and limits of the evidence

All lint output is retained beside each gate. `state-unproduced` generally names fixture-supplied observations or decisions, not a secretly missing producer. `state-dead-end` often names end-of-episode receipts, but also genuine unfinished lifecycles such as deferred discovery and pending proposals. We did not label everything as a shared port just to silence the warnings: there is no approved composed interface yet. These warnings must be revisited when proposing continuous operation.

There are no learned weights. Default unit weights are uncalibrated scheduling measures; counts and outcomes from these runs must not be presented as estimates of real human behavior. Chapter samples mainly differ in independent-event order; the shared reminder resource yields limited behavioral diversity. This is far short of a rich generative companion, including humor, relationship development and temperament-driven discretionary choices.

**Open-loop:** synthetic ordered inputs, nine admitted standalone candidates, 93 reproducible sampled runs; 87 satisfy the stated sampled checks and six expose known deficiencies. No deployed bundle was replayed.

**Closed-loop:** not run. The fixture supplies predetermined inputs and has no physical household, responsive person, actuator or real observation stream. No real interaction data was used.

## Questions for the creative team and architect

1. What makes a promised return “the return from the appointment,” and how should cancellation, an early trip home or a restart affect it?
2. When a completion report and a reminder coincide, should reconciliation always precede interruption? What source/epoch evidence makes that safe?
3. The fiction sometimes assumes hearing a kettle, knowing ingredients, and recognizing a guest. Which are connected observations, human reports, or deliberately open fictional assumptions?
4. What consent and retention distinguish a tentative visitor preference from household taste? What broad information may Nina volunteer before handing a private question back?
5. Which episodes should independently challenge these candidates? Book II is available to the creative team as unread material; no holdout claim is made for our derived controls.
6. Should a quiet work scene suppress routine announcements while preserving critical ones by priority, distinct resources, or a host contract? The current sketch authorizes a scene but does not implement that policy.

Review the mechanisms and objections before requesting production interfaces or deploying a rule. The creative director's letter is treated as an invitation to identify missing distinctions, not permission to manufacture observations or reshape canonical prose.
