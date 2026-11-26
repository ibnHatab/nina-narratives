# Chapter 8: The missing hours

Candidate mechanism, awaiting editorial and integration review. Source: `narratives/book-01-small-universe-of-home.md` at `94e2c5829e6ebefa3bd41e35e513bba943dc8e12`, Chapter 8. No canonical prose was changed.

## Source scenes

- `B01-C08-S01`: “There were no events from which to remember them.”; “I don't know what happened while I was offline.”
- `B01-C08-S02`: “an activity he had already completed.”; “The other was still relevant.”
- `B01-C08-S03`: “after their connection became reliable.”; “She restored the authorized household settings”
- `B01-C08-S04`: “a reasonably good one for things that did.”

## Evidence and scope

The chapter reports successful restoration; the request/confirmation split is a proposed host contract. No invented events fill the offline gap. Persistence, clock reconciliation and exactly-once delivery across an actual restart are outside this in-memory simulation.

`cases.json` supplies fictional observations and explicit human choices in time order. Initial state is a scenario assumption. `hypothesis_*` atoms are interpretations, never observations or hidden truth. Outputs are simulated decisions or receipts, not household actions. No fitted weights: the kernel defaults are uncalibrated scheduling weights; sample frequencies are not empirical probabilities.

The `authored` case checks the represented chapter events. Other cases are derived controls, not independent held-out stories. The host checks required and forbidden atoms at each quiescent phase boundary; the complete run has a 128-event cap. The three seeds can change independent-event ordering; they do not establish rich narrative diversity.
