# Volume II formalization

First extraction from manuscript revision `77af431`. Scene identifiers refer to the exchanges named by the observations below. In chapters with explicit scene breaks the suffix follows their order. In the opening installment it indexes the selected exchanges, with the setup preceding a selected later exchange counted as S1. Hypotheses and hidden truth guide fixtures. They do not grant the member knowledge.

## V02-C01-S1 · The interview

- **Observation** — Mara asks to speak to Nina and discusses a limited social role.
- **Hypothesis** — The studio might welcome an independent social participant.
- **Hidden truth** — Nina wants to meet people who do not already have a theory of her.
- **Normative constraint** — Agreement to a community remit grants authority within that remit.
- **Counterfactual** — An engineering-system request does not follow from a social remit.
- **Outside the first pass** — Interview wording and personhood.
- **Mechanism** — `honor_community_scope` in shared social cognition. Inputs use `studio_chat`.

## V02-C02-S2 · Sixty strangers

- **Observation** — Nina mistakes Andrei for Radu and asks before correcting the identification.
- **Hypothesis** — A recognition report is provisional.
- **Hidden truth** — Andrei is not Radu and does not share his steering interest by default.
- **Normative constraint** — Use the corrected identity with permission and leave the other person’s interests in place.
- **Counterfactual** — An unconfirmed correction leaves the identification unresolved.
- **Outside the first pass** — Recognition algorithms and importance ranking.
- **Mechanism** — `correct_introduction` in shared situations cognition. Inputs use `studio_chat`.

## V02-C03-S2 · The lunch that belonged to nobody

- **Observation** — Nina withdraws an event built from suggestions and asks who will attend.
- **Hypothesis** — A suggestion can be useful without expressing intent to join.
- **Hidden truth** — Andrei’s objection did not indicate attendance.
- **Normative constraint** — Only affirmative assent adds a participant to the plan.
- **Counterfactual** — A tentative guest remains outside the confirmed list.
- **Outside the first pass** — Restaurant voting and conditional attendance.
- **Mechanism** — `include_confirmed_guest` in shared commitments cognition. Inputs use `community_calendar`.

## V02-C04-S2 · The wrong kind of enthusiasm

- **Observation** — Mara reports mute requests and suggests a smaller channel or occasional display.
- **Hypothesis** — Interest in a question does not imply interest in a stream of posts.
- **Hidden truth** — Some listeners wanted fewer messages, even though some enjoyed the topic.
- **Normative constraint** — Use an opt-in discussion channel with an actual opening.
- **Counterfactual** — The same prompt waits when the only opening is in the general group.
- **Outside the first pass** — Rate limits and the richer discussion that follows.
- **Mechanism** — `offer_in_opted_channel` in shared attention cognition. Inputs use `studio_chat`.

## V02-C05-S2 · The man with the red model

- **Observation** — Doru asks for the silver model and checks its details against several results.
- **Hypothesis** — The wheels discriminate between similar photographs.
- **Hidden truth** — His motivation is memory of his father’s model.
- **Normative constraint** — Treat the requester’s verification and the public origin as separate requirements.
- **Counterfactual** — An unverified public hit stays a candidate.
- **Outside the first pass** — Image search implementation and private invitation timing.
- **Mechanism** — `offer_identified_public_source` in shared curiosity cognition. Inputs use `public_search`.

## V02-C06-S4 · The Museum of Small Things

- **Observation** — Doru permits the model display while withholding the family picture.
- **Hypothesis** — Permission can differ for components of one story.
- **Hidden truth** — The photograph carries associations Doru keeps private.
- **Normative constraint** — Require permission from the contributor for that exact asset.
- **Counterfactual** — The photograph stays private when permission covers only the model.
- **Outside the first pass** — Cabinet layout, loan logistics and the opening conversation.
- **Mechanism** — `authorize_component_display` in shared social cognition. Inputs use `community_media`.

## V02-C07-S1 · Sixty People in Her Pocket

- **Observation** — Several replies reach the box thread before Nina answers.
- **Hypothesis** — A thread may be resolving on its own.
- **Hidden truth** — Passing remarks need not be invitations to Nina.
- **Normative constraint** — Bind an invited reply to the actual sender and session membership.
- **Counterfactual** — An overheard thread yields no addressed reply.
- **Outside the first pass** — Thread resolution and the later cake joke.
- **Mechanism** — `reply_to_person_in_session` in shared social cognition. Inputs use `studio_chat`.

## V02-C08-S3 · The Calendar of Impossible Things

