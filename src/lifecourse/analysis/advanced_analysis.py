import numpy as np
import pandas as pd
import psutil
import time
from scipy import stats
from lifecourse.analysis.run_helpers import run_sim
from lifecourse.model.parameters import POP_SIZE, DISTRIBUTIONS

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


def calculate_evsi(psa_results, research_designs, wtp_threshold=30000, debug=False):
    """
    Calculate Expected Value of Sample Information (EVSI) for different research designs.

    EVSI quantifies the expected value of conducting additional research by measuring
    how much uncertainty reduction improves decision making.

    Parameters:
    -----------
    psa_results : pd.DataFrame
        PSA results with columns: dCost, dQALY, ICER, net_benefit
    research_designs : list of dict
        List of research design specifications, each containing:
        - 'name': str, design identifier
        - 'sample_size': int, number of additional observations
        - 'target_param': str, parameter being studied (optional)
    wtp_threshold : float
        Willingness-to-pay threshold for net benefit calculation
    debug : bool
        Enable debug output

    Returns:
    --------
    dict: EVSI results for each research design
    """
    print("\n--- Calculating Expected Value of Sample Information (EVSI) ---")

    if debug:
        start_time = time.time()
        print(f"Starting EVSI calculation with {len(psa_results)} PSA samples")

    # Ensure we have net benefit column
    if "net_benefit" not in psa_results.columns:
        psa_results = psa_results.copy()
        psa_results["net_benefit"] = (
            psa_results["dQALY"] * wtp_threshold - psa_results["dCost"]
        )

    # Current EVPI (Expected Value of Perfect Information)
    current_evpi = calculate_evpi(psa_results, wtp_threshold)

    evsi_results = {}

    for design in research_designs:
        design_name = design["name"]
        sample_size = design["sample_size"]

        if debug:
            print(f"\nEvaluating research design: {design_name} (n={sample_size})")

        # For each PSA sample, simulate posterior distribution after new data
        posterior_net_benefits = []

        for idx, psa_sample in psa_results.iterrows():
            # Simulate new data collection and Bayesian updating
            # This is a simplified approach - in practice would use proper Bayesian methods
            posterior_nb = simulate_bayesian_update(
                psa_sample["net_benefit"],
                sample_size,
                psa_results["net_benefit"].std(),
                design.get("target_param"),
            )
            posterior_net_benefits.append(posterior_nb)

        # Calculate expected value of information for this design
        posterior_net_benefits = np.array(posterior_net_benefits)

        # EVSI = E[max(0, ENB_post - ENB_prior)] - EVPI
        # Simplified: difference between expected posterior and current expected NB
        expected_posterior_nb = np.mean(posterior_net_benefits)
        current_expected_nb = np.mean(psa_results["net_benefit"])

        # Calculate the value of the information
        info_value = max(0, expected_posterior_nb - current_expected_nb)

        # EVSI is the expected value of this information minus current EVPI
        evsi = info_value - current_evpi

        # Ensure EVSI is not negative
        evsi = max(0, evsi)

        evsi_results[design_name] = {
            "sample_size": sample_size,
            "evsi": evsi,
            "expected_posterior_nb": expected_posterior_nb,
            "current_expected_nb": current_expected_nb,
            "info_value": info_value,
            "current_evpi": current_evpi,
        }

        if debug:
            print(f"  EVSI: £{evsi:,.0f}")
            print(f"  Information value: £{info_value:,.0f}")
            print(f"  Current EVPI: £{current_evpi:,.0f}")

    if debug:
        end_time = time.time()
        print(f"\nEVSI calculation completed in {end_time - start_time:.2f} seconds")

    return evsi_results


def calculate_evpi(psa_results, wtp_threshold=30000):
    """
    Calculate Expected Value of Perfect Information (EVPI).

    EVPI measures the expected value of eliminating all uncertainty.

    Parameters:
    -----------
    psa_results : pd.DataFrame
        PSA results with net benefit column
    wtp_threshold : float
        Willingness-to-pay threshold

    Returns:
    --------
    float: Expected Value of Perfect Information
    """
    if "net_benefit" not in psa_results.columns:
        psa_results = psa_results.copy()
        psa_results["net_benefit"] = (
            psa_results["dQALY"] * wtp_threshold - psa_results["dCost"]
        )

    # EVPI = E[max(NB)] - max(E[NB])
    expected_nb = np.mean(psa_results["net_benefit"])
    max_expected_nb = np.max(psa_results["net_benefit"])

    evpi = max_expected_nb - expected_nb
    return max(0, evpi)  # Ensure non-negative


def simulate_bayesian_update(current_nb, sample_size, uncertainty, target_param=None):
    """
    Simulate Bayesian updating with new sample information.

    This is a simplified simulation of how new data would update our beliefs.
    In practice, this would involve proper Bayesian updating of the parameter distributions.

    Parameters:
    -----------
    current_nb : float
        Current net benefit estimate
    sample_size : int
        Size of new sample
    uncertainty : float
        Current uncertainty (standard deviation)
    target_param : str, optional
        Specific parameter being targeted

    Returns:
    --------
    float: Updated net benefit estimate after Bayesian updating
    """
    # Simplified Bayesian updating model
    # In reality, this would update the full parameter distribution

    # Information gain reduces uncertainty proportionally to sqrt(sample_size)
    uncertainty_reduction = np.sqrt(sample_size) / (np.sqrt(sample_size) + 1)

    # New uncertainty after updating
    new_uncertainty = uncertainty * (1 - uncertainty_reduction)

    # Simulate posterior distribution (simplified)
    # Add some bias correction based on sample size
    bias_correction = np.random.normal(0, new_uncertainty / np.sqrt(sample_size))

    # Updated estimate with reduced uncertainty
    updated_nb = current_nb + bias_correction

    return updated_nb


