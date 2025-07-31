import yaml
import os
from .simulation_configs import DEFAULT_CONFIG, MINIMAL_TEST_CONFIG


def load_config(config_name=None, config_file_path=None):
    """
    Loads simulation configuration.

    Args:
        config_name (str, optional): Name of a predefined configuration (e.g., 'DEFAULT_CONFIG').
                                     If provided, overrides default settings.
        config_file_path (str, optional): Path to a YAML configuration file.
                                          If provided, overrides settings from config_name.

    Returns:
        dict: The loaded and validated configuration dictionary.

    Raises:
        ValueError: If an unknown config_name is provided or a required key is missing.
        FileNotFoundError: If config_file_path does not exist.
    """
    config = DEFAULT_CONFIG.copy()

    if config_name:
        if config_name == "DEFAULT_CONFIG":
            pass  # Already loaded
        elif config_name == "MINIMAL_TEST_CONFIG":
            config.update(MINIMAL_TEST_CONFIG)
        else:
            raise ValueError(f"Unknown configuration name: {config_name}")

    if config_file_path:
        if not os.path.exists(config_file_path):
            raise FileNotFoundError(f"Configuration file not found: {config_file_path}")
        with open(config_file_path, "r") as f:
            file_config = yaml.safe_load(f)
        if file_config:
            config.update(file_config)

    # Basic validation: Ensure essential keys are present
    required_keys = [
        "POP_SIZE",
        "PSA_N",
        "SIMULATION_YEARS",
        "CALIBRATION_POP_SIZE",
        "STRUCTURAL_UNCERTAINTY_POP_SIZE",
    ]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration key: {key}")

    # Type validation (example for a few keys)
    if not isinstance(config["POP_SIZE"], int) or config["POP_SIZE"] < 0:
        raise ValueError("POP_SIZE must be a non-negative integer.")
    if (
        not isinstance(config["SIMULATION_YEARS"], int)
        or config["SIMULATION_YEARS"] <= 0
    ):
        raise ValueError("SIMULATION_YEARS must be a positive integer.")

    return config
