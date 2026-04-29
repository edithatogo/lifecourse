import warnings
from importlib import import_module
from importlib.util import find_spec
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np

from lifecourse.backend_evaluation import BackendUnavailableError

PlotBackend = Literal["matplotlib", "plotnine"]


def _save_current_figure(filename: str) -> None:
    """Save the active Matplotlib figure and close it to release resources."""

    plt.savefig(filename)
    if plt.figure.__class__.__module__ != "unittest.mock":
        plt.close()


def _apply_tight_layout() -> None:
    """Apply Matplotlib tight layout without warning on intentionally dense figures."""

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Tight layout not applied.*",
            category=UserWarning,
        )
        plt.tight_layout()


def _plot_deterministic_icers_plotnine(det_df):
    if find_spec("plotnine") is None:
        raise BackendUnavailableError(
            "plotnine backend requested but `plotnine` is not installed. "
            "Install the optional `visualization` extra before using backend='plotnine'."
        )

    p9 = import_module("plotnine")
    plot = (
        p9.ggplot(det_df, p9.aes(x="scenario", y="ICER"))
        + p9.geom_col(fill="#2f6f73")
        + p9.labs(
            title="Deterministic ICERs (£/QALY)",
            x="Scenario",
            y="ICER (£/QALY)",
        )
        + p9.theme_minimal()
        + p9.theme(axis_text_x=p9.element_text(rotation=35, ha="right"))
    )
    plot.save("results/deterministic_icers.png", verbose=False)


def plot_deterministic_icers(det_df, backend: PlotBackend = "matplotlib"):
    """Plots the deterministic ICERs for each scenario."""
    if backend == "plotnine":
        _plot_deterministic_icers_plotnine(det_df)
        return

    plt.figure()
    plt.bar(det_df["scenario"], det_df["ICER"])
    plt.title("Deterministic ICERs (£/QALY)")
    plt.ylabel("ICER (£/QALY)")
    _save_current_figure("results/deterministic_icers.png")
    # plt.show()


def plot_ce_plane(dcost, dqaly, wtp):
    """Plots the Cost-Effectiveness Plane."""
    plt.figure()
    plt.scatter(dqaly, dcost, alpha=0.6)
    plt.axvline(x=0, color="grey", linestyle="--", linewidth=0.8)
    plt.axhline(y=0, color="grey", linestyle="--", linewidth=0.8)
    plt.plot(wtp, wtp * 20000, color="green", linestyle=":", label="WTP £20,000/QALY")
    plt.plot(wtp, wtp * 30000, color="red", linestyle=":", label="WTP £30,000/QALY")
    plt.xlabel("Incremental QALYs (Delta QALY)")
    plt.ylabel("Incremental Cost (Delta Cost)")
    plt.title("Cost-Effectiveness Plane with WTP Thresholds")
    plt.grid(True)
    plt.legend()
    _save_current_figure("results/ce_plane.png")
    # plt.show()


def plot_ceac(wtp, nb):
    """Plots the Cost-Effectiveness Acceptability Curve."""
    prob = (nb > 0).mean(axis=0)
    plt.figure()
    plt.plot(wtp, prob)
    plt.title("Cost-Effectiveness Acceptability Curve (CEAC)")
    plt.xlabel("Willingness-to-Pay per QALY")
    plt.ylabel("Probability Cost-Effective")
    plt.ylim(0, 1)
    plt.grid(True)
    _save_current_figure("results/ceac.png")
    # plt.show()


def plot_evpi(wtp, nb):
    """Plots the Expected Value of Perfect Information."""
    evpi = np.mean(np.maximum(0, nb), axis=0) - np.maximum(0, np.mean(nb, axis=0))
    plt.figure()
    plt.plot(wtp, evpi)
    plt.title("Expected Value of Perfect Information (EVPI)")
    plt.xlabel("Willingness-to-Pay per QALY")
    plt.ylabel("EVPI")
    plt.grid(True)
    _save_current_figure("results/evpi.png")
    # plt.show()


def plot_enmb(wtp, nb):
    """Plots the Expected Net Monetary Benefit."""
    enmb = np.mean(nb, axis=0)
    plt.figure()
    plt.plot(wtp, enmb)
    plt.axhline(y=0, color="grey", linestyle="--", linewidth=0.8)
    plt.title("Expected Net Monetary Benefit (ENMB) Curve")
    plt.xlabel("Willingness-to-Pay per QALY")
    plt.ylabel("Expected Net Monetary Benefit (£)")
    plt.grid(True)
    _save_current_figure("results/enmb.png")
    # plt.show()


def plot_tornado(tor_df):
    """Plots the Tornado sensitivity analysis."""
    plt.figure(figsize=(10, len(tor_df) * 0.4))
    labels = [
        f"{row['param']} ({row['change_type']})" for idx, row in tor_df.iterrows()
    ]
    colors = ["red" if x < 0 else "green" for x in tor_df["ICER_diff"]]
    plt.barh(labels, tor_df["ICER_diff"], color=colors)
    plt.axvline(0, color="black", lw=0.8)
    plt.xlabel("Change in ICER from base (£/QALY)")
    plt.title("Tornado Sensitivity Analysis (Selected Parameters)")
    _apply_tight_layout()
    _save_current_figure("results/tornado_sensitivity.png")
    # plt.show()


