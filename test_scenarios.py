#!/usr/bin/env python3

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from lifecourseid.data_loader import load_scenarios_from_yaml


def test_scenario_grid():
    print("Testing scenario grid functionality...")

    # Load scenarios from YAML
    scenarios = load_scenarios_from_yaml("config/scenarios.yaml")

    print(f"Total scenarios loaded: {len(scenarios)}")
    for name, overrides in scenarios.items():
        print(f"  {name}: {overrides}")

    # Check if grid scenarios are properly generated
    grid_scenario_count = 0
    for name in scenarios.keys():
        if "_" in name and name not in [
            "base",
            "low_familial_prop",
            "high_familial_prop",
            "low_yield_wgs",
            "high_yield_wgs",
            "targeted_age_25",
            "high_coverage",
        ]:
            grid_scenario_count += 1
            print(f"Grid scenario found: {name}")

    print(f"Grid scenarios generated: {grid_scenario_count}")

    if grid_scenario_count > 0:
        print("SUCCESS: Scenario grid functionality is working")
        return True
    else:
        print("FAILURE: Scenario grid functionality is not working")
        return False


if __name__ == "__main__":
    test_scenario_grid()
