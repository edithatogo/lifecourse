# HEOML Extension Namespaces

HEOML v0.1 keeps the core run-bundle profile small. Adjacent health economics
and outcomes research (HEOR) projects should add optional, namespaced extension
profiles instead of changing the core schema for project-specific needs.

Initial reserved namespaces:

- `heoml.extensions.voiage`: Value of Information handoff and result metadata.
- `heoml.extensions.innovate`: health-intervention uptake, adoption,
  implementation diffusion, and policy-spread artifacts.
- `heoml.extensions.mars`: surrogate or metamodel references, training
  metadata, validation metrics, and response-surface artifacts.
- `heoml.extensions.engines`: static, Markov, continuous-time, DES,
  agent/network, and hybrid engine traces.
- `heoml.extensions.evidence`: parameter sources, assumption audits, and
  evidence provenance.
- `heoml.extensions.calibration`: calibration targets, priors, posterior
  diagnostics, and validation reports.

Each extension profile should define:

- owner and status
- extension schema version
- compatible HEOML core versions
- artifact references and checksums
- required and optional fields
- stability labels for experimental, stable, and deprecated fields

Extensions should be consumable without importing `lifecourse` internals.
