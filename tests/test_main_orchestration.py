import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestMainOrchestration(unittest.TestCase):
    """Test the main orchestration logic in main.py"""

    @patch("lifecourse.main.LocalCluster")
    @patch("lifecourse.main.Client")
    @patch("lifecourse.main.load_config")
    @patch("lifecourse.main.get_parameter_attributes")
    @patch("lifecourse.main.load_scenarios_from_yaml")
    @patch("lifecourse.main.apply_scenario_overrides")
    @patch("lifecourse.main.run_sim")
    @patch("lifecourse.main.run_scenario")
    def test_main_orchestration_flow(
        self,
        mock_run_scenario,
        mock_run_sim,
        mock_apply_scenario_overrides,
        mock_load_scenarios,
        mock_get_parameter_attributes,
        mock_load_config,
        mock_client,
        mock_cluster,
    ):
        """Test that the main orchestration flow executes all modules correctly"""
        # Mock configuration
        mock_load_config.return_value = {
            "POP_SIZE": 100,
            "PSA_N": 0,  # No PSA for this test to simplify
            "SIMULATION_YEARS": 5,
            "CALIBRATION_POP_SIZE": 100,
            "STRUCTURAL_UNCERTAINTY_POP_SIZE": 100,
        }

        # Mock get_parameter_attributes to return mocked functions
        mock_distributions = {}
        mock_sample_params = MagicMock()
        mock_get_mean_params = MagicMock()
        mock_get_mean_params.return_value = {
            "param1": 0.5,
            "param2": 1.0,
            "severity_mild_prop": 0.7,
            "cost_inp_mild": 10000,
            "cost_inp_severe": 20000,
            "cost_test": 500,
            "cost_dx": 1000,
            "cost_tx": 5000,
            "u_diag": 0.8,
            "u_undx": 0.9,
            "u_no_id": 0.95,
            "wgs_cost": 2000,
            "wgs_diag_qaly_adjustment": 0.01,
            "mort_hr_mild": 1.2,
            "mort_hr_severe": 2.0,
            "familial_prop": 0.15,
            "yield_wgs": 0.6,
            "min_test_age": 18,
        }
        mock_get_parameter_attributes.return_value = (
            mock_distributions,
            2020,
            mock_sample_params,
            mock_get_mean_params,
        )

        # Mock scenarios
        mock_load_scenarios.return_value = {
            "base": {"familial_prop": None},
            "high_yield": {"yield_wgs": 0.8},
        }

        # Mock scenario overrides
        mock_apply_scenario_overrides.side_effect = lambda base, overrides: (
            {**base, **overrides} if overrides else base
        )

        # Mock run_sim to return deterministic values
        mock_run_sim.return_value = (10000.0, 2.5)  # (dCost, dQALY)

        # Mock run_scenario to return deterministic values
        mock_run_scenario.return_value = (
            (10000.0, 2.5),
            pd.DataFrame(
                {
                    "arm": ["prospective", "retrospective"] * 5,
                    "year": list(range(2020, 2025)) * 2,
                    "annual_cost": [5000.0] * 10,
                    "cost_health": [1000.0] * 10,
                    "cost_edu": [500.0] * 10,
                    "cost_respite": [300.0] * 10,
                    "cost_mobility": [200.0] * 10,
                    "cost_welfare": [100.0] * 10,
                    "cost_emp": [150.0] * 10,
                    "cost_morbidity": [250.0] * 10,
                    "costs": [5000.0] * 10,
                    "qalys": [1.0] * 10,
                    "ses_q0_pct": [20.0] * 10,
                    "ses_q1_pct": [20.0] * 10,
                    "ses_q2_pct": [20.0] * 10,
                    "ses_q3_pct": [20.0] * 10,
                    "ses_q4_pct": [20.0] * 10,
                }
            ),
        )

        # Mock Dask cluster and client
        mock_cluster_instance = MagicMock()
        mock_cluster.return_value = mock_cluster_instance
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.dashboard_link = "http://localhost:8787"
        mock_client_instance.map.return_value = []
        mock_client_instance.gather.return_value = []

        # Import and run main function with test arguments
        from lifecourse.main import main

        # Mock command line arguments
        with patch("sys.argv", ["main.py", "--config_name", "MINIMAL_TEST_CONFIG"]):
            try:
                main()
            except SystemExit:
                pass  # argparse calls sys.exit after parsing

        # Verify that all key functions were called
        mock_load_config.assert_called_once()
        mock_get_parameter_attributes.assert_called_once()
        mock_load_scenarios.assert_called_once_with("config/scenarios.yaml")
        mock_cluster.assert_called_once()
        mock_client.assert_called_once()

        # Verify that run_sim was called for deterministic scenarios
        self.assertGreaterEqual(
            mock_run_sim.call_count, 2
        )  # At least base and one scenario

        # Verify that Dask cluster was properly closed
        mock_client_instance.close.assert_called_once()
        mock_cluster_instance.close.assert_called_once()

    @patch("lifecourse.main.LocalCluster")
    @patch("lifecourse.main.Client")
    @patch("lifecourse.main.load_config")
    @patch("lifecourse.main.get_parameter_attributes")
    @patch("lifecourse.data_loader.load_scenarios_from_yaml")
    @patch("lifecourse.main.apply_scenario_overrides")
    @patch("lifecourse.main.run_sim")
    @patch("lifecourse.main.calculate_budget_impact_with_adoption")
    @patch("lifecourse.main.run_scenario")
    def test_psa_module_execution(
        self,
        mock_run_scenario,
        mock_budget_impact,
        mock_run_sim,
        mock_apply_scenario_overrides,
        mock_load_scenarios,
        mock_get_parameter_attributes,
        mock_load_config,
        mock_client,
        mock_cluster,
    ):
        """Test that the PSA module executes correctly"""
        # Mock configuration with PSA enabled
        mock_load_config.return_value = {
            "POP_SIZE": 100,
            "PSA_N": 3,
            "SIMULATION_YEARS": 3,
            "CALIBRATION_POP_SIZE": 100,
            "STRUCTURAL_UNCERTAINTY_POP_SIZE": 100,
        }

        # Mock parameters with all required fields
        base_params = {
            "cost_inp_mild": 10000,
            "cost_inp_severe": 20000,
            "cost_outp_mild": 2000,
            "cost_outp_severe": 6000,
            "cost_pharm_mild": 400,
            "cost_pharm_severe": 1000,
            "edu0_sup0": 16107,
            "edu0_sup1": 27903,
            "edu0_sup2": 46733,
            "edu1_sup0": 18958,
            "edu1_sup1": 30789,
            "edu1_sup2": 49604,
            "respite": 13024,
            "mobility": 2493,
            "welfare_mild": 3000,
            "welfare_severe": 8000,
            "morb_cost_epilepsy": 2000,
            "morb_cost_asd": 1500,
            "morb_cost_mental": 1000,
            "wgs_diag_cost_adjustment": -1000,
            "u_base_mild": 0.78,
            "u_base_severe": 0.65,
            "u_decay": 0.0005,
            "u_diag": 0.02,
            "u_carer": 0.05,
            "morb_qaly_epilepsy": 0.04,
            "morb_qaly_asd": 0.03,
            "morb_qaly_mental": 0.05,
            "wgs_diag_qaly_adjustment": 0.01,
            "mort_hr_mild": 2.0,
            "mort_hr_severe": 4.0,
            "morb_prob_epilepsy": 0.25,
            "morb_prob_asd": 0.30,
            "morb_prob_mental": 0.35,
            "familial_prop": 0.15,
            "yield_wgs": 0.6,
            "severity_mild_prop": 0.7,
            "fertility_multiplier": 1.0,
            "min_test_age": 18,
            "severity_severe_prop": 0.3,  # Added for completeness
        }

        # Mock DISTRIBUTIONS with required keys for tornado analysis
        mock_distributions = {
            "familial_prop": {"dist": "beta", "alpha": 30, "beta": 150},
            "yield_wgs": {"dist": "beta", "alpha": 45, "beta": 55},
            "u_diag": {"dist": "beta", "alpha": 20, "beta": 980},
            "cost_inp_severe": {"dist": "gamma", "shape": 1.0, "scale": 20000},
        }

        # Mock get_parameter_attributes return values
        mock_start_year = 2020
        mock_sample_params = MagicMock(return_value=base_params)
        mock_get_mean_params = MagicMock(return_value=base_params)
        mock_get_parameter_attributes.return_value = (
            mock_distributions,
            mock_start_year,
            mock_sample_params,
            mock_get_mean_params,
        )

        # Mock run_sim to return different values for each PSA run
        mock_run_sim.side_effect = lambda *args, **kwargs: (
            10000.0,
            2.5,
        )  # Simple mock that always returns the same values

        # Mock run_scenario
        mock_run_scenario.return_value = (
            (10000.0, 2.5),
            pd.DataFrame(
                {
                    "arm": ["prospective", "retrospective"] * 3,
                    "year": list(range(2020, 2023)) * 2,
                    "annual_cost": [5000.0] * 6,
                    "cost_health": [1000.0] * 6,
                    "cost_edu": [500.0] * 6,
                    "cost_respite": [300.0] * 6,
                    "cost_mobility": [200.0] * 6,
                    "cost_welfare": [100.0] * 6,
                    "cost_emp": [150.0] * 6,
                    "cost_morbidity": [250.0] * 6,
                    "costs": [5000.0] * 6,
                    "qalys": [1.0] * 6,
                    "ses_q0_pct": [20.0] * 6,
                    "ses_q1_pct": [20.0] * 6,
                    "ses_q2_pct": [20.0] * 6,
                    "ses_q3_pct": [20.0] * 6,
                    "ses_q4_pct": [20.0] * 6,
                }
            ),
        )

        # Mock Dask cluster and client
        mock_cluster_instance = MagicMock()
        mock_cluster.return_value = mock_cluster_instance
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.dashboard_link = "http://localhost:8787"

        # Mock Dask map and gather functions
        def mock_map(func, args_list, **kwargs):
            # Create futures that will return our mock results
            futures = []
            for i in range(len(args_list)):
                future = MagicMock()
                future.result.return_value = (
                    10000.0 + i * 1000,
                    2.5 - i * 0.1,
                )  # Different values for each run
                futures.append(future)
            return futures

        def mock_gather(futures):
            # Return the results from the futures
            return [future.result() for future in futures]

        mock_client_instance.map.side_effect = mock_map
        mock_client_instance.gather.side_effect = mock_gather

        # Mock budget impact
        mock_budget_impact.return_value = {
            "years": np.array([2020, 2021, 2022]),
            "adoption_rates": np.array([0.2, 0.6, 1.0]),
            "incremental_costs": np.array([1000, 2000, 3000]),
            "adopted_costs": np.array([200, 1200, 3000]),
            "cumulative_budget_impact": np.array([200, 1400, 4400]),
            "curve_type": "stepwise",
            "max_adoption": 1.0,
            "curve_params": {"steps": [(1, 0.2), (3, 0.6), (5, 1.0)]},
        }

        # Import and run main function
        from lifecourse.main import main

        # Mock command line arguments
        with patch("sys.argv", ["main.py", "--config_name", "MINIMAL_TEST_CONFIG"]):
            try:
                main()
            except SystemExit:
                pass  # argparse calls sys.exit after parsing

        # Verify that sample_params_from_dist was called for each PSA run
        self.assertEqual(mock_sample_params.call_count, 3)

        # Verify that run_sim was called for deterministic scenarios
        self.assertGreaterEqual(mock_run_sim.call_count, 1)

    @patch("lifecourse.main.LocalCluster")
    @patch("lifecourse.main.Client")
    @patch("lifecourse.main.load_config")
    @patch("lifecourse.main.get_parameter_attributes")
    @patch("lifecourse.main.load_scenarios_from_yaml")
    @patch("lifecourse.main.apply_scenario_overrides")
    @patch("lifecourse.main.run_sim")
    def test_debug_mode(
        self,
        mock_run_sim,
        mock_apply_scenario_overrides,
        mock_load_scenarios,
        mock_get_parameter_attributes,
        mock_load_config,
        mock_client,
        mock_cluster,
    ):
        """Test that debug mode works correctly"""
        # Mock configuration
        mock_load_config.return_value = {
            "POP_SIZE": 100,
            "PSA_N": 0,  # No PSA for simpler test
            "SIMULATION_YEARS": 2,
            "CALIBRATION_POP_SIZE": 100,
            "STRUCTURAL_UNCERTAINTY_POP_SIZE": 100,
        }

        # Mock get_parameter_attributes to return mocked functions
        mock_distributions = {}
        mock_start_year = 2020
        mock_sample_params = MagicMock(
            return_value={
                "param1": 0.5,
                "param2": 1.0,
                "severity_mild_prop": 0.7,
                "cost_inp_mild": 10000,
                "cost_inp_severe": 20000,
                "cost_test": 500,
                "cost_dx": 1000,
                "cost_tx": 5000,
                "u_diag": 0.8,
                "u_undx": 0.9,
                "u_no_id": 0.95,
                "wgs_cost": 2000,
                "wgs_diag_qaly_adjustment": 0.01,
                "mort_hr_mild": 1.2,
                "mort_hr_severe": 2.0,
                "familial_prop": 0.15,
                "yield_wgs": 0.6,
                "min_test_age": 18,
            }
        )
        mock_get_mean_params = MagicMock(
            return_value={
                "param1": 0.5,
                "param2": 1.0,
                "severity_mild_prop": 0.7,
                "cost_inp_mild": 10000,
                "cost_inp_severe": 20000,
                "cost_test": 500,
                "cost_dx": 1000,
                "cost_tx": 5000,
                "u_diag": 0.8,
                "u_undx": 0.9,
                "u_no_id": 0.95,
                "wgs_cost": 2000,
                "wgs_diag_qaly_adjustment": 0.01,
                "mort_hr_mild": 1.2,
                "mort_hr_severe": 2.0,
                "familial_prop": 0.15,
                "yield_wgs": 0.6,
                "min_test_age": 18,
            }
        )
        mock_get_parameter_attributes.return_value = (
            mock_distributions,
            mock_start_year,
            mock_sample_params,
            mock_get_mean_params,
        )
        mock_load_scenarios.side_effect = lambda *args, **kwargs: {"base": {}}
        mock_apply_scenario_overrides.side_effect = lambda base, overrides: base
        mock_run_sim.return_value = (10000.0, 2.5)

        # Mock Dask cluster and client
        mock_cluster_instance = MagicMock()
        mock_cluster.return_value = mock_cluster_instance
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.dashboard_link = "http://localhost:8787"

        # Import and run main function with debug flag
        from lifecourse.main import main

        # Mock command line arguments with debug flag
        with patch(
            "sys.argv", ["main.py", "--config_name", "MINIMAL_TEST_CONFIG", "--debug"]
        ):
            try:
                main()
            except SystemExit:
                pass  # argparse calls sys.exit after parsing

        # Verify that the function executed without errors
        mock_run_sim.assert_called()


if __name__ == "__main__":
    unittest.main()
