import pandas as pd
import numpy as np
import argparse
import os
import sys
import psutil
from dask.distributed import LocalCluster, Client

# Add project root to path for config imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.config_loader import load_config

from lifecourse.model.parameter_loader import get_parameter_attributes
from lifecourse.analysis.run_helpers import run_sim, run_scenario
from lifecourse.data_loader import load_scenarios_from_yaml, apply_scenario_overrides
from lifecourse.analysis.advanced_analysis import (
    calculate_budget_impact_with_adoption,
    get_adoption_curve
)


def get_system_resources():
    """Get system resources to optimize Dask configuration"""
    cpu_count = os.cpu_count() or 4
    total_memory_gb = psutil.virtual_memory().total / (1024**3)
    return cpu_count, total_memory_gb


def main():
    parser = argparse.ArgumentParser(
        description="Run lifecourse Simulation and Analysis."
    )
    parser.add_argument(
        "--config_name",
        type=str,
        default="DEFAULT_CONFIG",
        help="Name of the simulation configuration to use (e.g., DEFAULT_CONFIG, MINIMAL_TEST_CONFIG).",
    )
    parser.add_argument(
        "--config_file",
        type=str,
        help="Path to an external YAML configuration file to load and override settings.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with detailed output and single-threaded execution.",
    )
    args = parser.parse_args()

    # Load configuration using the new robust loader
    config = load_config(
        config_name=args.config_name, config_file_path=args.config_file
    )

    # Load parameters dynamically based on configuration
    DISTRIBUTIONS, START_YEAR, sample_params_from_dist, get_mean_params = get_parameter_attributes(
        config, 'DISTRIBUTIONS', 'START_YEAR', 'sample_params_from_dist', 'get_mean_params'
    )

    # Update global parameters based on loaded configuration
    current_pop_size = config["POP_SIZE"]
    current_psa_n = config["PSA_N"]
    simulation_end_year = START_YEAR + config["SIMULATION_YEARS"] - 1

    # Dynamically set YEARS based on simulation_years
    YEARS = list(range(START_YEAR, simulation_end_year + 1))

    print("--- Running lifecourse Simulation and Analysis ---")
    print(
        f"Simulation Parameters: Population Size={current_pop_size}, PSA Runs={current_psa_n}, Simulation Years={config['SIMULATION_YEARS']}"
    )

    # Get system resources for optimal Dask configuration
    cpu_count, total_memory_gb = get_system_resources()

    # Initialize Dask cluster for parallel processing with optimized settings
    if args.debug:
        # Use single-threaded execution for debugging
        cluster = LocalCluster(
            n_workers=1,
            threads_per_worker=1,
            memory_limit="2GB",
            silence_logs=False,
        )
    else:
        # Optimize Dask cluster based on system resources
        # Calculate optimal workers and threads based on system resources
        # Reserve some resources for the main process
        available_memory_gb = max(
            1, total_memory_gb - 2
        )  # Reserve 2GB for main process

        # Use number of workers based on CPU cores but limit by available memory
        # Assume each worker needs about 1GB of memory
        max_workers_by_memory = int(available_memory_gb)
        n_workers = min(
            cpu_count, max_workers_by_memory, 8
        )  # Cap at 8 workers to avoid excessive overhead

        # Distribute threads among workers
        threads_per_worker = max(1, cpu_count // n_workers)

        # Calculate memory limit per worker
        memory_limit_per_worker = f"{max(1, int(available_memory_gb // n_workers))}GB"

        print(
            f"System resources: {cpu_count} CPUs, {total_memory_gb:.1f}GB total memory"
        )
        print(
            f"Dask configuration: {n_workers} workers, {threads_per_worker} threads/worker, {memory_limit_per_worker} memory/worker"
        )

        cluster = LocalCluster(
            n_workers=n_workers,
            threads_per_worker=threads_per_worker,
            memory_limit=memory_limit_per_worker,
            silence_logs=True,  # Reduce logging for better performance
        )
    client = Client(cluster)

    try:
        print(f"Dask dashboard link: {client.dashboard_link}")

        # Module 6: Deterministic Scenarios
        print("\n--- Running Module 6: Deterministic Scenarios ---")
        base_mean_params = get_mean_params(DISTRIBUTIONS)

        # Load scenarios from YAML
        scenarios_config = load_scenarios_from_yaml("config/scenarios.yaml")

        results = []
        for name, overrides in scenarios_config.items():
            current_params_for_run = apply_scenario_overrides(
                base_mean_params, overrides
            )

            dc, dq = run_sim(
                current_params_for_run,
                pop_size=current_pop_size,
                years=YEARS,
                debug=args.debug,
            )
            icer = (dc / dq) if dq != 0 else 0
            results.append({"scenario": name, "dCost": dc, "dQALY": dq, "ICER": icer})

        from lifecourse.analysis.plotting import plot_deterministic_icers

        det_df = pd.DataFrame(results)
        det_df.to_csv("results/deterministic_summary.csv", index=False)
        print(det_df)

        plot_deterministic_icers(det_df)

        # Module 7: Probabilistic Sensitivity Analysis (PSA)
        if current_psa_n > 0:
            print("\n--- Running Module 7: Probabilistic Sensitivity Analysis ---")
            psa_out = []

            psa_args = []
            for i in range(current_psa_n):
                sampled_params = sample_params_from_dist(DISTRIBUTIONS, seed=i)
                psa_args.append((sampled_params, current_pop_size, i, YEARS))

            # Use client.map for better parallelization with optimized batching
            # Batch size based on number of workers to balance load
            batch_size = max(1, n_workers)

            futures = client.map(
                lambda args: run_sim(
                    args[0],
                    args[1],
                    args[2],
                    args[3],
                    args.debug if hasattr(args, "debug") else False,
                ),
                psa_args,
                batch_size=batch_size,  # Optimize batch size for better scheduling
            )
            # progress(futures) # Dask progress bar, can be noisy in CLI

            results = client.gather(futures)

            for i, (dc, dq) in enumerate(results):
                original_sampled_params = psa_args[i][0]
                row_data = {"run": i, "dCost": dc, "dQALY": dq}
                row_data.update(original_sampled_params)
                psa_out.append(row_data)

            psa_df_pd = pd.DataFrame(psa_out)
            psa_df_pd.to_csv("results/psa_samples.csv", index=False)
            print("PSA results saved to results/psa_samples.csv")

            from lifecourse.analysis.plotting import (
                plot_deterministic_icers,
                plot_ce_plane,
                plot_ceac,
                plot_evpi,
                plot_enmb,
            )

            # Module 8: CE-Plane, CEAC, EVPI & ENMB
            print("\n--- Running Module 8: CE-Plane, CEAC, EVPI & ENMB ---")
            wtp = np.linspace(0, 150000, 40)
            dcost = psa_df_pd["dCost"].to_numpy()
            dqaly = psa_df_pd["dQALY"].to_numpy()

            valid_psa = dqaly > 0
            nb = dqaly[valid_psa, None] * wtp[None, :] - dcost[valid_psa, None]

            plot_ce_plane(dcost, dqaly, wtp)
            plot_ceac(wtp, nb)
            plot_evpi(wtp, nb)
            plot_enmb(wtp, nb)

            # Module 9: One-Way Sensitivity (Tornado)
            print("\n--- Running Module 9: One-Way Sensitivity (Tornado) ---")
            tornado = []
            base_params = base_mean_params  # From Module 6

            if "severity_mild_prop" in base_params:
                base_params["severity_severe_prop"] = (
                    1.0 - base_params["severity_mild_prop"]
                )

            base_dc, base_dq = run_sim(
                base_params, pop_size=current_pop_size, years=YEARS, debug=args.debug
            )
            base_icer = (base_dc / base_dq) if base_dq != 0 else 0

            tornado_params_to_vary = [
                "familial_prop",
                "yield_wgs",
                "u_diag",
                "cost_inp_severe",
            ]

            for param_name in tornado_params_to_vary:
                dist_info = DISTRIBUTIONS[param_name]
                low_val, high_val, mean_val = 0, 0, 0
                if dist_info["dist"] == "beta":
                    mean_val = dist_info["alpha"] / (
                        dist_info["alpha"] + dist_info["beta"]
                    )
                    variance = (dist_info["alpha"] * dist_info["beta"]) / (
                        (dist_info["alpha"] + dist_info["beta"]) ** 2
                        * (dist_info["alpha"] + dist_info["beta"] + 1)
                    )
                    std_dev = np.sqrt(variance)
                    low_val, high_val = (
                        max(0, mean_val - 2 * std_dev),
                        min(1, mean_val + 2 * std_dev),
                    )
                elif dist_info["dist"] == "gamma":
                    mean_val = dist_info["shape"] * dist_info["scale"]
                    std_dev = np.sqrt(dist_info["shape"] * dist_info["scale"] ** 2)
                    low_val, high_val = (
                        max(0, mean_val - 2 * std_dev),
                        mean_val + 2 * std_dev,
                    )
                elif dist_info["dist"] == "lognormal":
                    mean_val = dist_info["scale"] * np.exp(dist_info["s"] ** 2 / 2)
                    low_val, high_val = mean_val * 0.90, mean_val * 1.10
                else:
                    continue

                for val in [low_val, high_val]:
                    p_temp = base_params.copy()
                    p_temp[param_name] = val
                    dc, dq = run_sim(
                        p_temp, pop_size=current_pop_size, years=YEARS, debug=args.debug
                    )
                    icer = (dc / dq) if dq != 0 else 0
                    change_type = "Low" if val < mean_val else "High"
                    tornado.append(
                        {"param": param_name, "change_type": change_type, "ICER": icer}
                    )

            from lifecourse.analysis.plotting import (
                plot_deterministic_icers,
                plot_ce_plane,
                plot_ceac,
                plot_evpi,
                plot_enmb,
                plot_tornado,
            )

            tor_df = pd.DataFrame(tornado)
            tor_df["ICER_diff"] = tor_df["ICER"] - base_icer
            tor_df["abs_diff"] = tor_df["ICER_diff"].abs()
            tor_df = tor_df.sort_values(by="abs_diff", ascending=True)

            plot_tornado(tor_df)

            # Module 10: Sub-group Analyses
            print("\n--- Running Module 10: Sub-group Analyses ---")
            sg = []
            mean_params_for_subgroup = base_mean_params  # from Module 6

            if "severity_mild_prop" in mean_params_for_subgroup:
                mean_params_for_subgroup["severity_severe_prop"] = (
                    1.0 - mean_params_for_subgroup["severity_mild_prop"]
                )

            # Load subgroup scenarios from YAML (or define here if not in YAML)
            subgroup_scenarios_config = load_scenarios_from_yaml(
                "config/scenarios.yaml"
            )

            for name, overrides in subgroup_scenarios_config.items():
                # Only run specific subgroup scenarios if desired, or all if not filtered
                if (
                    name in ["targeted_age_25", "high_coverage"] or "severity" in name
                ):  # Example filter
                    p_temp = mean_params_for_subgroup.copy()
                    for param_name, value in overrides.items():
                        if value is not None:
                            if (
                                isinstance(value, (int, float))
                                and param_name in p_temp
                                and isinstance(p_temp[param_name], (int, float))
                            ):
                                if (
                                    value < -0.5 or value > 0.5
                                ):  # Heuristic for absolute vs relative
                                    p_temp[param_name] = value  # Absolute value
                                else:
                                    p_temp[param_name] = (
                                        p_temp[param_name] + value
                                    )  # Relative adjustment
                            else:
                                p_temp[param_name] = (
                                    value  # Absolute value or non-numeric
                                )

                    # Special handling for severity subgroups if defined in YAML
                    if "severity_mild_prop" in overrides:
                        p_temp["severity_mild_prop"] = overrides["severity_mild_prop"]
                        p_temp["severity_severe_prop"] = (
                            1.0 - overrides["severity_mild_prop"]
                        )

                    dc, dq = run_sim(
                        p_temp, pop_size=current_pop_size, years=YEARS, debug=args.debug
                    )
                    icer = (dc / dq) if dq != 0 else 0
                    sg.append({"group": name, "ICER": icer})

            # Original hardcoded subgroup analyses (can be removed if fully replaced by YAML)
            # for sev_prop, label in [(1.0, 'Mild Only'), (0.0, 'Severe Only')]:
            #     p_temp = mean_params_for_subgroup.copy()
            #     p_temp['severity_mild_prop'] = sev_prop
            #     p_temp['severity_severe_prop'] = 1.0 - sev_prop
            #     dc, dq = run_sim(p_temp, pop_size=current_pop_size) # Smaller population for testing
            #     sg.append({'group': f"Severity: {label}", 'ICER': (dc / dq) if dq != 0 else 0})

            # for age in [0, 18, 30]:
            #     p_temp = mean_params_for_subgroup.copy()
            #     p_temp['min_test_age'] = age
            #     dc, dq = run_sim(p_temp, pop_size=current_pop_size) # Smaller population for testing
            #     sg.append({'group': f"Min Test Age: {age}", 'ICER': (dc / dq) if dq != 0 else 0})

            (_, int_full_df) = run_scenario(
                mean_params_for_subgroup, pop_size=current_pop_size, years=YEARS
            )
            dfp = int_full_df[int_full_df["arm"] == "prospective"]
            dfr = int_full_df[int_full_df["arm"] == "retrospective"]
            for yrs_n in [
                10,
                20,
                config["SIMULATION_YEARS"],
            ]:  # Use simulation_years for full horizon
                yr = START_YEAR + yrs_n - 1
                if yr in dfp["year"].values and yr in dfr["year"].values:
                    c1 = float(dfp.loc[dfp["year"] == yr, "costs"].values[0])
                    c0 = float(dfr.loc[dfr["year"] == yr, "costs"].values[0])
                    q1 = float(dfp.loc[dfp["year"] == yr, "qalys"].values[0])
                    q0 = float(dfr.loc[dfr["year"] == yr, "qalys"].values[0])
                    dc, dq = (c1 - c0), (q1 - q0)
                    sg.append(
                        {
                            "group": f"Horizon: {yrs_n} yrs",
                            "ICER": (dc / dq) if dq != 0 else 0,
                        }
                    )

            from lifecourse.analysis.plotting import (
                plot_deterministic_icers,
                plot_ce_plane,
                plot_ceac,
                plot_evpi,
                plot_enmb,
                plot_tornado,
                plot_subgroup_analysis,
            )

            sg_df = pd.DataFrame(sg)
            base_dc_subgroup, base_dq_subgroup = run_sim(
                mean_params_for_subgroup,
                pop_size=current_pop_size,
                years=YEARS,
                debug=args.debug,
            )
            base_icer_subgroup = (
                (base_dc_subgroup / base_dq_subgroup) if base_dq_subgroup != 0 else 0
            )

            plot_subgroup_analysis(sg_df, base_icer_subgroup)

            from lifecourse.analysis.plotting import (
                plot_deterministic_icers,
                plot_ce_plane,
                plot_ceac,
                plot_evpi,
                plot_enmb,
                plot_tornado,
                plot_subgroup_analysis,
                plot_cost_mix_stacked_area,
            )

            # Module 11: Cost-Mix Stacked Area (Prospective)
            print("\n--- Running Module 11: Cost-Mix Stacked Area (Prospective) ---")
            (_, mix_data) = run_scenario(
                mean_params_for_subgroup, pop_size=current_pop_size, years=YEARS
            )
            plot_cost_mix_stacked_area(
                mix_data,
                "prospective",
                "Cost Mix Over Time (Prospective Arm - Discounted Annual Costs)",
                "results/cost_mix_prospective.png",
            )

            # Module 12: 5-Year Budget Impact with Adoption Curves
            print("\n--- Running Module 12: 5-Year Budget Impact with Adoption Curves ---")
            budg = []
            yrs_budget = YEARS[:5]  # Use a fixed 5-year horizon for budget impact
            dfp = mix_data[mix_data["arm"] == "prospective"]
            dfr = mix_data[mix_data["arm"] == "retrospective"]

            # Define adoption curve configurations
            adoption_curves = [
                {'type': 'logistic', 'max_adoption': 1.0, 'growth_rate': 1.0, 'inflection_point': 3.0},
                {'type': 'exponential', 'max_adoption': 1.0, 'decay_rate': 0.5},
                {'type': 'stepwise', 'steps': [(1, 0.2), (3, 0.6), (5, 1.0)]}
            ]

            # Extract incremental costs for each year
            incremental_costs = []
            for yr in yrs_budget:
                if yr in dfp["year"].values and yr in dfr["year"].values:
                    c1 = float(dfp.loc[dfp["year"] == yr, "annual_cost"].item())
                    c0 = float(dfr.loc[dfr["year"] == yr, "annual_cost"].item())
                    incremental_costs.append(c1 - c0)
                else:
                    incremental_costs.append(0.0)  # Default to 0 if year not found

            incremental_costs = np.array(incremental_costs)
            years_array = np.array(yrs_budget)

            # Calculate budget impact for each adoption curve
            for i, curve_config in enumerate(adoption_curves):
                curve_type = curve_config['type']
                curve_name = f"{curve_type}_curve"

                # Extract curve parameters
                curve_params = {k: v for k, v in curve_config.items() if k != 'type'}

                # Calculate budget impact using adoption curve
                budget_result = calculate_budget_impact_with_adoption(
                    incremental_costs, years_array, curve_type, **curve_params
                )

                # Add results to budg list for plotting
                for j, yr in enumerate(years_array):
                    budg.append({
                        "curve_type": curve_name,
                        "year": yr,
                        "budget_impact": budget_result['adopted_costs'][j],
                        "adoption_rate": budget_result['adoption_rates'][j],
                        "cumulative_budget_impact": budget_result['cumulative_budget_impact'][j]
                    })

            from lifecourse.analysis.plotting import (
                plot_deterministic_icers,
                plot_ce_plane,
                plot_ceac,
                plot_evpi,
                plot_enmb,
                plot_tornado,
                plot_subgroup_analysis,
                plot_cost_mix_stacked_area,
                plot_budget_impact,
            )

            budg_df = pd.DataFrame(budg)
            plot_budget_impact(budg_df)

            from lifecourse.analysis.plotting import (
                plot_deterministic_icers,
                plot_ce_plane,
                plot_ceac,
                plot_evpi,
                plot_enmb,
                plot_tornado,
                plot_subgroup_analysis,
                plot_cost_mix_stacked_area,
                plot_budget_impact,
                plot_ses_equity,
            )

            # Module 13: Equity by SES Quintile
            print("\n--- Running Module 13: Equity by SES Quintile ---")
            bas = mix_data[mix_data["arm"] == "prospective"]
            if simulation_end_year in bas["year"].values:
                row_series = bas[bas["year"] == simulation_end_year].iloc[0]
                ses_cols = [f"ses_q{i}_pct" for i in range(5)]
                ses_vals = [float(row_series[col]) for col in ses_cols]
                labels = [f"Quintile {i+1}" for i in range(5)]
                plot_ses_equity(ses_vals, labels, simulation_end_year)

            from lifecourse.analysis.plotting import (
                plot_deterministic_icers,
                plot_ce_plane,
                plot_ceac,
                plot_evpi,
                plot_enmb,
                plot_tornado,
                plot_subgroup_analysis,
                plot_cost_mix_stacked_area,
                plot_budget_impact,
                plot_ses_equity,
                plot_psa_histograms,
            )

            # Module 14: PSA Histograms
            print("\n--- Running Module 14: PSA Histograms (dCost, dQALY) ---")
            cost_list = psa_df_pd["dCost"].tolist()
            qaly_list = psa_df_pd["dQALY"].tolist()
            plot_psa_histograms(cost_list, qaly_list)

            from lifecourse.analysis.plotting import (
                plot_deterministic_icers,
                plot_ce_plane,
                plot_ceac,
                plot_evpi,
                plot_enmb,
                plot_tornado,
                plot_subgroup_analysis,
                plot_cost_mix_stacked_area,
                plot_budget_impact,
                plot_ses_equity,
                plot_psa_histograms,
                plot_ceaf,
            )

            # Module 15: CEAF (Cost-Effectiveness Acceptability Frontier)
            print("\n--- Running Module 15: CEAF ---")
            prob = (nb > 0).mean(axis=0)
            plot_ceaf(wtp, prob)

            # Module 16: Input Parameter Summary (Updated for Distributions)
            print("\n--- Running Module 16: Saving Input Parameter Summary ---")

            param_summary_list = []
            for param_name, dist_info in DISTRIBUTIONS.items():
                summary_str = f"Distribution: {dist_info['dist']}"
                if dist_info["dist"] == "beta":
                    summary_str += f", Alpha: {dist_info['alpha']:.2f}, Beta: {dist_info['beta']:.2f}"
                elif dist_info["dist"] == "gamma":
                    summary_str += f", Shape: {dist_info['shape']:.2f}, Scale: {dist_info['scale']:.2f}"
                elif dist_info["dist"] == "lognormal":
                    summary_str += (
                        f", S: {dist_info['s']:.2f}, Scale: {dist_info['scale']:.2f}"
                    )
                elif dist_info["dist"] == "normal":
                    summary_str += f", Loc: {dist_info['loc']:.2f}, Scale: {dist_info['scale']:.2f}"
                elif dist_info["dist"] == "uniform":
                    summary_str += (
                        f", Low: {dist_info['low']:.2f}, High: {dist_info['high']:.2f}"
                    )
                elif dist_info["dist"] == "fixed":
                    summary_str += f", Value: {dist_info['value']:.2f}"
                param_summary_list.append(
                    {"parameter": param_name, "distribution_details": summary_str}
                )

            param_df = pd.DataFrame(param_summary_list)
            param_df.to_csv(
                "results/input_parameters_with_distributions.csv", index=False
            )
            print(
                "Input parameters with distributions saved to results/input_parameters_with_distributions.csv"
            )

            # Module 17: Publication Comparison
            print("\n--- Running Module 17: Publication Comparison ---")
            published = {"base": {"dCost": 480000, "dQALY": 6.5, "ICER": 73846}}
            pub_df = (
                pd.DataFrame.from_dict(published, orient="index")
                .reset_index()
                .rename(columns={"index": "scenario"})
            )
            pub_df = pub_df.rename(
                columns={"dCost": "dCost_pub", "dQALY": "dQALY_pub", "ICER": "ICER_pub"}
            )

            df_cmp = det_df.merge(pub_df, on="scenario", how="left")
            df_cmp = df_cmp.rename(
                columns={"dCost": "dCost_sim", "dQALY": "dQALY_sim", "ICER": "ICER_sim"}
            )
            print("Comparison of Simulation vs. Published Data:")
            print(df_cmp.to_string())
            df_cmp.to_csv("results/publication_comparison.csv", index=False)

            # Module 18: Familial ID Prevalence Sensitivity Analysis
            print(
                "\n--- Running Module 18: Familial ID Prevalence Sensitivity Analysis ---"
            )
            mean_params_for_sens = base_mean_params  # from Module 6
            familial_prevalence_range = np.linspace(0.10, 0.23, 10)
            familial_sens_results = []
            for f_prop in familial_prevalence_range:
                p_temp = mean_params_for_sens.copy()
                p_temp["familial_prop"] = f_prop
                dc, dq = run_sim(
                    p_temp, pop_size=current_pop_size, years=YEARS, debug=args.debug
                )
                icer = (dc / dq) if dq != 0 else 0
                familial_sens_results.append(
                    {"familial_prop": f_prop, "dCost": dc, "dQALY": dq, "ICER": icer}
                )

            from lifecourse.analysis.plotting import (
                plot_deterministic_icers,
                plot_ce_plane,
                plot_ceac,
                plot_evpi,
                plot_enmb,
                plot_tornado,
                plot_subgroup_analysis,
                plot_cost_mix_stacked_area,
                plot_budget_impact,
                plot_ses_equity,
                plot_psa_histograms,
                plot_ceaf,
                plot_familial_prevalence_sensitivity,
            )

            familial_sens_df = pd.DataFrame(familial_sens_results)
            print("Familial ID Prevalence Sensitivity Results:")
            print(familial_sens_df.to_string())

            plot_familial_prevalence_sensitivity(familial_sens_df)

            # Module 19: EVPPI Analysis
            print("\n--- Running Module 19: EVPPI Analysis ---")

            def calculate_evppi_curve(psa_df_local, param_name, wtp_range):
                evppi_values = []
                dcost_np = psa_df_local["dCost"].values
                dqaly_np = psa_df_local["dQALY"].values
                param_values_np = psa_df_local[param_name].values
                X = np.vstack([np.ones(len(psa_df_local)), param_values_np]).T

                for wtp_val in wtp_range:
                    nmb_np = dqaly_np * wtp_val - dcost_np
                    coeffs = np.linalg.lstsq(X, nmb_np, rcond=None)[0]
                    nmb_predicted = X @ coeffs
                    evppi_val = np.mean(np.maximum(0, nmb_np)) - np.mean(
                        np.maximum(0, nmb_predicted)
                    )
                    evppi_values.append(evppi_val)
                return np.array(evppi_values)

            parameters_for_evppi_new = [
                "familial_prop",
                "yield_wgs",
                "u_diag",
                "cost_inp_severe",
            ]
            from lifecourse.analysis.plotting import (
                plot_deterministic_icers,
                plot_ce_plane,
                plot_ceac,
                plot_evpi,
                plot_enmb,
                plot_tornado,
                plot_subgroup_analysis,
                plot_cost_mix_stacked_area,
                plot_budget_impact,
                plot_ses_equity,
                plot_psa_histograms,
                plot_ceaf,
                plot_familial_prevalence_sensitivity,
                plot_evppi_curves,
            )

            evppi_results = {}
            print("Calculating EVPPI for key parameters...")
            for param in parameters_for_evppi_new:
                if param in psa_df_pd.columns:
                    evppi_curve = calculate_evppi_curve(psa_df_pd, param, wtp)
                    evppi_results[param] = evppi_curve

            plot_evppi_curves(evppi_results, wtp)

            from lifecourse.analysis.plotting import (
                plot_deterministic_icers,
                plot_ce_plane,
                plot_ceac,
                plot_evpi,
                plot_enmb,
                plot_tornado,
                plot_subgroup_analysis,
                plot_cost_mix_stacked_area,
                plot_budget_impact,
                plot_ses_equity,
                plot_psa_histograms,
                plot_ceaf,
                plot_familial_prevalence_sensitivity,
                plot_evppi_curves,
                plot_psa_icer_distribution,
            )

            # Module 20: PSA ICER Distribution
            print("\n--- Running Module 20: PSA ICER Distribution ---")
            dc = psa_df_pd["dCost"]
            dq = psa_df_pd["dQALY"]
            psa_icers_np = (dc / dq).replace([np.inf, -np.inf], np.nan).dropna()
            plot_psa_icer_distribution(psa_icers_np)

            from lifecourse.analysis.plotting import (
                plot_deterministic_icers,
                plot_ce_plane,
                plot_ceac,
                plot_evpi,
                plot_enmb,
                plot_tornado,
                plot_subgroup_analysis,
                plot_cost_mix_stacked_area,
                plot_budget_impact,
                plot_ses_equity,
                plot_psa_histograms,
                plot_ceaf,
                plot_familial_prevalence_sensitivity,
                plot_evppi_curves,
                plot_psa_icer_distribution,
            )

            # Module 21: Cost-Mix Stacked Area (Retrospective)
            print("\n--- Running Module 21: Cost-Mix Stacked Area (Retrospective) ---")
            plot_cost_mix_stacked_area(
                mix_data,
                "retrospective",
                "Cost Mix Over Time (Retrospective Arm - Discounted Annual Costs)",
                "results/cost_mix_retrospective.png",
            )

            print("Retrospective Cost Mix analysis complete.")

            # Module 22: Calibration Analysis
            print("\n--- Running Module 22: Calibration Analysis ---")
            from lifecourse.analysis.advanced_analysis import run_calibration

            calibration_result = run_calibration(
                base_mean_params,
                pop_size=config["CALIBRATION_POP_SIZE"],
                years=YEARS,
                debug=args.debug,
            )
            print(
                f"Calibration completed with error: {calibration_result['error_pct']:.2f}%"
            )

            # Module 23: Structural Uncertainty Analysis
            print("\n--- Running Module 23: Structural Uncertainty Analysis ---")
            from lifecourse.analysis.advanced_analysis import (
                run_structural_uncertainty,
            )

            structural_uncertainty_df = run_structural_uncertainty(
                base_mean_params,
                num_runs=10,
                pop_size=config["STRUCTURAL_UNCERTAINTY_POP_SIZE"],
                years=YEARS,
                debug=args.debug,
            )
            print("Structural uncertainty analysis completed.")
            # Save results to CSV
            structural_uncertainty_df.to_csv(
                "results/structural_uncertainty.csv", index=False
            )
            print(
                "Structural uncertainty results saved to results/structural_uncertainty.csv"
            )

            # Module 24: Expected Value of Sample Information (EVSI) Analysis
            if current_psa_n > 0:  # Only run EVSI if PSA was performed
                print("\n--- Running Module 24: Expected Value of Sample Information (EVSI) Analysis ---")
                from lifecourse.analysis.advanced_analysis import run_evsi_analysis

                evsi_summary = run_evsi_analysis(
                    base_mean_params,
                    psa_runs=current_psa_n,  # Use PSA_N from config
                    wtp_threshold=config.get("WTP_THRESHOLD", 30000),
                    pop_size=config["POP_SIZE"],
                    years=YEARS,
                    debug=args.debug,
                )
                print("EVSI analysis completed.")

                # Generate EVSI plots
                from lifecourse.analysis.plotting import plot_evsi_curves, plot_evsi_vs_sample_size
                plot_evsi_curves(evsi_summary['evsi_results'])
                plot_evsi_vs_sample_size(evsi_summary['evsi_results'])
                print("EVSI plots saved to results/ directory.")
            else:
                print("\n--- Skipping Module 24: EVSI Analysis (PSA not performed) ---")

            # Module 25: Concentration Index Analysis
            if current_psa_n > 0:  # Only run if PSA was performed
                print("\n--- Running Module 25: Concentration Index Analysis ---")
                from lifecourse.analysis.advanced_analysis import run_concentration_analysis

                ci_results = run_concentration_analysis(
                    base_mean_params,
                    psa_runs=current_psa_n,
                    pop_size=config["POP_SIZE"],
                    years=YEARS,
                    debug=args.debug,
                )
                print("Concentration index analysis completed.")

                # Generate concentration index plot
                from lifecourse.analysis.plotting import plot_concentration_indices
                plot_concentration_indices(ci_results)
                print("Concentration index plot saved to results/concentration_indices.png")
            else:
                print("\n--- Skipping Module 25: Concentration Index Analysis (PSA not performed) ---")

            # Module 26: Distributional Impacts Analysis
            if current_psa_n > 0:  # Only run if PSA was performed
                print("\n--- Running Module 26: Distributional Impacts Analysis ---")
                from lifecourse.analysis.advanced_analysis import run_distributional_impacts_analysis
                from lifecourse.analysis.plotting import (
                    plot_concentration_curves,
                    plot_equity_efficiency_tradeoffs,
                    plot_distributional_uncertainty
                )

                distributional_results = run_distributional_impacts_analysis(
                    base_mean_params,
                    psa_runs=current_psa_n,
                    pop_size=config["POP_SIZE"],
                    years=YEARS,
                    debug=args.debug,
                )
                print("Distributional impacts analysis completed.")

                # Generate distributional analysis plots
                plot_concentration_curves(distributional_results)
                print("Concentration curves plot saved to results/distributional_concentration_curves.png")

                plot_equity_efficiency_tradeoffs(distributional_results)
                print("Equity-efficiency trade-offs plot saved to results/distributional_equity_efficiency.png")

                plot_distributional_uncertainty(distributional_results)
                print("Distributional uncertainty plot saved to results/distributional_uncertainty.png")

                # Print key distributional findings
                print("\nKey Distributional Findings:")
                dist_stats = distributional_results['distributional_stats']
                print(f"ICER Mean: £{dist_stats['overall']['icer_mean']:,.0f}/QALY")
                print(f"ICER Median: £{dist_stats['overall']['icer_median']:,.0f}/QALY")
                print(f"Cost-QALY Correlation: {dist_stats['overall']['joint_distribution_corr']:.3f}")

                equity_eff = distributional_results['equity_efficiency']
                print(f"Equity-Efficiency Ratio: {equity_eff['equity_metrics']['equity_efficiency_ratio']:.3f}")
                print(f"Efficiency Loss for Equity: {equity_eff['tradeoff_analysis']['efficiency_loss_for_equity']:.1%}")
            else:
                print("\n--- Skipping Module 26: Distributional Impacts Analysis (PSA not performed) ---")

            # Module 27: Value-Based Pricing (VBP) Analysis
            if current_psa_n > 0:  # Only run if PSA was performed
                print("\n--- Running Module 27: Value-Based Pricing (VBP) Analysis ---")
                from lifecourse.analysis.advanced_analysis import run_vbp_analysis

                vbp_results = run_vbp_analysis(
                    base_mean_params,
                    psa_runs=current_psa_n,
                    wtp_range=config.get("VBP_WTP_RANGE", np.linspace(10000, 50000, 21)),
                    budget_constraints=config.get("VBP_BUDGET_CONSTRAINTS", {
                        'max_incremental_budget': 10000000,  # £10M
                        'population_size': 1000000  # 1M people
                    }),
                    pricing_scenarios=config.get("VBP_PRICING_SCENARIOS", [
                        {'name': 'base_case', 'price_adjustment': 0, 'reimbursement_rate': 1.0},
                        {'name': 'price_increase_10pct', 'price_adjustment': 0.1, 'reimbursement_rate': 1.0},
                        {'name': 'price_increase_25pct', 'price_adjustment': 0.25, 'reimbursement_rate': 1.0},
                        {'name': 'partial_reimbursement', 'price_adjustment': 0, 'reimbursement_rate': 0.8},
                        {'name': 'value_based_pricing', 'price_adjustment': 0.15, 'reimbursement_rate': 0.9}
                    ]),
                    pop_size=config["POP_SIZE"],
                    years=YEARS,
                    debug=args.debug,
                )
                print("VBP analysis completed.")

                # Generate VBP plots
                from lifecourse.analysis.plotting import (
                    plot_vbp_price_thresholds,
                    plot_vbp_optimal_ranges,
                    plot_vbp_reimbursement_scenarios
                )
                plot_vbp_price_thresholds(vbp_results['price_thresholds'])
                plot_vbp_optimal_ranges(vbp_results['optimal_price_ranges'])
                plot_vbp_reimbursement_scenarios(vbp_results['reimbursement_scenarios'])
                print("VBP plots saved to results/ directory.")
            else:
                print("\n--- Skipping Module 27: VBP Analysis (PSA not performed) ---")

            # Module 28: Multi-Criteria Decision Analysis (MCDA)
            if current_psa_n > 0:  # Only run if PSA was performed
                print("\n--- Running Module 27: Multi-Criteria Decision Analysis (MCDA) ---")
                from lifecourse.analysis.advanced_analysis import run_mcda_analysis

                # Create decision matrix from PSA results for MCDA
                # Use key health economic outcomes as criteria
                alternatives = [f'PSA_Run_{i+1}' for i in range(len(psa_df_pd))]

                # Define criteria based on PSA results
                criteria_data = {
                    'Incremental_Cost': psa_df_pd['dCost'].values,
                    'Incremental_QALY': psa_df_pd['dQALY'].values,
                    'ICER': psa_df_pd['ICER'].values if 'ICER' in psa_df_pd.columns else psa_df_pd['dCost'] / (psa_df_pd['dQALY'] + 1e-10),
                    'Cost_Effectiveness': -psa_df_pd['ICER'].values if 'ICER' in psa_df_pd.columns else -psa_df_pd['dCost'] / (psa_df_pd['dQALY'] + 1e-10),  # Negative ICER for "benefit"
                    'Efficiency': psa_df_pd['dQALY'].values / (psa_df_pd['dCost'].values + 1e-10)  # QALYs per £
                }

                decision_matrix = pd.DataFrame(criteria_data, index=alternatives)

                # Define pairwise comparisons for AHP (example healthcare decision criteria)
                pairwise_comparisons = {
                    ('Incremental_QALY', 'Incremental_Cost'): 5,  # QALYs much more important than cost
                    ('Incremental_QALY', 'ICER'): 4,
                    ('Incremental_QALY', 'Cost_Effectiveness'): 3,
                    ('Incremental_QALY', 'Efficiency'): 2,
                    ('Incremental_Cost', 'ICER'): 1/3,  # Cost less important than ICER
                    ('Incremental_Cost', 'Cost_Effectiveness'): 1/4,
                    ('Incremental_Cost', 'Efficiency'): 1/5,
                    ('ICER', 'Cost_Effectiveness'): 2,
                    ('ICER', 'Efficiency'): 3,
                    ('Cost_Effectiveness', 'Efficiency'): 2
                }

                # Define value functions for criteria
                value_functions = {
                    'Incremental_QALY': {'type': 'linear', 'direction': 'increasing'},
                    'Incremental_Cost': {'type': 'linear', 'direction': 'decreasing'},  # Lower cost is better
                    'ICER': {'type': 'linear', 'direction': 'decreasing'},  # Lower ICER is better
                    'Cost_Effectiveness': {'type': 'linear', 'direction': 'increasing'},
                    'Efficiency': {'type': 'linear', 'direction': 'increasing'}
                }

                mcda_results = run_mcda_analysis(
                    decision_matrix=decision_matrix,
                    weights=None,  # Will use AHP to determine weights
                    normalization_method=config.get("MCDA_NORMALIZATION", "linear"),
                    weight_method="ahp",
                    pairwise_comparisons=pairwise_comparisons,
                    value_functions=value_functions,
                    debug=args.debug,
                )
                print("MCDA analysis completed.")

                # Generate MCDA plots
                from lifecourse.analysis.plotting import (
                    plot_mcda_weights,
                    plot_mcda_ranking,
                    plot_mcda_radar,
                    plot_mcda_sensitivity_weights
                )
                plot_mcda_weights(mcda_results['weights'], mcda_results.get('ahp_analysis'))
                plot_mcda_ranking(mcda_results)
                plot_mcda_radar(mcda_results)
                plot_mcda_sensitivity_weights(mcda_results)
                print("MCDA plots saved to results/ directory.")
            else:
                print("\n--- Skipping Module 27: MCDA Analysis (PSA not performed) ---")

    finally:
        client.close()
        cluster.close()
        print("Dask cluster closed.")


if __name__ == "__main__":
    main()