def run_evsi_analysis(
    base_mean_params,
    psa_runs=1000,
    research_designs=None,
    wtp_threshold=30000,
    pop_size=POP_SIZE,
    years=None,
    debug=False,
):
    """
    Run complete EVSI analysis workflow.

    Parameters:
    -----------
    base_mean_params : dict
        Base parameter values
    psa_runs : int
        Number of PSA runs for uncertainty quantification
    research_designs : list of dict, optional
        Research designs to evaluate. If None, uses default designs.
    wtp_threshold : float
        Willingness-to-pay threshold
    pop_size : int
        Population size for simulations
    years : int, optional
        Simulation years
    debug : bool
        Enable debug output

    Returns:
    --------
    dict: Complete EVSI analysis results
    """
    print("\n--- Running EVSI Analysis ---")

    if debug:
        start_time = time.time()
        print(f"Starting EVSI analysis with {psa_runs} PSA runs")

    # Set default research designs if not provided
    if research_designs is None:
        research_designs = [
            {
                "name": "pilot_study_small",
                "sample_size": 50,
                "target_param": "yield_wgs",
            },
            {
                "name": "pilot_study_medium",
                "sample_size": 200,
                "target_param": "yield_wgs",
            },
            {
                "name": "pilot_study_large",
                "sample_size": 500,
                "target_param": "yield_wgs",
            },
            {"name": "full_trial", "sample_size": 1000, "target_param": "yield_wgs"},
            {
                "name": "registry_study",
                "sample_size": 2000,
                "target_param": "yield_wgs",
            },
        ]

    # Run PSA to get uncertainty distribution
    print("Running PSA for uncertainty quantification...")
    psa_results = run_psa(base_mean_params, psa_runs, pop_size, years, debug)

    # Calculate EVSI for each research design
    evsi_results = calculate_evsi(psa_results, research_designs, wtp_threshold, debug)

    # Prepare summary results
    summary = {
        "psa_results": psa_results,
        "evsi_results": evsi_results,
        "research_designs": research_designs,
        "wtp_threshold": wtp_threshold,
        "psa_runs": psa_runs,
    }

    # Print summary
    print("\nEVSI Analysis Summary:")
    print("=" * 50)
    for design_name, results in evsi_results.items():
        print(
            f"{design_name}: EVSI = £{results['evsi']:,.0f} "
            f"(sample size: {results['sample_size']})"
        )

    # Find optimal design
    optimal_design = max(evsi_results.items(), key=lambda x: x[1]["evsi"])
    print(
        f"\nOptimal research design: {optimal_design[0]} "
        f"(EVSI = £{optimal_design[1]['evsi']:,.0f})"
    )

    if debug:
        end_time = time.time()
        print(f"\nEVSI analysis completed in {end_time - start_time:.2f} seconds")

    return summary


def run_psa(
    base_mean_params, psa_runs=1000, pop_size=POP_SIZE, years=None, debug=False
):
    """
    Run Probabilistic Sensitivity Analysis to generate uncertainty distribution.

    Parameters:
    -----------
    base_mean_params : dict
        Base parameter values
    psa_runs : int
        Number of PSA runs
    pop_size : int
        Population size
    years : int, optional
        Simulation years
    debug : bool
        Enable debug output

    Returns:
    --------
    pd.DataFrame: PSA results with dCost, dQALY, ICER, net_benefit
    """
    if debug:
        print(f"Running {psa_runs} PSA simulations...")

    results = []
    for i in range(psa_runs):
        if debug and (i + 1) % 100 == 0:
            print(f"PSA run {i + 1}/{psa_runs}")

        # Sample parameters from distributions
        sampled_params = {}
        for param_name, dist_info in DISTRIBUTIONS.items():
            if dist_info["dist"] == "beta":
                sampled_params[param_name] = stats.beta.rvs(
                    dist_info["alpha"], dist_info["beta"]
                )
            elif dist_info["dist"] == "gamma":
                sampled_params[param_name] = stats.gamma.rvs(
                    a=dist_info["shape"], scale=dist_info["scale"]
                )
            elif dist_info["dist"] == "lognormal":
                sampled_params[param_name] = stats.lognorm.rvs(
                    s=dist_info["s"], scale=dist_info["scale"]
                )
            elif dist_info["dist"] == "normal":
                sampled_params[param_name] = stats.norm.rvs(
                    loc=dist_info["loc"], scale=dist_info["scale"]
                )
            elif dist_info["dist"] == "uniform":
                sampled_params[param_name] = stats.uniform.rvs(
                    loc=dist_info["low"], scale=dist_info["high"] - dist_info["low"]
                )
            elif dist_info["dist"] == "fixed":
                sampled_params[param_name] = dist_info["value"]
            else:
                raise ValueError(f"Unknown distribution type: {dist_info['dist']}")

        # Apply sampled parameters to base params
        sim_params = base_mean_params.copy()
        sim_params.update(sampled_params)

        # Run simulation
        dc, dq = run_sim(sim_params, pop_size=pop_size, years=years, debug=False)

        # Calculate ICER and net benefit (assuming £30,000 WTP)
        icer = dc / dq if dq > 0 else float("inf")
        net_benefit = dq * 30000 - dc  # Simplified net benefit

        results.append(
            {
                "run": i,
                "dCost": dc,
                "dQALY": dq,
                "ICER": icer,
                "net_benefit": net_benefit,
            }
        )

    return pd.DataFrame(results)


def calculate_concentration_index(health_variable, socioeconomic_rank, weights=None):
    """
    Calculate the concentration index for a health variable.

    The concentration index measures socioeconomic-related inequality in health.
    Values range from -1 to 1, where:
    - 0 indicates perfect equality
    - Positive values indicate health concentrates among richer groups
    - Negative values indicate health concentrates among poorer groups

    Parameters:
    -----------
    health_variable : array-like
        Health outcome variable (e.g., QALYs, costs, utilization)
    socioeconomic_rank : array-like
        Socioeconomic ranking (0-1 scale, where 1 is richest)
    weights : array-like, optional
        Population weights for each observation

    Returns:
    --------
    float : Concentration index
    """
    if weights is None:
        weights = np.ones(len(health_variable)) / len(health_variable)

    # Ensure inputs are numpy arrays
    y = np.array(health_variable)
    r = np.array(socioeconomic_rank)
    w = np.array(weights)

    # Normalize weights
    w = w / np.sum(w)

    # Sort by socioeconomic rank
    sort_idx = np.argsort(r)
    y_sorted = y[sort_idx]
    r_sorted = r[sort_idx]
    w_sorted = w[sort_idx]

    # Calculate weighted mean
    mu = np.sum(y_sorted * w_sorted)

    # Calculate concentration index
    if mu == 0:
        return 0.0

    # Cumulative weights
    cum_w = np.cumsum(w_sorted)
    cum_w = np.concatenate([[0], cum_w[:-1]])  # Shift for trapezoidal rule

    # Concentration index formula
    ci = (2 / mu) * np.sum((y_sorted - mu) * (cum_w + w_sorted / 2 - 0.5) * w_sorted)

    return ci


