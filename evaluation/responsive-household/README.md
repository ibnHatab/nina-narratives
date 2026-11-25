# What happened after Nina spoke

Two reminders become due when the resident returns from an appointment. There is time to mention one. Which one Nina chooses changes what the resident reports next, and that report changes the next choice. Six responsive runs produced five distinct speech histories. In five runs Nina repeated a reminder at the first opportunity after the resident asked for it later. Both promises eventually closed in all six. Judging only the final states would miss the social failure.

## Two histories from one resident

With resident seed 1 and policy seed 1, Nina mentioned dinner first. The resident reported it done. Nina then mentioned the call. The resident asked for it later. In the same decision epoch as that reply, Nina mentioned the call again. The resident reported the call done in the following epoch. The fourth opportunity passed in silence. [Raw witness](witness-1.json) · [Ordered rendering](epochs-1.json)

With the same resident and policy seed 19, Nina mentioned the call on the return home. The resident asked for it later. Nina immediately spent the next opportunity on the call a second time while dinner was still waiting. Only after the resident reported the call done did she mention dinner. The resident then reported dinner done. The identical final ledger conceals which obligation waited through the repeated interruption. [Raw witness](witness-19.json) · [Ordered rendering](epochs-19.json)

A paired intervention holds the first optional speaking opportunity back. In each of the three quiet controls the resident finishes dinner during the quiet interval and reports it. Dinner is never announced. This causal response belongs to the artificial resident. The experiment supplies no estimate of what a person would do. With resident seed 7 the resident initially wants dinner deferred. Policy seed 7 then serves the call between the two dinner reminders. This is the one responsive history in which a different obligation separates the request for delay from the repeat. [All runs](runs.json)

## What was tested

The OCaml compiler and Python manifest check succeeded. The loop's standalone-base revision gate returned class F, zero findings and zero warnings for its one scenario. Its scope is narrower than the simulator. Lint separately reported seven host-supplied predicates without internal producers. All 48 runs replayed their recorded Metis inputs and firings with zero divergences. Nine exercised resident feedback, including the three quiet controls. The other 39 were boundary controls. The original PR #1 fixtures and failures remain at baseline revision `d4df98ace9b90e942e05d89b2d772612580d8918`. [Gate](gate.json) · [Lint](lint.txt)

| Question | Observed result at policy seeds 1, 7 and 19 |
|---|---|
| Which return releases a promise? | A pre-binding return, unrelated outing and return after cancellation before departure each left both promises waiting. |
| Can an event be delivered twice? | Duplicate return and completion identities produced one projected return and one closure. Completion for a second call instance closed only that instance. |
| What survives restart? | A fresh Metis interpreter restored from a serialized checkpoint retained a valid observed return. Redelivery added no input. An empty observation interval stayed empty. The additional disk-journal probe recovered all five phases through delivery and served the other task next. |
| Where is the speech boundary? | An early completion prevented selection. A completion delivered after queuing and before the grant cancelled the queued reminder. A report received after delivery closed the promise while the earlier speech remained in the witness. |
| What if sources disagree? | Resident completion and checklist pending in either batch order produced a dispute. A later checklist report also reopened a closed promise. A fresh resident confirmation resolved it under the test's source policy. The journal retains both accounts. |

The separate exact kernel probes expose two host obligations. Handing the queued specialist both a completion and a grant in one unordered batch gives commit a one-step marginal of 0.5 at unit weights. Reusing an outing constant makes a previous return sufficient for a new promise with marginal 1. A wrong-instance delivery receipt gives spoken a marginal of 0. These are properties of specific net states. The responsive runs achieve their observed behavior by draining evidence before the grant and reserving an outing identity. [Exact probes and ownership](../../candidates/responsive-household/COMPOSITION.md)

## Narration and objections

The seed-19 witness has 35 fired rows. The built-in Foata projection puts the later retry and both completion inputs in its first beat. The additional epoch projection preserves receipt order and identifies the actor, action and task. For example, epoch 2 records a resident request, a transition to ready, a new queue entry, a commitment and a delivery receipt. The earlier spoken reminder remains part of the history. No marker consumption represents a lost call or a lost object. The deterministic renderer omits empty bookkeeping phases and retains an explicit empty epoch 5. The two prose histories above were checked against those rows. They attribute task closure to a report and claim no independent knowledge of completion. [Foata material](foata.json) · [Epoch material](epochs-19.json)

The initial sandbox could not resolve OpenRouter. A retry on the same saved witness returned all six renderings. The full rendering recovers the three spoken reminders but introduces a deadline. Epoch 2 moves the retry before the resident's request, and epoch 5 becomes epoch 0. Epochs 1 and 3 preserve the observed sequence and actor roles. The proposed upstream change is to carry observation epochs alongside Foata beats and attach speaker, patient and lifecycle semantics to transitions. [Semantic assessment](NARRATOR-REVIEW.md) · [Raw model results](model-attempts.json) · [Initial network errors](model-offline.json)

The resident has one busy task and always complies following one deferral. The model generates plausible short histories but makes recovery too easy. A real request for “later” might mean ten minutes, a particular event or an invitation to discuss timing. The candidate knows none of those. It immediately makes the reminder eligible. A second weakness is that a late cancellation or correction can race an irreversible delivery. The simulated speaker always acknowledges, and the host never retries an ambiguous transport outcome. No crash-between-speech-and-receipt guarantee was tested.

Two nonexclusive explanations of conflicting evidence are retained as hypotheses in dispute phases: the checklist may lag and the reported completion may refer to another task. These labels have no inference weights or independent evidential support. The adapter handles this small vocabulary using the existing semantic-world port difference operation. There is no new probability store. Neither report reliability nor human preferences have been calibrated. Reused identities, out-of-order corrections from the same publisher, persistent consent, private guest contexts, and critical delivery policy remain architectural work. The single opportunity in this model applies only to optional reminders. Critical notices require a separate contract.

## Reproduce from the repository root

The fiction references are B01-C01-S03 (return-triggered promise), B01-C04-S02 (revised explanation), B01-C06-S01 (reminder) and B01-C08-S02 (recovery), fiction revision `94e2c5829e6ebefa3bd41e35e513bba943dc8e12`. The resident and its alternatives are synthetic. No deployed input or reserved narrative was used. The run used Python 3.12.3, metispy 0.2.1 at `51609ca`, metis-lang `5807f7f`, metis-loop `7013647`, catalog `7eb6e7d`, semantic-world from metis-worlds `fba410a`, and metis-agent `1a80e6d`. The local interface reading used nina-live `df1edcd` and acasa `7ca6dfc`.

```sh
toolchain=../perotheia-packages
py="$toolchain/.venv/bin/python"
candidate=candidates/responsive-household
"$py" "$candidate/experiment.py" --metisc "$toolchain/metis-lang/src/metisc"
"$py" -m metis.lint "$candidate/household.llp" --manifest "$candidate/domain.yaml"
"$py" "$candidate/check_boundary.py"
"$py" "$candidate/check_restart.py"
"$py" "$candidate/narrate.py"
```

The optional model comparison uses the repository's configured Metis endpoint and makes six requests. Run it in a fresh results checkout to preserve the original failures.

```sh
(set +x; set -a; . "$HOME/.config/metis/openrouter.env" && "$py" "$candidate/narrate.py" --model)
```

For review, the maintainer needs to decide who assigns and retires outing and task identities, which source can resolve a dispute, what a deferral authorizes, and who owns the commit-to-receipt interval. The reusable candidate is a single standalone specialist. A future director would have to supply those contracts before composition. [Ownership note](../../candidates/responsive-household/COMPOSITION.md)
