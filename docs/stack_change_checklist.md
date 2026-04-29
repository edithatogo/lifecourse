# Stack Change Checklist

Use this checklist whenever a change affects dependencies, execution paths,
documentation surfaces, or release policy.

## Required Updates

- `docs/architecture_status.md`
- `docs/stack_strategy.md`
- `conductor/tech-stack.md`
- The relevant Conductor `spec.md` and `plan.md`
- `README.md` when the change is user-facing
- `CHANGELOG.md` when behavior, dependencies, or workflows change

## Dependency Classification

Classify each new dependency or optional extra as one of:

- `core`
- `optional`
- `experimental`
- `deferred`

Record the rationale for the classification in the track docs or architecture
status page.

## Governance Requirements

- Add CI coverage before promoting a dependency or runtime path.
- Add Renovate coverage for package ecosystems that are expected to move.
- Add security and ownership notes for new runtime or packaging surfaces.
- Keep release ownership and migration notes explicit before publishing
  externally.

## Track Documentation Expectations

Every active migration or governance track should state whether it needs:

- user docs
- contributor docs
- architecture docs
- scientific/model docs
- API/contract docs
- release docs

## Suggested Order

1. Update the architecture and stack strategy docs.
2. Update the relevant Conductor track docs.
3. Update README and CHANGELOG when user-facing behavior changes.
4. Run the docs checker and the relevant tests.
