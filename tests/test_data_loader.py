import unittest
import tempfile
import os
from unittest.mock import patch
from lifecourse.data_loader import (
    load_scenarios_from_yaml,
    apply_scenario_overrides,
    load_nz_population_distribution,
    load_nz_life_table_hazards,
)


class TestDataLoader(unittest.TestCase):
    def setUp(self):
        # Create a temporary YAML file for testing
        self.temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        )
        self.temp_file.write("""
scenarios:
  base:
    param1: null
    param2: 10
  scenario_a:
    param1: 5
    param2: null
  scenario_b:
    param1: null
    param2: 20

scenario_grid:
  param1: [1, 2]
  param2: [100, 200]
""")
        self.temp_file.close()

    def tearDown(self):
        # Clean up the temporary file
        os.unlink(self.temp_file.name)

    def test_load_scenarios_from_yaml(self):
        """Test loading scenarios from YAML file."""
        scenarios = load_scenarios_from_yaml(self.temp_file.name)

        # Check that all scenarios are loaded
        self.assertIn("base", scenarios)
        self.assertIn("scenario_a", scenarios)
        self.assertIn("scenario_b", scenarios)

        # Check specific values
        self.assertEqual(scenarios["base"]["param2"], 10)
        self.assertEqual(scenarios["scenario_a"]["param1"], 5)
        self.assertIsNone(scenarios["scenario_a"]["param2"])

    def test_scenario_grid_generation(self):
        """Test that scenario grid definitions are properly expanded."""
        scenarios = load_scenarios_from_yaml(self.temp_file.name)

        # Check that grid scenarios are generated
        self.assertIn("param1_1_param2_100", scenarios)
        self.assertIn("param1_1_param2_200", scenarios)
        self.assertIn("param1_2_param2_100", scenarios)
        self.assertIn("param1_2_param2_200", scenarios)

        # Check specific values in grid scenarios
        self.assertEqual(scenarios["param1_1_param2_100"]["param1"], 1)
        self.assertEqual(scenarios["param1_1_param2_100"]["param2"], 100)
        self.assertEqual(scenarios["param1_2_param2_200"]["param1"], 2)
        self.assertEqual(scenarios["param1_2_param2_200"]["param2"], 200)

    def test_scenario_grid_combinatorial_expansion(self):
        """Test that all combinations in scenario grid are generated."""
        scenarios = load_scenarios_from_yaml(self.temp_file.name)

        # Count grid scenarios by checking if they contain both parameter names
        grid_scenarios = [
            name for name in scenarios.keys() if "param1_" in name and "param2_" in name
        ]

        # Should have 2 * 2 = 4 combinations
        self.assertEqual(len(grid_scenarios), 4)

        # Check that all expected combinations exist
        expected_names = [
            "param1_1_param2_100",
            "param1_1_param2_200",
            "param1_2_param2_100",
            "param1_2_param2_200",
        ]

        for name in expected_names:
            self.assertIn(name, scenarios)

    def test_apply_scenario_overrides(self):
        """Test applying scenario overrides to base parameters."""
        base_params = {"param1": 100, "param2": 200, "param3": 300}

        overrides = {
            "param1": 150,  # Absolute value
            "param2": 0.1,  # Relative adjustment (small value)
            "param3": None,  # No change
        }

        result = apply_scenario_overrides(base_params, overrides)

        # Check absolute value override
        self.assertEqual(result["param1"], 150)

        # Check relative adjustment
        self.assertEqual(result["param2"], 200.1)  # 200 + 0.1

        # Check no change when None
        self.assertEqual(result["param3"], 300)

    def test_apply_scenario_overrides_with_severity_prop(self):
        """Test that severity proportions are correctly handled."""
        base_params = {"severity_mild_prop": 0.7, "severity_severe_prop": 0.3}

        overrides = {"severity_mild_prop": 0.8}

        result = apply_scenario_overrides(base_params, overrides)

        # Check that mild prop is updated
        self.assertEqual(result["severity_mild_prop"], 0.8)

        # Check that severe prop is automatically updated to maintain sum = 1
        # Using almost equal for floating point comparison
        self.assertAlmostEqual(result["severity_severe_prop"], 0.2, places=10)

    def test_scenario_name_sanitization(self):
        """Test that scenario names are properly sanitized."""
        # Create a temporary YAML file with decimal values
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        temp_file.write("""
scenario_grid:
  param_with_decimal: [0.1, 0.2]
  another_param: [1.5, 2.5]
""")
        temp_file.close()

        try:
            scenarios = load_scenarios_from_yaml(temp_file.name)

            # Check that decimal points are replaced with underscores in names
            self.assertIn("param_with_decimal_0_1_another_param_1_5", scenarios)
            self.assertIn("param_with_decimal_0_1_another_param_2_5", scenarios)
            self.assertIn("param_with_decimal_0_2_another_param_1_5", scenarios)
            self.assertIn("param_with_decimal_0_2_another_param_2_5", scenarios)
        finally:
            os.unlink(temp_file.name)

    @patch('pandas.read_csv')
    def test_load_nz_population_distribution(self, mock_read_csv):
        """Test loading NZ population distribution data."""
        # Mock the CSV data
        mock_data = {
            'Geography': ['New Zealand', 'Auckland', 'New Zealand'],
            'Age': ['0-4', '5-9', '10-14'],
            'Sex': ['Male', 'Female', 'Male'],
            'Population': [100, 200, 150]
        }
        import pandas as pd
        mock_df = pd.DataFrame(mock_data)
        mock_read_csv.return_value = mock_df

        result = load_nz_population_distribution()

        # Check that pandas.read_csv was called
        mock_read_csv.assert_called_once()

        # Check the result structure
        self.assertIsInstance(result, pd.DataFrame)
        self.assertListEqual(list(result.columns), ['age', 'sex', 'count'])

        # Check data transformation
        self.assertEqual(result.iloc[0]['age'], 0)  # '0-4' -> 0
        self.assertEqual(result.iloc[0]['sex'], 'Male')
        self.assertEqual(result.iloc[0]['count'], 100)

    @patch('pandas.read_csv')
    def test_load_nz_life_table_hazards(self, mock_read_csv):
        """Test loading NZ life table hazards data."""
        # Mock the CSV data
        mock_data = {
            'Sex': ['Male', 'Male', 'Female', 'Female'],
            'Age': [0, 1, 0, 1],
            'nMx': [0.01, 0.02, 0.005, 0.015]
        }
        import pandas as pd
        mock_df = pd.DataFrame(mock_data)
        mock_read_csv.return_value = mock_df

        result = load_nz_life_table_hazards()

        # Check that pandas.read_csv was called
        mock_read_csv.assert_called_once()

        # Check the result structure
        self.assertIsInstance(result, dict)
        self.assertIn('Male', result)
        self.assertIn('Female', result)

        # Check data transformation
        self.assertEqual(len(result['Male']), 2)
        self.assertEqual(len(result['Female']), 2)
        self.assertEqual(result['Male'][0], 0.01)  # Age 0 for Male
        self.assertEqual(result['Male'][1], 0.02)  # Age 1 for Male


if __name__ == "__main__":
    unittest.main()
