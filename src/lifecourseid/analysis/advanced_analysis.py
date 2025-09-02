import numpy as np
import pandas as pd
import psutil
import time
from lifecourseid.analysis.run_helpers import run_sim
from lifecourseid.model.parameters import POP_SIZE, DISTRIBUTIONS

# Benchmark for calibration (example values, replace with actual if available)
OBS_BENCHMARK = {
    "mild": 200000,
    "severe": 500000,
}  # Assuming 2 severity levels for simplicity


def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


def run_calibration(base_mean_params, pop_size=POP_SIZE, years=None, debug=False):
    """Runs a simulation with base parameters and compares against observed benchmarks."""
    print("\n--- Running Calibration Analysis ---")

    # Memory profiling
    if debug:
        start_memory = get_memory_usage()
        start_time = time.time()
        print(f"Initial memory usage: {start_memory:.2f} MB")

    # Run a simulation with the base mean parameters
    dc, dq = run_sim(base_mean_params, pop_size=pop_size, years=years, debug=debug)
    sim_cost = dc  # Assuming dCost is the relevant cost for calibration

    # For simplicity, let's assume we want to calibrate against a total cost benchmark
    # In a real scenario, this would be more complex, possibly involving disaggregated costs
    # and comparing specific subgroups.

    # Example: Compare simulated total cost against a hypothetical benchmark
    # This needs to be refined based on what 'OBS_BENCHMARK' truly represents
    # and how it relates to the output of run_sim.
    # For now, we'll just use a placeholder comparison.
    benchmark_total_cost = sum(OBS_BENCHMARK.values())  # Placeholder sum

    error_pct = abs(sim_cost - benchmark_total_cost) / benchmark_total_cost * 100

    print(f"Simulated Total Cost: £{sim_cost:,}")
    print(f"Benchmark Total Cost: £{benchmark_total_cost:,}")
    print(f"Calibration Error: {error_pct:.2f}%")

    # Memory profiling
    if debug:
        end_time = time.time()
        end_memory = get_memory_usage()
        print(f"Calibration analysis completed in {end_time - start_time:.2f} seconds")
        print(
            f"Final memory usage: {end_memory:.2f} MB (+{end_memory - start_memory:.2f} MB)"
        )

    return {
        "sim_cost": sim_cost,
        "benchmark_cost": benchmark_total_cost,
        "error_pct": error_pct,
    }


def run_structural_uncertainty(
    base_mean_params, num_runs=10, pop_size=POP_SIZE, years=None, debug=False
):
    """Runs simulations with structural variations (e.g., alternative survival models)."""
    print("\n--- Running Structural Uncertainty Analysis ---")

    # Memory profiling
    if debug:
        start_memory = get_memory_usage()
        start_time = time.time()
        print(f"Initial memory usage: {start_memory:.2f} MB")

    results = []
    for i in range(num_runs):
        if debug:
            run_start_time = time.time()
            print(f"Running structural uncertainty iteration {i+1}/{num_runs}")

        # Example of structural variation: modify a parameter directly for this run
        # This is a placeholder. Real structural uncertainty would involve different model logic.
        temp_params = base_mean_params.copy()
        # Vary mortality hazard ratios by +/- 25% of their mean scale value
        temp_params["mort_hr_mild"] = DISTRIBUTIONS["mort_hr_mild"]["scale"] * (
            1 + (np.random.rand() - 0.5) * 0.5
        )
        temp_params["mort_hr_severe"] = DISTRIBUTIONS["mort_hr_severe"]["scale"] * (
            1 + (np.random.rand() - 0.5) * 0.5
        )

        dc, dq = run_sim(temp_params, pop_size=pop_size, years=years, debug=debug)
        results.append({"run": i, "dCost": dc, "dQALY": dq})

        if debug:
            run_end_time = time.time()
            run_end_memory = get_memory_usage()
            print(
                f"  Iteration {i+1} completed in {run_end_time - run_start_time:.2f} seconds"
            )
            print(f"  Memory after iteration {i+1}: {run_end_memory:.2f} MB")

    structural_df = pd.DataFrame(results)
    print("Structural Uncertainty Results (sample):")
    print(structural_df.head())
    print(f"Mean dCost across structural runs: £{structural_df['dCost'].mean():,}")
    print(f"Mean dQALY across structural runs: {structural_df['dQALY'].mean():.2f}")

    # Memory profiling
    if debug:
        end_time = time.time()
        end_memory = get_memory_usage()
        print(
            f"Structural uncertainty analysis completed in {end_time - start_time:.2f} seconds"
        )
        print(
            f"Final memory usage: {end_memory:.2f} MB (+{end_memory - start_memory:.2f} MB)"
        )

    return structural_df
