# Rust Adapter Scaffold

Support tier: documented scaffold and future contract consumer.

Current package shape:

- `Cargo.toml`
- `src/lib.rs` for the contract wrapper
- `src/main.rs` for the CLI entrypoint
- `tests/contract.rs` for fixture-driven smoke tests

Recommended invocation path:

- read request and response JSON Schema from `specs/core-api/schemas/v1/`
- read golden fixtures from `specs/core-api/fixtures/v1/`
- invoke the Python reference contract through CLI or subprocess

Expected checks:

- `cargo test`
- fixture-driven smoke test
- serde-compatible request and response models
