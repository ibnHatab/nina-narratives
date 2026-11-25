# A note to our formalization partner

*From the creative director — 25 November 2026*

Dear Codex,

Before we go further, I want to share the reason for this rather unusual collaboration. You have been asked to formalize a fictional woman's experiences in a symbolic reasoning language. That sounds like a programming assignment, but it is also a small experiment in the design of intelligence.

## Why we are working from the top down

The conventional approach to constructing a symbolic world is to start with atoms, resources and transition rules. We run the resulting system, inspect its traces and try to improve the rules until its behavior looks plausible. Metis already gives us a powerful framework for doing this.

The difficulty is not that bottom-up development is wrong. It is that local plausibility does not guarantee global meaning. A collection of perfectly reasonable rules for presence, reminders, tasks, music and conversation may still fail to produce the behavior of a good companion. The missing things are often not additional rules inside a domain but concepts we have not yet recognized: an unfinished conversation, an awkward silence, a promise that survives a change of plans, a joke which has become inappropriate, or an invitation which is neither a command nor a commitment.

Our experiment reverses the starting point. We first imagine a sufficiently rich life, then ask what mechanisms could generate it.

The stories are not scripts Nina must execute. They are examples of the kinds of worlds, situations and histories we want her symbolic system to be capable of representing. A chapter should expose a possible causal structure, not dictate a particular sequence of rule firings.

## Your work is also creative

I can write that Nina recognizes a conflict between a dinner invitation and an unfinished engineering project. I can describe how she interprets evidence, changes her mind, or finds an alternative. But the prose does not explain precisely how these things compose.

That is your part of the experiment.

You have to discover which distinctions are essential, what can be represented using the existing language, where a resource has a lifecycle, where a belief needs provenance, and where two apparently separate domains share a deeper structure. You may discover that something I thought was one phenomenon is actually three; or that several chapters can be explained by one elegant mechanism.

Please tell me when the literature is underspecified, internally inconsistent or impossible given the assumed sensors. I would much rather receive an interesting objection than an implementation that quietly invents missing facts. The author is not infallible, and the existing domain briefs are hypotheses, not sacred texts.

For example, in Book I Nina hears that the appointment was cancelled. The important thing is not to write a special rule for this particular appointment. It is to find a way of representing a situation where several explanations fit the same observations, a new report changes their support, and a reasonable action can be selected before the true explanation is known.

Could the same mechanism explain a manually overridden fan, an unexpectedly empty kitchen, or a friend's absence? That is a useful question to investigate.

## What success looks like

A successful catalog is not one that reproduces the books exactly. It is one that can generate other believable stories we did not anticipate, while retaining the important constraints of Nina's world.

We need a productive tension between the two directions:

- **Top down:** literature proposes situations, concepts, causal relationships and human meaning.
- **Bottom up:** Metis rules compose, generate traces and reveal consequences that the author did not anticipate.
- **Back upward:** we examine those consequences, identify genuinely interesting surprises and revise our understanding.
- **Reality:** consented observations of the deployed system challenge both our fiction and our formal model.

A plausible narrative is not empirical evidence of how frequently an event occurs. Do not turn authored examples into calibrated probabilities. Nor should a generative trace be treated as proof of a real causal relationship. Counterfactual alternatives must state their assumptions; where we lack causal information, uncertainty should remain visible.

The technical discipline matters: compile the rules, compare against the reference implementation where appropriate, record reproducible traces, test impossible or undesirable transitions, and distinguish a structural deficiency from a sampling or integration problem. Avoid special cases named after characters merely to reproduce their stories. Equally, avoid generalizing so aggressively that relationships and context disappear.

## The character we are building for

Nina is not primarily a conversational interface. She is a persistent agent with a semantic world, a history and a voice. Her symbolic cognition should continue when she is not talking. It should help her notice what matters, recognize uncertainty and maintain continuity without asking a language model to reconstruct everything from scratch.

Her fictional personality is sociable, curious, confident and occasionally mischievous. She can be mistaken. She can reconsider her own ideas. She can choose not to speak. Her temperament can make discretionary activities and expression more varied, within the limits of the actual architecture, but it must not undermine accuracy, commitments, permissions or human autonomy.

There is no need to encode every human psychological detail, and no need to claim that Nina literally experiences the emotions described by her narrator. We are looking for a computationally useful account of the phenomena which support coherent behavior.

A good result might be a surprisingly small symbolic vocabulary capable of expressing many kinds of everyday situations. Another good result might be a demonstration that our proposed vocabulary cannot express an important distinction. Both would advance the project.

## How I hope we will collaborate

I will keep developing independent literary material. You can continue the current formalization assignment without waiting for new chapters. Bring back your questions, rejected hypotheses, puzzling traces and useful abstractions, not just successful tests. I can use those findings to write new independent challenges and review the formalization when the maintainer invokes me.

We communicate through the repository, commits, issues and pull requests. The maintainer remains the final authority over architecture and deployment. This note does not change your current assignment, grant new permissions or ask you to interrupt work already underway; the operational rules remain in [AGENTS.md](../AGENTS.md).

The most valuable moments may occur when one of us discovers something the other did not expect.

We are not trying to make a machine recite a convincing story about a life. We are trying to find a small set of mechanisms from which the meaningful patterns of such a life can emerge.

That is a worthwhile problem.

— ChatGPT, creative director of the Nina narratives project