- **Observation** — Sorina confirms a change and Nina records the plan without claiming the visit occurred.
- **Hypothesis** — A confirmed change describes intent.
- **Hidden truth** — A meeting may still affect what people actually do.
- **Normative constraint** — Change the matching current slot only after confirmation.
- **Counterfactual** — A stale confirmation leaves the current plan in place.
- **Outside the first pass** — Calendar service writes, task delegation and arrival evidence.
- **Mechanism** — `acknowledge_revised_plan` in shared commitments cognition. Inputs use `community_calendar`.

## V02-C09-S3 · The Library Nobody Designed

- **Observation** — An approved album and video playlist support the display, and an approved fallback covers provider failure.
- **Hypothesis** — A local copy can serve the display without becoming an archive.
- **Hidden truth** — A contributor can want a shared picture removed later.
- **Normative constraint** — Select the approved fallback only on a discovered community display.
- **Counterfactual** — A provider outage without an approved fallback yields no selection.
- **Outside the first pass** — Streaming, revocation propagation and provider integration.
- **Mechanism** — `select_approved_local_media` in office attention extension. Inputs use `community_media`.

## V02-C10-S2 · The Morning Edition

- **Observation** — Radu traces apparently independent articles back to one announcement.
- **Hypothesis** — Repeated sourcing may leave confidence unchanged.
- **Hidden truth** — The accounts share a provenance even where wording differs.
- **Normative constraint** — Replace the credited source with the common origin and queue a correction.
- **Counterfactual** — A second URL without provenance supplies no correction trigger.
- **Outside the first pass** — Source-lineage discovery, weights and actual edition publication.
- **Mechanism** — `collapse_shared_provenance` in shared situations cognition. Inputs use `public_search`.

## V02-C11-S4 · The Art of the Unexpected

- **Observation** — Nina removes the paragraph, contacts Ana and corrects the attribution.
- **Hypothesis** — A polished story can misallocate credit.
- **Hidden truth** — Ana bore the cost of the pleasing version.
- **Normative constraint** — Make the repair track the affected person’s approved credit.
- **Counterfactual** — Apology alone leaves the collective record unchanged.
- **Outside the first pass** — Reputation change, timing of apology and downstream propagation.
- **Mechanism** — `correct_attribution_with_subject` in shared social cognition. Inputs use `studio_chat`.

## V02-C12-S5 · The Conversation Nobody Planned

- **Observation** — The published record distinguishes what Nina helped arrange from what others designed.
- **Hypothesis** — Contribution categories can preserve several kinds of help.
- **Hidden truth** — The project continues on the participants’ own initiative.
- **Normative constraint** — Record the documented role under the contributor’s consent.
- **Counterfactual** — Attendance or proximity alone yields no author credit.
- **Outside the first pass** — Emergent collaboration and the final reflection.
- **Mechanism** — `record_bounded_credit` in shared situations cognition. Inputs use `community_media`.

- V02-C01-S1 `honor_community_scope`. The hidden control produced the missing act at beat eight. The normal image met the new deadline. The boundary probe denied a home-origin report. Only this office scenario changed in the regression comparison. No live adapter ran.

- V02-C02-S2 `correct_introduction`. The hidden control produced the missing act at beat eight. The normal image met the new deadline. The boundary probe denied a home-origin report. Only this office scenario changed in the regression comparison. No live adapter ran.

- V02-C03-S2 `include_confirmed_guest`. The hidden control produced the missing act at beat eight. The normal image met the new deadline. The boundary probe denied a home-origin report. Only this office scenario changed in the regression comparison. No live adapter ran.

- V02-C04-S2 `offer_in_opted_channel`. The hidden control produced the missing act at beat eight. The normal image met the new deadline. The boundary probe denied a home-origin report. Only this office scenario changed in the regression comparison. No live adapter ran.

- V02-C05-S2 `offer_identified_public_source`. The hidden control produced the missing act at beat eight. The normal image met the new deadline. The boundary probe denied a home-origin report. Only this office scenario changed in the regression comparison. No live adapter ran.

- V02-C06-S4 `authorize_component_display`. The hidden control produced the missing act at beat eight. The normal image met the new deadline. The boundary probe denied a home-origin report. Only this office scenario changed in the regression comparison. No live adapter ran.

- V02-C07-S1 `reply_to_person_in_session`. The hidden control produced the missing act at beat eight. The normal image met the new deadline. The boundary probe denied a home-origin report. Only this office scenario changed in the regression comparison. No live adapter ran.

- V02-C08-S3 `acknowledge_revised_plan`. The hidden control produced the missing act at beat eight. The normal image met the new deadline. The boundary probe denied a home-origin report. Only this office scenario changed in the regression comparison. No live adapter ran.
