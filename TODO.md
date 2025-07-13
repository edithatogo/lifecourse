# Project TODO List

This file tracks pending tasks and future work items for the LifeCourseID microsimulation project.

## High Priority
- **Validate simulation outputs:** Compare current simulation results against known benchmarks, previous validated versions, or published data to ensure accuracy and consistency after refactoring and test additions. (Part of Roadmap Phase 2)
  - *Status: Initial comparison attempted. Significant discrepancies found. Further investigation into dQALY sign flips and dCost magnitudes is the immediate next step.*
- **Review `GEMINI.md`:** Thoroughly review `GEMINI.md` for any specific agent instructions that might have been overlooked or need to be incorporated into development practices.
  - *Status: Reviewed. Key guidelines noted. No immediate changes required based on review, but will keep in mind for future work.*

## Medium Priority
- **Investigate dQALY Discrepancies:**
    - Meticulously compare QALY-related parameter definitions (means and distributions from `DISTRIBUTIONS` dict) between current `src/model/parameters.py` and `archive/old_notebooks/LifeCourseID, v7, 20250623.py`.
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
- See `ROADMAP.md` for longer-term feature development.
- Add pre-commit hooks.