def calculate_concentration_indices(psa_results, ses_quintiles=None):
    """
    Calculate concentration indices for key health economic outcomes.

    Parameters:
    -----------
    psa_results : pd.DataFrame
        PSA results with dCost, dQALY columns
    ses_quintiles : dict, optional
        SES distribution by quintile (Q1-Q5)

    Returns:
    --------
    dict : Concentration indices for different outcomes
    """
    if ses_quintiles is None:
        # Default equal distribution across quintiles
        ses_quintiles = {f"Q{i+1}": 0.2 for i in range(5)}

    # Create socioeconomic ranks (0-1 scale)
    # Quintile 1 (poorest) = 0.1, Quintile 5 (richest) = 0.9
    ses_ranks = []
    for i in range(5):
        rank = (i + 0.5) / 5  # 0.1, 0.3, 0.5, 0.7, 0.9
        weight = ses_quintiles[f"Q{i+1}"]
        ses_ranks.extend(
            [rank] * int(weight * 1000)
        )  # Assume 1000 observations per quintile

    # For PSA results, we need to simulate health outcomes by SES
    # This is a simplified approach - in practice would need SES-stratified results
    n_obs = len(psa_results)

    # Simulate health outcomes with SES gradient
    # Poorer groups have worse health outcomes
    ses_effect = np.array(ses_ranks[:n_obs]) - 0.5  # Centered around 0

    # Apply SES effect to health outcomes
    costs_with_ses = (
        psa_results["dCost"].values + ses_effect * 1000
    )  # SES effect on costs
    qalys_with_ses = (
        psa_results["dQALY"].values - ses_effect * 0.1
    )  # SES effect on QALYs

    # Calculate concentration indices
    ci_cost = calculate_concentration_index(costs_with_ses, ses_ranks[:n_obs])
    ci_qaly = calculate_concentration_index(qalys_with_ses, ses_ranks[:n_obs])

    # Concentration index for net benefit (more negative = more pro-poor)
    net_benefit = qalys_with_ses * 30000 - costs_with_ses  # £30k WTP
    ci_net_benefit = calculate_concentration_index(net_benefit, ses_ranks[:n_obs])

    return {
        "cost_ci": ci_cost,
        "qaly_ci": ci_qaly,
        "net_benefit_ci": ci_net_benefit,
        "interpretation": {
            "cost_ci": "Positive = costs concentrate among rich (pro-rich inequality)",
            "qaly_ci": "Negative = QALYs concentrate among poor (pro-poor inequality)",
            "net_benefit_ci": "Negative = net benefits concentrate among poor (equity-improving)",
        },
    }


def run_concentration_analysis(
    base_mean_params, psa_runs=100, pop_size=1000, years=None, debug=False
):
    """
    Run concentration index analysis for health inequality measurement.

    Parameters:
    -----------
    base_mean_params : dict
        Base parameter values
    psa_runs : int
        Number of PSA runs
    pop_size : int
        Population size for simulation
    years : list
        Simulation years
    debug : bool
        Enable debug output

    Returns:
    --------
    dict : Concentration analysis results
    """
    if debug:
        print("\n--- Calculating Concentration Indices ---")
        start_time = time.time()

    # Run PSA to get uncertainty distribution
    psa_results = run_psa(base_mean_params, psa_runs, pop_size, years, debug)

    # Calculate concentration indices
    ci_results = calculate_concentration_indices(psa_results)

    if debug:
        print(".4f")
        print(".4f")
        print(".4f")
        print(
            f"Concentration analysis completed in {time.time() - start_time:.2f} seconds"
        )

    return ci_results


def calculate_price_thresholds(psa_results, wtp_range=None, target_population=1000000):
    """
    Calculate price thresholds for value-based pricing analysis.

    Determines the maximum price per unit that would be cost-effective
    at different willingness-to-pay thresholds.

    Parameters:
    -----------
    psa_results : pd.DataFrame
        PSA results with dCost, dQALY columns
    wtp_range : array-like, optional
        Range of WTP thresholds to evaluate (£ per QALY)
    target_population : int
        Target population size for pricing analysis

    Returns:
    --------
    dict : Price threshold analysis results
    """
    if wtp_range is None:
        wtp_range = np.linspace(10000, 50000, 21)  # £10k to £50k per QALY

    thresholds = {}

    for wtp in wtp_range:
        # Calculate net benefit at this WTP threshold
        net_benefits = psa_results["dQALY"] * wtp - psa_results["dCost"]

        # Price threshold is the maximum price where expected net benefit >= 0
        # This represents the break-even price for cost-effectiveness
        expected_nb = np.mean(net_benefits)

        # For probabilistic analysis, we want the price where P(NB >= 0) >= threshold
        # Here we use expected value approach for simplicity
        if expected_nb >= 0:
            # If intervention is cost-effective on average, price threshold is infinite
            # (or limited by budget constraints)
            price_threshold = float("inf")
        else:
            # Calculate price needed to make expected NB = 0
            # NB = QALYs * WTP - Cost - Price * Units
            # For simplicity, assume price is additional cost per person
            price_threshold = -expected_nb  # Price needed to offset negative NB

        thresholds[wtp] = {
            "price_threshold": price_threshold,
            "expected_net_benefit": expected_nb,
            "probability_cost_effective": np.mean(net_benefits >= 0),
        }

    return {
        "thresholds": thresholds,
        "wtp_range": wtp_range,
        "target_population": target_population,
        "analysis_type": "price_threshold",
    }


def calculate_optimal_price_ranges(
    psa_results, budget_constraints=None, wtp_threshold=30000
):
    """
    Calculate optimal price ranges under budget and cost-effectiveness constraints.

    Parameters:
    -----------
    psa_results : pd.DataFrame
        PSA results with dCost, dQALY columns
    budget_constraints : dict, optional
        Budget constraints with keys: 'max_incremental_budget', 'population_size'
    wtp_threshold : float
        Willingness-to-pay threshold (£ per QALY)

    Returns:
    --------
    dict : Optimal price range analysis results
    """
    if budget_constraints is None:
        budget_constraints = {
            "max_incremental_budget": 10000000,  # £10M
            "population_size": 1000000,  # 1M people
        }

    max_budget = budget_constraints["max_incremental_budget"]
    pop_size = budget_constraints["population_size"]

    # Calculate base case (no price increase)
    base_cost = np.mean(psa_results["dCost"])
    base_qaly = np.mean(psa_results["dQALY"])

    # Calculate maximum price per person allowed by budget
    max_price_per_person = max_budget / pop_size

    # Calculate price range where intervention remains cost-effective
    net_benefits = psa_results["dQALY"] * wtp_threshold - psa_results["dCost"]

    # Minimum price: where expected NB = 0 (break-even)
    expected_nb = np.mean(net_benefits)
    if expected_nb >= 0:
        min_price = 0  # No minimum price needed
    else:
        min_price = -expected_nb  # Price needed to achieve NB = 0

    # Maximum price: constrained by budget and cost-effectiveness
    max_price_ce = float("inf")  # Could be higher if budget allows
    max_price_budget = max_price_per_person

    # For probabilistic analysis, consider uncertainty
    # Price where P(NB >= 0) >= 0.5 (more than 50% chance of being cost-effective)
    prob_ce = np.mean(net_benefits >= 0)
    if prob_ce < 0.5:
        # Calculate price increase needed to reach 50% probability
        # This is a simplified approach
        price_boost = (
            np.percentile(-net_benefits[net_benefits < 0], 50)
            if np.any(net_benefits < 0)
            else 0
        )
        max_price_ce = min_price + price_boost

    optimal_range = {
        "min_price": max(0, min_price),
        "max_price_budget": max_price_budget,
        "max_price_cost_effective": min(max_price_ce, max_price_budget),
        "expected_base_cost": base_cost,
        "expected_base_qaly": base_qaly,
        "probability_cost_effective": prob_ce,
        "budget_impact": base_cost * pop_size,
    }

    return {
        "optimal_range": optimal_range,
        "budget_constraints": budget_constraints,
        "wtp_threshold": wtp_threshold,
        "analysis_type": "optimal_price_range",
    }


