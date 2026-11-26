# Mapping proposals to Nina's home incarnation

Inspected target: `nina-live` at `d01f10f27dba8590ef56fe795580a5afe76b7119`. Its composition is `catalog/domains/composition.yaml`, named `home`; it includes lights, air, media, comfort, scenes, timers, agenda, music, habits, glow and persona under a director. There is no `nina-live/domains/home` directory in this checkout.

This is a design compatibility assessment against the existing manifests and interface, not a successful composition link. Candidate predicates are local simulation vocabulary, not approved shared interface names. No fictional observation is translated into a real command.

| Chapter | Existing boundary | Missing contract / review question |
|---|---|---|
| I | `timers` supports scene-triggered reminders; `agenda` carries calendar events/to-dos | A return **from this appointment** differs from any `home` mode transition. Needs event identity, freshness and retained promise ownership. Kettle evidence needs an actual observation source; the fiction does not grant a sensor. |
| II | `air` has reported power beliefs and commands; `scenes` sends `scene_air`, `scene_music`, `scene_timers`; `music` can duck during speech | Work concentration is not presence. Quiet-work is not an existing `home/night/away` scene. Define consent, nonzero-air constraints, critical-notification exceptions, command/report correlation and manual-override evidence before integration. |
| III | `music` handles household taste/radio; `habits` stores request history | Guest identity, tentative visitor preferences, consent/retention, private disclosure and corrected inventory require separate contracts. Never map a guest preference into household taste implicitly. |
| IV | `agenda` is the calendar boundary; `persona` can react to distress | Dismissed briefing and silence must not become a `distress` fact. Sourced reports can revise explanations without changing observations. Unread channels remain unknown. |
| V | No research-budget/permission specialist is named in `home` | Autonomous research needs a scoped capability, measurable budget, cancellation and obligation preemption. The fictional one-token budget is not a runtime cost model. |
| VI | `agenda`, `timers`, scene orchestration | Dinner commitment, dependencies and recipe plans are richer than timers. Changed circumstances should offer reconsideration; only fresh consent changes a plan. Human messaging needs explicit permission. |
| VII | `persona`, `glow`, `scenes`, `air`, `timers` | Separate expressive mood from obligations. A voice-session end must not stop persistent cognition. Night ventilation needs existing authorization; the chapter does not state its grant. |
| VIII | Each specialist's host and persistence/reconciliation boundary | Checkpoint age, missing events, reminder completion and fresh device reports need epochs and source identity. A restore request is not confirmed restoration. No invented offline history. |

Existing shared `home` interface predicates are scene and mood wishes; the director routes them. None of the new epistemic, promise or consent predicates has an interface owner or host publisher yet. Interface/link checks for an integrated package therefore remain **not run**, not implicitly passed. Before a deployment proposal, an architect must name those owners, typed messages, consumption rights and freshness rules; then a new gate should exercise the real composition and its goldens.

The chapter sketches intentionally omit low-level device actuation. They should be consolidated into reusable candidate units only after the reviewers agree on the important distinctions. The shared `mechanisms` experiment starts that consolidation for situations and commitments without overriding any existing home rule.
