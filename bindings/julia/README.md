# Julia Adapter Scaffold

Support tier: experimental, smoke-tested scaffold.

Recommended invocation path:

- read request and response JSON Schema from `specs/core-api/schemas/v1/`
- read golden fixtures from `specs/core-api/fixtures/v1/`
- invoke the Python reference contract through CLI or subprocess

Expected checks:

- `Pkg.test`
- fixture-driven smoke test
- schema-first request construction