def analyze_reimbursement_scenarios(
    psa_results, pricing_scenarios, wtp_threshold=30000
):
    """
    Analyze different reimbursement scenarios under value-based pricing.

    Parameters:
    -----------
    psa_results : pd.DataFrame
        PSA results with dCost, dQALY columns
    pricing_scenarios : list of dict
        Different pricing scenarios to evaluate
    wtp_threshold : float
        Willingness-to-pay threshold (£ per QALY)

    Returns:
    --------
    dict : Reimbursement scenario analysis results
    """
    scenario_results = {}

    for scenario in pricing_scenarios:
        scenario_name = scenario["name"]
        price_adjustment = scenario.get("price_adjustment", 0)
        reimbursement_rate = scenario.get("reimbursement_rate", 1.0)
        population_size = scenario.get("population_size", 1000000)

        # Adjust costs based on pricing scenario
        adjusted_costs = psa_results["dCost"] + price_adjustment

        # Calculate reimbursed costs (what payer actually pays)
        reimbursed_costs = adjusted_costs * reimbursement_rate

        # Calculate net benefits from payer perspective
        payer_net_benefits = psa_results["dQALY"] * wtp_threshold - reimbursed_costs

        # Calculate budget impact
        budget_impact = np.mean(reimbursed_costs) * population_size

        # Calculate cost-effectiveness metrics
        icer = (
            np.mean(reimbursed_costs) / np.mean(psa_results["dQALY"])
            if np.mean(psa_results["dQALY"]) > 0
            else float("inf")
        )

        scenario_results[scenario_name] = {
            "price_adjustment": price_adjustment,
            "reimbursement_rate": reimbursement_rate,
            "population_size": population_size,
            "expected_cost": np.mean(adjusted_costs),
            "expected_reimbursed_cost": np.mean(reimbursed_costs),
            "expected_qaly": np.mean(psa_results["dQALY"]),
            "expected_net_benefit": np.mean(payer_net_benefits),
            "icer": icer,
            "budget_impact": budget_impact,
            "probability_cost_effective": np.mean(payer_net_benefits >= 0),
        }

    return {
        "scenario_results": scenario_results,
        "pricing_scenarios": pricing_scenarios,
        "wtp_threshold": wtp_threshold,
        "analysis_type": "reimbursement_scenarios",
    }


def run_vbp_analysis(
    base_mean_params,
    psa_runs=1000,
    wtp_range=None,
    budget_constraints=None,
    pricing_scenarios=None,
    pop_size=POP_SIZE,
    years=None,
    debug=False,
):
    """
    Run complete Value-Based Pricing analysis.

    Parameters:
    -----------
    base_mean_params : dict
        Base parameter values
    psa_runs : int
        Number of PSA runs for uncertainty quantification
    wtp_range : array-like, optional
        Range of WTP thresholds for price threshold analysis
    budget_constraints : dict, optional
        Budget constraints for optimal price range analysis
    pricing_scenarios : list of dict, optional
        Pricing scenarios for reimbursement analysis
    pop_size : int
        Population size for simulations
    years : int, optional
        Simulation years
    debug : bool
        Enable debug output

    Returns:
    --------
    dict : Complete VBP analysis results
    """
    print("\n--- Running Value-Based Pricing (VBP) Analysis ---")

    if debug:
        start_time = time.time()
        print(f"Starting VBP analysis with {psa_runs} PSA runs")

    # Set default scenarios if not provided
    if pricing_scenarios is None:
        pricing_scenarios = [
            {"name": "base_case", "price_adjustment": 0, "reimbursement_rate": 1.0},
            {
                "name": "price_increase_10pct",
                "price_adjustment": 0.1,
                "reimbursement_rate": 1.0,
            },
            {
                "name": "price_increase_25pct",
                "price_adjustment": 0.25,
                "reimbursement_rate": 1.0,
            },
            {
                "name": "partial_reimbursement",
                "price_adjustment": 0,
                "reimbursement_rate": 0.8,
            },
            {
                "name": "value_based_pricing",
                "price_adjustment": 0.15,
                "reimbursement_rate": 0.9,
            },
        ]

    # Run PSA to get uncertainty distribution
    print("Running PSA for uncertainty quantification...")
    psa_results = run_psa(base_mean_params, psa_runs, pop_size, years, debug)

    # Perform VBP analyses
    price_thresholds = calculate_price_thresholds(psa_results, wtp_range)
    optimal_ranges = calculate_optimal_price_ranges(psa_results, budget_constraints)
    reimbursement_analysis = analyze_reimbursement_scenarios(
        psa_results, pricing_scenarios
    )

    # Prepare comprehensive results
    vbp_results = {
        "psa_results": psa_results,
        "price_thresholds": price_thresholds,
        "optimal_price_ranges": optimal_ranges,
        "reimbursement_scenarios": reimbursement_analysis,
        "psa_runs": psa_runs,
        "analysis_timestamp": pd.Timestamp.now(),
    }

    # Print summary
    print("\nVBP Analysis Summary:")
    print("=" * 50)
    print("Price Threshold Analysis:")
    for wtp, data in list(price_thresholds["thresholds"].items())[:3]:  # Show first 3
        threshold = data["price_threshold"]
        prob_ce = data["probability_cost_effective"]
        print(
            f"  WTP £{wtp:,.0f}/QALY: Threshold = £{threshold:,.0f}, P(CE) = {prob_ce:.2%}"
        )

    print("\nOptimal Price Range:")
    opt_range = optimal_ranges["optimal_range"]
    print(
        f"  Range: £{opt_range['min_price']:,.0f} - £{opt_range['max_price_cost_effective']:,.0f}"
    )
    print(f"  Budget constraint: £{opt_range['max_price_budget']:,.0f}")

    print("\nReimbursement Scenarios:")
    for scenario_name, results in reimbursement_analysis["scenario_results"].items():
        print(
            f"  {scenario_name}: ICER = £{results['icer']:,.0f}, P(CE) = {results['probability_cost_effective']:.2%}"
        )

    if debug:
        end_time = time.time()
        print(f"\nVBP analysis completed in {end_time - start_time:.2f} seconds")

    return vbp_results


