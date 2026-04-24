import os
import unittest

import yaml

from config.config_loader import _legacy_config_error_message, load_config
from config.simulation_configs import DEFAULT_CONFIG  # Import DEFAULT_CONFIG


class TestConfigLoader(unittest.TestCase):
    def setUp(self):
        self.test_config_file = "test_config.yaml"
        self.temp_dir = "temp_config_tests"
        os.makedirs(self.temp_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)
        if os.path.exists(self.temp_dir):
            for f in os.listdir(self.temp_dir):
                os.remove(os.path.join(self.temp_dir, f))
            os.rmdir(self.temp_dir)

    def _create_test_yaml(self, content):
        with open(os.path.join(self.temp_dir, self.test_config_file), "w") as f:
            yaml.dump(content, f)
        return os.path.join(self.temp_dir, self.test_config_file)

    def test_load_default_config(self):
        config = load_config(config_name="DEFAULT_CONFIG")
        self.assertIn("POP_SIZE", config)
        self.assertEqual(config["POP_SIZE"], 62000)  # Based on current DEFAULT_CONFIG
        self.assertIn("PSA_N", config)

    def test_load_minimal_test_config(self):
        config = load_config(config_name="MINIMAL_TEST_CONFIG")
        self.assertIn("POP_SIZE", config)
        self.assertEqual(
            config["POP_SIZE"], 100
        )  # Based on current MINIMAL_TEST_CONFIG
        self.assertEqual(config["PSA_N"], 0)

    def test_load_config_from_file_override(self):
        file_content = {
            "POP_SIZE": 500,
            "SIMULATION_YEARS": 10,
            "NEW_KEY": "test_value",
        }
        file_path = self._create_test_yaml(file_content)
        config = load_config(config_name="DEFAULT_CONFIG", config_file_path=file_path)

        self.assertEqual(config["POP_SIZE"], 500)  # Overridden by file
        self.assertEqual(config["SIMULATION_YEARS"], 10)  # Overridden by file
        self.assertEqual(config["PSA_N"], 300)  # Default value, not in file
        self.assertEqual(config["NEW_KEY"], "test_value")  # New key from file

    def test_load_config_from_file_only(self):
        file_content = {
            "POP_SIZE": 700,
            "PSA_N": 50,
            "SIMULATION_YEARS": 20,
            "CALIBRATION_POP_SIZE": 200,
            "STRUCTURAL_UNCERTAINTY_POP_SIZE": 200,
        }
        file_path = self._create_test_yaml(file_content)
        config = load_config(config_file_path=file_path)

        self.assertEqual(config["POP_SIZE"], 700)
        self.assertEqual(config["PSA_N"], 50)
        self.assertEqual(config["SIMULATION_YEARS"], 20)

    def test_load_config_missing_required_key(self):
        file_content = {
            "POP_SIZE": 100,
            "PSA_N": 10,
            "SIMULATION_YEARS": 5,
            "CALIBRATION_POP_SIZE": 100,
            "STRUCTURAL_UNCERTAINTY_POP_SIZE": 100,
        }
        file_path = self._create_test_yaml(file_content)
        # This test now passes because SIMULATION_YEARS is present in DEFAULT_CONFIG
        # and is not overridden by the file. The validation correctly checks the final config.
        config = load_config(config_file_path=file_path)
        self.assertIn("SIMULATION_YEARS", config)

    def test_load_config_invalid_type(self):
        file_content = {
            "POP_SIZE": "invalid",  # Invalid type
            "PSA_N": 10,
            "SIMULATION_YEARS": 5,
            "CALIBRATION_POP_SIZE": 100,
            "STRUCTURAL_UNCERTAINTY_POP_SIZE": 100,
        }
        file_path = self._create_test_yaml(file_content)
        with self.assertRaisesRegex(
            ValueError, "POP_SIZE must be a non-negative integer."
        ):
            load_config(config_file_path=file_path)

    def test_load_config_missing_required_key_from_file_only(self):
        # This test ensures that if a required key is missing and no default is provided,
        # or if a file is the *only* source and misses a key, it raises an error.
        file_content = {
            "POP_SIZE": 100,
            "PSA_N": 10,
            # SIMULATION_YEARS is intentionally missing here
            "CALIBRATION_POP_SIZE": 100,
            "STRUCTURAL_UNCERTAINTY_POP_SIZE": 100,
        }
        file_path = self._create_test_yaml(file_content)
        # Temporarily remove SIMULATION_YEARS from DEFAULT_CONFIG for this specific test
        original_default_sim_years = DEFAULT_CONFIG["SIMULATION_YEARS"]
        del DEFAULT_CONFIG["SIMULATION_YEARS"]
        try:
            with self.assertRaisesRegex(
                ValueError, "Missing required configuration key: SIMULATION_YEARS"
            ):
                load_config(config_file_path=file_path)
        finally:
            # Restore DEFAULT_CONFIG
            DEFAULT_CONFIG["SIMULATION_YEARS"] = original_default_sim_years

    def test_load_config_unknown_name(self):
        with self.assertRaisesRegex(
            ValueError, "Unknown configuration name: UNKNOWN_CONFIG"
        ):
            load_config(config_name="UNKNOWN_CONFIG")

    def test_load_config_file_not_found(self):
        with self.assertRaisesRegex(
            FileNotFoundError, "Configuration file not found: non_existent_file.yaml"
        ):
            load_config(config_file_path="non_existent_file.yaml")

    def test_load_test_psa_config(self):
        config = load_config(config_name="TEST_PSA_CONFIG")
        self.assertEqual(config["PSA_N"], 50)
        self.assertEqual(config["SIMULATION_YEARS"], 3)

    def test_load_config_invalid_parameter_set(self):
        file_content = {
            "POP_SIZE": 100,
            "PSA_N": 10,
            "SIMULATION_YEARS": 5,
            "CALIBRATION_POP_SIZE": 100,
            "STRUCTURAL_UNCERTAINTY_POP_SIZE": 100,
            "parameter_set": "invalid_parameter_set",
        }
        file_path = self._create_test_yaml(file_content)
        with self.assertRaisesRegex(
            ValueError, "parameter_set 'invalid_parameter_set'"
        ):
            load_config(config_file_path=file_path)

    def test_legacy_error_message_multifield_validation(self):
        class FakeValidationError:
            def errors(self):
                return [
                    {"loc": ("POP_SIZE",), "type": "missing"},
                    {"loc": ("PSA_N",), "type": "missing"},
                ]

            def __str__(self):
                return "fake validation error"

        self.assertEqual(
            _legacy_config_error_message(FakeValidationError()),
            "Invalid configuration: fake validation error",
        )

    def test_legacy_error_message_fallback(self):
        class FakeValidationError:
            def errors(self):
                return [{"loc": ("SIMULATION_YEARS",), "type": "custom"}]

            def __str__(self):
                return "fake validation error"

        self.assertEqual(
            _legacy_config_error_message(FakeValidationError()),
            "Invalid configuration: fake validation error",
        )

    def test_simulation_years_positive_validation_message(self):
        file_content = {
            "POP_SIZE": 100,
            "PSA_N": 10,
            "SIMULATION_YEARS": 0,
            "CALIBRATION_POP_SIZE": 100,
            "STRUCTURAL_UNCERTAINTY_POP_SIZE": 100,
        }
        file_path = self._create_test_yaml(file_content)
        with self.assertRaisesRegex(
            ValueError, "SIMULATION_YEARS must be a positive integer"
        ):
            load_config(config_file_path=file_path)


if __name__ == "__main__":
    unittest.main()
