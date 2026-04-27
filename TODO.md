# Legacy TODO List

This file is preserved for historical context. Current tracked work lives in `ROADMAP.md` and the Conductor workspace under `conductor/`.

## High Priority

- **MCDA Module Implementation:** Implement Multi-Criteria Decision Analysis (MCDA) as the next priority advanced analysis feature for health economic evaluation.
  - *Status: COMPLETED - Full MCDA implementation with decision matrix creation, AHP weighting, value functions, workflow integration, visualization functions, and comprehensive unit tests.*

- **Validate simulation outputs:** Compare current simulation results against known benchmarks, previous validated versions, or published data to ensure accuracy and consistency after refactoring and test additions. (Part of Roadmap Phase 2)
  - *Status: COMPLETED - Critical bugs identified and fixed: retrospective arm incorrectly assigned diagnosed status to all individuals instead of only familial ones, and random state synchronization issues between arms. Output signs now correct with prospective intervention showing appropriate cost savings and QALY gains.*

- **Review `GEMINI.md`:** Thoroughly review `GEMINI.md` for any specific agent instructions that might have been overlooked or need to be incorporated into development practices.
  - *Status: Reviewed. Key guidelines noted. No immediate changes required based on review, but will keep in mind for future work.*

## Medium Priority

- **Investigate dQALY Discrepancies:**
  - Meticulously compare QALY-related parameter definitions (means and distributions from `DISTRIBUTIONS` dict) between the current model code and a validated archived notebook version.
  - Use short (2-year) validation runs to test the impact of aligning any identified QALY parameter discrepancies one by one.
  - If parameter alignment doesn't resolve dQALY sign flips, perform a more intense line-by-line re-comparison of the QALY calculation logic within `_cost_qaly` (current vs. v7).

- **Address `main.py` Performance/Timeout for Full Runs:**
  - Investigate why `main.py` times out on full 81-year simulations (even with `pop_size=100` and no LocalCluster/plotting) while unit tests of `run_sim` are fast.
  - This is needed for full magnitude validation of `dCost` and final ICERs against the 81-year benchmark.

- **Enhance test coverage:**
  - Add more detailed assertions to existing placeholder tests (e.g., `tests/test_advanced_analysis.py`, `tests/test_plotting.py`).
  - Add tests for `main.py`'s orchestration logic (once its performance issues are understood).

- **Configuration (`config/scenarios.yaml`):** (Roadmap Phase 3)
  - Review and fully implement robust loading and dynamic scenario generation from `config/scenarios.yaml`.

## Low Priority

- **Address `pandas` vs `Dask` consideration:** Evaluate if transitioning parts of Dask to Pandas with PyArrow would simplify codebase.
- **Explore Roadmap Phase 4 (Performance Optimization):** Profile code after current issues are resolved.
- **Develop CLI (Roadmap Phase 5):** Plan/implement CLI.

## Backlog / Future Ideas

- See `ROADMAP.md` and `conductor/` for the maintained planning surface.
- Treat the items above as archival notes unless they are re-entered into active planning.