def create_decision_matrix(criteria, alternatives, scores):
    """
    Create a structured decision matrix for MCDA analysis.

    Parameters:
    -----------
    criteria : list
        List of criteria names
    alternatives : list
        List of alternative names/options
    scores : dict
        Dictionary with criteria as keys and lists of scores as values

    Returns:
    --------
    pd.DataFrame : Decision matrix with alternatives as rows, criteria as columns
    """
    if len(criteria) != len(scores):
        raise ValueError("Number of criteria must match number of score arrays")

    for criterion, score_list in scores.items():
        if len(score_list) != len(alternatives):
            raise ValueError(
                f"Score list for {criterion} must match number of alternatives"
            )

    # Create decision matrix
    decision_matrix = pd.DataFrame(scores, index=alternatives)

    return decision_matrix


def normalize_decision_matrix(decision_matrix, normalization_method="linear"):
    """
    Normalize the decision matrix using various normalization methods.

    Parameters:
    -----------
    decision_matrix : pd.DataFrame
        Decision matrix to normalize
    normalization_method : str
        Normalization method: 'linear', 'vector', 'minmax'

    Returns:
    --------
    pd.DataFrame : Normalized decision matrix
    """
    normalized_matrix = decision_matrix.copy()

    if normalization_method == "linear":
        # Linear normalization: divide by sum of column
        for column in normalized_matrix.columns:
            col_sum = normalized_matrix[column].sum()
            if col_sum != 0:
                normalized_matrix[column] = normalized_matrix[column] / col_sum

    elif normalization_method == "vector":
        # Vector normalization: divide by Euclidean norm
        for column in normalized_matrix.columns:
            norm = np.sqrt((normalized_matrix[column] ** 2).sum())
            if norm != 0:
                normalized_matrix[column] = normalized_matrix[column] / norm

    elif normalization_method == "minmax":
        # Min-max normalization
        for column in normalized_matrix.columns:
            col_min = normalized_matrix[column].min()
            col_max = normalized_matrix[column].max()
            col_range = col_max - col_min
            if col_range != 0:
                normalized_matrix[column] = (
                    normalized_matrix[column] - col_min
                ) / col_range

    else:
        raise ValueError(f"Unknown normalization method: {normalization_method}")

    return normalized_matrix


def apply_weights(normalized_matrix, weights):
    """
    Apply weights to the normalized decision matrix.

    Parameters:
    -----------
    normalized_matrix : pd.DataFrame
        Normalized decision matrix
    weights : dict
        Dictionary with criteria names as keys and weights as values

    Returns:
    --------
    pd.DataFrame : Weighted normalized decision matrix
    """
    if set(weights.keys()) != set(normalized_matrix.columns):
        raise ValueError("Weights must be provided for all criteria")

    # Check that weights sum to 1 (or close to 1)
    total_weight = sum(weights.values())
    if not np.isclose(total_weight, 1.0, atol=1e-6):
        print(
            f"Warning: Weights sum to {total_weight:.6f}, not 1.0. Normalizing weights."
        )
        weights = {k: v / total_weight for k, v in weights.items()}

    weighted_matrix = normalized_matrix.copy()
    for criterion in weighted_matrix.columns:
        weighted_matrix[criterion] = weighted_matrix[criterion] * weights[criterion]

    return weighted_matrix


def calculate_weighted_sum(weighted_matrix):
    """
    Calculate weighted sum scores for each alternative.

    Parameters:
    -----------
    weighted_matrix : pd.DataFrame
        Weighted normalized decision matrix

    Returns:
    --------
    pd.Series : Weighted sum scores for each alternative
    """
    return weighted_matrix.sum(axis=1)


def analytic_hierarchy_process(criteria, pairwise_comparisons):
    """
    Calculate criteria weights using Analytic Hierarchy Process (AHP).

    Parameters:
    -----------
    criteria : list
        List of criteria names
    pairwise_comparisons : dict
        Dictionary with (criterion_i, criterion_j) tuples as keys
        and comparison values (1-9 scale) as values

    Returns:
    --------
    dict : Criteria weights and consistency information
    """
    n = len(criteria)
    if n < 2:
        return {criteria[0]: 1.0}

    # Create pairwise comparison matrix
    matrix = np.ones((n, n))

    # Fill matrix with pairwise comparisons
    criteria_index = {crit: i for i, crit in enumerate(criteria)}

    for (crit_i, crit_j), value in pairwise_comparisons.items():
        i, j = criteria_index[crit_i], criteria_index[crit_j]
        matrix[i, j] = value
        matrix[j, i] = 1.0 / value  # Reciprocal

    # Calculate eigenvalues and eigenvectors
    eigenvalues, eigenvectors = np.linalg.eig(matrix)
    max_eigenvalue = np.real(max(eigenvalues))
    principal_eigenvector = np.real(eigenvectors[:, np.argmax(eigenvalues)])

    # Normalize eigenvector to get weights
    weights = principal_eigenvector / principal_eigenvector.sum()

    # Calculate consistency ratio
    ci = (max_eigenvalue - n) / (n - 1)
    ri = {1: 0, 2: 0, 3: 0.58, 4: 0.9, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45}.get(
        n, 1.49
    )
    cr = ci / ri if ri > 0 else 0

    weights_dict = dict(zip(criteria, weights))

    return {
        "weights": weights_dict,
        "consistency_ratio": cr,
        "consistent": cr < 0.1,  # CR < 0.1 is generally considered acceptable
        "pairwise_matrix": matrix,
        "max_eigenvalue": max_eigenvalue,
    }


def value_function_model(
    criterion_values, preference_type="linear", direction="increasing"
):
    """
    Apply value function modeling to transform criterion values to utility scores.

    Parameters:
    -----------
    criterion_values : array-like
        Raw criterion values to transform
    preference_type : str
        Type of value function: 'linear', 'exponential', 'logarithmic', 'step'
    direction : str
        Preference direction: 'increasing' (higher is better) or 'decreasing' (lower is better)

    Returns:
    --------
    np.ndarray : Utility scores between 0 and 1
    """
    values = np.array(criterion_values)

    if direction == "decreasing":
        values = -values  # Flip for decreasing preference

    # Normalize to 0-1 range
    v_min, v_max = values.min(), values.max()
    if v_max == v_min:
        return np.ones_like(values) * 0.5  # All values equal, return neutral utility

    normalized = (values - v_min) / (v_max - v_min)

    if preference_type == "linear":
        utilities = normalized
    elif preference_type == "exponential":
        utilities = 1 - np.exp(-2 * normalized)  # Exponential value function
    elif preference_type == "logarithmic":
        # Avoid log(0) by adding small epsilon
        utilities = np.log(normalized + 1e-10) / np.log(1 + 1e-10)
        utilities = (utilities - utilities.min()) / (utilities.max() - utilities.min())
    elif preference_type == "step":
        # Step function: 0 below median, 1 above median
        median_val = np.median(normalized)
        utilities = (normalized >= median_val).astype(float)
    else:
        raise ValueError(f"Unknown preference type: {preference_type}")

    return utilities


