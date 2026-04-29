import os
import sys
import tempfile
import unittest
from contextlib import suppress
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lifecourse.main import main as main_main


class TestE2EMain(unittest.TestCase):
    """End-to-end tests for main.py orchestration."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Create results directory
        os.makedirs("results", exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil

        shutil.rmtree(self.temp_dir)

    @patch("lifecourse.main.LocalCluster")
    @patch("lifecourse.main.Client")
    @patch("lifecourse.main.load_config")
    @patch("lifecourse.main.get_parameter_attributes")
    @patch("lifecourse.main.load_scenarios_from_yaml")
    @patch("lifecourse.main.apply_scenario_overrides")
    @patch("lifecourse.main.run_sim")
    def test_main_minimal_test_config(
        self,
        mock_run_sim,
        mock_apply_overrides,
        mock_load_scenarios,
        mock_get_parameter_attributes,
        mock_load_config,
        mock_client,
        mock_cluster,
    ):
        """Test main.py with MINIMAL_TEST_CONFIG."""
        # Mock configuration
        mock_load_config.return_value = {
            "POP_SIZE": 100,
            "PSA_N": 0,  # No PSA for simpler test
            "SIMULATION_YEARS": 2,
            "CALIBRATION_POP_SIZE": 100,
            "STRUCTURAL_UNCERTAINTY_POP_SIZE": 100,
        }

        # Mock parameters and scenarios
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
            "severity_severe_prop": 0.3,
        }

        # Mock get_parameter_attributes return values
        mock_distributions = {}
        mock_start_year = 2020
        mock_sample_params = MagicMock()
        mock_get_mean_params = MagicMock(return_value=base_params)
        mock_get_parameter_attributes.return_value = (
            mock_distributions,
            mock_start_year,
            mock_sample_params,
            mock_get_mean_params,
        )

        mock_load_scenarios.return_value = {"base": {}}
        mock_apply_overrides.return_value = base_params
        mock_run_sim.return_value = (10000.0, 2.5)

        # Mock Dask
        mock_cluster_instance = MagicMock()
        mock_cluster.return_value = mock_cluster_instance
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.dashboard_link = "http://localhost:8787"

        # Run main with MINIMAL_TEST_CONFIG
        with (
            patch(
                "sys.argv",
                ["main.py", "--config_name", "MINIMAL_TEST_CONFIG", "--debug"],
            ),
            suppress(SystemExit),
        ):
            main_main()

        # Verify deterministic summary was created
        self.assertTrue(os.path.exists("results/deterministic_summary.csv"))
        df = pd.read_csv("results/deterministic_summary.csv")
        self.assertIn("scenario", df.columns)
        self.assertIn("dCost", df.columns)
        self.assertIn("dQALY", df.columns)

        # Verify mocks were called appropriately
        mock_load_config.assert_called_once()
        mock_get_parameter_attributes.assert_called_once()
        mock_get_mean_params.assert_called_once_with({})
        mock_load_scenarios.assert_called_once()

    @patch("lifecourse.main.LocalCluster")
    @patch("lifecourse.main.Client")
    @patch("lifecourse.main.load_config")
    @patch("lifecourse.main.get_parameter_attributes")
    @patch("lifecourse.main.load_scenarios_from_yaml")
    @patch("lifecourse.main.apply_scenario_overrides")
    @patch("lifecourse.main.run_sim")
    @patch("lifecourse.main.calculate_budget_impact_with_adoption")
    def test_main_psa_execution(
        self,
        mock_budget_impact,
        mock_run_sim,
        mock_apply_overrides,
        mock_load_scenarios,
        mock_get_parameter_attributes,
        mock_load_config,
        mock_client,
        mock_cluster,
    ):
        """Test main.py PSA execution."""
        # Mock configuration with PSA enabled
        mock_load_config.return_value = {
            "POP_SIZE": 100,
            "PSA_N": 3,
            "SIMULATION_YEARS": 3,
            "CALIBRATION_POP_SIZE": 100,
            "STRUCTURAL_UNCERTAINTY_POP_SIZE": 100,
        }

        # Mock parameters
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
            "severity_severe_prop": 0.3,
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

        mock_load_scenarios.return_value = {"base": {}}
        mock_apply_overrides.return_value = base_params
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

        # Mock run_sim for PSA
        def mock_run_sim_func(*args, **kwargs):
            return (10000.0, 2.5)

        mock_run_sim.side_effect = mock_run_sim_func

        # Mock Dask
        mock_cluster_instance = MagicMock()
        mock_cluster.return_value = mock_cluster_instance
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.dashboard_link = "http://localhost:8787"

        # Mock Dask map and gather
        def mock_map(func, args_list, **kwargs):
            futures = []
            for i in range(len(args_list)):
                future = MagicMock()
                future.result.return_value = (10000.0 + i * 1000, 2.5 + i * 0.2)
                futures.append(future)
            return futures

        def mock_gather(futures):
            return [f.result.return_value for f in futures]

        mock_client_instance.map.side_effect = mock_map
        mock_client_instance.gather.side_effect = mock_gather

        # Run main with PSA
        with (
            patch("sys.argv", ["main.py", "--config_name", "MINIMAL_TEST_CONFIG"]),
            suppress(SystemExit),
        ):
            main_main()

        # Verify PSA results were created
        self.assertTrue(os.path.exists("results/psa_samples.csv"))
        df = pd.read_csv("results/psa_samples.csv")
        self.assertEqual(len(df), 3)  # 3 PSA runs
        self.assertIn("dCost", df.columns)
        self.assertIn("dQALY", df.columns)


if __name__ == "__main__":
    unittest.main()
