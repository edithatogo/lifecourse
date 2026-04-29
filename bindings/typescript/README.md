# TypeScript Adapter Scaffold

Support tier: experimental, smoke-tested scaffold.

Current package shape:

- `package.json`
- `tsconfig.json`
- `src/index.ts` for the contract wrapper
- `test/contract.test.ts` for fixture-driven smoke tests

Recommended invocation path:

- read request and response JSON Schema from `specs/core-api/schemas/v1/`
- read golden fixtures from `specs/core-api/fixtures/v1/`
- invoke the Python reference contract through CLI or subprocess

Expected checks:

- `tsc`
- fixture-driven smoke test
- generated or checked contract types
