import logging
import os
from typing import Any

import yaml
from lifecourse.config_validation import SimulationConfig
from pydantic import ValidationError

from .simulation_configs import DEFAULT_CONFIG, MINIMAL_TEST_CONFIG, TEST_PSA_CONFIG

_LOG = logging.getLogger(__name__)

# Try import without mutating sys.path; if that fails we gracefully fall back
# to a best-effort None factory. Tests and local dev should prefer installing
# the package in editable mode instead of depending on sys.path hacks.
try:
    from lifecourse.model.parameter_factory import get_parameter_factory
except Exception:  # pragma: no cover - environment dependent
    _LOG.debug(
        "Could not import lifecourse.model.parameter_factory; parameter factory disabled"
    )
    get_parameter_factory = None


def _legacy_config_error_message(exc: ValidationError) -> str:
    """Map common validation failures to the repo's legacy error contract."""
    errors = exc.errors()
    if len(errors) != 1:
        return f"Invalid configuration: {exc}"

    error = errors[0]
    field = str(error.get("loc", ("configuration",))[0])
    error_type = error.get("type", "")

    if error_type == "missing":
        return f"Missing required configuration key: {field}"

    if error_type in {"int_parsing", "int_type", "int_from_float"}:
        return f"{field} must be a non-negative integer."

    if error_type == "greater_than_equal":
        return f"{field} must be a non-negative integer."

    if error_type == "greater_than":
        return f"{field} must be a positive integer."

    return f"Invalid configuration: {exc}"


def load_config(
    config_name: str | None = None, config_file_path: str | None = None
) -> dict[str, Any]:
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
        elif config_name == "TEST_PSA_CONFIG":
            config.update(TEST_PSA_CONFIG)
        else:
            raise ValueError(f"Unknown configuration name: {config_name}")

    if config_file_path:
        if not os.path.exists(config_file_path):
            raise FileNotFoundError(f"Configuration file not found: {config_file_path}")
        with open(config_file_path) as f:
            file_config = yaml.safe_load(f)
        if file_config:
            config.update(file_config)

    try:
        validated_config = SimulationConfig.model_validate(config)
    except ValidationError as exc:
        raise ValueError(_legacy_config_error_message(exc)) from exc

    config = validated_config.model_dump()

    # Validate parameter_set if parameter factory is available
    if get_parameter_factory is not None:
        factory = get_parameter_factory()
        available_sets = factory.get_available_parameter_sets()
        if config["parameter_set"] not in available_sets:
            raise ValueError(
                f"parameter_set '{config['parameter_set']}' is not valid. "
                f"Available sets: {available_sets}"
            )

    return config
