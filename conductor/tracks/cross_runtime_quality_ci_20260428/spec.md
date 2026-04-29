# Cross-Runtime Quality and CI

## Overview

Extend the existing Python quality posture to future Rust, Go, TypeScript, C#,
R, and Julia surfaces. CI should begin with smoke checks and scale to stricter
gates as each runtime becomes production-supported.

## Functional Requirements

- Add workflow sessions or CI jobs for Rust, Go, TypeScript, C#/.NET 11, R, and
  Julia once their scaffolds exist.
- Keep existing Python `uv`, `nox`, `ruff`, `basedpyright`, `pytest`,
  `Hypothesis`, `mutmut`, and `scalene` workflows intact.
- Add language-equivalent gates for formatting, linting, typing/static checks,
  tests, mutation/fuzz/property testing where appropriate, benchmarks, and
  security scanning.
- Extend Renovate configuration for new ecosystems when package manifests are
  introduced.

## Non-Functional Requirements

- Keep CI time bounded by using smoke checks for experimental adapters.
- Avoid mandatory heavyweight benchmarks on every pull request.
- Keep security and supply-chain checks visible before package publication.
- Document unsupported local toolchains clearly rather than silently skipping
  required production checks.

## Acceptance Criteria

- A cross-runtime quality matrix documents tool choices and CI status.
- New runtime manifests are covered by dependency automation.
- Rust, Go, TypeScript, C#, R, and Julia checks are wired once corresponding
  scaffold files exist.
- CI distinguishes experimental smoke checks from release-blocking checks.

## Out Of Scope

- Enforcing full release gates for adapters that are still experimental.
- Introducing a second CI platform without a concrete GitHub Actions limitation.
