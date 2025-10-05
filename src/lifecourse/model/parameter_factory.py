"""
Dynamic Parameter Loading System

This module provides a factory pattern for dynamically loading parameter sets
based on configuration, enabling country-specific or custom parameter configurations.
"""

import importlib
from typing import Dict, Any
from .parameter_validation import validate_parameter_set


class ParameterFactory:
    """
    Factory for loading parameter modules dynamically based on configuration.

    Supports loading different parameter sets (e.g., Australia, New Zealand, custom)
    through a registry system.
    """
    
    def __init__(self):
        self._registry = {}
        self._register_default_parameter_sets()
    
    def _register_default_parameter_sets(self):
        """Register the default parameter sets available in the system."""
        self.register_parameter_set("australia", "lifecourse.model.parameters")
        self.register_parameter_set("nz", "lifecourse.model.parameters_nz")
        self.register_parameter_set("new_zealand", "lifecourse.model.parameters_nz")
    
    def register_parameter_set(self, name: str, module_path: str):
        """
        Register a parameter set by name and module path.
        
        Args:
            name: Identifier for the parameter set (e.g., 'australia', 'nz')
            module_path: Full module path (e.g., 'lifecourse.model.parameters')
        """
        self._registry[name.lower()] = module_path
    
    def get_available_parameter_sets(self) -> list[str]:
        """Return list of available parameter set names."""
        return list(self._registry.keys())
    
    def load_parameter_set(self, parameter_set_name: str) -> Any:
        """
        Dynamically load a parameter module by name.
        
        Args:
            parameter_set_name: Name of the parameter set to load
        
        Returns:
            The loaded parameter module
        
        Raises:
            ValueError: If parameter set is not registered
            ImportError: If module cannot be imported
        """
        if parameter_set_name.lower() not in self._registry:
            available = self.get_available_parameter_sets()
            raise ValueError(
                f"Unknown parameter set '{parameter_set_name}'. "
                f"Available sets: {available}"
            )
        
        module_path = self._registry[parameter_set_name.lower()]
        
        try:
            # Import the module dynamically
            module = importlib.import_module(module_path)

            # Validate that it has required attributes
            self._validate_parameter_module(module, parameter_set_name)

            # Additional validation for parameter completeness
            validation_errors = validate_parameter_set(module, parameter_set_name)
            if validation_errors:
                raise ValueError(
                    f"Parameter validation failed for '{parameter_set_name}':\n" +
                    "\n".join(f"  - {error}" for error in validation_errors)
                )

            return module

        except ImportError as e:
            raise ImportError(
                f"Failed to import parameter module '{module_path}' "
                f"for parameter set '{parameter_set_name}': {e}"
            )
    
    def _validate_parameter_module(self, module: Any, parameter_set_name: str):
        """
        Validate that a parameter module has the required attributes.
        
        Args:
            module: The loaded parameter module
            parameter_set_name: Name of the parameter set (for error messages)
        
        Raises:
            ValueError: If required attributes are missing
        """
        required_attributes = [
            'DISTRIBUTIONS',
            'START_YEAR', 
            'END_YEAR',
            'POP_SIZE',
            'DISCOUNT',
            'sample_params_from_dist',
            'get_mean_params'
        ]
        
        missing_attributes = []
        for attr in required_attributes:
            if not hasattr(module, attr):
                missing_attributes.append(attr)
        
        if missing_attributes:
            raise ValueError(
                f"Parameter module for '{parameter_set_name}' is missing "
                f"required attributes: {missing_attributes}"
            )


# Global factory instance
_parameter_factory = ParameterFactory()


def get_parameter_factory() -> ParameterFactory:
    """Get the global parameter factory instance."""
    return _parameter_factory


def load_parameters_from_config(config: Dict[str, Any]) -> Any:
    """
    Load parameter module based on configuration.
    
    Args:
        config: Configuration dictionary that may contain 'parameter_set' key
    
    Returns:
        The loaded parameter module
    """
    # Default to 'australia' if not specified
    parameter_set = config.get('parameter_set', 'australia')
    
    factory = get_parameter_factory()
    return factory.load_parameter_set(parameter_set)


def register_custom_parameter_set(name: str, module_path: str):
    """
    Register a custom parameter set.
    
    Args:
        name: Identifier for the custom parameter set
        module_path: Full module path to the parameter module
    """
    factory = get_parameter_factory()
    factory.register_parameter_set(name, module_path)
