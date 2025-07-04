import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def plot_deterministic_icers(det_df):
    """Plots the deterministic ICERs for each scenario."""
    plt.figure()
    plt.bar(det_df['scenario'], det_df['ICER'])
    plt.title('Deterministic ICERs (£/QALY)')
    plt.ylabel('ICER (£/QALY)')
    plt.savefig('results/deterministic_icers.png')
    # plt.show()

def plot_ce_plane(dcost, dqaly, wtp):
    """Plots the Cost-Effectiveness Plane."""
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

def plot_ceac(wtp, nb):
    """Plots the Cost-Effectiveness Acceptability Curve."""
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

def plot_evpi(wtp, nb):
    """Plots the Expected Value of Perfect Information."""
    evpi = np.mean(np.maximum(0, nb), axis=0) - np.maximum(0, np.mean(nb, axis=0))
    plt.figure()
    plt.plot(wtp, evpi)
    plt.title('Expected Value of Perfect Information (EVPI)')
    plt.xlabel('Willingness-to-Pay per QALY')
    plt.ylabel('EVPI')
    plt.grid(True)
    plt.savefig('results/evpi.png')
    # plt.show()

def plot_enmb(wtp, nb):
    """Plots the Expected Net Monetary Benefit."""
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

def plot_tornado(tor_df):
    """Plots the Tornado sensitivity analysis."""
    plt.figure(figsize=(10, len(tor_df) * 0.4))
    labels = [f"{row['param']} ({row['change_type']})" for idx, row in tor_df.iterrows()]
    colors = ['red' if x < 0 else 'green' for x in tor_df['ICER_diff']]
    plt.barh(labels, tor_df['ICER_diff'], color=colors)
    plt.axvline(0, color='black', lw=0.8)
    plt.xlabel('Change in ICER from base (£/QALY)')
    plt.title('Tornado Sensitivity Analysis (Selected Parameters)')
    plt.tight_layout()
    plt.savefig('results/tornado_sensitivity.png')
    # plt.show()

def plot_subgroup_analysis(sg_df, base_icer):
    """Plots the sub-group analysis."""
    plt.figure()
    plt.scatter(sg_df['ICER'], sg_df['group'], marker='o')
    plt.axvline(base_icer, color='grey', linestyle='--', label=f'Base Case ICER ({base_icer:,.0f})')
    plt.xlabel('ICER (£/QALY)')
    plt.title('Sub-group Analyses')
    plt.legend()
    plt.tight_layout()
    plt.grid(axis='x')
    plt.savefig('results/subgroup_analysis.png')
    # plt.show()

def plot_cost_mix_stacked_area(mix_data, arm, title, filename):
    """Plots the cost-mix stacked area for a given arm."""
    pm = mix_data[mix_data['arm'] == arm]
    cost_cols = ['cost_health', 'cost_edu', 'cost_respite', 'cost_mobility', 'cost_welfare', 'cost_emp', 'cost_morbidity']
    data = [pm[col] for col in cost_cols]

    plt.figure(figsize=(10, 6))
    plt.stackplot(pm['year'], *data, labels=[c.replace('cost_', '').capitalize() for c in cost_cols])
    plt.legend(loc='upper left')
    plt.title(title)
    plt.xlabel('Year')
    plt.ylabel('Annual Cost')
    plt.savefig(filename)
    # plt.show()

def plot_budget_impact(budg_df):
    """Plots the 5-year budget impact."""
    plt.figure()
    for u in budg_df['uptake'].unique():
        sub = budg_df[budg_df['uptake'] == u]
        plt.plot(sub['year'], sub['budget_impact'], label=f"Uptake {int(u*100)}%", marker='o')
    plt.title('5-Year Budget Impact')
    plt.xlabel('Year')
    plt.ylabel('Incremental Budget Impact')
    plt.legend()
    plt.grid(True)
    plt.savefig('results/budget_impact.png')
    # plt.show()

def plot_ses_equity(ses_vals, labels, year):
    """Plots the equity by SES quintile."""
    plt.figure()
    plt.bar(labels, ses_vals)
    plt.title(f'SES Distribution of Population in Final Year ({year})')
    plt.xlabel('SES Quintile')
    plt.ylabel('Percentage of Population (%)')
    plt.tight_layout()
    plt.savefig('results/ses_equity.png')
    # plt.show()

def plot_psa_histograms(cost_list, qaly_list):
    """Plots the PSA histograms for dCost and dQALY."""
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

def plot_ceaf(wtp, prob):
    """Plots the CEAC and CEAF."""
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

def plot_familial_prevalence_sensitivity(familial_sens_df):
    """Plots the sensitivity to familial ID prevalence."""
    plt.figure(figsize=(8, 6))
    plt.plot(familial_sens_df['familial_prop'], familial_sens_df['ICER'], marker='o', linestyle='-')
    plt.xlabel('Familial ID Prevalence')
    plt.ylabel('ICER (£/QALY)')
    plt.title('Sensitivity to Familial ID Prevalence')
    plt.grid(True)
    plt.savefig('results/familial_prevalence_sensitivity.png')
    # plt.show()

def plot_evppi_curves(evppi_results, wtp):
    """Plots the EVPPI curves."""
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

def plot_psa_icer_distribution(psa_icers_np):
    """Plots the PSA ICER distribution."""
    finite_icers = psa_icers_np[np.isfinite(psa_icers_np)]
    if len(finite_icers) > 0:
        lower_bound, upper_bound = np.percentile(finite_icers, [1, 99])
        finite_icers_capped = finite_icers[(finite_icers >= lower_bound) & (finite_icers <= upper_bound)]
    else:
        finite_icers_capped = np.array([])

    plt.figure(figsize=(8, 6))
    if len(finite_icers_capped) > 0:
        plt.hist(finite_icers_capped, bins=50, color='purple', edgecolor='black')
        plt.title('PSA Distribution of ICERs (Capped at 1st and 99th Percentiles)')
        plt.xlabel('ICER (£/QALY)')
        plt.ylabel('Frequency')
        plt.grid(True)
    plt.savefig('results/psa_icer_distribution.png')
    # plt.show()
