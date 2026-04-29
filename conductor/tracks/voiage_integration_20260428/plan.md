# `voiage` Integration Plan

## Phase 1: Contract And Boundary

- [ ] Task: Add tests for VOI artifact schema expectations.
    - [ ] Cover net-benefit matrix shape, strategy names, parameter samples, WTP thresholds, population, time horizon, discount rate, and provenance.
    - [ ] Cover invalid or misaligned sample counts with clear diagnostics.
- [ ] Task: Define the `lifecourse` VOI artifact contract.
    - [ ] Keep the contract compatible with `voiage.ValueArray` and `voiage.ParameterSet`.
    - [ ] Use JSON for metadata and Arrow/Parquet or CSV for tabular artifacts according to the model contract policy.
    - [ ] Place the VOI contract inside the broader run-bundle interchange profile.
    - [ ] Align the run-bundle profile with HEOML as the shared portable artifact layer.
    - [ ] Explicitly reject pickle as a portable interchange format.
- [ ] Task: Document project ownership boundaries.
    - [ ] `lifecourse` owns simulation outputs and run bundles.
    - [ ] `voiage` owns VOI algorithms, method settings, and VOI result objects.
    - [ ] Link to the corresponding `voiage` Conductor track, docs, and `specs/integrations/lifecourse/v1/` scaffold.
- [ ] Task: Document existing interchange standards and fit.
    - [ ] Record why ONNX, PMML, and PFA are not primary formats for this health-economic model.
    - [ ] Record why PharmML and OMOP CDM are useful references but not direct replacements for the bundle contract.
    - [ ] Record where TreeAge-style feature mapping may be useful later.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Contract And Boundary' (Protocol in workflow.md)

## Phase 2: Optional Adapter Scaffold

- [ ] Task: Add optional-import adapter tests.
    - [ ] Verify missing `voiage` raises actionable installation guidance.
    - [ ] Verify installed `voiage` can receive a minimal fixed fixture.
- [ ] Task: Implement a thin `lifecourse` adapter for `voiage`.
    - [ ] Convert net-benefit arrays to `voiage.ValueArray`.
    - [ ] Convert parameter samples to `voiage.ParameterSet`.
    - [ ] Call only stable public API functions such as `evpi`, `evppi`, `evsi`, and `enbs`.
- [ ] Task: Add optional dependency wiring.
    - [ ] Add a `voi` or `voiage` optional extra only after the dependency target and version policy are settled.
    - [ ] Keep base install unchanged.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Optional Adapter Scaffold' (Protocol in workflow.md)

## Phase 3: Parity And Promotion Evidence

- [ ] Task: Add EVPI and EVPPI parity fixtures.
    - [ ] Compare internal `lifecourse` outputs and `voiage` outputs under fixed seeds.
    - [ ] Define numeric tolerance and scaling rules.
- [ ] Task: Add EVSI and ENBS validation fixtures when study-design data exists.
    - [ ] Keep EVSI experimental until method assumptions and input contracts are documented.
- [ ] Task: Add benchmark and dependency impact checks.
    - [ ] Compare internal and `voiage` runtime on representative PSA outputs.
    - [ ] Measure dependency impact of the optional extra.
- [ ] Task: Decide backend status.
    - [ ] Keep `voiage` experimental unless parity, docs, CI, and dependency split are sufficient.
    - [ ] Promote only after acceptance criteria are satisfied.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Parity And Promotion Evidence' (Protocol in workflow.md)

## Phase 4: Reporting And Documentation

- [ ] Task: Add `voiage` provenance to reporting bundles.
    - [ ] Include package version, method, backend, method settings, scaling metadata, and diagnostics.
    - [ ] Include the HEOML profile version and manifest identifier where available.
- [ ] Task: Add portable interchange bundle docs.
    - [ ] Document manifest, schemas, inputs, parameters, scenarios, outputs, diagnostics, figures, and VOI directories.
    - [ ] Document JSON, JSON Schema, Arrow/Parquet, CSV, and figure artifact responsibilities.
    - [ ] Document pickle as local-debug-only and non-portable.
- [ ] Task: Add user-facing VOI integration docs.
    - [ ] Explain when to use internal VOI calculations versus `voiage`.
    - [ ] Include install command, minimal example, output interpretation, and limitations.
- [ ] Task: Add contributor docs for cross-repo compatibility.
    - [ ] Explain fixture ownership, version compatibility, and release coordination.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Reporting And Documentation' (Protocol in workflow.md)

## Phase 5: Upstream `voiage` Coordination

- [ ] Task: Propose dependency extras in `voiage`.
    - [ ] Split heavy dependencies such as JAX, NumPyro, scikit-learn, statsmodels, plotting, and CLI tooling into optional extras where practical.
    - [ ] Keep NumPy-based EVPI/EVPPI usable in the lightest install.
- [ ] Task: Propose stable integration result schemas in `voiage`.
    - [ ] Include method name, inputs, assumptions, scaling metadata, diagnostics, and version.
- [ ] Task: Add shared compatibility fixture to `voiage`.
    - [ ] Use a `lifecourse`-style net-benefit and parameter sample fixture.
    - [ ] Verify `voiage` consumes it through public APIs.
- [ ] Task: Align release and compatibility notes.
    - [ ] Document supported `lifecourse` and `voiage` version combinations.
    - [ ] Require changelog notes for public API changes affecting integration.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Upstream voiage Coordination' (Protocol in workflow.md)
