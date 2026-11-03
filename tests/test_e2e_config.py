import os
import sys
import tempfile
import unittest

import yaml

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config.config_loader import load_config
from lifecourse.data_loader import apply_scenario_overrides, load_scenarios_from_yaml


class TestE2EConfig(unittest.TestCase):
    """End-to-end tests for configuration loading and scenario overrides."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_load_config_default(self):
        """Test loading default configuration."""
        config = load_config()
        self.assertIsInstance(config, dict)
        self.assertIn("POP_SIZE", config)
        self.assertIn("PSA_N", config)
        self.assertIn("SIMULATION_YEARS", config)

    def test_load_config_minimal_test(self):
        """Test loading MINIMAL_TEST_CONFIG."""
        config = load_config("MINIMAL_TEST_CONFIG")
        self.assertEqual(config["POP_SIZE"], 100)
        self.assertEqual(config["PSA_N"], 0)
        self.assertEqual(config["SIMULATION_YEARS"], 5)

    def test_load_config_from_file(self):
        """Test loading configuration from YAML file."""
        config_data = {
            "POP_SIZE": 200,
            "PSA_N": 10,
            "SIMULATION_YEARS": 10,
        }
        with open("test_config.yaml", "w") as f:
            yaml.safe_dump(config_data, f)

        config = load_config(config_file_path="test_config.yaml")
        self.assertEqual(config["POP_SIZE"], 200)
        self.assertEqual(config["PSA_N"], 10)
        self.assertEqual(config["SIMULATION_YEARS"], 10)

    def test_load_config_invalid_name(self):
        """Test loading invalid configuration name raises ValueError."""
        with self.assertRaises(ValueError):
            load_config("INVALID_CONFIG")

    def test_load_config_missing_file(self):
        """Test loading from missing file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_config(config_file_path="nonexistent.yaml")

    def test_load_config_invalid_pop_size(self):
        """Test loading config with invalid POP_SIZE raises ValueError."""
        config_data = {
            "POP_SIZE": -1,  # Invalid negative value
            "PSA_N": 10,
            "SIMULATION_YEARS": 10,
        }
        with open("invalid_config.yaml", "w") as f:
            yaml.safe_dump(config_data, f)

        with self.assertRaises(ValueError):
            load_config(config_file_path="invalid_config.yaml")

    def test_load_scenarios_from_yaml(self):
        """Test loading scenarios from YAML file."""
        scenarios_data = {
            "scenarios": {
                "base": {"familial_prop": None, "yield_wgs": None},
                "high_familial": {"familial_prop": 0.2, "yield_wgs": None},
                "low_yield": {"familial_prop": None, "yield_wgs": 0.4},
            },
            "scenario_grid": {
                "familial_prop": [0.1, 0.2],
                "yield_wgs": [0.5, 0.6],
            },
        }
        with open("scenarios.yaml", "w") as f:
            yaml.safe_dump(scenarios_data, f)

        scenarios = load_scenarios_from_yaml("scenarios.yaml")
        self.assertIn("base", scenarios)
        self.assertIn("high_familial", scenarios)
        self.assertIn("low_yield", scenarios)
        # Grid scenarios should be expanded
        self.assertGreater(len(scenarios), 3)

    def test_apply_scenario_overrides_relative(self):
        """Test applying relative scenario overrides."""
        base_params = {"familial_prop": 0.1, "yield_wgs": 0.5, "min_test_age": 20}
        overrides = {"familial_prop": 0.05, "yield_wgs": -0.1}  # Relative adjustments

        result = apply_scenario_overrides(base_params, overrides)
        self.assertAlmostEqual(result["familial_prop"], 0.15)  # 0.1 + 0.05
        self.assertAlmostEqual(result["yield_wgs"], 0.4)  # 0.5 - 0.1
        self.assertEqual(result["min_test_age"], 20)  # Unchanged

    def test_apply_scenario_overrides_absolute(self):
        """Test applying absolute scenario overrides."""
        base_params = {"familial_prop": 0.1, "yield_wgs": 0.5, "min_test_age": 20}
        overrides = {
            "familial_prop": 0.7,
            "yield_wgs": 0.8,
            "min_test_age": 25,
        }  # Absolute values (>0.5)

        result = apply_scenario_overrides(base_params, overrides)
        self.assertEqual(result["familial_prop"], 0.7)
        self.assertEqual(result["yield_wgs"], 0.8)
        self.assertEqual(result["min_test_age"], 25)

    def test_apply_scenario_overrides_mixed(self):
        """Test applying mixed relative and absolute overrides."""
        base_params = {"familial_prop": 0.1, "yield_wgs": 0.5, "min_test_age": 20}
        overrides = {
            "familial_prop": 0.02,
            "yield_wgs": 0.8,
            "min_test_age": 25,
        }  # Mixed (0.02 relative, 0.8 absolute)

        result = apply_scenario_overrides(base_params, overrides)
        self.assertAlmostEqual(result["familial_prop"], 0.12)  # Relative: 0.1 + 0.02
        self.assertEqual(result["yield_wgs"], 0.8)  # Absolute
        self.assertEqual(result["min_test_age"], 25)  # Absolute

    def test_apply_scenario_overrides_none_values(self):
        """Test applying overrides with None values (use base)."""
        base_params = {"familial_prop": 0.1, "yield_wgs": 0.5}
        overrides = {"familial_prop": None, "yield_wgs": 0.02}  # None means use base

        result = apply_scenario_overrides(base_params, overrides)
        self.assertEqual(result["familial_prop"], 0.1)  # Unchanged
        self.assertEqual(result["yield_wgs"], 0.52)  # Relative adjustment

    def test_scenario_grid_expansion(self):
        """Test that scenario grid generates all combinations."""
        scenarios_data = {
            "scenarios": {"base": {}},
            "scenario_grid": {
                "familial_prop": [0.1, 0.2],
                "yield_wgs": [0.5, 0.6],
            },
        }
        with open("scenarios.yaml", "w") as f:
            yaml.safe_dump(scenarios_data, f)

        scenarios = load_scenarios_from_yaml("scenarios.yaml")
        # Should have base + 4 grid combinations
        self.assertEqual(len(scenarios), 5)
        # Check that grid scenarios exist (dots become underscores)
        expected_names = [
            "base",
            "familial_prop_0_1_yield_wgs_0_5",
            "familial_prop_0_1_yield_wgs_0_6",
            "familial_prop_0_2_yield_wgs_0_5",
            "familial_prop_0_2_yield_wgs_0_6",
        ]
        for name in expected_names:
            self.assertIn(name, scenarios)


if __name__ == "__main__":
    unittest.main()
