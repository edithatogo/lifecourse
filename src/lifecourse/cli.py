import argparse

from lifecourse.analysis.advanced_analysis import (
    run_calibration,
    run_structural_uncertainty,
)
from lifecourse.analysis.run_helpers import run_sim
from lifecourse.data_loader import apply_scenario_overrides, load_scenarios_from_yaml
from lifecourse.model.parameter_loader import get_parameter_attributes


def main() -> None:
    parser = argparse.ArgumentParser(description="Run lifecourse scenarios")
    parser.add_argument(
        "scenario", nargs="?", help="Scenario name defined in config/scenarios.yaml"
    )
    parser.add_argument(
        "--pop-size", type=int, default=100, help="Population size for the run"
    )
    parser.add_argument(
        "--config", default="config/scenarios.yaml", help="Path to scenario YAML file"
    )
    parser.add_argument(
        "--calibration", action="store_true", help="Run calibration analysis"
    )
    parser.add_argument(
        "--structural-uncertainty",
        action="store_true",
        help="Run structural uncertainty analysis",
    )
    parser.add_argument(
        "--years", type=int, default=81, help="Number of simulation years (default: 81)"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode with detailed output"
    )
    args = parser.parse_args()

    # If no scenario specified and no special analysis requested, show help
    if not args.scenario and not (args.calibration or args.structural_uncertainty):
        parser.print_help()
        return

    # Load parameters dynamically (default to Australia for CLI)
    config = {"parameter_set": "australia"}
    DISTRIBUTIONS, START_YEAR, get_mean_params = get_parameter_attributes(
        config, "DISTRIBUTIONS", "START_YEAR", "get_mean_params"
    )

    base_params = get_mean_params(DISTRIBUTIONS)

    # Create years range
    years = list(range(START_YEAR, START_YEAR + args.years))

    if args.calibration:
        print("Running calibration analysis...")
        result = run_calibration(
            base_params, pop_size=args.pop_size, years=years, debug=args.debug
        )
        print(f"Calibration completed with error: {result['error_pct']:.2f}%")
        return

    if args.structural_uncertainty:
        print("Running structural uncertainty analysis...")
        run_structural_uncertainty(
            base_params,
            num_runs=10,
            pop_size=args.pop_size,
            years=years,
            debug=args.debug,
        )
        print("Structural uncertainty analysis completed.")
        return

    if args.scenario:
        scenarios = load_scenarios_from_yaml(args.config)
        if args.scenario not in scenarios:
            raise ValueError(f"Scenario '{args.scenario}' not found in {args.config}")

        params = apply_scenario_overrides(base_params, scenarios[args.scenario])

        dcost, dqaly = run_sim(
            params, pop_size=args.pop_size, years=years, debug=args.debug
        )
        icer = dcost / dqaly if dqaly != 0 else 0
        print(f"Scenario: {args.scenario}")
        print(f"dCost: {dcost:.2f}\ndQALY: {dqaly:.4f}\nICER: {icer:.2f}")


if __name__ == "__main__":
    main()
