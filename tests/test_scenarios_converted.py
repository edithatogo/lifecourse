from lifecourse.data_loader import load_scenarios_from_yaml


def test_scenario_grid_generation():
    scenarios = load_scenarios_from_yaml("config/scenarios.yaml")

    assert isinstance(scenarios, dict)
    assert len(scenarios) > 0

    # Ensure keys are strings and values are mappings
    for name, overrides in scenarios.items():
        assert isinstance(name, str)
        assert isinstance(overrides, dict)
