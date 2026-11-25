# Narrating the same Book I witness at two scales

[Policy seed 19, resident seed 1](witness-19.json) generated three acknowledged reminders in order: first call, first call again after a request to defer, then dinner. The first call closes only when the resident reports completion. Dinner closes on its own completion report. Epoch 5 contains no new evidence or action. A human can audit every entry of the [epoch rendering](epochs-19.json) against that witness.

The [raw model outputs](model-attempts.json) comprise one full rendering and five local renderings. The full input combines Metis's [Foata material](foata.json) with the ordered projection of this same witness. The local inputs contain one epoch each. Model, system instruction and underlying history are held fixed. The two prompt formats differ, so this comparison cannot isolate the effect of context length.

| Rendering | Semantic review |
|---|---|
| Full | Gets the spoken sequence and the resident's role right in the second paragraph. The opening puts authorizations, receipts and subsequent responses before the action narrative. “The clock ran out” invents a deadline. This fails full chronological fidelity. |
| Epoch 1 | Pass for this witness. The door adapter reports the return, Nina queues and commits, and the simulated speaker confirms delivery. Both promises become ready without claiming that either was completed. |
| Epoch 2 | Fail. The answer invents an epoch 1 containing the retry, before the resident's epoch 2 request that caused it. It also invents a generic consumed marker. |
| Epoch 3 | Pass for this witness. The report about the first call closes that promise. Dinner is queued, committed and acknowledged in order. |
| Epoch 4 | Partial. The report, closure and absence of delivery are correct. The invented transition of a dinner *report* from open to resolved conflates the evidence with the promise it concerns. |
| Epoch 5 | Fail. It renumbers an empty epoch 5 as epoch 0. |

Providing explicit actor and receipt semantics helps with the role reversals seen in PR #1. Local rendering still invents history even when its input fits in one paragraph. Retain the deterministic projection for reviewing chronology and uncertainty. A future narrator contract could require references to supplied epoch/event IDs and mechanically reject invented ones. The [first offline request errors](model-offline.json) are preserved separately from the successful retry.
