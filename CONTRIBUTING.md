# Contributing to `lifecourse`

Thanks for contributing. This guide covers the current developer workflow, test expectations, and repository conventions for the maintained codebase.

## Start Here

Use `uv` for local setup:

```bash
uv sync --all-extras --dev
```

Run the main checks locally before opening a pull request:

```bash
uv run pytest -q
uv run ruff check .
uv run basedpyright
uv run python scripts/check_docs.py
uv run pytest tests/test_release_governance_docs.py -q --no-cov
uv run pytest tests/test_stack_change_checklist.py -q --no-cov
```

If you are working on a focused change, it is fine to run the smallest relevant test subset first, then finish with the full checks above.

## Workflow

- Prefer Conductor for spec-driven work when a change is being planned or tracked.
- Keep task scope small and commit only the files needed for the current change.
- Update tests alongside implementation changes.
- Preserve the current `uv`- and `pyproject.toml`-based workflow unless a follow-up track explicitly changes it.
- Run `uv run python scripts/check_docs.py` when you touch docs, docs links, or release/support policy pages.
- Run `uv run pytest tests/test_release_governance_docs.py -q --no-cov` when you touch `RELEASE.md` or registry/deprecation guidance.
- Run `uv run pytest tests/test_stack_change_checklist.py -q --no-cov` when you touch stack strategy or dependency-governance docs.

## Commit Hooks

This repository uses pre-commit hooks for formatting and linting.

- Let the hooks run automatically on commit, or run them manually before committing.
- If a partial commit is causing hook noise, stage only the files for the current change.

## Dask Guidance

The model still uses Dask in the maintained simulation path, so keep Dask-specific code defensive.

- Use `lifecourse.model.dask_utils.safe_from_pandas(df, npartitions=...)` when returning small pandas DataFrames from factories.
- Before concatenating Dask DataFrames that may have lost division metadata, call `lifecourse.model.dask_utils.ensure_known_divisions(ddf)` on each input.
- If you introduce a new source of unknown-division warnings, add a regression test and fix the producer rather than masking the symptom.

## Repository Conventions

- Use the `src/` layout and put application code under `src/lifecourse/`.
- Keep generated artifacts out of commits. Results belong in `results/`.
- Prefer descriptive docstrings and explicit types on public functions.
- Follow the code style in `conductor/code_styleguides/`.

## Pull Requests

- Open a pull request against `main` with a concise description.
- Include tests for behavior changes.
- Mention any follow-up work that should become a separate track if the change grows beyond the current scope.
