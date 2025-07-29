import numpy as np
import pandas as pd
from src.analysis.run_helpers import run_sim
from src.model.parameters import POP_SIZE, DISTRIBUTIONS, sample_params_from_dist

# Benchmark for calibration (example values, replace with actual if available)
OBS_BENCHMARK = {'mild': 200000, 'severe': 500000} # Assuming 2 severity levels for simplicity

def run_calibration(base_mean_params, pop_size=POP_SIZE):
    """Runs a simulation with base parameters and compares against observed benchmarks."""
    print("\n--- Running Calibration Analysis ---")
    # Run a simulation with the base mean parameters
    dc, dq = run_sim(base_mean_params, pop_size=pop_size)
    sim_cost = dc # Assuming dCost is the relevant cost for calibration

    # For simplicity, let's assume we want to calibrate against a total cost benchmark
    # In a real scenario, this would be more complex, possibly involving disaggregated costs
    # and comparing specific subgroups.

    # Example: Compare simulated total cost against a hypothetical benchmark
    # This needs to be refined based on what 'OBS_BENCHMARK' truly represents
    # and how it relates to the output of run_sim.
    # For now, we'll just use a placeholder comparison.
    benchmark_total_cost = sum(OBS_BENCHMARK.values()) # Placeholder sum

    error_pct = abs(sim_cost - benchmark_total_cost) / benchmark_total_cost * 100

    print(f"Simulated Total Cost: £{sim_cost:,}")
    print(f"Benchmark Total Cost: £{benchmark_total_cost:,}")
    print(f"Calibration Error: {error_pct:.2f}%")

    return {'sim_cost': sim_cost, 'benchmark_cost': benchmark_total_cost, 'error_pct': error_pct}


def run_structural_uncertainty(base_mean_params, num_runs=10, pop_size=POP_SIZE):
    """Runs simulations with structural variations (e.g., alternative survival models)."""
    print("\n--- Running Structural Uncertainty Analysis ---")
    results = []
    for i in range(num_runs):
        # Example of structural variation: modify a parameter directly for this run
        # This is a placeholder. Real structural uncertainty would involve different model logic.
        temp_params = base_mean_params.copy()
        # Vary mortality hazard ratios by +/- 25% of their mean scale value
        temp_params['mort_hr_mild'] = DISTRIBUTIONS['mort_hr_mild']['scale'] * (1 + (np.random.rand() - 0.5) * 0.5) 
        temp_params['mort_hr_severe'] = DISTRIBUTIONS['mort_hr_severe']['scale'] * (1 + (np.random.rand() - 0.5) * 0.5)

        dc, dq = run_sim(temp_params, pop_size=pop_size)
        results.append({'run': i, 'dCost': dc, 'dQALY': dq})

    structural_df = pd.DataFrame(results)
    print("Structural Uncertainty Results (sample):")
    print(structural_df.head())
    print(f"Mean dCost across structural runs: £{structural_df['dCost'].mean():,}")
    print(f"Mean dQALY across structural runs: {structural_df['dQALY'].mean():.2f}")

    return structural_df
