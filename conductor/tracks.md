# Project Tracks

This file tracks all major tracks for the project. Each track has its own detailed plan in its respective folder.

---

- [x] **Track: Establish the modernization foundation: adopt `uv` and `pyproject.toml` as the tooling authority, add strict `ruff` and `basedpyright` gates, enforce `>90%` coverage in CI, and introduce `pydantic v2`/`pandera` validation boundaries.**
  *Link: [./archive/modernization_foundation_20260423/](./archive/modernization_foundation_20260423/)*

---

- [x] **Track: Evaluate and begin safe migration toward polars and JAX/XLA backends while preserving the current numpy/pandas/dask runtime.**
  *Link: [./archive/data_engine_numerical_backend_20260428/](./archive/data_engine_numerical_backend_20260428/)*

---

- [x] **Track: Introduce an optional Polars-backed New Zealand population ingestion path while preserving the default pandas API.**
  *Link: [./archive/polars_population_ingestion_pilot_20260428/](./archive/polars_population_ingestion_pilot_20260428/)*

---

- [x] **Track: Add an explicit optional JAX dispatch hook for distributional net-benefit statistics while preserving default numpy behavior.**
  *Link: [./archive/jax_distributional_statistics_pilot_20260428/](./archive/jax_distributional_statistics_pilot_20260428/)*

---

- [x] **Track: Introduce an optional Polars-backed New Zealand life-table hazard ingestion path while preserving the default pandas/numpy API.**
  *Link: [./archive/polars_life_table_ingestion_pilot_20260428/](./archive/polars_life_table_ingestion_pilot_20260428/)*

---

- [x] **Track: Create deterministic backend benchmark baselines for future Polars, JAX, and Dask migration decisions.**
  *Link: [./archive/backend_benchmark_baseline_20260428/](./archive/backend_benchmark_baseline_20260428/)*

---

- [x] **Track: Migrate selected internal tabular transformations toward Polars where benchmarks justify the change.**
  *Link: [./archive/polars_internal_tabular_migration_20260428/](./archive/polars_internal_tabular_migration_20260428/)*

---

- [x] **Track: Migrate selected pure numerical kernels to optional JAX execution where benchmarks justify it.**
  *Link: [./archive/jax_numerical_kernel_migration_20260428/](./archive/jax_numerical_kernel_migration_20260428/)*

---

- [x] **Track: Decide and pilot the future of Dask orchestration using benchmark and profiling evidence.**
  *Link: [./archive/dask_orchestration_decision_20260428/](./archive/dask_orchestration_decision_20260428/)*

---

- [x] **Track: Evaluate and optionally pilot BlackJAX or Optuna for calibration workflows.**
  *Link: [./archive/advanced_calibration_backends_20260428/](./archive/advanced_calibration_backends_20260428/)*

---

- [x] **Track: Evaluate and pilot optional plotnine migration for selected visualization outputs.**
  *Link: [./archive/plotnine_visualization_migration_20260428/](./archive/plotnine_visualization_migration_20260428/)*

---

- [x] **Track: Add selected reproducibility, dependency, and release automation after backend migration decisions stabilize.**
  *Link: [./archive/repro_release_automation_20260428/](./archive/repro_release_automation_20260428/)*

---

- [x] **Track: Harden CI/CD, workflow management, mutation testing, profiling, dependency automation, typed input boundaries, and architecture documentation.**
  *Link: [./archive/engineering_hardening_20260428/](./archive/engineering_hardening_20260428/)*

---

- [ ] **Track: Define a language-neutral model contract, add cross-language access paths, and migrate selected kernels to Rust over time.**
  *Link: [./tracks/language_bindings_rust_core_20260428/](./tracks/language_bindings_rust_core_20260428/)*

---

- [ ] **Track: Define the language-neutral model contract, schema artifacts, golden fixtures, and Python reference execution surface.**
  *Link: [./tracks/model_contract_schema_20260428/](./tracks/model_contract_schema_20260428/)*

---

- [ ] **Track: Add wrapper-first language adapter scaffolds for R, Julia, Go, TypeScript, C#, Rust, and Python around the stable model contract.**
  *Link: [./tracks/language_adapter_scaffolds_20260428/](./tracks/language_adapter_scaffolds_20260428/)*

---

- [ ] **Track: Migrate selected pure model kernels to Rust incrementally with Python parity, benchmarks, profiling, and safety gates.**
  *Link: [./tracks/rust_kernel_migration_20260428/](./tracks/rust_kernel_migration_20260428/)*