def plot_subgroup_analysis(sg_df, base_icer):
    """Plots the sub-group analysis."""
    plt.figure()
    plt.scatter(sg_df["ICER"], sg_df["group"], marker="o")
    plt.axvline(
        base_icer,
        color="grey",
        linestyle="--",
        label=f"Base Case ICER ({base_icer:,.0f})",
    )
    plt.xlabel("ICER (£/QALY)")
    plt.title("Sub-group Analyses")
    plt.legend()
    _apply_tight_layout()
    plt.grid(axis="x")
    _save_current_figure("results/subgroup_analysis.png")
    # plt.show()


def plot_cost_mix_stacked_area(mix_data, arm, title, filename):
    """Plots the cost-mix stacked area for a given arm."""
    pm = mix_data[mix_data["arm"] == arm]
    cost_cols = [
        "cost_health",
        "cost_edu",
        "cost_respite",
        "cost_mobility",
        "cost_welfare",
        "cost_emp",
        "cost_morbidity",
    ]
    data = [pm[col] for col in cost_cols]

    plt.figure(figsize=(10, 6))
    plt.stackplot(
        pm["year"],
        *data,
        labels=[c.replace("cost_", "").capitalize() for c in cost_cols],
    )
    plt.legend(loc="upper left")
    plt.title(title)
    plt.xlabel("Year")
    plt.ylabel("Annual Cost")
    _save_current_figure(filename)
    # plt.show()


