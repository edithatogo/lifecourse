import os
import sys
import unittest

import numpy as np
import pandas as pd

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lifecourse.analysis.run_helpers import (
    get_memory_usage,
    run_scenario,
    run_sim,
    select_dask_scheduler,
)
from lifecourse.model.parameters import (
    DISTRIBUTIONS,
    START_YEAR,
    sample_params_from_dist,
)

TEST_YEARS = range(START_YEAR, START_YEAR + 2)
TEST_POP_SIZE = 10


class TestRunHelpersIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sampled_params = sample_params_from_dist(DISTRIBUTIONS, seed=123)

    def test_select_dask_scheduler_uses_synchronous_for_debug(self):
        self.assertEqual(
            select_dask_scheduler(
                pop_size=100_000, years=range(2020, 2030), debug=True
            ),
            "synchronous",
        )

    def test_select_dask_scheduler_uses_synchronous_for_small_runs(self):
        self.assertEqual(
            select_dask_scheduler(pop_size=250, years=range(2020, 2022)),
            "synchronous",
        )

    def test_select_dask_scheduler_preserves_threads_for_larger_runs(self):
        self.assertEqual(
            select_dask_scheduler(pop_size=5_000, years=range(2020, 2030)),
            "threads",
        )

    def test_run_sim_output_type_and_values(self):
        dc, dq = run_sim(self.sampled_params, pop_size=TEST_POP_SIZE, years=TEST_YEARS)
        self.assertIsInstance(dc, (float, int, np.number))
        self.assertIsInstance(dq, (float, int, np.number))
        self.assertFalse(np.isnan(dc), "d_cost should not be NaN")
        self.assertFalse(np.isnan(dq), "d_qaly should not be NaN")

    def test_run_sim_deterministic_with_seed(self):
        dc1, dq1 = run_sim(
            self.sampled_params, pop_size=TEST_POP_SIZE, seed_idx=5, years=TEST_YEARS
        )
        dc2, dq2 = run_sim(
            self.sampled_params, pop_size=TEST_POP_SIZE, seed_idx=5, years=TEST_YEARS
        )
        self.assertAlmostEqual(
            dc1, dc2, places=7, msg="d_cost should be identical for the same seed_idx"
        )
        self.assertAlmostEqual(
            dq1, dq2, places=7, msg="d_qaly should be identical for the same seed_idx"
        )

        dc3, dq3 = run_sim(
            self.sampled_params, pop_size=TEST_POP_SIZE, seed_idx=6, years=TEST_YEARS
        )
        self.assertIsInstance(dc3, (float, int, np.number))
        self.assertIsInstance(dq3, (float, int, np.number))

    def test_run_sim_different_pop_sizes(self):
        # Test with a smaller population size
        dc_small, dq_small = run_sim(self.sampled_params, pop_size=5, years=TEST_YEARS)
        self.assertIsInstance(dc_small, (float, int, np.number))
        self.assertIsInstance(dq_small, (float, int, np.number))
        self.assertFalse(
            np.isnan(dc_small), "d_cost should not be NaN for small pop_size"
        )
        self.assertFalse(
            np.isnan(dq_small), "d_qaly should not be NaN for small pop_size"
        )

        # Test with a larger population size (but still small for quick testing)
        dc_large, dq_large = run_sim(self.sampled_params, pop_size=50, years=TEST_YEARS)
        self.assertIsInstance(dc_large, (float, int, np.number))
        self.assertIsInstance(dq_large, (float, int, np.number))
        self.assertFalse(
            np.isnan(dc_large), "d_cost should not be NaN for large pop_size"
        )
        self.assertFalse(
            np.isnan(dq_large), "d_qaly should not be NaN for large pop_size"
        )

    def test_run_sim_different_year_ranges(self):
        # Test with a single year
        dc_single_year, dq_single_year = run_sim(
            self.sampled_params,
            pop_size=TEST_POP_SIZE,
            years=range(START_YEAR, START_YEAR + 1),
        )
        self.assertIsInstance(dc_single_year, (float, int, np.number))
        self.assertIsInstance(dq_single_year, (float, int, np.number))

        # Test with a longer year range
        dc_long_years, dq_long_years = run_sim(
            self.sampled_params,
            pop_size=TEST_POP_SIZE,
            years=range(START_YEAR, START_YEAR + 5),
        )
        self.assertIsInstance(dc_long_years, (float, int, np.number))
        self.assertIsInstance(dq_long_years, (float, int, np.number))

    def test_run_scenario_output_type_and_structure(self):
        (dc, dq), df_output = run_scenario(
            self.sampled_params, pop_size=TEST_POP_SIZE, years=TEST_YEARS
        )

        self.assertIsInstance(dc, (float, int, np.number))
        self.assertIsInstance(dq, (float, int, np.number))
        self.assertFalse(np.isnan(dc))
        self.assertFalse(np.isnan(dq))

        self.assertIsInstance(df_output, pd.DataFrame)
        self.assertFalse(df_output.empty)

        expected_rows = 2 * len(TEST_YEARS)
        self.assertEqual(len(df_output), expected_rows)

        expected_cols = [
            "arm",
            "year",
            "annual_cost",
            "cost_health",
            "cost_edu",
            "cost_respite",
            "cost_mobility",
            "cost_welfare",
            "cost_emp",
            "cost_morbidity",
            "costs",
            "qalys",
            "ses_q0_pct",
            "ses_q1_pct",
            "ses_q2_pct",
            "ses_q3_pct",
            "ses_q4_pct",
        ]
        for col in expected_cols:
            self.assertIn(
                col,
                df_output.columns,
                f"Expected column '{col}' not in run_scenario DataFrame",
            )

        self.assertTrue(all(y in df_output["year"].unique() for y in TEST_YEARS))
        self.assertListEqual(
            sorted(df_output["arm"].unique()), ["prospective", "retrospective"]
        )

        numeric_cols_to_check = ["annual_cost", "costs", "qalys", "ses_q0_pct"]
        for col in numeric_cols_to_check:
            self.assertFalse(
                df_output[col].isnull().any(),
                f"run_scenario DataFrame column '{col}' should not contain NaNs",
            )

    def test_run_scenario_cumulative_values(self):
        (_, _), df_output = run_scenario(
            self.sampled_params, pop_size=TEST_POP_SIZE, years=TEST_YEARS
        )

        for arm_name in ["retrospective", "prospective"]:
            arm_data = df_output[df_output["arm"] == arm_name].sort_values(by="year")
            self.assertTrue(
                np.all(np.diff(arm_data["costs"]) >= -1e-9),
                f"Cumulative costs for {arm_name} arm should be non-decreasing",
            )
            self.assertTrue(
                np.all(np.diff(arm_data["qalys"]) >= -1e-9),
                f"Cumulative QALYs for {arm_name} arm should be non-decreasing",
            )

    def test_run_scenario_with_overrides(self):
        # Create a dummy scenario with overrides
        overridden_params = self.sampled_params.copy()
        overridden_params["yield_wgs"] = 0.9  # Override yield_wgs
        overridden_params["min_test_age"] = 10  # Override min_test_age

        # Run scenario with overridden parameters
        (dc, dq), df_output = run_scenario(
            overridden_params, pop_size=TEST_POP_SIZE, years=TEST_YEARS
        )

        # Assertions on the output (e.g., check if costs/qalys are different from base run)
        # This is a high-level check, detailed validation would be in unit tests for _cost_qaly etc.
        self.assertIsInstance(dc, (float, int, np.number))
        self.assertIsInstance(dq, (float, int, np.number))
        self.assertFalse(np.isnan(dc))
        self.assertFalse(np.isnan(dq))

        # More specific checks could involve running a base scenario and comparing results,
        # but for integration, just ensuring it runs and produces plausible output is key.
        # For example, if yield_wgs is higher, dQALY might be higher (but not guaranteed due to randomness)
        # A simple check: ensure the output DataFrame is not empty and has expected columns.
        self.assertFalse(df_output.empty)
        expected_cols = [
            "arm",
            "year",
            "annual_cost",
            "cost_health",
            "cost_edu",
            "cost_respite",
            "cost_mobility",
            "cost_welfare",
            "cost_emp",
            "cost_morbidity",
            "costs",
            "qalys",
            "ses_q0_pct",
            "ses_q1_pct",
            "ses_q2_pct",
            "ses_q3_pct",
            "ses_q4_pct",
        ]
        for col in expected_cols:
            self.assertIn(
                col,
                df_output.columns,
                f"Expected column '{col}' not in run_scenario DataFrame with overrides",
            )

    def test_get_memory_usage(self):
        """Test get_memory_usage function returns a float."""
        memory_mb = get_memory_usage()
        self.assertIsInstance(memory_mb, float)
        self.assertGreater(memory_mb, 0, "Memory usage should be positive")

    def test_run_sim_debug_mode(self):
        """Test run_sim with debug=True to cover debug code paths."""
        import io
        from contextlib import redirect_stdout

        # Capture stdout to verify debug output
        f = io.StringIO()
        with redirect_stdout(f):
            dc, dq = run_sim(
                self.sampled_params,
                pop_size=TEST_POP_SIZE,
                years=TEST_YEARS,
                debug=True,
            )

        output = f.getvalue()
        self.assertIsInstance(dc, (float, int, np.number))
        self.assertIsInstance(dq, (float, int, np.number))
        # Check for debug output indicators
        self.assertIn("Initial memory usage", output)
        self.assertIn("Memory after initialization", output)
        self.assertIn("Processing year", output)

    def test_run_scenario_empty_population(self):
        """Test run_scenario with pop_size=0 to cover empty population handling."""
        (dc, dq), df_output = run_scenario(
            self.sampled_params, pop_size=0, years=TEST_YEARS
        )

        self.assertEqual(dc, 0.0, "d_cost should be 0 for empty population")
        self.assertEqual(dq, 0.0, "d_qaly should be 0 for empty population")

        # Check DataFrame structure for empty population
        expected_cols = [
            "arm",
            "year",
            "annual_cost",
            "cost_health",
            "cost_edu",
            "cost_respite",
            "cost_mobility",
            "cost_welfare",
            "cost_emp",
            "cost_morbidity",
            "costs",
            "qalys",
            "ses_q0_pct",
            "ses_q1_pct",
            "ses_q2_pct",
            "ses_q3_pct",
            "ses_q4_pct",
        ]
        for col in expected_cols:
            self.assertIn(col, df_output.columns)

        # DataFrame should be empty
        self.assertEqual(len(df_output), 0, "DataFrame should be empty for pop_size=0")


if __name__ == "__main__":
    unittest.main()
