# Language Adapter Scaffolds

## Overview

Add minimal, contract-first access paths for R, Julia, Go, TypeScript, C#,
Rust, and Python. Adapters should call the stable Python contract through CLI,
subprocess, or generated schema clients first. Native bindings are deferred
until the contract and support model are stable.

## Functional Requirements

- Create a clear package layout for language adapters.
- Add minimal examples for R, Julia, Go, TypeScript, C#, and Rust consumers.
- Reuse the contract schemas and golden fixtures from the contract track.
- Prefer wrapper-first access paths before FFI, C ABI, WASM, or handwritten
  native bindings.
- Keep Python as the maintained reference binding and document how other
  adapters invoke it.

## Non-Functional Requirements

- Do not duplicate model logic in adapters.
- Keep scaffolds small enough to run in CI as smoke checks.
- Use idiomatic package/test layout for each language.
- Keep installation assumptions explicit and documented.

## Acceptance Criteria

- Each target language has a scaffold, smoke test, and documented invocation
  path.
- At least one non-Python adapter can run a golden fixture through the contract.
- Adapters do not bypass schema validation.
- Native binding work remains explicitly deferred unless separately justified.

## Out Of Scope

- Publishing packages to CRAN, Julia registry, npm, NuGet, Go module proxies, or
  crates.io.
- Reimplementing model logic outside Python or Rust kernels.
- Promoting native FFI as the default before wrapper parity exists.
