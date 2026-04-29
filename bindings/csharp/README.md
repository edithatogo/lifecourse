# C# Adapter Scaffold

Support tier: experimental, smoke-tested scaffold targeting .NET 11.

Current package shape:

- `LifecourseContract.csproj`
- `Program.cs` for the CLI entrypoint
- `ContractRunner.cs` for the Python contract wrapper
- `tests/LifecourseContract.Tests.csproj` for smoke tests

Recommended invocation path:

- read request and response JSON Schema from `specs/core-api/schemas/v1/`
- read golden fixtures from `specs/core-api/fixtures/v1/`
- invoke the Python reference contract through CLI or subprocess

Expected checks:

- `dotnet test`
- fixture-driven smoke test
- analyzer-friendly project defaults
