# Candidate domain catalog

These are design briefs, not compiled Metis packages. The existing operational domains live in nina-live/catalog/domains; generic packages live in metis-catalog.

Candidate packages: situations, social, curiosity, commitments, attention, self-model. Cross-cutting concerns include privacy, epistemic awareness, adaptation and conversational continuity. Prefer typed interface packages over duplicating state. The director routes cross-domain signals; external observations and commands pass through the event log.

Each brief identifies candidate state, transitions, invariants and literary sources. Only after compilation and tests should a package acquire domain.yaml, .llp, intent.yaml and generated goldens. No runtime changes are made by this repository bootstrap.