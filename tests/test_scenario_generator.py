"""
Tests for Dynamic Scenario Generation functionality.
"""

import os
import tempfile
from unittest.mock import patch

from lifecourse.analysis.scenario_generator import (
    DistributionScenarioGenerator,
    DynamicScenarioManager,
    FamilyScenarioGenerator,
    GridScenarioGenerator,
    TemplateScenarioGenerator,
    get_scenario_manager,
)
from lifecourse.data_loader import load_scenarios_from_yaml


class TestGridScenarioGenerator:
    """Test grid-based scenario generation."""

    def test_generate_scenarios(self):
        generator = GridScenarioGenerator()
        config = {"parameters": {"param_a": [1, 2], "param_b": [0.1, 0.2]}}

        scenarios = generator.generate_scenarios(config)

        # Should generate 2 * 2 = 4 scenarios
        assert len(scenarios) == 4
        assert "param_a_1_param_b_0_1" in scenarios
        assert "param_a_2_param_b_0_2" in scenarios

        # Check parameter values
        scenario = scenarios["param_a_1_param_b_0_1"]
        assert scenario["param_a"] == 1
        assert scenario["param_b"] == 0.1


class TestDistributionScenarioGenerator:
    """Test distribution-based scenario generation."""

    def test_generate_scenarios_uniform(self):
        generator = DistributionScenarioGenerator(random_seed=42)
        config = {
            "sample_size": 3,
            "parameters": {
                "param_a": {"type": "uniform", "params": {"low": 0.0, "high": 1.0}}
            },
        }

        scenarios = generator.generate_scenarios(config)

        assert len(scenarios) == 3
        for name, overrides in scenarios.items():
            assert "sample_" in name
            assert 0.0 <= overrides["param_a"] <= 1.0

    def test_generate_scenarios_beta(self):
        generator = DistributionScenarioGenerator(random_seed=42)
        config = {
            "sample_size": 2,
            "parameters": {
                "param_a": {"type": "beta", "params": {"alpha": 2.0, "beta": 2.0}}
            },
        }

        scenarios = generator.generate_scenarios(config)

        assert len(scenarios) == 2
        for _name, overrides in scenarios.items():
            assert 0.0 <= overrides["param_a"] <= 1.0


class TestTemplateScenarioGenerator:
    """Test template-based scenario generation."""

    def test_generate_grid_template(self):
        generator = TemplateScenarioGenerator()
        config = {
            "templates": [
                {
                    "name": "test_template",
                    "description": "Test template",
                    "base_parameters": {},
                    "variable_parameters": {"param_a": [1, 2], "param_b": [0.1, 0.2]},
                    "generation_method": "grid",
                }
            ]
        }

        scenarios = generator.generate_scenarios(config)

        assert len(scenarios) == 4
        assert "test_template_1_0_1" in scenarios

    def test_generate_random_template(self):
        generator = TemplateScenarioGenerator()
        config = {
            "templates": [
                {
                    "name": "random_template",
                    "description": "Random template",
                    "base_parameters": {},
                    "variable_parameters": {"param_a": [1, 2, 3]},
                    "generation_method": "random",
                    "sample_size": 2,
                }
            ]
        }

        scenarios = generator.generate_scenarios(config)

        assert len(scenarios) == 2
        for name in scenarios:
            assert "random_template_sample_" in name


class TestFamilyScenarioGenerator:
    """Test family-based scenario generation."""

    def test_generate_family_scenarios(self):
        generator = FamilyScenarioGenerator()
        config = {
            "families": [
                {
                    "name": "test_family",
                    "description": "Test family",
                    "base_scenario": {"param_a": 1.0},
                    "variations": {"high": {"param_a": 2.0}, "low": {"param_a": 0.5}},
                    "inheritance_mode": "override",
                }
            ]
        }

        scenarios = generator.generate_scenarios(config)

        assert len(scenarios) == 3  # base + 2 variations
        assert "test_family_base" in scenarios
        assert "test_family_high" in scenarios
        assert "test_family_low" in scenarios

        assert scenarios["test_family_high"]["param_a"] == 2.0
        assert scenarios["test_family_low"]["param_a"] == 0.5

    def test_inheritance_modes(self):
        generator = FamilyScenarioGenerator()

        # Test additive inheritance
        result = generator._apply_inheritance(
            {"param_a": 1.0}, {"param_a": 0.5}, "additive"
        )
        assert result["param_a"] == 1.5

        # Test multiplicative inheritance
        result = generator._apply_inheritance(
            {"param_a": 2.0}, {"param_a": 3.0}, "multiplicative"
        )
        assert result["param_a"] == 6.0


class TestDynamicScenarioManager:
    """Test the main scenario manager."""

    def test_generate_scenarios(self):
        manager = DynamicScenarioManager()

        config = {
            "grid": {"parameters": {"param_a": [1, 2]}},
            "distribution": {
                "sample_size": 1,
                "parameters": {
                    "param_b": {"type": "uniform", "params": {"low": 0, "high": 1}}
                },
            },
        }

        scenarios = manager.generate_scenarios(config)

        assert len(scenarios) >= 2  # At least grid scenarios + distribution

    def test_get_scenario_manager(self):
        manager = get_scenario_manager()
        assert isinstance(manager, DynamicScenarioManager)


class TestDynamicScenarioIntegration:
    """Test integration with data_loader."""

    def test_load_scenarios_with_dynamic(self):
        """Test loading scenarios that include dynamic generation."""
        config_content = """
scenarios:
  manual_scenario:
    param_a: 1.0

dynamic_scenarios:
  grid:
    parameters:
      param_b: [0.1, 0.2]
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            scenarios = load_scenarios_from_yaml(temp_path)

            # Should have manual scenario + grid scenarios
            assert "manual_scenario" in scenarios
            assert len(scenarios) >= 3  # manual + 2 grid scenarios

        finally:
            os.unlink(temp_path)

    def test_load_scenarios_without_dynamic(self):
        """Test loading scenarios without dynamic generation (backward compatibility)."""
        config_content = """
scenarios:
  scenario1:
    param_a: 1.0
  scenario2:
    param_a: 2.0
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            scenarios = load_scenarios_from_yaml(temp_path)

            assert len(scenarios) == 2
            assert "scenario1" in scenarios
            assert "scenario2" in scenarios

        finally:
            os.unlink(temp_path)

    @patch("lifecourse.analysis.scenario_generator.get_scenario_manager")
    def test_dynamic_generation_import_error(self, mock_get_manager):
        """Test graceful handling when scenario generator is not available."""
        mock_get_manager.side_effect = ImportError("Module not found")

        config_content = """
scenarios:
  manual_scenario:
    param_a: 1.0

dynamic_scenarios:
  grid:
    parameters:
      param_b: [0.1, 0.2]
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            scenarios = load_scenarios_from_yaml(temp_path)

            # Should still load manual scenarios even if dynamic fails
            assert "manual_scenario" in scenarios
            assert len(scenarios) == 1

        finally:
            os.unlink(temp_path)