def run_mcda_analysis(
    decision_matrix,
    weights=None,
    normalization_method="linear",
    weight_method="equal",
    pairwise_comparisons=None,
    value_functions=None,
    debug=False,
):
    """
    Run complete Multi-Criteria Decision Analysis.

    Parameters:
    -----------
    decision_matrix : pd.DataFrame
        Decision matrix with alternatives as rows, criteria as columns
    weights : dict, optional
        Criteria weights. If None, uses weight_method to determine weights
    normalization_method : str
        Normalization method for decision matrix
    weight_method : str
        Method to determine weights: 'equal', 'ahp', 'custom'
    pairwise_comparisons : dict, optional
        Pairwise comparisons for AHP (required if weight_method='ahp')
    value_functions : dict, optional
        Value function specifications for each criterion
    debug : bool
        Enable debug output

    Returns:
    --------
    dict : Complete MCDA analysis results
    """
    print("\n--- Running Multi-Criteria Decision Analysis (MCDA) ---")

    if debug:
        start_time = time.time()
        print(
            f"Starting MCDA analysis with {len(decision_matrix)} alternatives and {len(decision_matrix.columns)} criteria"
        )

    # Step 1: Apply value functions if specified
    transformed_matrix = decision_matrix.copy()
    if value_functions:
        for criterion, vf_spec in value_functions.items():
            if criterion in transformed_matrix.columns:
                preference_type = vf_spec.get("type", "linear")
                direction = vf_spec.get("direction", "increasing")
                transformed_matrix[criterion] = value_function_model(
                    transformed_matrix[criterion], preference_type, direction
                )

    # Step 2: Determine weights
    if weights is None:
        if weight_method == "equal":
            weights = {
                crit: 1.0 / len(decision_matrix.columns)
                for crit in decision_matrix.columns
            }
        elif weight_method == "ahp":
            if pairwise_comparisons is None:
                raise ValueError("pairwise_comparisons required for AHP weight method")
            ahp_result = analytic_hierarchy_process(
                list(decision_matrix.columns), pairwise_comparisons
            )
            weights = ahp_result["weights"]
            if debug:
                print(
                    f"AHP Consistency Ratio: {ahp_result['consistency_ratio']:.4f} (Acceptable: <0.1)"
                )
        else:
            raise ValueError(f"Unknown weight method: {weight_method}")

    # Step 3: Normalize decision matrix
    normalized_matrix = normalize_decision_matrix(
        transformed_matrix, normalization_method
    )

    # Step 4: Apply weights
    weighted_matrix = apply_weights(normalized_matrix, weights)

    # Step 5: Calculate final scores
    final_scores = calculate_weighted_sum(weighted_matrix)

    # Step 6: Rank alternatives
    ranking = final_scores.sort_values(ascending=False)

    # Prepare comprehensive results
    mcda_results = {
        "original_matrix": decision_matrix,
        "transformed_matrix": transformed_matrix,
        "normalized_matrix": normalized_matrix,
        "weighted_matrix": weighted_matrix,
        "weights": weights,
        "final_scores": final_scores,
        "ranking": ranking,
        "normalization_method": normalization_method,
        "weight_method": weight_method,
        "analysis_timestamp": pd.Timestamp.now(),
    }

    if weight_method == "ahp" and pairwise_comparisons is not None:
        ahp_result = analytic_hierarchy_process(
            list(decision_matrix.columns), pairwise_comparisons
        )
        mcda_results["ahp_analysis"] = ahp_result

    # Print summary
    print("\nMCDA Analysis Summary:")
    print("=" * 50)
    print(f"Alternatives evaluated: {len(decision_matrix)}")
    print(f"Criteria considered: {len(decision_matrix.columns)}")
    print(f"Weight method: {weight_method}")
    print(f"Normalization method: {normalization_method}")

    print("\nCriteria Weights:")
    for criterion, weight in weights.items():
        print(f"  {criterion}: {weight:.4f}")

    print("\nTop 5 Alternatives:")
    for i, (alternative, score) in enumerate(ranking.head(5).items()):
        print(f"  {i+1}. {alternative}: {score:.4f}")

    if debug:
        end_time = time.time()
        print(f"\nMCDA analysis completed in {end_time - start_time:.2f} seconds")

    return mcda_results


def run_distributional_impacts_analysis(
    base_mean_params, psa_runs=100, pop_size=1000, years=None, debug=False
):
    """
    Run comprehensive distributional impacts analysis for cost-effectiveness evaluation.

    This analysis goes beyond simple subgroup ICERs to examine:
    - Concentration curves and Lorenz curves for health outcomes
    - Distributional cost-effectiveness analysis (DCEA)
    - Atkinson inequality indices
    - Equity-efficiency trade-offs

    Parameters:
    -----------
    base_mean_params : dict
        Base parameter values
    psa_runs : int
        Number of PSA runs for uncertainty analysis
    pop_size : int
        Population size for simulation
    years : list
        Simulation years
    debug : bool
        Enable debug output

    Returns:
    --------
    dict : Comprehensive distributional analysis results
    """
    if debug:
        print("\n--- Running Distributional Impacts Analysis ---")
        start_time = time.time()

    # Run PSA to get uncertainty distribution
    psa_results = run_psa(base_mean_params, psa_runs, pop_size, years, debug)

    # Calculate distributional statistics
    distributional_results = calculate_distributional_statistics(psa_results)

    # Calculate equity-efficiency trade-offs
    equity_efficiency_results = calculate_equity_efficiency_tradeoffs(psa_results)

    # Calculate Atkinson indices for different inequality aversion levels
    atkinson_results = calculate_atkinson_indices(psa_results)

    if debug:
        print(
            f"Distributional impacts analysis completed in {time.time() - start_time:.2f} seconds"
        )

    return {
        "distributional_stats": distributional_results,
        "equity_efficiency": equity_efficiency_results,
        "atkinson_indices": atkinson_results,
        "psa_results": psa_results,
    }


def calculate_distributional_statistics(psa_results):
    """
    Calculate comprehensive distributional statistics for cost-effectiveness outcomes.

    Parameters:
    -----------
    psa_results : pd.DataFrame
        PSA results with dCost, dQALY columns

    Returns:
    --------
    dict : Distributional statistics
    """
    # Calculate net benefits at different WTP thresholds
    wtp_thresholds = [20000, 30000, 50000]  # £20k, £30k, £50k per QALY

    distributional_stats = {}

    for wtp in wtp_thresholds:
        net_benefits = psa_results["dQALY"] * wtp - psa_results["dCost"]

        distributional_stats[f"wtp_{wtp}"] = {
            "mean_net_benefit": np.mean(net_benefits),
            "median_net_benefit": np.median(net_benefits),
            "net_benefit_std": np.std(net_benefits),
            "prob_cost_effective": np.mean(net_benefits > 0),
            "net_benefit_skewness": stats.skew(net_benefits),
            "net_benefit_kurtosis": stats.kurtosis(net_benefits),
            "net_benefit_percentiles": np.percentile(net_benefits, [5, 25, 75, 95]),
        }

    # Overall distributional characteristics
    distributional_stats["overall"] = {
        "icer_mean": np.mean(psa_results["dCost"] / psa_results["dQALY"]),
        "icer_median": np.median(psa_results["dCost"] / psa_results["dQALY"]),
        "icer_cv": np.std(psa_results["dCost"] / psa_results["dQALY"])
        / np.mean(psa_results["dCost"] / psa_results["dQALY"]),
        "cost_skewness": stats.skew(psa_results["dCost"]),
        "qaly_skewness": stats.skew(psa_results["dQALY"]),
        "joint_distribution_corr": np.corrcoef(
            psa_results["dCost"], psa_results["dQALY"]
        )[0, 1],
    }

    return distributional_stats


