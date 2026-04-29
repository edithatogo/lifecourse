# Ecosystem Module Incubation Strategy

## Purpose

The health economics and outcomes research (HEOR) ecosystem should grow through
focused sibling projects and well-scoped subtrees, not by turning `lifecourse`
into a catch-all package. `lifecourse` should remain the health-economic
simulation and reporting package. Adjacent methods, interchange formats,
diffusion models, surrogate models, operational modelling, workflow utilities,
and quality tooling should integrate through versioned artifacts and adapters
only when they support HEOR use cases such as cost-effectiveness analysis, HTA,
reimbursement, implementation, uncertainty quantification, evidence synthesis,
operational flow modelling, or health-policy evaluation.

The gap this ecosystem addresses is not generic modelling. It is the lack of a
coherent, open, interoperable software stack for health economics and outcomes
research.

## Current Ecosystem Map

- `lifecourse` owns disease and policy simulation, scenario execution,
  health-economic outcomes, PSA outputs, reporting bundles, and model-run
  provenance.
- `voiage` owns Value of Information analysis, EVPI, EVPPI, EVSI, ENBS,
  VOI-specific study designs, VOI metamodels, and VOI result objects.
- `innovate` owns intervention uptake, innovation diffusion, policy adoption,
  implementation spread, and network-style adoption dynamics.
- `mars` owns MARS-style regression splines and surrogate/metamodel APIs. Its
  core API should remain stable; ecosystem-specific use should happen through
  adapters, examples, or companion packages.
- `HEOML` owns portable health-economic model and output artifacts. It is
  currently embedded in `lifecourse` so it can mature against real outputs, but
  it should later become an independent specification repository.

## Recommended Candidate Modules

These names are provisional. They describe HEOR boundaries, not immediate
repository creation decisions. A module should not be created in this ecosystem
unless it has a clear health economics, outcomes research, HTA, evidence,
implementation, or health-policy evaluation role.

### `lifecourse-engines`

Reusable simulation engine interfaces and experimental engine implementations.
This would be the right home for static decision models, cohort Markov models,
continuous-time models, discrete-event simulation, agent/network simulation,
and hybrid engines once those concepts are ready to move beyond planning. DES is
the natural fit for operational modelling, pathway timing, queues, capacity,
and waiting-time questions.

Keep current disease-specific logic in `lifecourse`; keep general engine
contracts and experimental engines outside the disease package once they start
to accumulate their own dependencies.

### `evidentia` or `evidencekit`

Evidence provenance, parameter source metadata, assumption audits, evidence
grading, uncertainty-source classification, evidence tables, and traceability
reports for HEOR models. This is likely reusable across `lifecourse`, future
disease models, and HEOML bundles.

### `calibrage` or `calibrationkit`

Reusable calibration and validation tooling for health-economic and outcomes
models: target datasets, calibration recipes, posterior diagnostics, Optuna
workflows, BlackJAX workflows, external validation reports, and calibration
bundle schemas. Keep it separate if the workflow becomes reusable across
disease models or has heavy Bayesian/search dependencies.

### `reportkit-he`

Publication-ready health-economic report generation: table templates, figure
registries, audit appendices, standard run summaries, and model-review packs.
This should consume HEOML bundles rather than importing simulation internals.

### `treeage-feature-map`

A feature reference map for TreeAge-style decision-tree, Markov, and
operational-model capabilities. This is a planning artifact, not an
interoperability target or a core maintained package dependency. Use it to
compare scope, outputs, and feature coverage when designing HEOR modules or
simulation engines.

### `policykit-he`

Jurisdiction, payer, reimbursement, budget-impact, implementation, and policy
scenario tooling. This becomes useful if policy configuration grows beyond
simple `lifecourse` scenario definitions.

### `registrykit`

Reference dataset catalogues, jurisdiction packs, DVC conventions, file
checksums, data dictionaries, and input-bundle validation. This should stay
artifact-oriented and should not own scientific model logic.

### `workflowkit`

Reproducible experiment orchestration, local and CI task graphs, provenance
capture, workflow manifests, and later remote execution support. This should
start as recipes or templates before becoming a package, because workflow
engines can impose heavy operational choices.

### `qualitykit`

