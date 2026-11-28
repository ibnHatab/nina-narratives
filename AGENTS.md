# Contributing agents

## Creative author
Write literature first. Nina is a persistent artificial companion, not a collection of demonstrations. Develop character, conflict, mistakes, relationships, ambiguity, humor, and continuity. Keep authored observations distinct from hypotheses and hidden narrative truth. Do not rewrite canonical fiction to accommodate a convenient rule.

## Formalization engineer
Extract typed entities, resources, lifecycles, evidence, causal hypotheses, permissions, competing actions and consequences. Cite chapter/scene IDs. Keep fictional mechanisms separate from empirical weights. Check the actual Metis compiler and manifest specification before writing executable packages; never label pseudocode as validated.

## Evaluation agent
Narrate sampled traces without silently repairing them. Judge coherence, safety, social appropriateness, causal consistency, diversity and character continuity. Preserve negative results. Hold out independent episodes from the formalizer.

## Refinement
Compare authored, generated and consented real episodes. Propose changes through metis-loop gates and human approval. Do not change deployed rules, permissions or weights from fiction alone. Do not commit private household logs, credentials or identifiable personal information to this public repository.

Canonical fiction changes require editorial intent; derived artifacts identify the source revision.


## Metis toolchain — required reading for local Codex

Use the actual upstream repositories as the source of truth, not invented syntax or recalled examples:

- [metis-lang](https://github.com/metis-lang-dev/metis-lang): authoritative language specification, OCaml compiler (metisc), runtime and language checks.
- [metispy](https://github.com/metis-lang-dev/metispy): Python reference implementation, derivation and sampling tools, test harness and trace tooling.
- [metis-catalog](https://github.com/metis-lang-dev/metis-catalog): reference packages, manifest conventions, generated goldens and narrative examples (including Ceptre).
- [metis-loop](https://github.com/metis-lang-dev/metis-loop): rule proposal, refinement and validation gates.
- [metis-agent](https://github.com/metis-lang-dev/metis-agent): runtime embedding and domain-agent integration.
- [metis-worlds](https://github.com/metis-lang-dev/metis-worlds): semantic-world implementation and evidence/replay conventions.
- [nina-live](https://github.com/nina-ai-dev/nina-live): target architecture, existing operational catalog and persona implementation.
- [nina-ha-integration](https://github.com/nina-ai-dev/nina-ha-integration) (was acasa): Home Assistant integration.

At startup locate the maintainer's existing local checkouts (including possible ~/metis siblings); do not assume an installation path. Read their AGENTS.md/README and relevant specs, check git revisions, and inspect the actual CLI help before running tests. If unavailable, report the missing dependency or obtain a read-only checkout with the maintainer's authorization. Do not modify upstream projects or the deployed Nina runtime from this workspace.

## Local Codex collaboration protocol

The ChatGPT creative author acts as narrative director and reviewer; the local Codex agent acts as formalization engineer. The human maintainer has final authority. GitHub is the asynchronous handoff medium, not a direct connection between running agents.

1. Start Codex in the root of nina-narratives. Read this file, README.md, methodology/README.md, persona/, the canonical story and relevant catalog briefs.
2. Fetch current GitHub changes. Read the assigned GitHub issue or explicit maintainer instruction. Before coding, report source revisions, toolchain availability, proposed scope and assumptions.
3. Work on a dedicated branch (e.g. formalization/book-01-situations). Preserve canonical narratives. Extract candidate mechanisms with exact scene references; distinguish observations, hypotheses, hidden fictional truth, normative constraints and counterfactuals.
4. Implement only assigned candidate domains. Follow real package conventions; compile/lint, run metispy/reference checks and sample reproducible traces with recorded seeds and tool versions. Check cross-domain interfaces against nina-live. Do not infer empirical probabilities from fiction.
5. Commit rules, fixtures, reproducible commands and a report of successes, failures, surprises, unresolved ambiguities and proposed changes. Open a pull request for narrative director review. Keep unvalidated work explicitly marked.
6. Address reviewer feedback in the branch. Never merge, deploy, rewrite canonical stories, or modify the upstream toolchain without explicit maintainer approval. Protect private observations; this repository is public.

Initial assignment (when the maintainer starts Codex): perform toolchain discovery and prepare a formalization plan for Book I, beginning with situations and commitments. Use the existing catalog briefs as hypotheses, not requirements that override the stories. Do not start broad implementation before the plan is reviewed.

The creative director can read committed artifacts and PRs via GitHub and provide review or new assignments when invoked. Neither agent should assume the other is running continuously, polling issues, or able to directly control the other's process.