def calculate_equity_efficiency_tradeoffs(psa_results, ses_weights=None):
    """
    Calculate equity-efficiency trade-offs using distributional cost-effectiveness analysis.

    Parameters:
    -----------
    psa_results : pd.DataFrame
        PSA results with dCost, dQALY columns
    ses_weights : array-like, optional
        Socioeconomic weights for equity analysis

    Returns:
    --------
    dict : Equity-efficiency trade-off results
    """
    if ses_weights is None:
        # Default: equal weights (no equity consideration)
        ses_weights = np.ones(len(psa_results)) / len(psa_results)

    # Calculate weighted outcomes
    weighted_costs = psa_results["dCost"] * ses_weights
    weighted_qalys = psa_results["dQALY"] * ses_weights

    # Efficiency metrics (unweighted)
    efficiency_metrics = {
        "mean_ic_er": np.mean(psa_results["dCost"] / psa_results["dQALY"]),
        "icer_uncertainty": np.std(psa_results["dCost"] / psa_results["dQALY"]),
        "prob_cost_effective": np.mean(
            (psa_results["dCost"] / psa_results["dQALY"]) <= 30000
        ),
    }

    # Equity metrics (weighted)
    equity_metrics = {
        "weighted_mean_icer": np.sum(weighted_costs) / np.sum(weighted_qalys),
        "equity_efficiency_ratio": (np.sum(weighted_costs) / np.sum(weighted_qalys))
        / (np.mean(psa_results["dCost"]) / np.mean(psa_results["dQALY"])),
        "weighted_prob_cost_effective": np.mean(
            (weighted_costs / weighted_qalys) <= 30000
        ),
    }

    # Trade-off analysis
    tradeoff_analysis = {
        "efficiency_loss_for_equity": equity_metrics["equity_efficiency_ratio"] - 1,
        "equity_premium": (
            equity_metrics["weighted_mean_icer"] - efficiency_metrics["mean_ic_er"]
        )
        / efficiency_metrics["mean_ic_er"],
    }

    return {
        "efficiency_metrics": efficiency_metrics,
        "equity_metrics": equity_metrics,
        "tradeoff_analysis": tradeoff_analysis,
    }


def calculate_atkinson_indices(psa_results, epsilon_values=None):
    """
    Calculate Atkinson inequality indices for different inequality aversion levels.

    Parameters:
    -----------
    psa_results : pd.DataFrame
        PSA results with dCost, dQALY columns
    epsilon_values : array-like, optional
        Inequality aversion parameters (0 = no aversion, ∞ = extreme aversion)

    Returns:
    --------
    dict : Atkinson indices for different outcomes and epsilon values
    """
    if epsilon_values is None:
        epsilon_values = [0.5, 1.0, 1.5, 2.0]  # Different inequality aversion levels

    # Ensure positive values for Atkinson index calculation
    # Add small constant to avoid zero/negative values
    epsilon = 1e-6
    positive_costs = psa_results["dCost"] + abs(np.min(psa_results["dCost"])) + epsilon
    positive_qalys = psa_results["dQALY"] + abs(np.min(psa_results["dQALY"])) + epsilon

    atkinson_results = {}

    for epsilon_val in epsilon_values:
        if epsilon_val == 1:
            # Special case for epsilon = 1 (logarithmic)
            atkinson_cost = 1 - np.exp(np.mean(np.log(positive_costs))) / np.mean(
                positive_costs
            )
            atkinson_qaly = 1 - np.exp(np.mean(np.log(positive_qalys))) / np.mean(
                positive_qalys
            )
        else:
            # General Atkinson formula
            mean_cost = np.mean(positive_costs)
            mean_qaly = np.mean(positive_qalys)

            cost_term = np.mean(positive_costs ** (1 - epsilon_val))
            qaly_term = np.mean(positive_qalys ** (1 - epsilon_val))

            atkinson_cost = 1 - (cost_term ** (1 / (1 - epsilon_val))) / mean_cost
            atkinson_qaly = 1 - (qaly_term ** (1 / (1 - epsilon_val))) / mean_qaly

        atkinson_results[f"epsilon_{epsilon_val}"] = {
            "cost_inequality": atkinson_cost,
            "qaly_inequality": atkinson_qaly,
            "interpretation": f"Higher values indicate greater inequality aversion (ε={epsilon_val})",
        }

    return atkinson_results


def calculate_concentration_index(values, ranks):
    """
    Calculate concentration index for inequality measurement.

    Parameters:
    -----------
    values : array-like
        Values to analyze (costs, QALYs, etc.)
    ranks : array-like
        Socioeconomic ranks (0-1 scale, 0=poorest, 1=richest)

    Returns:
    --------
    float : Concentration index (-1 to 1, negative = pro-poor, positive = pro-rich)
    """
    # Convert to numpy arrays if needed
    values = np.asarray(values)
    ranks = np.asarray(ranks)

    # Sort by socioeconomic rank
    sorted_indices = np.argsort(ranks)
    sorted_values = values[sorted_indices]
    sorted_ranks = ranks[sorted_indices]

    # Calculate concentration index
    n = len(values)
    mean_value = np.mean(values)

    # Covariance between values and ranks
    covariance = np.cov(sorted_values, sorted_ranks)[0, 1]

    # Concentration index = 2 * covariance / mean
    ci = 2 * covariance / mean_value

    return ci


# ============================================================================
# Adoption Curve Modeling for Budget Impact Analysis
# ============================================================================


def logistic_adoption_curve(
    years, max_adoption=1.0, growth_rate=1.0, inflection_point=3.0
):
    """
    Calculate logistic adoption curve (S-shaped adoption pattern).

    The logistic curve models adoption that starts slowly, accelerates, then slows as it approaches saturation.

    Parameters:
    -----------
    years : array-like
        Time points (years) for adoption calculation
    max_adoption : float, optional
        Maximum adoption rate (default: 1.0 = 100%)
    growth_rate : float, optional
        Growth rate parameter controlling curve steepness (default: 1.0)
    inflection_point : float, optional
        Year when adoption rate is 50% of maximum (default: 3.0)

    Returns:
    --------
    np.ndarray : Adoption rates for each year
    """
    years = np.asarray(years)
    # Logistic function: max_adoption / (1 + exp(-growth_rate * (t - inflection_point)))
    adoption = max_adoption / (1 + np.exp(-growth_rate * (years - inflection_point)))
    return adoption