Shared quality scaffolds for Python, Rust, and language bindings: mutation-test
configuration, property-test invariants, contract-test fixtures, profiling
workloads, schema-validation checks, and release-quality templates.

## Where New Work Should Live

- Put work in `lifecourse` when it directly changes maintained simulation,
  model outputs, disease/cohort logic, reporting bundles, or supported CLI/API
  behavior.
- Put work in `heoml/` when it defines portable artifact fields, schemas,
  examples, validators, or interchange governance that must be tested against
  `lifecourse` outputs before extraction.
- Put work in a sibling project when it has an independent HEOR audience, public
  API, dependency profile, release cadence, or reuse story.
- Put work in an adapter when it only translates artifacts between two mature
  packages.
- Keep work as a design note when the dependency burden, API boundary, or user
  need is still unclear.
- Reject or defer work that is generally useful for modelling but does not
  materially support HEOR workflows.

## Incubation Ladder

1. Design note or Conductor track: clarify scope, owner, dependency risk,
   expected users, and artifacts.
2. Embedded subtree: use only when real schemas, examples, fixtures, or docs
   need to mature next to `lifecourse` outputs before extraction.
3. Standalone repository: promote when the contract, fixtures, validation,
   documentation, and release ownership are stable enough to survive outside
   `lifecourse`.
4. Optional integration: add a `lifecourse[...]` extra or adapter only after
   compatibility tests, version policy, docs, and CI smoke coverage exist.
5. Supported integration: promote only after numerical or artifact parity tests,
   examples, changelog policy, and deprecation rules are in place.

## Dependency Rules

- Do not add speculative ecosystem dependencies to `lifecourse` core.
- Use optional extras for `voiage`, `innovate`, `mars`, and future modules.
- Require Renovate coverage, smoke CI, security checks, documentation, and a
  removal path for each optional dependency.
- Require fixed fixtures and schema validation before cross-project contracts
  are described as stable.
- Prefer artifact exchange over direct Python imports for mature boundaries.
- Keep async for orchestration, remote execution, progress streaming, and
  subprocess/service adapters; do not use async to solve CPU-bound kernels.

## HEOML Extension Model

HEOML should keep a small core profile for portable health-economic run
bundles. Sibling modules should extend it through namespaced extension profiles,
for example:

- `heoml.extensions.voiage`: VOI handoff and VOI result metadata.
- `heoml.extensions.innovate`: uptake, adoption, diffusion, and policy-spread
  artifacts.
- `heoml.extensions.mars`: surrogate/metamodel references, training metadata,
  validation metrics, and response-surface artifact links.
- `heoml.extensions.engines`: engine-specific traces for Markov,
  continuous-time, DES, agent/network, and hybrid models.
- `heoml.extensions.evidence`: parameter evidence, source traceability, and
  assumption audit artifacts.
- `heoml.extensions.calibration`: calibration targets, priors, posterior
  diagnostics, and validation reports.

Extension schemas should declare version, owner, status, artifact references,
compatibility, and whether the fields are stable, experimental, or deprecated.

## Recommended First Follow-Up Tracks

- HEOML extraction readiness: validators, fixture bundles, extension namespace
  governance, and standalone repo criteria.
- Engine incubation: define the minimal engine protocol before implementing
  static, Markov, continuous-time, DES, agent/network, or hybrid engines.
- Operational modelling and TreeAge feature mapping: document which
  decision-tree, Markov, and operational-model features should be reflected in
  the ecosystem taxonomy, especially for DES and other pathway-oriented
  engines.
- Evidence provenance module: decide whether evidence metadata remains inside
  `lifecourse` or becomes a reusable sibling package.
- Calibration module: decide whether BlackJAX/Optuna workflows should live in
  `lifecourse` or a reusable calibration package.
- Ecosystem compatibility fixtures: small shared bundles proving that
  `lifecourse`, `voiage`, `innovate`, `mars`, and HEOML can exchange artifacts
  without importing internals.
- HEOR naming brainstorm: shortlist `calibrate`, `evidence`, `process`,
  `report`, `registry`, `workflow`, `quality`, `engines`, and `heoml`; keep
  PM4Py in the ecosystem-only process-mining bucket; require a CLI surface for
  every future module and an explicit MCP decision where orchestration matters.
