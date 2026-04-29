"""
Parameter Validation Module

This module provides validation for dynamically loaded parameter sets to ensure
they are compatible and complete for the lifecourse simulation.
"""

from typing import Any


class ParameterValidator:
    """
    Validator for parameter sets to ensure compatibility and completeness.

    Checks that parameter modules have required attributes and that
    parameter values are within reasonable ranges.
    """

    def __init__(self):
        self.required_attributes = [
            "DISTRIBUTIONS",
            "START_YEAR",
            "END_YEAR",
            "POP_SIZE",
            "DISCOUNT",
            "sample_params_from_dist",
            "get_mean_params",
        ]

        # Define expected parameter ranges for validation
        self.parameter_ranges = {
            "START_YEAR": (2000, 2050),
            "END_YEAR": (2050, 2150),
            "POP_SIZE": (1000, 100000),
            "DISCOUNT": (0.0, 0.1),
        }

        # Required distribution parameters (subset that must exist)
        self.required_distribution_keys = [
            "familial_prop",
            "yield_wgs",
            "severity_mild_prop",
            "mort_hr_mild",
            "mort_hr_severe",
            "u_base_mild",
            "u_base_severe",
        ]

    def validate_parameter_module(
        self, param_module: Any, parameter_set_name: str
    ) -> list[str]:
        """
        Validate a parameter module for completeness and compatibility.

        Args:
            param_module: The parameter module to validate
            parameter_set_name: Name of the parameter set (for error messages)

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check required attributes
        for attr in self.required_attributes:
            if not hasattr(param_module, attr):
                errors.append(f"Missing required attribute: {attr}")

        # If basic attributes are missing, can't continue validation
        if errors:
            return errors

        # Validate parameter ranges
        range_errors = self._validate_parameter_ranges(param_module, parameter_set_name)
        errors.extend(range_errors)

        # Validate distributions
        dist_errors = self._validate_distributions(param_module, parameter_set_name)
        errors.extend(dist_errors)

        return errors

    def _validate_parameter_ranges(
        self, param_module: Any, parameter_set_name: str
    ) -> list[str]:
        """Validate that parameters are within expected ranges."""
        errors = []

        for param_name, (min_val, max_val) in self.parameter_ranges.items():
            if hasattr(param_module, param_name):
                value = getattr(param_module, param_name)
                if not isinstance(value, int | float):
                    errors.append(f"{param_name} must be numeric, got {type(value)}")
                elif not (min_val <= value <= max_val):
                    errors.append(
                        f"{param_name}={value} is outside expected range [{min_val}, {max_val}]"
                    )

        # Additional validation for END_YEAR > START_YEAR
        if (
            hasattr(param_module, "START_YEAR")
            and hasattr(param_module, "END_YEAR")
            and param_module.END_YEAR <= param_module.START_YEAR
        ):
            errors.append(
                f"END_YEAR ({param_module.END_YEAR}) must be greater than "
                f"START_YEAR ({param_module.START_YEAR})"
            )

        return errors

    def _validate_distributions(
        self, param_module: Any, parameter_set_name: str
    ) -> list[str]:
        """Validate that required distributions exist and are properly formatted."""
        errors = []

        if not hasattr(param_module, "DISTRIBUTIONS"):
            return errors  # Already caught in attribute validation

        distributions = param_module.DISTRIBUTIONS

        # Check required distribution keys exist
        for key in self.required_distribution_keys:
            if key not in distributions:
                errors.append(f"Missing required distribution parameter: {key}")

        # Validate distribution formats
        for param_name, dist_info in distributions.items():
            if not isinstance(dist_info, dict):
                errors.append(f"Distribution for {param_name} must be a dictionary")
                continue

            # Check for required distribution keys
            if "dist" not in dist_info and not any(
                k in dist_info for k in ["alpha", "beta", "loc", "scale", "s"]
            ):
                errors.append(
                    f"Distribution for {param_name} missing distribution specification"
                )

            # For beta distributions, check alpha/beta parameters
            if dist_info.get("dist") == "beta" and (
                "alpha" not in dist_info or "beta" not in dist_info
            ):
                errors.append(
                    f"Beta distribution for {param_name} missing alpha/beta parameters"
                )

        return errors

    def validate_compatibility(
        self, param_module1: Any, param_module2: Any, name1: str, name2: str
    ) -> list[str]:
        """
        Validate compatibility between two parameter sets.

        Args:
            param_module1: First parameter module
            param_module2: Second parameter module
            name1: Name of first parameter set
            name2: Name of second parameter set

        Returns:
            List of compatibility issues
        """
        errors = []

        # Check that both have same distribution parameters
        if hasattr(param_module1, "DISTRIBUTIONS") and hasattr(
            param_module2, "DISTRIBUTIONS"
        ):
            keys1 = set(param_module1.DISTRIBUTIONS.keys())
            keys2 = set(param_module2.DISTRIBUTIONS.keys())

            if keys1 != keys2:
                missing_in_2 = keys1 - keys2
                missing_in_1 = keys2 - keys1

                if missing_in_2:
                    errors.append(
                        f"Parameters in {name1} but missing in {name2}: {missing_in_2}"
                    )
                if missing_in_1:
                    errors.append(
                        f"Parameters in {name2} but missing in {name1}: {missing_in_1}"
                    )

        # Check that START_YEAR matches (important for temporal consistency)
        if (
            hasattr(param_module1, "START_YEAR")
            and hasattr(param_module2, "START_YEAR")
            and param_module1.START_YEAR != param_module2.START_YEAR
        ):
            errors.append(
                f"START_YEAR mismatch: {name1}={param_module1.START_YEAR}, "
                f"{name2}={param_module2.START_YEAR}"
            )

        return errors


# Global validator instance
_parameter_validator = ParameterValidator()


def get_parameter_validator() -> ParameterValidator:
    """Get the global parameter validator instance."""
    return _parameter_validator


def validate_parameter_set(param_module: Any, parameter_set_name: str) -> list[str]:
    """
    Convenience function to validate a parameter set.

    Args:
        param_module: Parameter module to validate
        parameter_set_name: Name of the parameter set

    Returns:
        List of validation errors (empty if valid)
    """
    validator = get_parameter_validator()
    return validator.validate_parameter_module(param_module, parameter_set_name)


def validate_parameter_compatibility(
    param_module1: Any, param_module2: Any, name1: str, name2: str
) -> list[str]:
    """
    Convenience function to validate compatibility between parameter sets.

    Args:
        param_module1: First parameter module
        param_module2: Second parameter module
        name1: Name of first parameter set
        name2: Name of second parameter set

    Returns:
        List of compatibility issues
    """
    validator = get_parameter_validator()
    return validator.validate_compatibility(param_module1, param_module2, name1, name2)
