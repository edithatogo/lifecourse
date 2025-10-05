"""
Parameter Loader Module

This module provides a clean interface for loading parameter modules dynamically
based on configuration, replacing hardcoded parameter imports throughout the codebase.
"""

from typing import Dict, Any
from .parameter_factory import load_parameters_from_config


class ParameterLoader:
    """
    Loader for parameter modules with caching and validation.

    Provides a clean interface for loading parameters based on configuration,
    with caching to avoid repeated imports.
    """

    def __init__(self):
        self._cache = {}

    def load_parameters(self, config: Dict[str, Any]) -> Any:
        """
        Load parameter module based on configuration.

        Args:
            config: Configuration dictionary containing parameter_set

        Returns:
            The loaded parameter module
        """
        parameter_set = config.get("parameter_set", "australia")

        # Check cache first
        if parameter_set in self._cache:
            return self._cache[parameter_set]

        # Load and cache
        param_module = load_parameters_from_config(config)
        self._cache[parameter_set] = param_module

        return param_module

    def clear_cache(self):
        """Clear the parameter module cache."""
        self._cache.clear()

    def get_cached_parameter_sets(self) -> list[str]:
        """Return list of currently cached parameter sets."""
        return list(self._cache.keys())


# Global loader instance
_parameter_loader = ParameterLoader()


def get_parameter_loader() -> ParameterLoader:
    """Get the global parameter loader instance."""
    return _parameter_loader


def load_parameters(config: Dict[str, Any]) -> Any:
    """
    Convenience function to load parameters from configuration.

    Args:
        config: Configuration dictionary

    Returns:
        The loaded parameter module
    """
    loader = get_parameter_loader()
    return loader.load_parameters(config)


def get_parameter_attributes(config: Dict[str, Any], *attributes: str) -> tuple:
    """
    Load parameters and extract specific attributes.

    Args:
        config: Configuration dictionary
        *attributes: Attribute names to extract from the parameter module

    Returns:
        Tuple of requested attributes

    Example:
        DISTRIBUTIONS, START_YEAR, POP_SIZE = get_parameter_attributes(
            config, 'DISTRIBUTIONS', 'START_YEAR', 'POP_SIZE'
        )
    """
    param_module = load_parameters(config)

    values = []
    for attr in attributes:
        if not hasattr(param_module, attr):
            raise AttributeError(
                f"Parameter module for '{config.get('parameter_set', 'australia')}' "
                f"does not have attribute '{attr}'"
            )
        values.append(getattr(param_module, attr))

    return tuple(values)
