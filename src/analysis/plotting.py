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
