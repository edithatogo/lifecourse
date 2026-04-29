# Core API Contract

This directory contains the language-neutral request and response contract
schemas used by the maintained `lifecourse` Python implementation and future
bindings.

The canonical schema files are generated from
`src/lifecourse/model_contract.py` and stored under `schemas/v1/`.

Human-readable examples live under `examples/v1/` and deterministic fixture
pairs live under `fixtures/v1/`.

The contract is intentionally small:

- request and response models for model execution
- engine metadata and capabilities
- seed policy, analysis options, artifacts, and diagnostics

Artifact metadata rules are documented in
[docs/interchange/artifact_formats.md](../../docs/interchange/artifact_formats.md).

The embedded HEOML profile remains the portable artifact layer. This core API
contract defines the execution surface that produces those artifacts.
