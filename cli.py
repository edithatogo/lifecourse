import argparse
from src.data_loader import load_scenarios_from_yaml, apply_scenario_overrides
from src.model.parameters import DISTRIBUTIONS, get_mean_params
from src.analysis.run_helpers import run_sim


def main():
    parser = argparse.ArgumentParser(description="Run LifeCourseID scenarios")
    parser.add_argument("scenario", help="Scenario name defined in config/scenarios.yaml")
    parser.add_argument("--pop-size", type=int, default=100, help="Population size for the run")
    parser.add_argument("--config", default="config/scenarios.yaml", help="Path to scenario YAML file")
    args = parser.parse_args()

    scenarios = load_scenarios_from_yaml(args.config)
    if args.scenario not in scenarios:
        raise ValueError(f"Scenario '{args.scenario}' not found in {args.config}")

    base_params = get_mean_params(DISTRIBUTIONS)
    params = apply_scenario_overrides(base_params, scenarios[args.scenario])

    dcost, dqaly = run_sim(params, pop_size=args.pop_size)
    icer = dcost / dqaly if dqaly != 0 else 0
    print(f"Scenario: {args.scenario}")
    print(f"dCost: {dcost:.2f}\ndQALY: {dqaly:.4f}\nICER: {icer:.2f}")


if __name__ == "__main__":
    main()
