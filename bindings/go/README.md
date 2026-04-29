# Go Adapter Scaffold

Support tier: documented scaffold.

Current package shape:

- `go.mod`
- `internal/contract` for the Python contract wrapper
- `cmd/lifecourse-contract` for the CLI entrypoint

Recommended invocation path:

- read request and response JSON Schema from `specs/core-api/schemas/v1/`
- read golden fixtures from `specs/core-api/fixtures/v1/`
- invoke the Python reference contract through CLI or subprocess

Expected checks:

- `go test`
- fixture-driven smoke test
- generated or checked contract structs