---

- [ ] **Track: Add cross-runtime CI, quality gates, mutation testing, profiling, security checks, and dependency automation for new adapters and Rust code.**
  *Link: [./tracks/cross_runtime_quality_ci_20260428/](./tracks/cross_runtime_quality_ci_20260428/)*

---

- [ ] **Track: Define versioning, release, documentation, support tiers, and governance for contract schemas, adapters, and Rust core migration.**
  *Link: [./tracks/bindings_release_docs_governance_20260428/](./tracks/bindings_release_docs_governance_20260428/)*

---

- [ ] **Track: Create the documentation and stack-readiness plan for markdown hygiene, docs checks, docs tooling, stack policy, and public-surface documentation.**
  *Link: [./tracks/documentation_stack_readiness_20260428/](./tracks/documentation_stack_readiness_20260428/)*

---

- [ ] **Track: Integrate lifecourse with the separate edithatogo/voiage Value of Information library through optional artifact-based adapters and shared VOI schemas.**
  *Link: [./tracks/voiage_integration_20260428/](./tracks/voiage_integration_20260428/)*

---

- [ ] **Track: Create the embedded HEOML interchange profile subtree for portable health-economic model artifacts, schemas, examples, fixtures, governance, and future extraction into its own repository.**
  *Link: [./tracks/heoml_interchange_profile_20260429/](./tracks/heoml_interchange_profile_20260429/)*

---

- [ ] **Track: Define a HEOR ecosystem module incubation strategy for sibling projects and future subtrees beyond lifecourse, voiage, innovate, and mars.**
  *Link: [./tracks/ecosystem_module_incubation_20260429/](./tracks/ecosystem_module_incubation_20260429/)*

---

- [ ] **Track: Add the HEOR module naming brainstorm for `calibrate`, `evidence`, `process`, `report`, `registry`, `workflow`, `quality`, `engines`, `heoml`, and PM4Py-as-ecosystem-only.**
  *Link: [./tracks/heor_module_naming_brainstorm_20260429/](./tracks/heor_module_naming_brainstorm_20260429/)*

---

- [ ] **Track: Add parameter provenance, evidence metadata, source traceability, and assumption audit outputs for health-economic model inputs.**
  *Link: [./tracks/evidence_parameter_provenance_20260428/](./tracks/evidence_parameter_provenance_20260428/)*

---

- [ ] **Track: Introduce a modular simulation-engine architecture supporting discrete-time microsimulation now and future continuous-time, Markov, static, DES, and hybrid model approaches.**
  *Link: [./tracks/simulation_engine_modularity_20260428/](./tracks/simulation_engine_modularity_20260428/)*

---

- [ ] **Track: Refactor toward a multi-cohort architecture with disease-specific strategy modules and cohort-specific parameter packages.**
  *Link: [./tracks/multi_cohort_architecture_20260428/](./tracks/multi_cohort_architecture_20260428/)*

---

- [ ] **Track: Add richer genomic testing pathway modelling for test types, counseling, VUS, incidental findings, uptake, and cascade testing.**
  *Link: [./tracks/genomic_testing_pathways_20260428/](./tracks/genomic_testing_pathways_20260428/)*

---

- [ ] **Track: Add calibration targets, external validation checks, baseline comparison artifacts, and acceptance thresholds for model credibility.**
  *Link: [./tracks/validation_calibration_targets_20260428/](./tracks/validation_calibration_targets_20260428/)*

---

- [x] **Track: Create real documentation content for the Starlight documentation site, configure all plugins (polyglot, versions, links-validator, llms-txt), create the migration conductor track, and deploy to GitHub Pages.**
  *Link: [./tracks/migrate_starlight/](./tracks/migrate_starlight/)*
  *completed: 2026-05-17*

---

- [x] **Track: Migrate documentation site from markdown-first to Starlight with automated API reference, link validation, versioning, LLM export, and GitHub Pages CI/CD.**
  *Link: [./tracks/starlight_migration_20260513/](./tracks/starlight_migration_20260513/)*
  *completed: 2026-05-17*

---

- [ ] **Track: Create reproducible analysis bundles with run manifests, checksums, assumption audits, output indexes, and publication-ready reporting artifacts.**
  *Link: [./tracks/reproducible_reporting_bundle_20260428/](./tracks/reproducible_reporting_bundle_20260428/)*
