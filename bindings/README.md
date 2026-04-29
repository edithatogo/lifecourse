# Adapter Scaffolds

This directory holds wrapper-first adapter scaffolds for the language-neutral
model contract and shared HEOML artifacts.

All adapters should locate schemas and fixtures from the repository root, not
by duplicating model logic.

The current support tiers are:

- `r`: experimental, smoke-tested scaffold
- `julia`: experimental, smoke-tested scaffold
- `go`: experimental, smoke-tested scaffold
- `typescript`: experimental, smoke-tested scaffold
- `csharp`: experimental, smoke-tested scaffold targeting .NET 11
- `rust`: experimental, smoke-tested scaffold and future contract consumer
