# Chapter 6: The dinner that nearly did not happen

Candidate mechanism, awaiting editorial and integration review. Source: `narratives/book-01-small-universe-of-home.md` at `94e2c5829e6ebefa3bd41e35e513bba943dc8e12`, Chapter 6. No canonical prose was changed.

## Source scenes

- `B01-C06-S01`: “At five forty-five, she mentioned it.”; “Another ten minutes.”
- `B01-C06-S02`: “We can simplify the recipe, or you can tell Elena.”; “Do it.”
- `B01-C06-S03`: “The conflict disappeared.”; “We can restore the original dinner.”; “No, the simple one is fine.”
- `B01-C06-S04`: “They improvised.”

## Evidence and scope

Clock/deadline comparison is supplied by a simulated input, not calculated from the story. Timers, ingredient allocation and notify-Elena execution are not implemented. The two options represent a human decision, not random action weights.

`cases.json` supplies fictional observations and explicit human choices in time order. Initial state is a scenario assumption. `hypothesis_*` atoms are interpretations, never observations or hidden truth. Outputs are simulated decisions or receipts, not household actions. No fitted weights: the kernel defaults are uncalibrated scheduling weights; sample frequencies are not empirical probabilities.

The `authored` case checks the represented chapter events. Other cases are derived controls, not independent held-out stories. The host checks required and forbidden atoms at each quiescent phase boundary; the complete run has a 128-event cap. The three seeds can change independent-event ordering; they do not establish rich narrative diversity.
