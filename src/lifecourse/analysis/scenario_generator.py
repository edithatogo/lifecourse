"""
Dynamic Scenario Generation for LifeCourseID Microsimulation Model

This module provides automated scenario creation from configuration templates,
supporting statistical distributions, scenario families, and complex parameter
variations for health economic evaluation.
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from itertools import product
import random


@dataclass
class ScenarioTemplate:
    """Template for generating scenarios with parameter specifications."""

    name: str
    description: str
    base_parameters: Dict[str, Any]
    variable_parameters: Dict[str, Union[List[Any], Dict[str, Any]]]
    generation_method: str = "grid"  # grid, random, distribution
    sample_size: Optional[int] = None


@dataclass
class ScenarioFamily:
    """Family of related scenarios with inheritance."""

    name: str
    description: str
    base_scenario: Dict[str, Any]
    variations: Dict[str, Dict[str, Any]]
    inheritance_mode: str = "override"  # override, additive, multiplicative


class ScenarioGenerator(ABC):
    """Abstract base class for scenario generators."""

    @abstractmethod
    def generate_scenarios(self, config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Generate scenarios from configuration."""
        pass


class GridScenarioGenerator(ScenarioGenerator):
    """Generate scenarios from parameter grids."""

    def generate_scenarios(self, config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Generate scenarios from grid specification."""
        parameters = config.get("parameters", {})
        scenarios = {}

        # Extract parameter names and values
        param_names = list(parameters.keys())
        param_values = [parameters[name] for name in param_names]

        # Generate all combinations
        for combo in product(*param_values):
            scenario_name = "_".join(
                [
                    f"{name}_{str(value).replace('.', '_')}"
                    for name, value in zip(param_names, combo)
                ]
            )

            scenario_overrides = dict(zip(param_names, combo))
            scenarios[scenario_name] = scenario_overrides

        return scenarios


class DistributionScenarioGenerator(ScenarioGenerator):
    """Generate scenarios by sampling from statistical distributions."""

    def __init__(self, random_seed: int = 42):
        self.random_seed = random_seed
        np.random.seed(random_seed)
        random.seed(random_seed)

    def generate_scenarios(self, config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Generate scenarios by sampling from distributions."""
        parameters = config.get("parameters", {})
        sample_size = config.get("sample_size", 10)
        scenarios = {}

        for i in range(sample_size):
            scenario_overrides = {}
            scenario_name = f"sample_{i+1:03d}"

            for param_name, dist_config in parameters.items():
                value = self._sample_from_distribution(dist_config)
                scenario_overrides[param_name] = value

            scenarios[scenario_name] = scenario_overrides

        return scenarios

    def _sample_from_distribution(self, dist_config: Dict[str, Any]) -> float:
        """Sample a value from a statistical distribution."""
        dist_type = dist_config.get("type", "uniform")
        params = dist_config.get("params", {})

        if dist_type == "uniform":
            return np.random.uniform(params.get("low", 0), params.get("high", 1))
        elif dist_type == "normal":
            return np.random.normal(params.get("mean", 0), params.get("std", 1))
        elif dist_type == "beta":
            return np.random.beta(params.get("alpha", 1), params.get("beta", 1))
        elif dist_type == "gamma":
            return np.random.gamma(params.get("shape", 1), params.get("scale", 1))
        elif dist_type == "lognormal":
            return np.random.lognormal(params.get("mean", 0), params.get("sigma", 1))
        else:
            raise ValueError(f"Unsupported distribution type: {dist_type}")


class TemplateScenarioGenerator(ScenarioGenerator):
    """Generate scenarios from templates with variable substitution."""

    def generate_scenarios(self, config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Generate scenarios from templates."""
        templates = config.get("templates", [])
        scenarios = {}

        for template_config in templates:
            template = ScenarioTemplate(**template_config)
            generated = self._generate_from_template(template)
            scenarios.update(generated)

        return scenarios

    def _generate_from_template(
        self, template: ScenarioTemplate
    ) -> Dict[str, Dict[str, Any]]:
        """Generate scenarios from a single template."""
        scenarios = {}

        if template.generation_method == "grid":
            # Generate grid combinations
            param_names = list(template.variable_parameters.keys())
            param_values = [template.variable_parameters[name] for name in param_names]

            for combo in product(*param_values):
                scenario_name = f"{template.name}_{'_'.join([str(v).replace('.', '_') for v in combo])}"
                scenario_overrides = dict(zip(param_names, combo))
                scenarios[scenario_name] = scenario_overrides

        elif template.generation_method == "random":
            sample_size = template.sample_size or 10
            for i in range(sample_size):
                scenario_overrides = {}
                scenario_name = f"{template.name}_sample_{i+1:03d}"

                for param_name, values in template.variable_parameters.items():
                    if isinstance(values, list):
                        scenario_overrides[param_name] = random.choice(values)
                    else:
                        # Assume it's a distribution config
                        scenario_overrides[param_name] = self._sample_from_distribution(
                            values
                        )

                scenarios[scenario_name] = scenario_overrides

        return scenarios

    def _sample_from_distribution(self, dist_config: Dict[str, Any]) -> float:
        """Sample from distribution (simplified version for templates)."""
        dist_type = dist_config.get("type", "uniform")
        params = dist_config.get("params", {})

        if dist_type == "uniform":
            return random.uniform(params.get("low", 0), params.get("high", 1))
        elif dist_type == "choice":
            return random.choice(params.get("values", [0, 1]))
        else:
            return params.get("default", 0)


class FamilyScenarioGenerator(ScenarioGenerator):
    """Generate scenario families with inheritance."""

    def generate_scenarios(self, config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Generate scenarios from family specifications."""
        families = config.get("families", [])
        scenarios = {}

        for family_config in families:
            family = ScenarioFamily(**family_config)
            generated = self._generate_family_scenarios(family)
            scenarios.update(generated)

        return scenarios

    def _generate_family_scenarios(
        self, family: ScenarioFamily
    ) -> Dict[str, Dict[str, Any]]:
        """Generate scenarios for a family."""
        scenarios = {}

        # Base scenario
        scenarios[f"{family.name}_base"] = family.base_scenario.copy()

        # Generate variations
        for var_name, var_overrides in family.variations.items():
            scenario_overrides = self._apply_inheritance(
                family.base_scenario, var_overrides, family.inheritance_mode
            )
            scenarios[f"{family.name}_{var_name}"] = scenario_overrides

        return scenarios

    def _apply_inheritance(
        self, base: Dict[str, Any], overrides: Dict[str, Any], mode: str
    ) -> Dict[str, Any]:
        """Apply inheritance rules to generate scenario overrides."""
        result = base.copy()

        for key, value in overrides.items():
            if mode == "override":
                result[key] = value
            elif mode == "additive" and key in base:
                if isinstance(base[key], (int, float)) and isinstance(
                    value, (int, float)
                ):
                    result[key] = base[key] + value
                else:
                    result[key] = value
            elif mode == "multiplicative" and key in base:
                if isinstance(base[key], (int, float)) and isinstance(
                    value, (int, float)
                ):
                    result[key] = base[key] * value
                else:
                    result[key] = value
            else:
                result[key] = value

        return result


class DynamicScenarioManager:
    """Main manager for dynamic scenario generation."""

    def __init__(self):
        self.generators = {
            "grid": GridScenarioGenerator(),
            "distribution": DistributionScenarioGenerator(),
            "template": TemplateScenarioGenerator(),
            "family": FamilyScenarioGenerator(),
        }

    def generate_scenarios(self, config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Generate scenarios from dynamic configuration."""
        all_scenarios = {}

        # Process each generation type
        for gen_type, gen_config in config.items():
            if gen_type in self.generators:
                generator = self.generators[gen_type]
                scenarios = generator.generate_scenarios(gen_config)
                all_scenarios.update(scenarios)

        return all_scenarios

    def add_generator(self, name: str, generator: ScenarioGenerator):
        """Add a custom scenario generator."""
        self.generators[name] = generator


# Global instance for easy access
_scenario_manager = None


def get_scenario_manager() -> DynamicScenarioManager:
    """Get the global scenario manager instance."""
    global _scenario_manager
    if _scenario_manager is None:
        _scenario_manager = DynamicScenarioManager()
    return _scenario_manager
