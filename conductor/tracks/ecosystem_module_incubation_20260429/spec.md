# Ecosystem Module Incubation

## Overview

Define how `lifecourse` should participate in a health economics and outcomes
research (HEOR) ecosystem without merging unrelated concerns into this
repository. Existing sibling projects already have clear roles:

- `lifecourse`: health-economic simulation, scenario execution, reporting, and
  model-run artifacts.
- `voiage`: Value of Information analysis, EVPI, EVPPI, EVSI, ENBS, and
  VOI-specific metamodel workflows.
- `innovate`: innovation, policy, intervention uptake, diffusion, and network
  adoption modelling.
- `mars`: MARS-style regression splines and surrogate/metamodel support with a
  stable core API that should not be distorted by ecosystem needs.
- `HEOML`: shared artifact and interchange profile, currently embedded in
  `lifecourse` and designed for later extraction.

The missing piece is an incubation policy for additional modules and subtrees
that address HEOR gaps but do not yet belong in `lifecourse`, `voiage`,
`innovate`, or `mars`. Generic modelling ideas are out of scope unless they
directly support cost-effectiveness, HTA, reimbursement, implementation,
uncertainty, evidence, outcomes, or health-policy evaluation workflows.

## Goals

- Identify candidate HEOR modules that could become standalone repositories,
  embedded experimental subtrees, or optional adapters.
- Keep `lifecourse` focused on simulation and health-economic outputs.
- Keep mature sibling projects independent, integrated through artifacts,
  schemas, adapters, and versioned contracts.
- Protect fixed APIs, especially `mars`, from ecosystem-driven scope creep.
- Avoid adding speculative heavy dependencies to core installs.
- Define promotion criteria for moving an idea from notes, to subtree, to
  standalone project, to supported ecosystem integration.

## Candidate Future Modules

These are candidate HEOR modules to evaluate. They are not approved
dependencies or implementation commitments until a track promotes them.

- `heoml`: health-economic model, output, and workflow interchange artifacts.
  This already exists as an embedded subtree and is the strongest candidate for
  extraction into its own repository.
- `lifecourse-engines`: reusable simulation engine interfaces and optional
  static, cohort Markov, continuous-time, DES, agent/network, and hybrid engine
  experiments. This should remain separate from disease-specific cohort logic.
- `evidentia` or `evidencekit`: HEOR parameter evidence synthesis, provenance,
  assumption audit, evidence grading, uncertainty-source metadata, and evidence
  tables.
- `calibrage` or `calibrationkit`: health-economic calibration, validation target management,
  posterior diagnostics, BlackJAX/Optuna workflows, and benchmarked calibration
  recipes that can be reused across disease models.
- `reportkit-he`: publication-ready health-economic report bundles, figure
  registries, table templates, run summaries, and audit appendices.
- `policykit-he`: jurisdiction, reimbursement, budget-impact, implementation,
  and payer-perspective scenario tooling.
- `registrykit`: reference dataset catalogues, DVC/data-versioning conventions,
  jurisdiction packs, and reproducible input bundle validation.
- `workflowkit`: reproducible experiment orchestration, local/CI execution
  recipes, provenance capture, task graphs, and later remote execution support.
- `qualitykit`: shared mutation/property/profiling/contract-test scaffolds for
  Python, Rust, and language adapters.

## Functional Requirements

- Document the recommended ownership boundary for each existing and proposed
  HEOR module.
- Define when a new idea should live in `lifecourse`, an embedded subtree, a
  sibling repository, or a lightweight adapter.
- Require a clear HEOR use case before creating a new module or integration.
- Extend HEOML planning so future ecosystem modules can add namespaced
  extension profiles without changing the HEOML core contract.
- Document how `innovate` and `mars` can integrate without becoming required
  `lifecourse` dependencies.
- Preserve the `mars` core API as stable and fixed; any ecosystem-specific
  support should be through adapters, examples, or optional companion packages.
- Add a promotion ladder from concept to experimental subtree to standalone
  package to supported integration.
- Add dependency rules for advanced modules, including optional extras,
  smoke-CI, Renovate coverage, security checks, documentation, and deprecation
  paths.

## Non-Functional Requirements

- The strategy must reduce architectural coupling, not create a monorepo by
  accident.
- The strategy must stay focused on health economics and outcomes research.
- All ecosystem integrations must be artifact-first where practical.
- Cross-project contracts must be versioned and testable.
- New module names are provisional until a repository is created.
- No new runtime dependency should be introduced by this planning track.

## Acceptance Criteria

- `docs/ecosystem/module_incubation_strategy.md` describes the ecosystem map,
  candidate modules, boundaries, dependency policy, promotion ladder, and first
  recommended tracks.
- `docs/stack_strategy.md` includes the ecosystem-module policy.
- `conductor/tech-stack.md` includes the dependency and incubation guidance.
- HEOML docs mention extension namespaces for modules such as `voiage`,
  `innovate`, `mars`, and future engine/calibration/evidence modules.
- `conductor/tracks.md` links this track.

## Out Of Scope

- Creating new external repositories.
- Adding Git submodules.
- Adding new runtime dependencies.
- Modifying the `mars`, `innovate`, or `voiage` repositories in this track.
- Changing the stable `mars` core API.
- Implementing concrete adapters for the candidate future modules.
