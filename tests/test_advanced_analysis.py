import unittest
from unittest.mock import patch, call
import pandas as pd
import numpy as np
from src.analysis.advanced_analysis import run_calibration, run_structural_uncertainty

TEST_YEARS = range(2020, 2022)

class TestAdvancedAnalysis(unittest.TestCase):

    def setUp(self):
        # Define base parameters used across tests
        self.base_params = {
            'param1': 10,
            'param2': 20,
            'mort_hr_mild': 1.5,
            'mort_hr_severe': 2.5
        }
        # Mock the distributions dictionary needed by run_structural_uncertainty
        self.mock_distributions = {
            'mort_hr_mild': {'scale': 1.5},
            'mort_hr_severe': {'scale': 2.5}
        }

    @patch('src.analysis.advanced_analysis.run_sim')
    def test_run_calibration(self, mock_run_sim):
        # Configure the mock to return a fixed cost and QALY value
        mock_run_sim.return_value = (525000, 100) # (dCost, dQALY)

        # Run the calibration function
        result = run_calibration(self.base_params, pop_size=100, years=TEST_YEARS)

        # Assertions
        mock_run_sim.assert_called_once_with(self.base_params, pop_size=100, years=TEST_YEARS)
        self.assertIsInstance(result, dict)
        self.assertIn('sim_cost', result)
        self.assertIn('error_pct', result)
        self.assertEqual(result['sim_cost'], 525000)
        # Benchmark is hardcoded as {'mild': 200000, 'severe': 500000}, sum = 700000
        expected_error = abs(525000 - 700000) / 700000 * 100
        self.assertAlmostEqual(result['error_pct'], expected_error)

    @patch('src.analysis.advanced_analysis.DISTRIBUTIONS', new_callable=lambda: {
        'mort_hr_mild': {'scale': 1.5},
        'mort_hr_severe': {'scale': 2.5}
    })
    @patch('src.analysis.advanced_analysis.run_sim')
    def test_run_structural_uncertainty(self, mock_run_sim, mock_dist):
        # Configure the mock to return consistent values for each call
        mock_run_sim.return_value = (10000, 50) # (dCost, dQALY)
        
        num_runs = 5 # Small number for testing
        df = run_structural_uncertainty(self.base_params, num_runs=num_runs, pop_size=100, years=TEST_YEARS)

        # Assertions
        self.assertEqual(mock_run_sim.call_count, num_runs)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), num_runs)
        self.assertEqual(list(df.columns), ['run', 'dCost', 'dQALY'])
        self.assertTrue(all(df['dCost'] == 10000))

if __name__ == '__main__':
    unittest.main()