def exponential_adoption_curve(years, max_adoption=1.0, decay_rate=0.5):
    """
    Calculate exponential adoption curve (rapid initial adoption that slows over time).

    The exponential curve models adoption that starts quickly but slows asymptotically.

    Parameters:
    -----------
    years : array-like
        Time points (years) for adoption calculation
    max_adoption : float, optional
        Maximum adoption rate (default: 1.0 = 100%)
    decay_rate : float, optional
        Decay rate controlling how quickly adoption slows (default: 0.5)

    Returns:
    --------
    np.ndarray : Adoption rates for each year
    """
    years = np.asarray(years)
    # Exponential decay: max_adoption * (1 - exp(-decay_rate * t))
    adoption = max_adoption * (1 - np.exp(-decay_rate * years))
    return adoption


def stepwise_adoption_curve(years, steps=None):
    """
    Calculate stepwise adoption curve (discrete adoption phases).

    The stepwise curve models adoption in distinct phases or steps.

    Parameters:
    -----------
    years : array-like
        Time points (years) for adoption calculation
    steps : list of tuples, optional
        List of (year, adoption_rate) tuples defining step changes.
        Default creates a 3-step adoption pattern.

    Returns:
    --------
    np.ndarray : Adoption rates for each year
    """
    if steps is None:
        # Default 3-step pattern: 20% at year 1, 60% at year 3, 100% at year 5
        steps = [(1, 0.2), (3, 0.6), (5, 1.0)]

    years = np.asarray(years)
    adoption = np.zeros_like(years, dtype=float)

    for i, year in enumerate(years):
        # Find the highest step year that is <= current year
        applicable_steps = [rate for step_year, rate in steps if step_year <= year]
        if applicable_steps:
            adoption[i] = max(applicable_steps)

    return adoption


def get_adoption_curve(curve_type, years, **kwargs):
    """
    Get adoption rates using specified curve type.

    Parameters:
    -----------
    curve_type : str
        Type of adoption curve ('logistic', 'exponential', 'stepwise')
    years : array-like
        Time points (years) for adoption calculation
    **kwargs : dict
        Additional parameters for the specific curve type

    Returns:
    --------
    np.ndarray : Adoption rates for each year
    """
    curve_type = curve_type.lower()

    if curve_type == "logistic":
        return logistic_adoption_curve(years, **kwargs)
    elif curve_type == "exponential":
        return exponential_adoption_curve(years, **kwargs)
    elif curve_type == "stepwise":
        return stepwise_adoption_curve(years, **kwargs)
    else:
        raise ValueError(
            f"Unknown curve type: {curve_type}. Must be 'logistic', 'exponential', or 'stepwise'"
        )


def calculate_budget_impact_with_adoption(
    incremental_costs, years, curve_type="logistic", max_adoption=1.0, **curve_params
):
    """
    Calculate budget impact using adoption curve modeling.

    Parameters:
    -----------
    incremental_costs : array-like
        Incremental costs for each year
    years : array-like
        Years corresponding to the costs
    curve_type : str, optional
        Type of adoption curve ('logistic', 'exponential', 'stepwise')
    max_adoption : float, optional
        Maximum adoption rate
    **curve_params : dict
        Additional parameters for the adoption curve

    Returns:
    --------
    dict : Budget impact results with adoption rates and cumulative costs
    """
    incremental_costs = np.asarray(incremental_costs)
    years = np.asarray(years)

    # Get adoption rates
    adoption_rates = get_adoption_curve(
        curve_type, years, max_adoption=max_adoption, **curve_params
    )

    # Calculate adopted incremental costs
    adopted_costs = incremental_costs * adoption_rates

    # Calculate cumulative budget impact
    cumulative_costs = np.cumsum(adopted_costs)

    return {
        "years": years,
        "adoption_rates": adoption_rates,
        "incremental_costs": incremental_costs,
        "adopted_costs": adopted_costs,
        "cumulative_budget_impact": cumulative_costs,
        "curve_type": curve_type,
        "max_adoption": max_adoption,
        "curve_params": curve_params,
    }


def run_budget_impact_analysis(
    base_mean_params,
    psa_runs=100,
    pop_size=1000,
    years=None,
    adoption_curves=None,
    debug=False,
):
    """
    Run comprehensive budget impact analysis with adoption curve modeling.

    Parameters:
    -----------
    base_mean_params : dict
        Base parameter values
    psa_runs : int
        Number of PSA runs for uncertainty analysis
    pop_size : int
        Population size for simulation
    years : list
        Simulation years
    adoption_curves : list of dict, optional
        List of adoption curve configurations
    debug : bool
        Enable debug output

    Returns:
    --------
    dict : Comprehensive budget impact analysis results
    """
    if debug:
        print("\n--- Running Budget Impact Analysis with Adoption Curves ---")
        start_time = time.time()

    # Default adoption curves if none provided
    if adoption_curves is None:
        adoption_curves = [
            {
                "type": "logistic",
                "max_adoption": 1.0,
                "growth_rate": 1.0,
                "inflection_point": 3.0,
            },
            {"type": "exponential", "max_adoption": 1.0, "decay_rate": 0.5},
            {"type": "stepwise", "steps": [(1, 0.2), (3, 0.6), (5, 1.0)]},
        ]

    # Run PSA to get uncertainty distribution
    psa_results = run_psa(base_mean_params, psa_runs, pop_size, years, debug)

    # Calculate budget impacts for each adoption curve
    budget_impacts = {}

    for i, curve_config in enumerate(adoption_curves):
        curve_type = curve_config["type"]
        curve_name = f"{curve_type}_curve_{i+1}"

        # Extract curve parameters
        curve_params = {k: v for k, v in curve_config.items() if k != "type"}

        # Calculate budget impact for this curve
        # Note: In a full implementation, this would use year-specific incremental costs
        # For now, we'll use a simplified approach with average incremental costs
        avg_incremental_cost = np.mean(psa_results["dCost"])

        # Create synthetic year-specific costs (this would come from actual simulation)
        years_array = np.arange(1, len(years) + 1) if years else np.arange(1, 6)
        synthetic_costs = np.full(len(years_array), avg_incremental_cost)

        budget_result = calculate_budget_impact_with_adoption(
            synthetic_costs, years_array, curve_type, **curve_params
        )

        budget_impacts[curve_name] = budget_result

    if debug:
        print(
            f"Budget impact analysis completed in {time.time() - start_time:.2f} seconds"
        )

    return {
        "budget_impacts": budget_impacts,
        "adoption_curves": adoption_curves,
        "psa_results": psa_results,
    }
