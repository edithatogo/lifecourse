import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lifecourse.cli import main as cli_main


class TestE2ECLI(unittest.TestCase):
    """End-to-end tests for CLI functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Create a minimal scenarios.yaml for testing
        self.scenarios_content = """
scenarios:
  base:
    familial_prop: null
    yield_wgs: null
  test_scenario:
    familial_prop: 0.1
    yield_wgs: 0.5
"""
        with open("scenarios.yaml", "w") as f:
            f.write(self.scenarios_content)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil

        shutil.rmtree(self.temp_dir)

    @patch("lifecourse.cli.run_sim")
    @patch("lifecourse.cli.get_parameter_attributes")
    @patch("lifecourse.cli.load_scenarios_from_yaml")
    @patch("lifecourse.cli.apply_scenario_overrides")
    def test_cli_base_scenario_execution(
        self,
        mock_apply_overrides,
        mock_load_scenarios,
        mock_get_parameter_attributes,
        mock_run_sim,
    ):
        """Test CLI execution with base scenario."""
        # Mock dependencies
        mock_params = {"param1": 0.5, "familial_prop": 0.1, "yield_wgs": 0.6}

        def mock_get_mean_params(_distributions):
            return mock_params

        mock_get_parameter_attributes.return_value = ({}, 2020, mock_get_mean_params)
        mock_load_scenarios.return_value = {"base": {}}
        mock_apply_overrides.return_value = mock_params
        mock_run_sim.return_value = (10000.0, 2.5)

        # Capture stdout
        import io

        f = io.StringIO()
        with (
            redirect_stdout(f),
            # Simulate CLI call: python -m lifecourse.cli base --pop-size 100
            patch("sys.argv", ["lifecourse.cli", "base", "--pop-size", "100"]),
        ):
            cli_main()

        output = f.getvalue()
        self.assertIn("Scenario: base", output)
        self.assertIn("dCost: 10000.00", output)
        self.assertIn("dQALY: 2.5000", output)

        # Verify mocks were called
        mock_load_scenarios.assert_called_once_with("config/scenarios.yaml")
        mock_get_parameter_attributes.assert_called_once()
        mock_apply_overrides.assert_called_once()
        mock_run_sim.assert_called_once()

    @patch("lifecourse.cli.run_sim")
    @patch("lifecourse.cli.get_parameter_attributes")
    @patch("lifecourse.cli.load_scenarios_from_yaml")
    @patch("lifecourse.cli.apply_scenario_overrides")
    def test_cli_custom_scenario_execution(
        self,
        mock_apply_overrides,
        mock_load_scenarios,
        mock_get_parameter_attributes,
        mock_run_sim,
    ):
        """Test CLI execution with custom scenario."""
        # Mock dependencies
        base_params = {"familial_prop": 0.1, "yield_wgs": 0.6}

        def mock_get_mean_params(_distributions):
            return base_params

        mock_get_parameter_attributes.return_value = ({}, 2020, mock_get_mean_params)
        mock_load_scenarios.return_value = {
            "test_scenario": {"familial_prop": 0.1, "yield_wgs": 0.5}
        }
        mock_apply_overrides.return_value = {"familial_prop": 0.1, "yield_wgs": 0.5}
        mock_run_sim.return_value = (15000.0, 3.0)

        # Capture stdout
        import io

        f = io.StringIO()
        with (
            redirect_stdout(f),
            # Simulate CLI call: python -m lifecourse.cli test_scenario --pop-size 200
            patch("sys.argv", ["lifecourse.cli", "test_scenario", "--pop-size", "200"]),
        ):
            cli_main()

        output = f.getvalue()
        self.assertIn("Scenario: test_scenario", output)
        self.assertIn("dCost: 15000.00", output)
        self.assertIn("dQALY: 3.0000", output)

    def test_cli_no_scenario_help(self):
        """Test CLI shows help when no scenario provided."""
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f), patch("sys.argv", ["lifecourse.cli"]):
            cli_main()

        output = f.getvalue()
        self.assertIn("usage:", output.lower())

    @patch("lifecourse.cli.run_calibration")
    def test_cli_calibration_mode(self, mock_run_calibration):
        """Test CLI calibration mode."""
        mock_run_calibration.return_value = {"error_pct": 25.0}

        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with (
            redirect_stdout(f),
            patch("sys.argv", ["lifecourse.cli", "--calibration", "--pop-size", "100"]),
        ):
            cli_main()

        output = f.getvalue()
        self.assertIn("Calibration completed", output)
        mock_run_calibration.assert_called_once()

    @patch("lifecourse.cli.run_structural_uncertainty")
    def test_cli_structural_uncertainty_mode(self, mock_run_structural_uncertainty):
        """Test CLI structural uncertainty mode."""
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with (
            redirect_stdout(f),
            patch(
                "sys.argv",
                ["lifecourse.cli", "--structural-uncertainty", "--pop-size", "100"],
            ),
        ):
            cli_main()

        output = f.getvalue()
        self.assertIn("Structural uncertainty analysis completed", output)
        mock_run_structural_uncertainty.assert_called_once()


if __name__ == "__main__":
    unittest.main()
