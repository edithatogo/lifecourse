import types
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from lifecourse.analysis.plotting import (
    plot_budget_impact,
    plot_ce_plane,
    plot_ceac,
    plot_ceaf,
    plot_concentration_indices,
    plot_cost_mix_stacked_area,
    plot_deterministic_icers,
    plot_enmb,
    plot_evpi,
    plot_evppi_curves,
    plot_familial_prevalence_sensitivity,
    plot_psa_histograms,
    plot_psa_icer_distribution,
    plot_ses_equity,
    plot_subgroup_analysis,
    plot_tornado,
)
from lifecourse.backend_evaluation import BackendUnavailableError


class TestPlotting(unittest.TestCase):
    @patch("matplotlib.pyplot.savefig")
    def test_plot_deterministic_icers(self, mock_savefig):
        """Test that the deterministic ICER plot function runs without error."""
        data = {"scenario": ["A", "B"], "ICER": [10000, 20000]}
        df = pd.DataFrame(data)
        plot_deterministic_icers(df)
        mock_savefig.assert_called_once_with("results/deterministic_icers.png")

    @patch("lifecourse.analysis.plotting.find_spec")
    def test_plot_deterministic_icers_fails_clearly_without_plotnine(
        self, mock_find_spec
    ):
        """Test optional plotnine backend reports missing dependency clearly."""
        mock_find_spec.return_value = None
        df = pd.DataFrame({"scenario": ["A"], "ICER": [10000]})

        with self.assertRaisesRegex(BackendUnavailableError, "plotnine backend"):
            plot_deterministic_icers(df, backend="plotnine")

    @patch("lifecourse.analysis.plotting.import_module")
    @patch("lifecourse.analysis.plotting.find_spec")
    def test_plot_deterministic_icers_can_dispatch_to_plotnine(
        self, mock_find_spec, mock_import_module
    ):
        """Test selected pilot plot can use a plotnine-like backend."""
        calls = []

        class FakePlot:
            def __add__(self, other):
                calls.append(type(other).__name__)
                return self

            def save(self, filename, verbose=False):
                calls.append(("save", filename, verbose))

        class FakeComponent:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

        fake_plotnine = types.SimpleNamespace(
            aes=FakeComponent,
            element_text=FakeComponent,
            geom_col=FakeComponent,
            ggplot=lambda data, mapping: FakePlot(),
            labs=FakeComponent,
            theme=FakeComponent,
            theme_minimal=FakeComponent,
        )
        mock_find_spec.return_value = object()
        mock_import_module.return_value = fake_plotnine
        df = pd.DataFrame({"scenario": ["A", "B"], "ICER": [10000, 20000]})

        plot_deterministic_icers(df, backend="plotnine")

        self.assertIn(("save", "results/deterministic_icers.png", False), calls)

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
            "curve_type": ["linear", "linear", "exponential", "exponential"],
            "year": [2024, 2025, 2024, 2025],
            "budget_impact": [100, 120, 250, 300],
            "adoption_rate": [0.2, 0.2, 0.5, 0.5],
        }
        df = pd.DataFrame(data)
        plot_budget_impact(df)
        # Function saves two figures
        assert mock_savefig.call_count == 2
        mock_savefig.assert_any_call("results/budget_impact.png")
        mock_savefig.assert_any_call("results/adoption_rates.png")

    @patch("matplotlib.pyplot.savefig")
    def test_plot_ses_equity(self, mock_savefig):
        """Test the SES equity plot function."""
        ses_vals = [10, 20, 30, 25, 15]
        labels = [f"Q{i + 1}" for i in range(5)]
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

    # Enhanced tests with more detailed assertions
    @patch("matplotlib.pyplot.figure")
    @patch("matplotlib.pyplot.bar")
    @patch("matplotlib.pyplot.title")
    @patch("matplotlib.pyplot.ylabel")
    @patch("matplotlib.pyplot.savefig")
    def test_plot_deterministic_icers_detailed(
        self, mock_savefig, mock_ylabel, mock_title, mock_bar, mock_figure
    ):
        """Test the deterministic ICER plot function with detailed assertions."""
        data = {"scenario": ["A", "B"], "ICER": [10000, 20000]}
        df = pd.DataFrame(data)
        plot_deterministic_icers(df)

        # Check that the functions are called
        self.assertGreaterEqual(mock_figure.call_count, 1)
        mock_bar.assert_called_once()
        mock_title.assert_called_once_with("Deterministic ICERs (£/QALY)")
        mock_ylabel.assert_called_once_with("ICER (£/QALY)")
        mock_savefig.assert_called_once_with("results/deterministic_icers.png")

    @patch("matplotlib.pyplot.figure")
    @patch("matplotlib.pyplot.scatter")
    @patch("matplotlib.pyplot.plot")
    @patch("matplotlib.pyplot.xlabel")
    @patch("matplotlib.pyplot.ylabel")
    @patch("matplotlib.pyplot.title")
    @patch("matplotlib.pyplot.legend")
    @patch("matplotlib.pyplot.grid")
    @patch("matplotlib.pyplot.savefig")
    def test_plot_ce_plane_detailed(
        self,
        mock_savefig,
        mock_grid,
        mock_legend,
        mock_title,
        mock_ylabel,
        mock_xlabel,
        mock_plot,
        mock_scatter,
        mock_figure,
    ):
        """Test the CE plane plot function with detailed assertions."""
        dcost = np.array([1000, 2000, 3000])
        dqaly = np.array([1, 2, 3])
        wtp = np.array([20000, 30000])

        plot_ce_plane(dcost, dqaly, wtp)

        # Check that the functions are called
        self.assertGreaterEqual(mock_figure.call_count, 1)
        mock_scatter.assert_called_once()
        mock_plot.assert_called()
        mock_xlabel.assert_called_once_with("Incremental QALYs (Delta QALY)")
        mock_ylabel.assert_called_once_with("Incremental Cost (Delta Cost)")
        mock_title.assert_called_once_with(
            "Cost-Effectiveness Plane with WTP Thresholds"
        )
        mock_legend.assert_called_once()
        mock_grid.assert_called_once()
        mock_savefig.assert_called_once_with("results/ce_plane.png")

    @patch("matplotlib.pyplot.figure")
    @patch("matplotlib.pyplot.plot")
    @patch("matplotlib.pyplot.xlabel")
    @patch("matplotlib.pyplot.ylabel")
    @patch("matplotlib.pyplot.title")
    @patch("matplotlib.pyplot.grid")
    @patch("matplotlib.pyplot.savefig")
    def test_plot_ceac_detailed(
        self,
        mock_savefig,
        mock_grid,
        mock_title,
        mock_ylabel,
        mock_xlabel,
        mock_plot,
        mock_figure,
    ):
        """Test the CEAC plot function with detailed assertions."""
        wtp = np.array([0, 50000, 100000])
        nb = np.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]])  # All positive

        plot_ceac(wtp, nb)

        # Check that the functions are called
        self.assertGreaterEqual(mock_figure.call_count, 1)
        mock_plot.assert_called()
        mock_xlabel.assert_called_once_with("Willingness-to-Pay per QALY")
        mock_ylabel.assert_called_once_with("Probability Cost-Effective")
        mock_title.assert_called_once_with(
            "Cost-Effectiveness Acceptability Curve (CEAC)"
        )
        mock_grid.assert_called_once()
        mock_savefig.assert_called_once_with("results/ceac.png")

    @patch("matplotlib.pyplot.savefig")
    def test_plot_concentration_indices(self, mock_savefig):
        """Test the concentration indices plot function."""
        ci_results = {
            "cost_ci": 0.15,
            "qaly_ci": -0.08,
            "net_benefit_ci": -0.12,
            "interpretation": {
                "cost_ci": "Positive = costs concentrate among rich",
                "qaly_ci": "Negative = QALYs concentrate among poor",
                "net_benefit_ci": "Negative = net benefits concentrate among poor",
            },
        }
        plot_concentration_indices(ci_results)
        mock_savefig.assert_called_once_with("results/concentration_indices.png")


if __name__ == "__main__":
    unittest.main()