def plot_budget_impact(budg_df):
    """Plots the 5-year budget impact with adoption curves."""
    plt.figure(figsize=(12, 8))

    # Plot budget impact for each curve type
    for curve_type in budg_df["curve_type"].unique():
        sub = budg_df[budg_df["curve_type"] == curve_type]
        plt.plot(
            sub["year"],
            sub["budget_impact"],
            label=f"{curve_type.replace('_', ' ').title()}",
            marker="o",
            linewidth=2,
        )

    plt.title("5-Year Budget Impact with Adoption Curves")
    plt.xlabel("Year")
    plt.ylabel("Incremental Budget Impact")
    plt.legend()
    plt.grid(True, alpha=0.3)
    _apply_tight_layout()
    _save_current_figure("results/budget_impact.png")
    # plt.show()

    # Create additional plot showing adoption rates over time
    plt.figure(figsize=(12, 6))

    for curve_type in budg_df["curve_type"].unique():
        sub = budg_df[budg_df["curve_type"] == curve_type]
        plt.plot(
            sub["year"],
            sub["adoption_rate"] * 100,
            label=f"{curve_type.replace('_', ' ').title()}",
            marker="s",
            linewidth=2,
        )

    plt.title("Adoption Rates Over Time")
    plt.xlabel("Year")
    plt.ylabel("Adoption Rate (%)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    _apply_tight_layout()
    _save_current_figure("results/adoption_rates.png")
    # plt.show()


def plot_ses_equity(ses_vals, labels, year):
    """Plots the equity by SES quintile."""
    plt.figure()
    plt.bar(labels, ses_vals)
    plt.title(f"SES Distribution of Population in Final Year ({year})")
    plt.xlabel("SES Quintile")
    plt.ylabel("Percentage of Population (%)")
    _apply_tight_layout()
    _save_current_figure("results/ses_equity.png")
    # plt.show()


def plot_psa_histograms(cost_list, qaly_list):
    """Plots the PSA histograms for dCost and dQALY."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    ax1.hist(cost_list, bins=30, color="skyblue", edgecolor="black")
    ax1.set_title("PSA Distribution of Incremental Cost")
    ax1.set_xlabel("Delta Cost")
    ax1.set_ylabel("Frequency")

    ax2.hist(qaly_list, bins=30, color="salmon", edgecolor="black")
    ax2.set_title("PSA Distribution of Incremental QALYs")
    ax2.set_xlabel("Delta QALY")
    ax2.set_ylabel("Frequency")

    _apply_tight_layout()
    _save_current_figure("results/psa_histograms.png")
    # plt.show()


def plot_ceaf(wtp, prob):
    """Plots the CEAC and CEAF."""
    ceaf = np.maximum.accumulate(prob)
    plt.figure()
    plt.plot(wtp, prob, label="CEAC")
    plt.plot(wtp, ceaf, label="CEAF", linestyle="--")
    plt.title("CEAC and CEAF")
    plt.xlabel("Willingness-to-Pay per QALY")
    plt.ylabel("Probability")
    plt.legend()
    plt.grid(True)
    _save_current_figure("results/ceaf.png")
    # plt.show()


def plot_familial_prevalence_sensitivity(familial_sens_df):
    """Plots the sensitivity to familial ID prevalence."""
    plt.figure(figsize=(8, 6))
    plt.plot(
        familial_sens_df["familial_prop"],
        familial_sens_df["ICER"],
        marker="o",
        linestyle="-",
    )
    plt.xlabel("Familial ID Prevalence")
    plt.ylabel("ICER (£/QALY)")
    plt.title("Sensitivity to Familial ID Prevalence")
    plt.grid(True)
    _save_current_figure("results/familial_prevalence_sensitivity.png")
    # plt.show()


def plot_evppi_curves(evppi_results, wtp):
    """Plots the EVPPI curves."""
    if evppi_results:
        plt.figure(figsize=(10, 6))
        for param, evppi_curve_host in evppi_results.items():
            plt.plot(
                wtp,
                evppi_curve_host,
                label=f"EVPPI ({param.replace('_', ' ').title()})",
            )
        plt.title("Expected Value of Partial Perfect Information (EVPPI) Curves")
        plt.xlabel("Willingness-to-Pay per QALY")
        plt.ylabel("EVPPI (£)")
        plt.legend()
        plt.grid(True)
        _save_current_figure("results/evppi_curves.png")
        # plt.show()


def plot_psa_icer_distribution(psa_icers_np):
    """Plots the PSA ICER distribution."""
    finite_icers = psa_icers_np[np.isfinite(psa_icers_np)]
    if len(finite_icers) > 0:
        lower_bound, upper_bound = np.percentile(finite_icers, [1, 99])
        finite_icers_capped = finite_icers[
            (finite_icers >= lower_bound) & (finite_icers <= upper_bound)
        ]
    else:
        finite_icers_capped = np.array([])

    plt.figure(figsize=(8, 6))
    if len(finite_icers_capped) > 0:
        plt.hist(finite_icers_capped, bins=50, color="purple", edgecolor="black")
        plt.title("PSA Distribution of ICERs (Capped at 1st and 99th Percentiles)")
        plt.xlabel("ICER (£/QALY)")
        plt.ylabel("Frequency")
        plt.grid(True)
    _save_current_figure("results/psa_icer_distribution.png")
    # plt.show()


def plot_evsi_curves(evsi_results):
    """Plots EVSI curves for different research designs."""
    plt.figure(figsize=(10, 6))

    designs = list(evsi_results.keys())
    evsi_values = [results["evsi"] for results in evsi_results.values()]
    sample_sizes = [results["sample_size"] for results in evsi_results.values()]

    # Create bar plot
    bars = plt.bar(range(len(designs)), evsi_values, color="skyblue", edgecolor="black")

    # Add value labels on bars
    for _i, (bar, evsi) in enumerate(zip(bars, evsi_values, strict=False)):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(evsi_values) * 0.01,
            f"£{evsi:,.0f}",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    plt.title("Expected Value of Sample Information (EVSI)\nby Research Design")
    plt.xlabel("Research Design")
    plt.ylabel("EVSI (£)")
    plt.xticks(
        range(len(designs)),
        [f"{d}\n(n={s})" for d, s in zip(designs, sample_sizes, strict=False)],
        rotation=45,
        ha="right",
    )
    plt.grid(True, alpha=0.3)
    _apply_tight_layout()
    _save_current_figure("results/evsi_curves.png")
    # plt.show()


def plot_evsi_vs_sample_size(evsi_results):
    """Plots EVSI vs sample size to show diminishing returns."""
    plt.figure(figsize=(8, 6))

    sample_sizes = [results["sample_size"] for results in evsi_results.values()]
    evsi_values = [results["evsi"] for results in evsi_results.values()]
    design_names = list(evsi_results.keys())

    plt.plot(sample_sizes, evsi_values, "bo-", linewidth=2, markersize=8)
    plt.fill_between(sample_sizes, evsi_values, alpha=0.3, color="blue")

    # Add design labels
    for _i, (x, y, name) in enumerate(
        zip(sample_sizes, evsi_values, design_names, strict=False)
    ):
        plt.annotate(
            name,
            (x, y),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7),
        )

    plt.title("EVSI vs Sample Size\n(Diminishing Returns Analysis)")
    plt.xlabel("Sample Size")
    plt.ylabel("Expected Value of Sample Information (£)")
    plt.grid(True, alpha=0.3)
    _apply_tight_layout()
    _save_current_figure("results/evsi_vs_sample_size.png")
    # plt.show()


def plot_concentration_indices(ci_results):
    """Plots concentration indices for health inequality analysis."""
    plt.figure(figsize=(10, 6))

    outcomes = ["cost_ci", "qaly_ci", "net_benefit_ci"]
    values = [ci_results[outcome] for outcome in outcomes]
    labels = ["Costs", "QALYs", "Net Benefit"]

    # Create horizontal bar chart
    bars = plt.barh(
        range(len(outcomes)), values, color=["red", "green", "blue"], alpha=0.7
    )

    # Add value labels
    for _i, (bar, value) in enumerate(zip(bars, values, strict=False)):
        plt.text(
            value + (0.01 if value >= 0 else -0.01),
            bar.get_y() + bar.get_height() / 2,
            f"{value:.3f}",
            va="center",
            ha="left" if value >= 0 else "right",
            fontweight="bold",
        )

    plt.axvline(x=0, color="black", linestyle="-", alpha=0.5)
    plt.title("Concentration Indices\nHealth Inequality Analysis")
    plt.xlabel("Concentration Index (-1 to 1)")
    plt.ylabel("Health Economic Outcome")
    plt.yticks(range(len(labels)), labels)
    plt.xlim(-1, 1)
    plt.grid(True, alpha=0.3)

    # Add interpretation text
    ci_results.get("interpretation", {})
    plt.figtext(
        0.02,
        0.02,
        "Interpretation:\n• Cost CI > 0: Costs concentrate among rich\n• QALY CI < 0: QALYs concentrate among poor\n• Net Benefit CI < 0: Benefits favor poor (equity-improving)",
        fontsize=8,
        style="italic",
    )

    _apply_tight_layout()
    _save_current_figure("results/concentration_indices.png")
    # plt.show()


def plot_vbp_price_thresholds(price_thresholds_results):
    """
    Plot price thresholds across different WTP values.

    Parameters:
    -----------
    price_thresholds_results : dict
        Results from calculate_price_thresholds function
    """
    plt.figure(figsize=(12, 8))

    wtp_values = []
    thresholds = []
    prob_ce = []

    for wtp, data in price_thresholds_results["thresholds"].items():
        wtp_values.append(wtp)
        thresholds.append(data["price_threshold"])
        prob_ce.append(data["probability_cost_effective"])

    # Create dual y-axis plot
    fig, ax1 = plt.subplots(figsize=(12, 8))

    # Plot price thresholds
    color = "tab:blue"
    ax1.set_xlabel("Willingness-to-Pay Threshold (£/QALY)")
    ax1.set_ylabel("Maximum Price Threshold (£)", color=color)
    line1 = ax1.plot(
        wtp_values,
        thresholds,
        "o-",
        color=color,
        linewidth=2,
        markersize=6,
        label="Price Threshold",
    )
    ax1.tick_params(axis="y", labelcolor=color)
    ax1.grid(True, alpha=0.3)

    # Create second y-axis for probability
    ax2 = ax1.twinx()
    color = "tab:red"
    ax2.set_ylabel("Probability Cost-Effective", color=color)
    line2 = ax2.plot(
        wtp_values,
        prob_ce,
        "s--",
        color=color,
        linewidth=2,
        markersize=6,
        label="P(Cost-Effective)",
    )
    ax2.tick_params(axis="y", labelcolor=color)
    ax2.set_ylim(0, 1)

    # Combine legends
    lines = line1 + line2
    labels = [line.get_label() for line in lines]
    ax1.legend(lines, labels, loc="upper left")

    plt.title(
        "Value-Based Pricing: Price Thresholds vs WTP\nMaximum Acceptable Price for Cost-Effectiveness"
    )
    _apply_tight_layout()
    _save_current_figure("results/vbp_price_thresholds.png")
    # plt.show()


def plot_vbp_optimal_ranges(optimal_ranges_results):
    """
    Plot optimal price ranges under budget constraints.

    Parameters:
    -----------
    optimal_ranges_results : dict
        Results from calculate_optimal_price_ranges function
    """
    plt.figure(figsize=(10, 6))

    opt_range = optimal_ranges_results["optimal_range"]

    # Create bar chart for price ranges
    labels = ["Minimum Price", "Budget-Constrained Max", "Cost-Effectiveness Max"]
    values = [
        opt_range["min_price"],
        opt_range["max_price_budget"],
        opt_range["max_price_cost_effective"],
    ]
    colors = ["lightcoral", "lightblue", "lightgreen"]

    bars = plt.bar(labels, values, color=colors, alpha=0.7)

    # Add value labels on bars
    for bar, value in zip(bars, values, strict=False):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_y() + bar.get_height() + 100,
            f"£{value:,.0f}",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    plt.ylabel("Price (£)")
    plt.title(
        "Value-Based Pricing: Optimal Price Range\nUnder Budget and Cost-Effectiveness Constraints"
    )
    plt.grid(True, alpha=0.3, axis="y")

    # Add interpretation text
    budget_constraint = optimal_ranges_results["budget_constraints"][
        "max_incremental_budget"
    ]
    pop_size = optimal_ranges_results["budget_constraints"]["population_size"]
    wtp = optimal_ranges_results["wtp_threshold"]

    plt.figtext(
        0.02,
        0.02,
        f"Analysis Parameters:\n• WTP Threshold: £{wtp:,.0f}/QALY\n• Budget Constraint: £{budget_constraint:,.0f}\n• Target Population: {pop_size:,.0f}\n• Expected Base Cost: £{opt_range['expected_base_cost']:,.0f}",
        fontsize=8,
        style="italic",
    )

    _apply_tight_layout()
    _save_current_figure("results/vbp_optimal_ranges.png")
    # plt.show()


def plot_vbp_reimbursement_scenarios(reimbursement_results):
    """
    Plot reimbursement scenario comparison.

    Parameters:
    -----------
    reimbursement_results : dict
        Results from analyze_reimbursement_scenarios function
    """
    plt.figure(figsize=(14, 10))

    scenarios = reimbursement_results["scenario_results"]
    scenario_names = list(scenarios.keys())

    # Extract data for plotting
    icers = [scenarios[name]["icer"] for name in scenario_names]
    prob_ce = [scenarios[name]["probability_cost_effective"] for name in scenario_names]
    budget_impacts = [
        scenarios[name]["budget_impact"] / 1e6 for name in scenario_names
    ]  # Convert to £M

    # Create subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

    # Plot 1: ICER comparison
    bars1 = ax1.bar(scenario_names, icers, color="skyblue", alpha=0.7)
    ax1.set_ylabel("ICER (£/QALY)")
    ax1.set_title("Incremental Cost-Effectiveness Ratio")
    ax1.tick_params(axis="x", rotation=45)
    ax1.grid(True, alpha=0.3, axis="y")

    # Add value labels
    for bar, value in zip(bars1, icers, strict=False):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_y() + bar.get_height() + 1000,
            f"£{value:,.0f}",
            ha="center",
            va="bottom",
            fontsize=8,
            rotation=90,
        )

    # Plot 2: Probability cost-effective
    bars2 = ax2.bar(scenario_names, prob_ce, color="lightgreen", alpha=0.7)
    ax2.set_ylabel("Probability Cost-Effective")
    ax2.set_title("Probability of Being Cost-Effective")
    ax2.set_ylim(0, 1)
    ax2.tick_params(axis="x", rotation=45)
    ax2.grid(True, alpha=0.3, axis="y")

    # Add percentage labels
    for bar, value in zip(bars2, prob_ce, strict=False):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_y() + bar.get_height() + 0.01,
            f"{value:.1%}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    # Plot 3: Budget impact
    bars3 = ax3.bar(scenario_names, budget_impacts, color="coral", alpha=0.7)
    ax3.set_ylabel("Budget Impact (£M)")
    ax3.set_title("Total Budget Impact")
    ax3.tick_params(axis="x", rotation=45)
    ax3.grid(True, alpha=0.3, axis="y")

    # Add value labels
    for bar, value in zip(bars3, budget_impacts, strict=False):
        ax3.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_y() + bar.get_height() + 0.1,
            f"£{value:.1f}M",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    # Plot 4: Scenario details table
    ax4.axis("off")
    ax4.set_title("Scenario Details")

    # Create table data
    table_data = []
    for name in scenario_names:
        scenario = scenarios[name]
        table_data.append(
            [
                name,
                f"£{scenario['expected_reimbursed_cost']:,.0f}",
                f"{scenario['reimbursement_rate']:.1%}",
                f"{scenario['price_adjustment']:.1%}",
            ]
        )

    table = ax4.table(
        cellText=table_data,
        colLabels=["Scenario", "Expected Cost", "Reimbursement", "Price Adj."],
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.5)

    plt.suptitle("Value-Based Pricing: Reimbursement Scenario Analysis", fontsize=14)
    _apply_tight_layout()
    _save_current_figure("results/vbp_reimbursement_scenarios.png")
    # plt.show()


def plot_mcda_weights(weights, ahp_analysis=None):
    """
    Plot criteria weights as a bar chart.

    Parameters:
    -----------
    weights : dict
        Dictionary of criteria weights
    ahp_analysis : dict, optional
        AHP analysis results for consistency information
    """
    plt.figure(figsize=(10, 6))

    criteria = list(weights.keys())
    weight_values = list(weights.values())

    bars = plt.bar(criteria, weight_values, color="lightblue", alpha=0.7)

    # Add value labels on bars
    for bar, value in zip(bars, weight_values, strict=False):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_y() + bar.get_height() + 0.01,
            f"{value:.3f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    plt.ylabel("Weight")
    plt.title("MCDA Criteria Weights")
    plt.xticks(rotation=45, ha="right")
    plt.grid(True, alpha=0.3, axis="y")

    # Add consistency information if available
    if ahp_analysis and "consistency_ratio" in ahp_analysis:
        cr = ahp_analysis["consistency_ratio"]
        consistent = ahp_analysis["consistent"]
        status = "Acceptable" if consistent else "Needs Review"
        plt.figtext(
            0.02,
            0.02,
            f"AHP Consistency Ratio: {cr:.4f} ({status})",
            fontsize=9,
            style="italic",
        )

    _apply_tight_layout()
    _save_current_figure("results/mcda_weights.png")
    # plt.show()


def plot_mcda_ranking(mcda_results, top_n=10):
    """
    Plot MCDA ranking of alternatives.

    Parameters:
    -----------
    mcda_results : dict
        Results from run_mcda_analysis function
    top_n : int
        Number of top alternatives to display
    """
    plt.figure(figsize=(12, 8))

    ranking = mcda_results["ranking"]
    top_ranking = ranking.head(top_n)

    bars = plt.barh(
        range(len(top_ranking)), top_ranking.values[::-1], color="lightgreen", alpha=0.7
    )

    plt.yticks(range(len(top_ranking)), top_ranking.index[::-1])
    plt.xlabel("MCDA Score")
    plt.title(f"Top {top_n} MCDA Ranking of Alternatives")
    plt.grid(True, alpha=0.3, axis="x")

    # Add score labels
    for _i, (bar, score) in enumerate(
        zip(bars, top_ranking.values[::-1], strict=False)
    ):
        plt.text(
            bar.get_width() + 0.001,
            bar.get_y() + bar.get_height() / 2,
            f"{score:.4f}",
            ha="left",
            va="center",
            fontsize=8,
        )

    _apply_tight_layout()
    _save_current_figure("results/mcda_ranking.png")
    # plt.show()


def plot_mcda_radar(mcda_results, alternatives_to_plot=None):
    """
    Create radar plot showing criteria scores for selected alternatives.

    Parameters:
    -----------
    mcda_results : dict
        Results from run_mcda_analysis function
    alternatives_to_plot : list, optional
        List of alternative names to include in radar plot. If None, plots top 3.
    """
    from math import pi

    import matplotlib.pyplot as plt

    weighted_matrix = mcda_results["weighted_matrix"]

    if alternatives_to_plot is None:
        # Plot top 3 alternatives
        ranking = mcda_results["ranking"]
        alternatives_to_plot = ranking.head(3).index.tolist()

    # Filter to selected alternatives
    plot_data = weighted_matrix.loc[alternatives_to_plot]

    # Number of criteria
    categories = list(plot_data.columns)
    n_criteria = len(categories)

    # Create angles for radar plot
    angles = [n / float(n_criteria) * 2 * pi for n in range(n_criteria)]
    angles += angles[:1]  # Close the plot

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(projection="polar"))

    # Plot each alternative
    colors = ["red", "blue", "green", "orange", "purple"]
    for i, alternative in enumerate(alternatives_to_plot):
        values = plot_data.loc[alternative].values.tolist()
        values += values[:1]  # Close the plot

        ax.plot(
            angles,
            values,
            "o-",
            linewidth=2,
            label=alternative,
            color=colors[i % len(colors)],
        )
        ax.fill(angles, values, alpha=0.25, color=colors[i % len(colors)])

    # Add labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=10)
    ax.set_ylim(0, max(plot_data.max()) * 1.1)
    ax.set_title("MCDA Criteria Scores - Radar Plot", size=14, pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1.0))
    ax.grid(True)

    _apply_tight_layout()
    _save_current_figure("results/mcda_radar.png")
    # plt.show()


def plot_mcda_sensitivity_weights(mcda_results, weight_variations=None):
    """
    Plot sensitivity analysis for different weight combinations.

    Parameters:
    -----------
    mcda_results : dict
        Results from run_mcda_analysis function
    weight_variations : list of dict, optional
        Different weight combinations to test. If None, creates variations.
    """
    if weight_variations is None:
        # Create some weight variations for sensitivity analysis
        criteria = list(mcda_results["weights"].keys())
        weight_variations = []

        # Equal weights
        weight_variations.append(
            {
                "name": "Equal Weights",
                "weights": {c: 1.0 / len(criteria) for c in criteria},
            }
        )

        # Emphasize different criteria
        for _i, criterion in enumerate(criteria):
            weights = {c: 0.1 for c in criteria}  # Base weight
            weights[criterion] = 0.6  # Emphasize this criterion
            # Normalize
            total = sum(weights.values())
            weights = {k: v / total for k, v in weights.items()}
            weight_variations.append(
                {"name": f"Emphasize {criterion}", "weights": weights}
            )

    plt.figure(figsize=(14, 8))

    # Get original ranking for comparison
    original_ranking = mcda_results["ranking"]
    top_alternatives = original_ranking.head(5).index.tolist()

    # Calculate rankings for each weight variation
    rankings_data = {}
    for var in weight_variations:
        # Recalculate weighted matrix with new weights
        normalized_matrix = mcda_results["normalized_matrix"]
        weighted_matrix = normalized_matrix.copy()
        for criterion in weighted_matrix.columns:
            weighted_matrix[criterion] = (
                weighted_matrix[criterion] * var["weights"][criterion]
            )

        scores = weighted_matrix.sum(axis=1)
        ranking = scores.sort_values(ascending=False)
        rankings_data[var["name"]] = ranking

    # Create ranking comparison plot
    x_positions = np.arange(len(top_alternatives))
    bar_width = 0.8 / len(weight_variations)

    for i, (var_name, ranking) in enumerate(rankings_data.items()):
        scores = [ranking.get(alt, 0) for alt in top_alternatives]
        plt.bar(
            x_positions + i * bar_width, scores, bar_width, label=var_name, alpha=0.7
        )

    plt.xlabel("Alternatives")
    plt.ylabel("MCDA Score")
    plt.title("MCDA Sensitivity Analysis - Weight Variations")
    plt.xticks(
        x_positions + bar_width * (len(weight_variations) - 1) / 2,
        top_alternatives,
        rotation=45,
        ha="right",
    )
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(True, alpha=0.3, axis="y")

    _apply_tight_layout()
    _save_current_figure("results/mcda_sensitivity_weights.png")
    # plt.show()


def plot_concentration_curves(distributional_results):
    """
    Plot concentration curves for costs and QALYs.

    Parameters:
    -----------
    distributional_results : dict
        Results from distributional impacts analysis
    """
    psa_results = distributional_results["psa_results"]

    # Create socioeconomic ranks (simplified - equal distribution)
    n_obs = len(psa_results)
    ses_ranks = np.linspace(0.01, 0.99, n_obs)  # 0 = poorest, 1 = richest

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

    # Concentration curve for costs
    sorted_indices = np.argsort(ses_ranks)
    sorted_costs = psa_results["dCost"].values[sorted_indices]
    cumulative_costs = np.cumsum(sorted_costs) / np.sum(sorted_costs)
    cumulative_population = np.linspace(0, 1, n_obs)

    ax1.plot(
        cumulative_population,
        cumulative_costs,
        "b-",
        linewidth=2,
        label="Concentration Curve",
    )
    ax1.plot([0, 1], [0, 1], "r--", linewidth=1, label="Line of Equality")
    ax1.set_title("Concentration Curve - Incremental Costs")
    ax1.set_xlabel("Cumulative Population (ranked by SES)")
    ax1.set_ylabel("Cumulative Costs")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Concentration curve for QALYs
    sorted_qalys = psa_results["dQALY"].values[sorted_indices]
    cumulative_qalys = np.cumsum(sorted_qalys) / np.sum(sorted_qalys)

    ax2.plot(
        cumulative_population,
        cumulative_qalys,
        "g-",
        linewidth=2,
        label="Concentration Curve",
    )
    ax2.plot([0, 1], [0, 1], "r--", linewidth=1, label="Line of Equality")
    ax2.set_title("Concentration Curve - Incremental QALYs")
    ax2.set_xlabel("Cumulative Population (ranked by SES)")
    ax2.set_ylabel("Cumulative QALYs")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Lorenz curve for net benefits (£30k WTP)
    net_benefits = psa_results["dQALY"] * 30000 - psa_results["dCost"]
    sorted_net_benefits = net_benefits.values[sorted_indices]
    cumulative_net_benefits = np.cumsum(sorted_net_benefits) / np.sum(
        sorted_net_benefits
    )

    ax3.plot(
        cumulative_population,
        cumulative_net_benefits,
        "purple",
        linewidth=2,
        label="Lorenz Curve",
    )
    ax3.plot([0, 1], [0, 1], "r--", linewidth=1, label="Line of Equality")
    ax3.set_title("Lorenz Curve - Net Benefits (£30k/QALY)")
    ax3.set_xlabel("Cumulative Population (ranked by SES)")
    ax3.set_ylabel("Cumulative Net Benefits")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Atkinson indices comparison
    atkinson_data = distributional_results["atkinson_indices"]
    epsilon_values = [float(k.split("_")[1]) for k in atkinson_data]
    cost_inequality = [v["cost_inequality"] for v in atkinson_data.values()]
    qaly_inequality = [v["qaly_inequality"] for v in atkinson_data.values()]

    ax4.plot(
        epsilon_values, cost_inequality, "b-o", linewidth=2, label="Cost Inequality"
    )
    ax4.plot(
        epsilon_values, qaly_inequality, "g-s", linewidth=2, label="QALY Inequality"
    )
    ax4.set_title("Atkinson Inequality Indices")
    ax4.set_xlabel("Inequality Aversion (ε)")
    ax4.set_ylabel("Inequality Index")
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    _apply_tight_layout()
    _save_current_figure("results/distributional_concentration_curves.png")
    # plt.show()


def plot_equity_efficiency_tradeoffs(distributional_results):
    """
    Plot equity-efficiency trade-offs from distributional analysis.

    Parameters:
    -----------
    distributional_results : dict
        Results from distributional impacts analysis
    """
    equity_efficiency = distributional_results["equity_efficiency"]

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

    # Efficiency vs Equity comparison
    efficiency_icers = [equity_efficiency["efficiency_metrics"]["mean_ic_er"]]
    equity_icers = [equity_efficiency["equity_metrics"]["weighted_mean_icer"]]

    bars1 = ax1.bar(
        ["Efficiency Focus", "Equity Focus"],
        [efficiency_icers[0], equity_icers[0]],
        color=["lightblue", "lightgreen"],
        alpha=0.7,
    )
    ax1.set_title("ICER Comparison: Efficiency vs Equity")
    ax1.set_ylabel("ICER (£/QALY)")
    ax1.grid(True, alpha=0.3, axis="y")

    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 500,
            f"£{height:,.0f}",
            ha="center",
            va="bottom",
        )

    # Probability cost-effective comparison
    efficiency_prob = equity_efficiency["efficiency_metrics"]["prob_cost_effective"]
    equity_prob = equity_efficiency["equity_metrics"]["weighted_prob_cost_effective"]

    bars2 = ax2.bar(
        ["Efficiency Focus", "Equity Focus"],
        [efficiency_prob, equity_prob],
        color=["lightblue", "lightgreen"],
        alpha=0.7,
    )
    ax2.set_title("Probability Cost-Effective (≤£30k/QALY)")
    ax2.set_ylabel("Probability")
    ax2.grid(True, alpha=0.3, axis="y")

    # Add value labels on bars
    for bar in bars2:
        height = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.01,
            f"{height:.3f}",
            ha="center",
            va="bottom",
        )

    # Trade-off analysis
    tradeoff_metrics = list(equity_efficiency["tradeoff_analysis"].keys())
    tradeoff_values = list(equity_efficiency["tradeoff_analysis"].values())

    ax3.bar(tradeoff_metrics, tradeoff_values, color=["coral", "orange"], alpha=0.7)
    ax3.set_title("Equity-Efficiency Trade-offs")
    ax3.set_ylabel("Ratio/Index")
    ax3.tick_params(axis="x", rotation=45)
    ax3.grid(True, alpha=0.3, axis="y")

    # Distributional statistics summary
    distributional_stats = distributional_results["distributional_stats"]
    wtp_levels = []
    mean_net_benefits = []

    for key, stats in distributional_stats.items():
        if key.startswith("wtp_"):
            wtp_levels.append(int(key.split("_")[1]))
            mean_net_benefits.append(stats["mean_net_benefit"])

    ax4.plot(wtp_levels, mean_net_benefits, "bo-", linewidth=2, markersize=8)
    ax4.axhline(
        y=0, color="r", linestyle="--", alpha=0.7, label="Cost-Effectiveness Threshold"
    )
    ax4.set_title("Mean Net Benefits by WTP Threshold")
    ax4.set_xlabel("Willingness-to-Pay (£/QALY)")
    ax4.set_ylabel("Mean Net Benefit (£)")
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    _apply_tight_layout()
    _save_current_figure("results/distributional_equity_efficiency.png")
    # plt.show()


def plot_distributional_uncertainty(distributional_results):
    """
    Plot distributional uncertainty analysis.

    Parameters:
    -----------
    distributional_results : dict
        Results from distributional impacts analysis
    """
    psa_results = distributional_results["psa_results"]

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

    # ICER distribution
    icers = psa_results["dCost"] / psa_results["dQALY"]
    valid_icers = icers[np.isfinite(icers) & (icers > 0)]

    ax1.hist(valid_icers, bins=30, alpha=0.7, color="skyblue", edgecolor="black")
    ax1.axvline(
        np.mean(valid_icers),
        color="red",
        linestyle="--",
        linewidth=2,
        label=f"Mean: £{np.mean(valid_icers):,.0f}",
    )
    ax1.axvline(
        np.median(valid_icers),
        color="green",
        linestyle="--",
        linewidth=2,
        label=f"Median: £{np.median(valid_icers):,.0f}",
    )
    ax1.set_title("ICER Distribution")
    ax1.set_xlabel("ICER (£/QALY)")
    ax1.set_ylabel("Frequency")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Cost-QALY scatter plot with uncertainty
    ax2.scatter(
        psa_results["dQALY"], psa_results["dCost"], alpha=0.6, color="purple", s=30
    )
    ax2.set_title("Cost-QALY Distribution")
    ax2.set_xlabel("Incremental QALYs")
    ax2.set_ylabel("Incremental Cost (£)")
    ax2.grid(True, alpha=0.3)

    # Add CE plane reference lines
    x_range = np.linspace(0, np.max(psa_results["dQALY"]), 100)
    ax2.plot(x_range, x_range * 20000, "r--", alpha=0.7, label="£20k/QALY")
    ax2.plot(x_range, x_range * 30000, "g--", alpha=0.7, label="£30k/QALY")
    ax2.plot(x_range, x_range * 50000, "b--", alpha=0.7, label="£50k/QALY")
    ax2.legend()

    # Net benefit distributions at different WTP
    wtp_values = [20000, 30000, 50000]
    colors = ["red", "green", "blue"]

    for wtp, color in zip(wtp_values, colors, strict=False):
        net_benefits = psa_results["dQALY"] * wtp - psa_results["dCost"]
        ax3.hist(
            net_benefits,
            bins=30,
            alpha=0.5,
            color=color,
            label=f"£{wtp // 1000}k/QALY",
            edgecolor="black",
        )

    ax3.axvline(x=0, color="black", linestyle="-", linewidth=1, label="Break-even")
    ax3.set_title("Net Benefit Distributions")
    ax3.set_xlabel("Net Benefit (£)")
    ax3.set_ylabel("Frequency")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Joint distribution analysis
    # Create 2D histogram
    hist, xedges, yedges = np.histogram2d(
        psa_results["dCost"],
        psa_results["dQALY"],
        bins=20,
        range=[
            [np.min(psa_results["dCost"]), np.max(psa_results["dCost"])],
            [np.min(psa_results["dQALY"]), np.max(psa_results["dQALY"])],
        ],
    )

    # Plot heatmap
    im = ax4.imshow(
        hist.T,
        origin="lower",
        aspect="auto",
        extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]],
        cmap="viridis",
    )
    ax4.set_title("Joint Distribution: Cost vs QALY")
    ax4.set_xlabel("Incremental Cost (£)")
    ax4.set_ylabel("Incremental QALYs")

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax4)
    cbar.set_label("Frequency")

    _apply_tight_layout()
    _save_current_figure("results/distributional_uncertainty.png")
    # plt.show()
