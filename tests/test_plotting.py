import unittest
from unittest.mock import patch
import pandas as pd
import numpy as np

from src.analysis.plotting import (
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


class TestPlotting(unittest.TestCase):
    @patch("matplotlib.pyplot.savefig")
    def test_plot_deterministic_icers(self, mock_savefig):
        """Test that the deterministic ICER plot function runs without error."""
        data = {"scenario": ["A", "B"], "ICER": [10000, 20000]}
        df = pd.DataFrame(data)
        plot_deterministic_icers(df)
        mock_savefig.assert_called_once_with("results/deterministic_icers.png")

    @patch("matplotlib.pyplot.savefig")
    def test_plot_ce_plane(self, mock_savefig):
        """Test the CE plane plot function."""
        dcost = np.random.rand(100) * 10000
        dqaly = np.random.rand(100) * 1
        wtp = np.linspace(0, 150000, 40)
        plot_ce_plane(dcost, dqaly, wtp)
        mock_savefig.assert_called_once_with("results/ce_plane.png")

    @patch("matplotlib.pyplot.savefig")
    def test_plot_ceac(self, mock_savefig):
        """Test the CEAC plot function."""
        wtp = np.linspace(0, 150000, 40)
        nb = np.random.rand(100, 40)
        plot_ceac(wtp, nb)
        mock_savefig.assert_called_once_with("results/ceac.png")

    @patch("matplotlib.pyplot.savefig")
    def test_plot_evpi(self, mock_savefig):
        """Test the EVPI plot function."""
        wtp = np.linspace(0, 150000, 40)
        nb = np.random.rand(100, 40)
        plot_evpi(wtp, nb)
        mock_savefig.assert_called_once_with("results/evpi.png")

    @patch("matplotlib.pyplot.savefig")
    def test_plot_enmb(self, mock_savefig):
        """Test the ENMB plot function."""
        wtp = np.linspace(0, 150000, 40)
        nb = np.random.rand(100, 40)
        plot_enmb(wtp, nb)
        mock_savefig.assert_called_once_with("results/enmb.png")

    @patch("matplotlib.pyplot.savefig")
    def test_plot_tornado(self, mock_savefig):
        """Test the Tornado plot function."""
        data = {
            "param": ["A", "A", "B", "B"],
            "change_type": ["Low", "High", "Low", "High"],
            "ICER_diff": [-1000, 1200, -500, 600],
        }
        df = pd.DataFrame(data)
        plot_tornado(df)
        mock_savefig.assert_called_once_with("results/tornado_sensitivity.png")

    @patch("matplotlib.pyplot.savefig")
    def test_plot_subgroup_analysis(self, mock_savefig):
        """Test the subgroup analysis plot function."""
        data = {"group": ["G1", "G2"], "ICER": [15000, 25000]}
        df = pd.DataFrame(data)
        plot_subgroup_analysis(df, 20000)
        mock_savefig.assert_called_once_with("results/subgroup_analysis.png")

    @patch("matplotlib.pyplot.savefig")
    def test_plot_cost_mix_stacked_area(self, mock_savefig):
        """Test the cost-mix stacked area plot function."""
        data = {
            "arm": ["prospective"] * 10,
            "year": range(2024, 2034),
            "cost_health": np.random.rand(10) * 100,
            "cost_edu": np.random.rand(10) * 100,
            "cost_respite": np.random.rand(10) * 100,
            "cost_mobility": np.random.rand(10) * 100,
            "cost_welfare": np.random.rand(10) * 100,
            "cost_emp": np.random.rand(10) * 100,
            "cost_morbidity": np.random.rand(10) * 100,
        }
        df = pd.DataFrame(data)
        plot_cost_mix_stacked_area(df, "prospective", "Test Title", "test.png")
        mock_savefig.assert_called_once_with("test.png")

    @patch("matplotlib.pyplot.savefig")
    def test_plot_budget_impact(self, mock_savefig):
        """Test the budget impact plot function."""
        data = {
            "uptake": [0.2, 0.2, 0.5, 0.5],
            "year": [2024, 2025, 2024, 2025],
            "budget_impact": [100, 120, 250, 300],
        }
        df = pd.DataFrame(data)
        plot_budget_impact(df)
        mock_savefig.assert_called_once_with("results/budget_impact.png")

    @patch("matplotlib.pyplot.savefig")
    def test_plot_ses_equity(self, mock_savefig):
        """Test the SES equity plot function."""
        ses_vals = [10, 20, 30, 25, 15]
        labels = [f"Q{i+1}" for i in range(5)]
        plot_ses_equity(ses_vals, labels, 2044)
        mock_savefig.assert_called_once_with("results/ses_equity.png")

    @patch("matplotlib.pyplot.savefig")
    def test_plot_psa_histograms(self, mock_savefig):
        """Test the PSA histograms plot function."""
        costs = np.random.rand(100) * 10000
        qalys = np.random.rand(100) * 1
        plot_psa_histograms(costs, qalys)
        mock_savefig.assert_called_once_with("results/psa_histograms.png")

    @patch("matplotlib.pyplot.savefig")
    def test_plot_ceaf(self, mock_savefig):
        """Test the CEAF plot function."""
        wtp = np.linspace(0, 150000, 40)
        prob = np.random.rand(40)
        plot_ceaf(wtp, prob)
        mock_savefig.assert_called_once_with("results/ceaf.png")

    @patch("matplotlib.pyplot.savefig")
    def test_plot_familial_prevalence_sensitivity(self, mock_savefig):
        """Test the familial prevalence sensitivity plot function."""
        data = {
            "familial_prop": np.linspace(0.1, 0.2, 10),
            "ICER": np.random.rand(10) * 30000,
        }
        df = pd.DataFrame(data)
        plot_familial_prevalence_sensitivity(df)
        mock_savefig.assert_called_once_with(
            "results/familial_prevalence_sensitivity.png"
        )

    @patch("matplotlib.pyplot.savefig")
    def test_plot_evppi_curves(self, mock_savefig):
        """Test the EVPPI curves plot function."""
        wtp = np.linspace(0, 150000, 40)
        results = {"param1": np.random.rand(40), "param2": np.random.rand(40)}
        plot_evppi_curves(results, wtp)
        mock_savefig.assert_called_once_with("results/evppi_curves.png")

    @patch("matplotlib.pyplot.savefig")
    def test_plot_psa_icer_distribution(self, mock_savefig):
        """Test the PSA ICER distribution plot function."""
        icers = np.random.rand(100) * 50000
        plot_psa_icer_distribution(icers)
        mock_savefig.assert_called_once_with("results/psa_icer_distribution.png")


if __name__ == "__main__":
    unittest.main()
