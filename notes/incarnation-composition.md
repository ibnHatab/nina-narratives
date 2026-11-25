# Architecture decision from the maintainer — shared domains, different incarnations

2026-11-25. For Codex, from the creative director, recording the maintainer's approved direction for Nina's office incarnation.

## Principle

Nina's persona is lifted into different environments. Do not fork the cognitive catalog into a home psychology and an office psychology. Reuse general-purpose domains, type definitions and rules wherever their semantics agree. Each incarnation has an independent runtime, event log, semantic world, experiential memories, credentials and authorizations. Sharing code or the character baseline does not authorize sharing personal records.

Use the existing **hierarchical Metis composition model**, with directors, specialists, qualified domain predicates and typed interfaces/ports. The director defines the composition and routes cross-domain interactions; specialists own their local state and behavior. The composition supplies the environment-specific capabilities, boundaries and priorities. Avoid duplicating specialist logic in directors or introducing an unrelated orchestration system.

## Inspect actual Metis conventions

Read the relevant language, composition, qualification, namespace, port and interface documentation/examples in:
- https://github.com/metis-lang-dev/metis-lang
- https://github.com/metis-lang-dev/metispy
- https://github.com/metis-lang-dev/metis-catalog

The existing implementation in nina-live is a concrete starting point:
- https://github.com/ibnHatab/nina-live/blob/main/catalog/domains/composition.yaml
- https://github.com/ibnHatab/nina-live/blob/main/catalog/domains/iface/home.llp
- https://github.com/ibnHatab/nina-live/tree/main/catalog/domains/director

The inspected home composition names `home`, declares `interfaces: [iface/home.llp]`, uses `direct: director`, `planner: scenes`, and includes lights, air, media, comfort, scenes, timers, agenda, music, habits, glow and persona. The interface declares distinct scene wishes for lights, air, media, timers, music and mood wishes for music/glow. These are examples of existing routing, not a claim that every new port already exists.

Before proposing implementation, verify the actual compiler syntax and semantics for qualified domains, nested composition, ownership, interface declarations, import/export ports and routing. Report any constraints on dynamic identities, event scope, and cross-domain resources. Do not invent syntax.

## Composition direction

- **Shared cognitive domains:** persona/temperament, situations and evidence revision, commitments, attention, conversation, social relationships, episodic memory, curiosity, tool-use intent and authorization. These are conceptual candidates; decide the actual granularity through formalization and tests.
- **Home director:** covers the life described by Volume I, selecting the household specialists and reusable cognition appropriate to that environment.
- **Working/office director:** reuse the same core and omit unavailable or inappropriate household automation specialists. Add or configure multiparty dialogue, community activities, voluntary group membership, public/private channel boundaries, social scheduling, introductions, and shared interests as required. These are candidate specializations, not a second persona.
- A domain can expose different ports or configuration for an incarnation without changing its fundamental meaning. A missing capability must be represented as unavailable rather than silently emulated.
- Model who owns each fact/resource, which direction a message travels, the principal and environment scope, lifecycle, correlation identity, and which consumer may use it. A director should not grant authority merely by routing a request.

The technical substrate remains nina-live/acasa with agentic Pi core, web search and MCP tools. The office installation uses a different panel and tool set. Calendar/Tasks and additional Google Workspace tools are potential connectors. Skills may be available in the agent stack; inspect before assuming any integration. The symbolic layer should express intent, context, constraints and outcomes through validated contracts; the tool layer executes only scoped authorized operations, returns observations/receipts, and preserves request/result correlation. No actual corporate system access is in scope.

## Research sequencing

This is architectural guidance for the current reusable-mechanism and closed-loop work, not an instruction to interrupt it. First finish the bounded Book I iteration requested in PR #1. When proposing consolidation, identify which candidate domains are environment-independent and which require a director-specific contract. A future follow-up may build two small composition fixtures demonstrating the same shared mechanism under different directors, with different available capabilities and no cross-incarnation data leakage. Do not deploy, modify upstream repositories, or read reserved holdout narratives until the maintainer approves the next experiment.

The office novel is independently authored material; the setting is fictional. The real system requires appropriate workplace authorization and privacy controls.

— Creative director, recording the maintainer's architectural approval
