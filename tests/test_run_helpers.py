import unittest
import numpy as np
import pandas as pd
from src.analysis.run_helpers import run_sim, run_scenario
from src.model.parameters import (
    DISTRIBUTIONS,
    START_YEAR,
    END_YEAR,
    sample_params_from_dist
)

TEST_YEARS = range(START_YEAR, START_YEAR + 2)
TEST_POP_SIZE = 10

class TestRunHelpersIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sampled_params = sample_params_from_dist(DISTRIBUTIONS, seed=123)

    def test_run_sim_output_type_and_values(self):
        dc, dq = run_sim(self.sampled_params, pop_size=TEST_POP_SIZE, years=TEST_YEARS)
        self.assertIsInstance(dc, (float, int, np.number))
        self.assertIsInstance(dq, (float, int, np.number))
        self.assertFalse(np.isnan(dc), "d_cost should not be NaN")
        self.assertFalse(np.isnan(dq), "d_qaly should not be NaN")

    def test_run_sim_deterministic_with_seed(self):
        dc1, dq1 = run_sim(self.sampled_params, pop_size=TEST_POP_SIZE, seed_idx=5, years=TEST_YEARS)
        dc2, dq2 = run_sim(self.sampled_params, pop_size=TEST_POP_SIZE, seed_idx=5, years=TEST_YEARS)
        self.assertAlmostEqual(dc1, dc2, places=7, msg="d_cost should be identical for the same seed_idx")
        self.assertAlmostEqual(dq1, dq2, places=7, msg="d_qaly should be identical for the same seed_idx")

        dc3, dq3 = run_sim(self.sampled_params, pop_size=TEST_POP_SIZE, seed_idx=6, years=TEST_YEARS)
        self.assertIsInstance(dc3, (float, int, np.number))
        self.assertIsInstance(dq3, (float, int, np.number))

    def test_run_scenario_output_type_and_structure(self):
        (dc, dq), df_output = run_scenario(self.sampled_params, pop_size=TEST_POP_SIZE, years=TEST_YEARS)

        self.assertIsInstance(dc, (float, int, np.number))
        self.assertIsInstance(dq, (float, int, np.number))
        self.assertFalse(np.isnan(dc))
        self.assertFalse(np.isnan(dq))

        self.assertIsInstance(df_output, pd.DataFrame)
        self.assertFalse(df_output.empty)

        expected_rows = 2 * len(TEST_YEARS)
        self.assertEqual(len(df_output), expected_rows)

        expected_cols = [
            'arm', 'year', 'annual_cost', 'cost_health', 'cost_edu',
            'cost_respite', 'cost_mobility', 'cost_welfare', 'cost_emp',
            'cost_morbidity', 'costs', 'qalys',
            'ses_q0_pct', 'ses_q1_pct', 'ses_q2_pct', 'ses_q3_pct', 'ses_q4_pct'
        ]
        for col in expected_cols:
            self.assertIn(col, df_output.columns, f"Expected column '{col}' not in run_scenario DataFrame")

        self.assertTrue(all(y in df_output['year'].unique() for y in TEST_YEARS))
        self.assertListEqual(sorted(df_output['arm'].unique()), ['prospective', 'retrospective'])

        numeric_cols_to_check = ['annual_cost', 'costs', 'qalys', 'ses_q0_pct']
        for col in numeric_cols_to_check:
            self.assertFalse(df_output[col].isnull().any(), f"run_scenario DataFrame column '{col}' should not contain NaNs")

    def test_run_scenario_cumulative_values(self):
        (_, _), df_output = run_scenario(self.sampled_params, pop_size=TEST_POP_SIZE, years=TEST_YEARS)

        for arm_name in ['retrospective', 'prospective']:
            arm_data = df_output[df_output['arm'] == arm_name].sort_values(by='year')
            self.assertTrue(np.all(np.diff(arm_data['costs']) >= -1e-9), f"Cumulative costs for {arm_name} arm should be non-decreasing")
            self.assertTrue(np.all(np.diff(arm_data['qalys']) >= -1e-9), f"Cumulative QALYs for {arm_name} arm should be non-decreasing")

if __name__ == '__main__':
    unittest.main()
