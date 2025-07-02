import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import yaml
from dask.distributed import LocalCluster, Client

from src.model.parameters import DISTRIBUTIONS, YEARS, START_YEAR, POP_SIZE, sample_params_from_dist
from src.analysis.run_helpers import run_sim, run_scenario

def load_scenarios_from_yaml(file_path):
    with open(file_path, 'r') as f:
        config = yaml.safe_load(f)
    return config['scenarios']

def main():
    print("--- Running LifeCourseID Simulation and Analysis ---")

    # Initialize Dask cluster for parallel processing
    cluster = LocalCluster()
    client = Client(cluster)

    try:
        print(f"Dask dashboard link: {client.dashboard_link}")

        # Module 6: Deterministic Scenarios
        print("\n--- Running Module 6: Deterministic Scenarios ---")
        base_mean_params = {}
        for k, v in DISTRIBUTIONS.items():
            if v['dist'] == 'beta':
                base_mean_params[k] = v['alpha'] / (v['alpha'] + v['beta'])
            elif v['dist'] == 'gamma':
                base_mean_params[k] = v['shape'] * v['scale']
            elif v['dist'] == 'lognormal':
                base_mean_params[k] = v['scale'] * np.exp(v['s']**2 / 2)
            elif v['dist'] == 'normal':
                base_mean_params[k] = v['loc']
            elif v['dist'] == 'uniform':
                base_mean_params[k] = (v['low'] + v['high']) / 2
            elif v['dist'] == 'fixed':
                base_mean_params[k] = v['value']

        if 'severity_mild_prop' in base_mean_params:
            base_mean_params['severity_severe_prop'] = 1.0 - base_mean_params['severity_mild_prop']

        # Load scenarios from YAML
        scenarios_config = load_scenarios_from_yaml('config/scenarios.yaml')

        results = []
        for name, overrides in scenarios_config.items():
            current_params_for_run = base_mean_params.copy()
            for param_name, value in overrides.items():
                if value is not None:
                    if isinstance(value, (int, float)) and param_name in base_mean_params and isinstance(base_mean_params[param_name], (int, float)):
                        # Check if it's a relative adjustment
                        if value < -0.5 or value > 0.5: # Heuristic for absolute vs relative
                            current_params_for_run[param_name] = value # Absolute value
                        else:
                            current_params_for_run[param_name] = base_mean_params[param_name] + value # Relative adjustment
                    else:
                        current_params_for_run[param_name] = value # Absolute value or non-numeric

            dc, dq = run_sim(current_params_for_run, pop_size=100) # Smaller population for testing
            icer = (dc / dq) if dq != 0 else 0
            results.append({'scenario': name, 'dCost': dc, 'dQALY': dq, 'ICER': icer})

        det_df = pd.DataFrame(results)
        det_df.to_csv('results/deterministic_summary.csv', index=False)
        print(det_df)

        plt.figure()
        plt.bar(det_df['scenario'], det_df['ICER'])
        plt.title('Deterministic ICERs (£/QALY)')
        plt.ylabel('ICER (£/QALY)')
        plt.savefig('results/deterministic_icers.png')
        # plt.show()

        # Module 7: Probabilistic Sensitivity Analysis (PSA)
        print("\n--- Running Module 7: Probabilistic Sensitivity Analysis ---")
        psa_n = 300
        psa_out = []

        psa_args = []
        for i in range(psa_n):
            sampled_params = sample_params_from_dist(DISTRIBUTIONS, seed=i)
            psa_args.append((sampled_params, 100, i)) # Smaller population for testing

        futures = client.map(lambda args: run_sim(args[0], args[1], args[2]), psa_args)
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

        # Module 8: CE-Plane, CEAC, EVPI & ENMB
        print("\n--- Running Module 8: CE-Plane, CEAC, EVPI & ENMB ---")
        wtp = np.linspace(0, 150000, 40)
        dcost = psa_df_pd['dCost'].to_numpy()
        dqaly = psa_df_pd['dQALY'].to_numpy()

        valid_psa = dqaly > 0
        nb = dqaly[valid_psa, None] * wtp[None, :] - dcost[valid_psa, None]

        plt.figure()
        plt.scatter(dqaly, dcost, alpha=0.6)
        plt.axvline(x=0, color='grey', linestyle='--', linewidth=0.8)
        plt.axhline(y=0, color='grey', linestyle='--', linewidth=0.8)
        plt.plot(wtp, wtp * 20000, color='green', linestyle=':', label='WTP £20,000/QALY')
        plt.plot(wtp, wtp * 30000, color='red', linestyle=':', label='WTP £30,000/QALY')
        plt.xlabel('Incremental QALYs (Delta QALY)')
        plt.ylabel('Incremental Cost (Delta Cost)')
        plt.title('Cost-Effectiveness Plane with WTP Thresholds')
        plt.grid(True)
        plt.legend()
        plt.savefig('results/ce_plane.png')
        # plt.show()

        prob = (nb > 0).mean(axis=0)
        plt.figure()
        plt.plot(wtp, prob)
        plt.title('Cost-Effectiveness Acceptability Curve (CEAC)')
        plt.xlabel('Willingness-to-Pay per QALY')
        plt.ylabel('Probability Cost-Effective')
        plt.ylim(0, 1)
        plt.grid(True)
        plt.savefig('results/ceac.png')
        # plt.show()

        evpi = np.mean(np.maximum(0, nb), axis=0) - np.maximum(0, np.mean(nb, axis=0))
        plt.figure()
        plt.plot(wtp, evpi)
        plt.title('Expected Value of Perfect Information (EVPI)')
        plt.xlabel('Willingness-to-Pay per QALY')
        plt.ylabel('EVPI')
        plt.grid(True)
        plt.savefig('results/evpi.png')
        # plt.show()

        enmb = np.mean(nb, axis=0)
        plt.figure()
        plt.plot(wtp, enmb)
        plt.axhline(y=0, color='grey', linestyle='--', linewidth=0.8)
        plt.title('Expected Net Monetary Benefit (ENMB) Curve')
        plt.xlabel('Willingness-to-Pay per QALY')
        plt.ylabel('Expected Net Monetary Benefit (£)')
        plt.grid(True)
        plt.savefig('results/enmb.png')
        # plt.show()

        # Module 9: One-Way Sensitivity (Tornado)
        print("\n--- Running Module 9: One-Way Sensitivity (Tornado) ---")
        tornado = []
        base_params = base_mean_params # From Module 6

        if 'severity_mild_prop' in base_params:
            base_params['severity_severe_prop'] = 1.0 - base_params['severity_mild_prop']

        base_dc, base_dq = run_sim(base_params, pop_size=100) # Smaller population for testing
        base_icer = base_dc / base_dq if base_dq != 0 else 0

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
                dc, dq = run_sim(p_temp, pop_size=100) # Smaller population for testing
                icer = (dc / dq) if dq != 0 else 0
                change_type = 'Low' if val < mean_val else 'High'
                tornado.append({'param': param_name, 'change_type': change_type, 'ICER': icer})

        tor_df = pd.DataFrame(tornado)
        tor_df['ICER_diff'] = tor_df['ICER'] - base_icer
        tor_df['abs_diff'] = tor_df['ICER_diff'].abs()
        tor_df = tor_df.sort_values(by='abs_diff', ascending=True)

        plt.figure(figsize=(10, len(tornado_params_to_vary) * 0.8))
        labels = [f"{row['param']} ({row['change_type']})" for idx, row in tor_df.iterrows()]
        colors = ['red' if x < 0 else 'green' for x in tor_df['ICER_diff']]
        plt.barh(labels, tor_df['ICER_diff'], color=colors)
        plt.axvline(0, color='black', lw=0.8)
        plt.xlabel('Change in ICER from base (£/QALY)')
        plt.title('Tornado Sensitivity Analysis (Selected Parameters)')
        plt.tight_layout()
        plt.savefig('results/tornado_sensitivity.png')
        # plt.show()

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

                dc, dq = run_sim(p_temp, pop_size=100) # Smaller population for testing
                icer = (dc / dq) if dq != 0 else 0
                sg.append({'group': name, 'ICER': icer})

        # Original hardcoded subgroup analyses (can be removed if fully replaced by YAML)
        # for sev_prop, label in [(1.0, 'Mild Only'), (0.0, 'Severe Only')]:
        #     p_temp = mean_params_for_subgroup.copy()
        #     p_temp['severity_mild_prop'] = sev_prop
        #     p_temp['severity_severe_prop'] = 1.0 - sev_prop
        #     dc, dq = run_sim(p_temp, pop_size=100) # Smaller population for testing
        #     sg.append({'group': f"Severity: {label}", 'ICER': (dc / dq) if dq != 0 else 0})

        # for age in [0, 18, 30]:
        #     p_temp = mean_params_for_subgroup.copy()
        #     p_temp['min_test_age'] = age
        #     dc, dq = run_sim(p_temp, pop_size=100) # Smaller population for testing
        #     sg.append({'group': f"Min Test Age: {age}", 'ICER': (dc / dq) if dq != 0 else 0})

        (_, int_full_df) = run_scenario(mean_params_for_subgroup, pop_size=100) # Smaller population for testing
        dfp = int_full_df[int_full_df['arm'] == 'prospective']
        dfr = int_full_df[int_full_df['arm'] == 'retrospective']
        for yrs_n in [10, 20, len(YEARS)]:
            yr = START_YEAR + yrs_n - 1
            if yr in dfp['year'].values and yr in dfr['year'].values:
                c1 = float(dfp.loc[dfp['year'] == yr, 'costs'].values[0])
                c0 = float(dfr.loc[dfr['year'] == yr, 'costs'].values[0])
                q1 = float(dfp.loc[dfp['year'] == yr, 'qalys'].values[0])
                q0 = float(dfr.loc[dfr['year'] == yr, 'qalys'].values[0])
                dc, dq = (c1 - c0), (q1 - q0)
                sg.append({'group': f"Horizon: {yrs_n} yrs", 'ICER': (dc / dq) if dq != 0 else 0})

        sg_df = pd.DataFrame(sg)
        base_dc_subgroup, base_dq_subgroup = run_sim(mean_params_for_subgroup, pop_size=10000) # Smaller population for testing
        base_icer_subgroup = base_dc_subgroup / base_dq_subgroup if base_dq_subgroup != 0 else 0

        plt.figure()
        plt.scatter(sg_df['ICER'], sg_df['group'], marker='o')
        plt.axvline(base_icer_subgroup, color='grey', linestyle='--', label=f'Base Case ICER ({base_icer_subgroup:,.0f})')
        plt.xlabel('ICER (£/QALY)')
        plt.title('Sub-group Analyses')
        plt.legend()
        plt.tight_layout()
        plt.grid(axis='x')
        plt.savefig('results/subgroup_analysis.png')
        # plt.show()

        # Module 11: Cost-Mix Stacked Area (Prospective)
        print("\n--- Running Module 11: Cost-Mix Stacked Area (Prospective) ---")
        (_, mix_data) = run_scenario(mean_params_for_subgroup, pop_size=100) # Smaller population for testing
        pm = mix_data[mix_data['arm'] == 'prospective']
        cost_cols = ['cost_health', 'cost_edu', 'cost_respite', 'cost_mobility', 'cost_welfare', 'cost_emp', 'cost_morbidity']
        data = [pm[col] for col in cost_cols]

        plt.figure(figsize=(10, 6))
        plt.stackplot(pm['year'], *data, labels=[c.replace('cost_', '').capitalize() for c in cost_cols])
        plt.legend(loc='upper left')
        plt.title('Cost Mix Over Time (Prospective Arm - Discounted Annual Costs)')
        plt.xlabel('Year')
        plt.ylabel('Annual Cost')
        plt.savefig('results/cost_mix_prospective.png')
        # plt.show()

        # Module 12: 5-Year Budget Impact
        print("\n--- Running Module 12: 5-Year Budget Impact ---")
        budg = []
        uptakes = [0.2, 0.5, 0.8]
        yrs = YEARS[:5]
        dfp = mix_data[mix_data['arm'] == 'prospective']
        dfr = mix_data[mix_data['arm'] == 'retrospective']

        for u in uptakes:
            for yr in yrs:
                if yr in dfp['year'].values and yr in dfr['year'].values:
                    c1 = float(dfp.loc[dfp['year'] == yr, 'annual_cost'].item())
                    c0 = float(dfr.loc[dfr['year'] == yr, 'annual_cost'].item())
                    incremental_cost = c1 - c0
                    budg.append({'uptake': u, 'year': yr, 'budget_impact': incremental_cost * u})

        budg_df = pd.DataFrame(budg)
        plt.figure()
        for u in uptakes:
            sub = budg_df[budg_df['uptake'] == u]
            plt.plot(sub['year'], sub['budget'], label=f"Uptake {int(u*100)}%", marker='o')
        plt.title('5-Year Budget Impact')
        plt.xlabel('Year')
        plt.ylabel('Incremental Budget Impact')
        plt.legend()
        plt.grid(True)
        plt.savefig('results/budget_impact.png')
        # plt.show()

        # Module 13: Equity by SES Quintile
        print("\n--- Running Module 13: Equity by SES Quintile ---")
        bas = mix_data[mix_data['arm'] == 'prospective']
        if YEARS[-1] in bas['year'].values:
            row_series = bas[bas['year'] == YEARS[-1]].iloc[0]
            ses_cols = [f'ses_q{i}_pct' for i in range(5)]
            ses_vals = [float(row_series[col]) for col in ses_cols]
            labels = [f'Quintile {i+1}' for i in range(5)]

            plt.figure()
            plt.bar(labels, ses_vals)
            plt.title(f'SES Distribution of Population in Final Year ({YEARS[-1]})')
            plt.xlabel('SES Quintile')
            plt.ylabel('Percentage of Population (%)')
            plt.tight_layout()
            plt.savefig('results/ses_equity.png')
            # plt.show()

        # Module 14: PSA Histograms
        print("\n--- Running Module 14: PSA Histograms (dCost, dQALY) ---")
        cost_list = psa_df_pd['dCost'].tolist()
        qaly_list = psa_df_pd['dQALY'].tolist()

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        ax1.hist(cost_list, bins=30, color='skyblue', edgecolor='black')
        ax1.set_title('PSA Distribution of Incremental Cost')
        ax1.set_xlabel('Delta Cost')
        ax1.set_ylabel('Frequency')

        ax2.hist(qaly_list, bins=30, color='salmon', edgecolor='black')
        ax2.set_title('PSA Distribution of Incremental QALYs')
        ax2.set_xlabel('Delta QALY')
        ax2.set_ylabel('Frequency')

        plt.tight_layout()
        plt.savefig('results/psa_histograms.png')
        # plt.show()

        # Module 15: CEAF (Cost-Effectiveness Acceptability Frontier)
        print("\n--- Running Module 15: CEAF ---")
        ceaf = np.maximum.accumulate(prob)

        plt.figure()
        plt.plot(wtp, prob, label='CEAC')
        plt.plot(wtp, ceaf, label='CEAF', linestyle='--')
        plt.title('CEAC and CEAF')
        plt.xlabel('Willingness-to-Pay per QALY')
        plt.ylabel('Probability')
        plt.legend()
        plt.grid(True)
        plt.savefig('results/ceaf.png')
        # plt.show()

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
            dc, dq = run_sim(p_temp, pop_size=10000) # Smaller population for testing
            icer = (dc / dq) if dq != 0 else 0
            familial_sens_results.append({'familial_prop': f_prop, 'dCost': dc, 'dQALY': dq, 'ICER': icer})

        familial_sens_df = pd.DataFrame(familial_sens_results)
        print("Familial ID Prevalence Sensitivity Results:")
        print(familial_sens_df.to_string())

        plt.figure(figsize=(8, 6))
        plt.plot(familial_sens_df['familial_prop'], familial_sens_df['ICER'], marker='o', linestyle='-')
        plt.xlabel('Familial ID Prevalence')
        plt.ylabel('ICER (£/QALY)')
        plt.title('Sensitivity to Familial ID Prevalence')
        plt.grid(True)
        plt.savefig('results/familial_prevalence_sensitivity.png')
        # plt.show()

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
        evppi_results = {}
        print("Calculating EVPPI for key parameters...")
        for param in parameters_for_evppi_new:
            if param in psa_df_pd.columns:
                evppi_curve = calculate_evppi_curve(psa_df_pd, param, wtp)
                evppi_results[param] = evppi_curve

        if evppi_results:
            plt.figure(figsize=(10, 6))
            for param, evppi_curve_host in evppi_results.items():
                plt.plot(wtp, evppi_curve_host, label=f'EVPPI ({param.replace("_", " ").title()})')
            plt.title('Expected Value of Partial Perfect Information (EVPPI) Curves')
            plt.xlabel('Willingness-to-Pay per QALY')
            plt.ylabel('EVPPI (£)')
            plt.legend()
            plt.grid(True)
            plt.savefig('results/evppi_curves.png')
            # plt.show()

        # Module 20: PSA ICER Distribution
        print("\n--- Running Module 20: PSA ICER Distribution ---")
        dc = psa_df_pd['dCost']
        dq = psa_df_pd['dQALY']
        psa_icers_np = (dc/dq).replace([np.inf, -np.inf], np.nan).dropna()

        finite_icers = psa_icers_np[np.isfinite(psa_icers_np)]
        if len(finite_icers) > 0:
            lower_bound, upper_bound = np.percentile(finite_icers, [1, 99])
            finite_icers_capped = finite_icers[(finite_icers >= lower_bound) & (finite_icers <= upper_bound)]
        else:
            finite_icers_capped = np.array([])

        plt.figure(figsize=(8, 6))
        if len(finite_icers_capped) > 0:
            # sns.histplot(finite_icers_capped, bins=50, kde=True, color='purple', edgecolor='black')
            plt.hist(finite_icers_capped, bins=50, color='purple', edgecolor='black') # Using plt.hist instead of sns.histplot to avoid seaborn dependency in main if not strictly needed
            plt.title('PSA Distribution of ICERs (Capped at 1st and 99th Percentiles)')
            plt.xlabel('ICER (£/QALY)')
            plt.ylabel('Frequency')
            plt.grid(True)
        plt.savefig('results/psa_icer_distribution.png')
        # plt.show()

        # Module 21: Cost-Mix Stacked Area (Retrospective)
        print("\n--- Running Module 21: Cost-Mix Stacked Area (Retrospective) ---")
        rm = mix_data[mix_data['arm'] == 'retrospective']
        cost_cols = ['cost_health', 'cost_edu', 'cost_respite', 'cost_mobility', 'cost_welfare', 'cost_emp', 'cost_morbidity']
        data_r = [rm[col] for col in cost_cols]

        plt.figure(figsize=(10, 6))
        plt.stackplot(rm['year'], *data_r, labels=[c.replace('cost_', '').capitalize() for c in cost_cols])
        plt.legend(loc='upper left')
        plt.title('Cost Mix Over Time (Retrospective Arm - Discounted Annual Costs)')
        plt.xlabel('Year')
        plt.ylabel('Annual Cost')
        plt.savefig('results/cost_mix_retrospective.png')
        # plt.show()

        print("Retrospective Cost Mix analysis complete.")

        # Module 22: Calibration Analysis
        run_calibration(base_mean_params, pop_size=10000) # Using a larger pop_size for calibration

        # Module 23: Structural Uncertainty Analysis
        run_structural_uncertainty(base_mean_params, num_runs=10, pop_size=10000)

    finally:
        client.close()
        cluster.close()
        print("Dask cluster closed.")

if __name__ == '__main__':
    main()
