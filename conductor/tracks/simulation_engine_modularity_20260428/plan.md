# Simulation Engine Modularity Plan

Documentation scope: architecture, scientific/model, API/contract, and release docs.

## Phase 1: Engine Contract And Taxonomy

- [ ] Task: Add tests for simulation engine metadata and selection.
    - [ ] Cover default engine selection, invalid engine names, seed policy, and diagnostic metadata.
    - [ ] Verify the current discrete-time engine can be selected without changing existing CLI behavior.
- [ ] Task: Document the simulation approach taxonomy.
    - [ ] Compare static decision models, cohort Markov, semi-Markov, individual discrete-time microsimulation, continuous-time simulation, discrete-event simulation, agent-based/network simulation, and hybrid models.
    - [ ] Explain when each approach is appropriate for genomic testing health-economic evaluation.
    - [ ] Call out DES as the operational modelling choice for pathways, queues, waiting times, and capacity constraints.
    - [ ] Call out TreeAge as a feature reference taxonomy rather than a required runtime dependency.
- [ ] Task: Define typed simulation engine interfaces.
    - [ ] Include run inputs, run outputs, artifact metadata, diagnostics, seed policy, and capability declarations.
    - [ ] Keep Dask-specific details behind the current engine implementation.
- [ ] Task: Define simulation-engine dependency policy.
    - [ ] Keep current discrete-time microsimulation dependencies as the only production default.
    - [ ] Classify candidate dependencies for static, Markov, continuous-time, DES, agent-based, network, and hybrid engines as core, optional, experimental, or deferred.
    - [ ] Require optional extras, Renovate coverage, CI smoke checks, and documentation for any new engine package.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Engine Contract And Taxonomy' (Protocol in workflow.md)

## Phase 2: Current Engine Adapter

- [ ] Task: Add parity tests for the current annual discrete-time engine adapter.
    - [ ] Compare direct `run_sim` behavior with registry-mediated execution for fixed seeds.
    - [ ] Cover retrospective and prospective arms.
- [ ] Task: Implement the discrete-time microsimulation engine adapter.
    - [ ] Wrap the current `PopulationSystemDask` and run-helper behavior.
    - [ ] Expose engine metadata and diagnostics through the shared contract.
- [ ] Task: Add engine registry and configuration selection.
    - [ ] Support default selection without requiring users to specify an engine.
    - [ ] Keep CLI parsing thin and delegate to the Python reference API.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Current Engine Adapter' (Protocol in workflow.md)

## Phase 3: Non-Default Engine Scaffold

- [ ] Task: Choose the lowest-risk second engine scaffold.
    - [ ] Prefer a static decision model for diagnostic testing scoping or a cohort Markov scaffold for aggregate state-transition analyses.
    - [ ] Prefer a dependency-free scaffold using existing numerical packages.
    - [ ] Defer continuous-time, DES, and agent-based dependencies until concrete pathway or interaction requirements exist.
- [ ] Task: Add tests for the selected scaffold.
    - [ ] Verify schema compatibility, deterministic outputs, diagnostics, and documentation examples.
- [ ] Task: Implement the selected scaffold.
    - [ ] Keep it experimental and clearly separated from production defaults.
    - [ ] Avoid duplicating disease-specific model logic where the cohort strategy interface should own it.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Non-Default Engine Scaffold' (Protocol in workflow.md)

## Phase 4: Documentation And Promotion Rules

- [ ] Task: Document engine compatibility and promotion criteria.
    - [ ] Define evidence required before a non-default engine can be production-supported.
    - [ ] Document compatibility with cohorts, parameter provenance, model contracts, and output bundles.
    - [ ] Document dependency promotion rules from deferred to experimental extra to production-supported extra.
- [ ] Task: Update architecture docs and user examples.
    - [ ] Show default discrete-time usage and experimental engine selection.
    - [ ] Explain engine limitations and appropriate use cases.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Documentation And Promotion Rules' (Protocol in workflow.md)
