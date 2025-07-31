import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import yaml
import argparse
from dask.distributed import LocalCluster, Client

from config.config_loader import load_config # Import the new config loader

from src.model.parameters import (
    DISTRIBUTIONS,
    START_YEAR,
    sample_params_from_dist,
    get_mean_params,
)
from src.analysis.run_helpers import run_sim, run_scenario
from src.data_loader import load_scenarios_from_yaml, apply_scenario_overrides

def main():
    parser = argparse.ArgumentParser(description="Run LifeCourseID Simulation and Analysis.")
    parser.add_argument('--config_name', type=str, default='DEFAULT_CONFIG',
                        help='Name of the simulation configuration to use (e.g., DEFAULT_CONFIG, MINIMAL_TEST_CONFIG).')
    parser.add_argument('--config_file', type=str,
                        help='Path to an external YAML configuration file to load and override settings.')
    args = parser.parse_args()

    # Load configuration using the new robust loader
    config = load_config(config_name=args.config_name, config_file_path=args.config_file)

    # Update global parameters based on loaded configuration
    current_pop_size = config['POP_SIZE']
    current_psa_n = config['PSA_N']
    simulation_end_year = START_YEAR + config['SIMULATION_YEARS'] - 1
    
    # Dynamically set YEARS based on simulation_years
    YEARS = list(range(START_YEAR, simulation_end_year + 1))

    print("--- Running LifeCourseID Simulation and Analysis ---")
    print(f"Simulation Parameters: Population Size={current_pop_size}, PSA Runs={current_psa_n}, Simulation Years={config['SIMULATION_YEARS']}")

    # Initialize Dask cluster for parallel processing
    cluster = LocalCluster()
    client = Client(cluster)

    try:
        print(f"Dask dashboard link: {client.dashboard_link}")

        # Module 6: Deterministic Scenarios
        print("\n--- Running Module 6: Deterministic Scenarios ---")
        base_mean_params = get_mean_params(DISTRIBUTIONS)

        # Load scenarios from YAML
        scenarios_config = load_scenarios_from_yaml('config/scenarios.yaml')

        results = []
        for name, overrides in scenarios_config.items():
            current_params_for_run = apply_scenario_overrides(base_mean_params, overrides)

            dc, dq = run_sim(current_params_for_run, pop_size=current_pop_size, years=YEARS)
            icer = (dc / dq) if dq != 0 else 0
            results.append({'scenario': name, 'dCost': dc, 'dQALY': dq, 'ICER': icer})

        from src.analysis.plotting import plot_deterministic_icers
        det_df = pd.DataFrame(results)
        det_df.to_csv('results/deterministic_summary.csv', index=False)
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

            futures = client.map(lambda args: run_sim(args[0], args[1], args[2], args[3]), psa_args)
            # progress(futures) # Dask progress bar, can be noisy in CLI

            results = client.gather(futures)

            for i, (dc, dq) in enumerate(results):
                original_sampled_params = psa_args[i][0]
                row_data = {'run': i, 'dCost': dc, 'dQALY': dq}
                row_data.update(original_sampled_params)
                psa_out.append(row_data)

            psa_df_pd = pd.DataFrame(psa_out)
            psa_df_pd.to_csv('results/psa_samples.csv', index=False)
            print("PSA results saved to results/psa_samples.csv")

            from src.analysis.plotting import (
        plot_deterministic_icers, plot_ce_plane, plot_ceac, plot_evpi, plot_enmb
    )
            # Module 8: CE-Plane, CEAC, EVPI & ENMB
            print("\n--- Running Module 8: CE-Plane, CEAC, EVPI & ENMB ---")
            wtp = np.linspace(0, 150000, 40)
            dcost = psa_df_pd['dCost'].to_numpy()
            dqaly = psa_df_pd['dQALY'].to_numpy()

            valid_psa = dqaly > 0
            nb = dqaly[valid_psa, None] * wtp[None, :] - dcost[valid_psa, None]

            plot_ce_plane(dcost, dqaly, wtp)
            plot_ceac(wtp, nb)
            plot_evpi(wtp, nb)
            plot_enmb(wtp, nb)

            # Module 9: One-Way Sensitivity (Tornado)
            print("\n--- Running Module 9: One-Way Sensitivity (Tornado) ---")
            tornado = []
            base_params = base_mean_params # From Module 6

            if 'severity_mild_prop' in base_params:
                base_params['severity_severe_prop'] = 1.0 - base_params['severity_mild_prop']

            base_dc, base_dq = run_sim(base_params, pop_size=current_pop_size, years=YEARS)
            base_icer = (base_dc / base_dq) if base_dq != 0 else 0

            tornado_params_to_vary = ['familial_prop', 'yield_wgs', 'u_diag', 'cost_inp_severe']

            for param_name in tornado_params_to_vary:
                dist_info = DISTRIBUTIONS[param_name]
                low_val, high_val, mean_val = 0, 0, 0
                if dist_info['dist'] == 'beta':
                    mean_val = dist_info['alpha'] / (dist_info['alpha'] + dist_info['beta'])
                    variance = (dist_info['alpha'] * dist_info['beta']) / ((dist_info['alpha'] + dist_info['beta'])**2 * (dist_info['alpha'] + dist_info['beta'] + 1))
                    std_dev = np.sqrt(variance)
                    low_val, high_val = max(0, mean_val - 2 * std_dev), min(1, mean_val + 2 * std_dev)
                elif dist_info['dist'] == 'gamma':
                    mean_val = dist_info['shape'] * dist_info['scale']
                    std_dev = np.sqrt(dist_info['shape'] * dist_info['scale']**2)
                    low_val, high_val = max(0, mean_val - 2 * std_dev), mean_val + 2 * std_dev
                elif dist_info['dist'] == 'lognormal':
                    mean_val = dist_info['scale'] * np.exp(dist_info['s']**2 / 2)
                    low_val, high_val = mean_val * 0.90, mean_val * 1.10
                else: continue

                for val in [low_val, high_val]:
                    p_temp = base_params.copy()
                    p_temp[param_name] = val
                    dc, dq = run_sim(p_temp, pop_size=current_pop_size, years=YEARS)
                    icer = (dc / dq) if dq != 0 else 0
                    change_type = 'Low' if val < mean_val else 'High'
                    tornado.append({'param': param_name, 'change_type': change_type, 'ICER': icer})

            from src.analysis.plotting import (
        plot_deterministic_icers, plot_ce_plane, plot_ceac, plot_evpi, plot_enmb,
        plot_tornado
    )
            tor_df = pd.DataFrame(tornado)
            tor_df['ICER_diff'] = tor_df['ICER'] - base_icer
            tor_df['abs_diff'] = tor_df['ICER_diff'].abs()
            tor_df = tor_df.sort_values(by='abs_diff', ascending=True)

            plot_tornado(tor_df)

            # Module 10: Sub-group Analyses
            print("\n--- Running Module 10: Sub-group Analyses ---")
            sg = []
            mean_params_for_subgroup = base_mean_params # from Module 6

            if 'severity_mild_prop' in mean_params_for_subgroup:
                mean_params_for_subgroup['severity_severe_prop'] = 1.0 - mean_params_for_subgroup['severity_mild_prop']

            # Load subgroup scenarios from YAML (or define here if not in YAML)
            subgroup_scenarios_config = load_scenarios_from_yaml('config/scenarios.yaml')

            for name, overrides in subgroup_scenarios_config.items():
                # Only run specific subgroup scenarios if desired, or all if not filtered
                if name in ['targeted_age_25', 'high_coverage'] or 'severity' in name: # Example filter
                    p_temp = mean_params_for_subgroup.copy()
                    for param_name, value in overrides.items():
                        if value is not None:
                            if isinstance(value, (int, float)) and param_name in p_temp and isinstance(p_temp[param_name], (int, float)):
                                if value < -0.5 or value > 0.5: # Heuristic for absolute vs relative
                                    p_temp[param_name] = value # Absolute value
                                else:
                                    p_temp[param_name] = p_temp[param_name] + value # Relative adjustment
                            else:
                                p_temp[param_name] = value # Absolute value or non-numeric

                    # Special handling for severity subgroups if defined in YAML
                    if 'severity_mild_prop' in overrides:
                        p_temp['severity_mild_prop'] = overrides['severity_mild_prop']
                        p_temp['severity_severe_prop'] = 1.0 - overrides['severity_mild_prop']

                    dc, dq = run_sim(p_temp, pop_size=current_pop_size, years=YEARS)
                    icer = (dc / dq) if dq != 0 else 0
                    sg.append({'group': name, 'ICER': icer})

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

            (_, int_full_df) = run_scenario(mean_params_for_subgroup, pop_size=current_pop_size, years=YEARS)
            dfp = int_full_df[int_full_df['arm'] == 'prospective']
            dfr = int_full_df[int_full_df['arm'] == 'retrospective']
            for yrs_n in [10, 20, args.simulation_years]: # Use simulation_years for full horizon
                yr = START_YEAR + yrs_n - 1
                if yr in dfp['year'].values and yr in dfr['year'].values:
                    c1 = float(dfp.loc[dfp['year'] == yr, 'costs'].values[0])
                    c0 = float(dfr.loc[dfr['year'] == yr, 'costs'].values[0])
                    q1 = float(dfp.loc[dfp['year'] == yr, 'qalys'].values[0])
                    q0 = float(dfr.loc[dfr['year'] == yr, 'qalys'].values[0])
                    dc, dq = (c1 - c0), (q1 - q0)
                    sg.append({'group': f"Horizon: {yrs_n} yrs", 'ICER': (dc / dq) if dq != 0 else 0})

            from src.analysis.plotting import (
        plot_deterministic_icers, plot_ce_plane, plot_ceac, plot_evpi, plot_enmb,
        plot_tornado, plot_subgroup_analysis
    )
            sg_df = pd.DataFrame(sg)
            base_dc_subgroup, base_dq_subgroup = run_sim(mean_params_for_subgroup, pop_size=current_pop_size, years=YEARS)
            base_icer_subgroup = (base_dc_subgroup / base_dq_subgroup) if base_dq_subgroup != 0 else 0

            plot_subgroup_analysis(sg_df, base_icer_subgroup)

            from src.analysis.plotting import (
        plot_deterministic_icers, plot_ce_plane, plot_ceac, plot_evpi, plot_enmb,
        plot_tornado, plot_subgroup_analysis, plot_cost_mix_stacked_area
    )
            # Module 11: Cost-Mix Stacked Area (Prospective)
            print("\n--- Running Module 11: Cost-Mix Stacked Area (Prospective) ---")
            (_, mix_data) = run_scenario(mean_params_for_subgroup, pop_size=current_pop_size, years=YEARS)
            plot_cost_mix_stacked_area(mix_data, 'prospective', 'Cost Mix Over Time (Prospective Arm - Discounted Annual Costs)', 'results/cost_mix_prospective.png')

            # Module 12: 5-Year Budget Impact
            print("\n--- Running Module 12: 5-Year Budget Impact ---")
            budg = []
            uptakes = [0.2, 0.5, 0.8]
            yrs_budget = YEARS[:5] # Use a fixed 5-year horizon for budget impact
            dfp = mix_data[mix_data['arm'] == 'prospective']
            dfr = mix_data[dfr['arm'] == 'retrospective']

            for u in uptakes:
                for yr in yrs_budget:
                    if yr in dfp['year'].values and yr in dfr['year'].values:
                        c1 = float(dfp.loc[dfp['year'] == yr, 'annual_cost'].item())
                        c0 = float(dfr.loc[dfr['year'] == yr, 'annual_cost'].item())
                        incremental_cost = c1 - c0
                        budg.append({'uptake': u, 'year': yr, 'budget_impact': incremental_cost * u})

            from src.analysis.plotting import (
        plot_deterministic_icers, plot_ce_plane, plot_ceac, plot_evpi, plot_enmb,
        plot_tornado, plot_subgroup_analysis, plot_cost_mix_stacked_area,
        plot_budget_impact
    )
            budg_df = pd.DataFrame(budg)
            plot_budget_impact(budg_df)

            from src.analysis.plotting import (
        plot_deterministic_icers, plot_ce_plane, plot_ceac, plot_evpi, plot_enmb,
        plot_tornado, plot_subgroup_analysis, plot_cost_mix_stacked_area,
        plot_budget_impact, plot_ses_equity
    )
            # Module 13: Equity by SES Quintile
            print("\n--- Running Module 13: Equity by SES Quintile ---")
            bas = mix_data[mix_data['arm'] == 'prospective']
            if YEARS[-1] in bas['year'].values:
                row_series = bas[bas['year'] == YEARS[-1]].iloc[0]
                ses_cols = [f'ses_q{i}_pct' for i in range(5)]
                ses_vals = [float(row_series[col]) for col in ses_cols]
                labels = [f'Quintile {i+1}' for i in range(5)]
                plot_ses_equity(ses_vals, labels, YEARS[-1])

            from src.analysis.plotting import (
        plot_deterministic_icers, plot_ce_plane, plot_ceac, plot_evpi, plot_enmb,
        plot_tornado, plot_subgroup_analysis, plot_cost_mix_stacked_area,
        plot_budget_impact, plot_ses_equity, plot_psa_histograms
    )
            # Module 14: PSA Histograms
            print("\n--- Running Module 14: PSA Histograms (dCost, dQALY) ---")
            cost_list = psa_df_pd['dCost'].tolist()
            qaly_list = psa_df_pd['dQALY'].tolist()
            plot_psa_histograms(cost_list, qaly_list)

            from src.analysis.plotting import (
        plot_deterministic_icers, plot_ce_plane, plot_ceac, plot_evpi, plot_enmb,
        plot_tornado, plot_subgroup_analysis, plot_cost_mix_stacked_area,
        plot_budget_impact, plot_ses_equity, plot_psa_histograms, plot_ceaf
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
                if dist_info['dist'] == 'beta':
                    summary_str += f", Alpha: {dist_info['alpha']:.2f}, Beta: {dist_info['beta']:.2f}"
                elif dist_info['dist'] == 'gamma':
                    summary_str += f", Shape: {dist_info['shape']:.2f}, Scale: {dist_info['scale']:.2f}"
                elif dist_info['dist'] == 'lognormal':
                    summary_str += f", S: {dist_info['s']:.2f}, Scale: {dist_info['scale']:.2f}"
                elif dist_info['dist'] == 'normal':
                    summary_str += f", Loc: {dist_info['loc']:.2f}, Scale: {dist_info['scale']:.2f}"
                elif dist_info['dist'] == 'uniform':
                    summary_str += f", Low: {dist_info['low']:.2f}, High: {dist_info['high']:.2f}"
                elif dist_info['dist'] == 'fixed':
                    summary_str += f", Value: {dist_info['value']:.2f}"
                param_summary_list.append({'parameter': param_name, 'distribution_details': summary_str})

            param_df = pd.DataFrame(param_summary_list)
            param_df.to_csv('results/input_parameters_with_distributions.csv', index=False)
            print("Input parameters with distributions saved to results/input_parameters_with_distributions.csv")

            # Module 17: Publication Comparison
            print("\n--- Running Module 17: Publication Comparison ---")
            published = {'base': {'dCost': 480000, 'dQALY': 6.5, 'ICER': 73846}}
            pub_df = pd.DataFrame.from_dict(published, orient='index').reset_index().rename(columns={'index': 'scenario'})
            pub_df = pub_df.rename(columns={'dCost': 'dCost_pub', 'dQALY': 'dQALY_pub', 'ICER': 'ICER_pub'})

            df_cmp = det_df.merge(pub_df, on='scenario', how='left')
            df_cmp = df_cmp.rename(columns={'dCost': 'dCost_sim', 'dQALY': 'dQALY_sim', 'ICER': 'ICER_sim'})
            print("Comparison of Simulation vs. Published Data:")
            print(df_cmp.to_string())
            df_cmp.to_csv('results/publication_comparison.csv', index=False)

            # Module 18: Familial ID Prevalence Sensitivity Analysis
            print("\n--- Running Module 18: Familial ID Prevalence Sensitivity Analysis ---")
            mean_params_for_sens = base_mean_params # from Module 6
            familial_prevalence_range = np.linspace(0.10, 0.23, 10)
            familial_sens_results = []
            for f_prop in familial_prevalence_range:
                p_temp = mean_params_for_sens.copy()
                p_temp['familial_prop'] = f_prop
                dc, dq = run_sim(p_temp, pop_size=current_pop_size, years=YEARS)
                icer = (dc / dq) if dq != 0 else 0
                familial_sens_results.append({'familial_prop': f_prop, 'dCost': dc, 'dQALY': dq, 'ICER': icer})

            from src.analysis.plotting import (
        plot_deterministic_icers, plot_ce_plane, plot_ceac, plot_evpi, plot_enmb,
        plot_tornado, plot_subgroup_analysis, plot_cost_mix_stacked_area,
        plot_budget_impact, plot_ses_equity, plot_psa_histograms, plot_ceaf,
        plot_familial_prevalence_sensitivity
    )
            familial_sens_df = pd.DataFrame(familial_sens_results)
            print("Familial ID Prevalence Sensitivity Results:")
            print(familial_sens_df.to_string())

            plot_familial_prevalence_sensitivity(familial_sens_df)

            # Module 19: EVPPI Analysis
            print("\n--- Running Module 19: EVPPI Analysis ---")

            def calculate_evppi_curve(psa_df_local, param_name, wtp_range):
                evppi_values = []
                dcost_np = psa_df_local['dCost'].values
                dqaly_np = psa_df_local['dQALY'].values
                param_values_np = psa_df_local[param_name].values
                X = np.vstack([np.ones(len(psa_df_local)), param_values_np]).T

                for wtp_val in wtp_range:
                    nmb_np = dqaly_np * wtp_val - dcost_np
                    coeffs = np.linalg.lstsq(X, nmb_np, rcond=None)[0]
                    nmb_predicted = X @ coeffs
                    evppi_val = np.mean(np.maximum(0, nmb_np)) - np.mean(np.maximum(0, nmb_predicted))
                    evppi_values.append(evppi_val)
                return np.array(evppi_values)

            parameters_for_evppi_new = ['familial_prop', 'yield_wgs', 'u_diag', 'cost_inp_severe']
            from src.analysis.plotting import (
        plot_deterministic_icers, plot_ce_plane, plot_ceac, plot_evpi, plot_enmb,
        plot_tornado, plot_subgroup_analysis, plot_cost_mix_stacked_area,
        plot_budget_impact, plot_ses_equity, plot_psa_histograms, plot_ceaf,
        plot_familial_prevalence_sensitivity, plot_evppi_curves
    )
            evppi_results = {}
            print("Calculating EVPPI for key parameters...")
            for param in parameters_for_evppi_new:
                if param in psa_df_pd.columns:
                    evppi_curve = calculate_evppi_curve(psa_df_pd, param, wtp)
                    evppi_results[param] = evppi_curve

            plot_evppi_curves(evppi_results, wtp)

            from src.analysis.plotting import (
        plot_deterministic_icers, plot_ce_plane, plot_ceac, plot_evpi, plot_enmb,
        plot_tornado, plot_subgroup_analysis, plot_cost_mix_stacked_area,
        plot_budget_impact, plot_ses_equity, plot_psa_histograms, plot_ceaf,
        plot_familial_prevalence_sensitivity, plot_evppi_curves,
        plot_psa_icer_distribution
    )
            # Module 20: PSA ICER Distribution
            print("\n--- Running Module 20: PSA ICER Distribution ---")
            dc = psa_df_pd['dCost']
            dq = psa_df_pd['dQALY']
            psa_icers_np = (dc/dq).replace([np.inf, -np.inf], np.nan).dropna()
            plot_psa_icer_distribution(psa_icers_np)

            from src.analysis.plotting import (
        plot_deterministic_icers, plot_ce_plane, plot_ceac, plot_evpi, plot_enmb,
        plot_tornado, plot_subgroup_analysis, plot_cost_mix_stacked_area,
        plot_budget_impact, plot_ses_equity, plot_psa_histograms, plot_ceaf,
        plot_familial_prevalence_sensitivity, plot_evppi_curves,
        plot_psa_icer_distribution
    )
            # Module 21: Cost-Mix Stacked Area (Retrospective)
            print("\n--- Running Module 21: Cost-Mix Stacked Area (Retrospective) ---")
            plot_cost_mix_stacked_area(mix_data, 'retrospective', 'Cost Mix Over Time (Retrospective Arm - Discounted Annual Costs)', 'results/cost_mix_retrospective.png')

            print("Retrospective Cost Mix analysis complete.")

            # Module 22: Calibration Analysis
            run_calibration(base_mean_params, pop_size=config['CALIBRATION_POP_SIZE'], years=YEARS) # Using current_pop_size and YEARS

            # Module 23: Structural Uncertainty Analysis
            run_structural_uncertainty(base_mean_params, num_runs=10, pop_size=config['STRUCTURAL_UNCERTAINTY_POP_SIZE'], years=YEARS)

    finally:
        client.close()
        cluster.close()
        print("Dask cluster closed.")

if __name__ == '__main__':
    main()

