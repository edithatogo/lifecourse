import unittest
import tempfile
import os
from lifecourseid.data_loader import load_scenarios_from_yaml, apply_scenario_overrides


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


if __name__ == "__main__":
    unittest.main()
