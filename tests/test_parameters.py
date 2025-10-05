import unittest
import numpy as np
import pandas as pd
from lifecourse.model.parameters import (
    get_gamma_params,
    get_beta_params,
    sample_params_from_dist,
    prepare_dask_params,
    DISTRIBUTIONS,
    INFLATION_FACTOR,
    DISCOUNT,
    MORB_KEYS,
    EMP_NP,  # Added for checking in prepare_dask_params
    NDIS_COST,
    CARER_HOURS_NP,
    WAGE_HR,
    HOSP_COST,
    HOSP_RATE_NP,  # Added
    MENTAL_HEALTH_COST,
    INFORMAL_CARE_COST,
    INCOME_PARAMS,
    EDUCATION_LEVELS,  # Added
    AGE_BANDS,
    AGE_BAND_P,
    FERT_AGE_SPEC,  # Added
    get_mean_params,
)


class TestParameterFunctions(unittest.TestCase):
    def test_get_gamma_params(self):
        params = get_gamma_params(mean=10, std_dev=2)
        self.assertEqual(params["dist"], "gamma")
        self.assertAlmostEqual(params["shape"], 25)
        self.assertAlmostEqual(params["scale"], 0.4)

        params_zero_std = get_gamma_params(mean=10, std_dev=0)
        self.assertEqual(params_zero_std["dist"], "fixed")
        self.assertEqual(params_zero_std["value"], 10)

        params_zero_mean = get_gamma_params(mean=0, std_dev=2)
        self.assertEqual(params_zero_mean["dist"], "fixed")
        self.assertEqual(params_zero_mean["value"], 0)

    def test_get_beta_params(self):
        params = get_beta_params(mean=0.5, std_dev=0.1)
        self.assertEqual(params["dist"], "beta")
        self.assertAlmostEqual(params["alpha"], 12)
        self.assertAlmostEqual(params["beta"], 12)

        params_zero_std = get_beta_params(mean=0.5, std_dev=0)
        self.assertEqual(params_zero_std["dist"], "fixed")
        self.assertEqual(params_zero_std["value"], 0.5)

        params_high_std = get_beta_params(mean=0.5, std_dev=1)
        # Extremely high variance is clamped so that alpha/beta remain positive
        self.assertEqual(params_high_std["dist"], "beta")
        self.assertGreater(params_high_std["alpha"], 0)
        self.assertGreater(params_high_std["beta"], 0)

        params_edge_mean_low = get_beta_params(mean=0, std_dev=0.1)
        self.assertEqual(params_edge_mean_low["dist"], "fixed")
        self.assertEqual(params_edge_mean_low["value"], 0)

        params_edge_mean_high = get_beta_params(mean=1, std_dev=0.1)
        self.assertEqual(params_edge_mean_high["dist"], "fixed")
        self.assertEqual(params_edge_mean_high["value"], 1)

    def test_sample_params_from_dist(self):
        test_distributions = {
            "param_beta": {"dist": "beta", "alpha": 2, "beta": 5},
            "param_gamma": {"dist": "gamma", "shape": 3, "scale": 2},
            "param_lognormal": {"dist": "lognormal", "s": 0.5, "scale": np.exp(1)},
            "param_normal": {"dist": "normal", "loc": 0, "scale": 1},
            "param_uniform": {"dist": "uniform", "low": 5, "high": 10},
            "param_fixed": {"dist": "fixed", "value": 42},
            "severity_mild_prop": get_beta_params(0.7, 0.03),
        }

        sampled = sample_params_from_dist(test_distributions, seed=123)

        self.assertIn("param_beta", sampled)
        self.assertTrue(0 < sampled["param_beta"] < 1)

        self.assertIn("param_gamma", sampled)
        self.assertTrue(sampled["param_gamma"] > 0)

        self.assertIn("param_lognormal", sampled)
        self.assertTrue(sampled["param_lognormal"] > 0)

        self.assertIn("param_normal", sampled)

        self.assertIn("param_uniform", sampled)
        self.assertTrue(5 <= sampled["param_uniform"] <= 10)

        self.assertIn("param_fixed", sampled)
        self.assertEqual(sampled["param_fixed"], 42)

        self.assertIn("severity_mild_prop", sampled)
        self.assertIn("severity_severe_prop", sampled)
        self.assertAlmostEqual(
            sampled["severity_mild_prop"] + sampled["severity_severe_prop"], 1.0
        )

        with self.assertRaises(ValueError):
            sample_params_from_dist({"bad_param": {"dist": "unknown"}})

    def test_sample_all_distributions(self):
        sampled_params = sample_params_from_dist(DISTRIBUTIONS, seed=42)
        # +1 for severity_severe_prop which is added in sample_params_from_dist
        self.assertEqual(len(sampled_params), len(DISTRIBUTIONS) + 1)

        self.assertTrue(0 < sampled_params["u_base_mild"] < 1)
        self.assertTrue(sampled_params["cost_inp_mild"] > 0)
        self.assertEqual(sampled_params["min_test_age"], 0)
        self.assertAlmostEqual(
            sampled_params["severity_mild_prop"]
            + sampled_params["severity_severe_prop"],
            1.0,
        )

    def test_prepare_dask_params(self):
        raw_sampled_params = sample_params_from_dist(DISTRIBUTIONS, seed=101)
        dask_params = prepare_dask_params(raw_sampled_params)

        self.assertIn("COST_INP_NP", dask_params)
        self.assertEqual(dask_params["COST_INP_NP"].shape, (2,))
        np.testing.assert_array_equal(
            dask_params["COST_INP_NP"],
            np.array(
                [
                    raw_sampled_params["cost_inp_mild"],
                    raw_sampled_params["cost_inp_severe"],
                ]
            ),
        )

        self.assertIn("EDU", dask_params)
        self.assertEqual(dask_params["EDU"].shape, (2, 3))
        np.testing.assert_array_equal(
            dask_params["EDU"][0, 0], raw_sampled_params["edu0_sup0"]
        )

        self.assertIn("MORB_COST_NP", dask_params)
        self.assertEqual(dask_params["MORB_COST_NP"].shape, (len(MORB_KEYS),))
        np.testing.assert_array_equal(
            dask_params["MORB_COST_NP"],
            np.array(
                [
                    raw_sampled_params["morb_cost_epilepsy"],
                    raw_sampled_params["morb_cost_asd"],
                    raw_sampled_params["morb_cost_mental"],
                ]
            ),
        )

        self.assertIn("U_BASE_NP", dask_params)
        np.testing.assert_array_equal(
            dask_params["U_BASE_NP"],
            np.array(
                [raw_sampled_params["u_base_mild"], raw_sampled_params["u_base_severe"]]
            ),
        )

        self.assertIn("MORT_HR", dask_params)
        np.testing.assert_array_equal(
            dask_params["MORT_HR"],
            np.array(
                [
                    raw_sampled_params["mort_hr_mild"],
                    raw_sampled_params["mort_hr_severe"],
                ]
            ),
        )

        self.assertIn("MORB_PROB", dask_params)
        self.assertIsInstance(dask_params["MORB_PROB"], dict)
        self.assertEqual(
            dask_params["MORB_PROB"]["epilepsy"],
            raw_sampled_params["morb_prob_epilepsy"],
        )

        self.assertIn("SEVERITY_DIST", dask_params)
        np.testing.assert_array_almost_equal(
            dask_params["SEVERITY_DIST"],
            np.array(
                [
                    raw_sampled_params["severity_mild_prop"],
                    raw_sampled_params["severity_severe_prop"],
                ]
            ),
        )
        self.assertAlmostEqual(np.sum(dask_params["SEVERITY_DIST"]), 1.0)

        self.assertIn("FERT_RATES_DF", dask_params)
        self.assertIsInstance(dask_params["FERT_RATES_DF"], pd.DataFrame)
        self.assertTrue(len(dask_params["FERT_RATES_DF"]) > 0)

        # Check fertility_multiplier application
        # Rebuild the base FERT_RATES_DF as it's done inside prepare_dask_params
        temp_fert_data = []
        for (s, (lo, hi)), r_val in FERT_AGE_SPEC.items():
            for age_val in range(lo, hi + 1):
                temp_fert_data.append({"severity": s, "age": age_val, "rate": r_val})
        base_fert_rates_df = pd.DataFrame(temp_fert_data)

        expected_df = base_fert_rates_df.copy()
        expected_df["rate"] *= raw_sampled_params["fertility_multiplier"]
        pd.testing.assert_frame_equal(
            dask_params["FERT_RATES_DF"]
            .sort_values(by=["severity", "age"])
            .reset_index(drop=True),
            expected_df.sort_values(by=["severity", "age"]).reset_index(drop=True),
        )

        # Check fixed parameters that are passed directly from globals
        fixed_globals_to_check = {
            "EMP_NP": EMP_NP,
            "NDIS_COST": NDIS_COST,
            "CARER_HOURS_NP": CARER_HOURS_NP,
            "WAGE_HR": WAGE_HR,
            "HOSP_COST": HOSP_COST,
            "HOSP_RATE_NP": HOSP_RATE_NP,
            "MENTAL_HEALTH_COST": MENTAL_HEALTH_COST,
            "INFORMAL_CARE_COST": INFORMAL_CARE_COST,
            "INCOME_PARAMS": INCOME_PARAMS,
            "EDUCATION_LEVELS": EDUCATION_LEVELS,
            "AGE_BANDS": AGE_BANDS,
            "AGE_BAND_P": AGE_BAND_P,
            "DISCOUNT": DISCOUNT,
            "INFLATION_FACTOR": INFLATION_FACTOR,
            "MORB_KEYS": MORB_KEYS,
        }
        for key, expected_value in fixed_globals_to_check.items():
            self.assertIn(key, dask_params)
            if isinstance(expected_value, np.ndarray):
                np.testing.assert_array_equal(
                    dask_params[key], expected_value, f"Mismatch for global param {key}"
                )
            elif isinstance(expected_value, dict) or isinstance(expected_value, list):
                self.assertEqual(
                    dask_params[key], expected_value, f"Mismatch for global param {key}"
                )
            else:  # Floats, ints
                self.assertAlmostEqual(
                    dask_params[key],
                    expected_value,
                    msg=f"Mismatch for global param {key}",
                )

        # Check parameters taken directly from sampled_params
        direct_sampled_keys = [
            "RESPITE",
            "MOBILITY",
            "WGS_DIAG_COST_ADJUSTMENT",
            "U_DECAY",
            "U_DIAG",
            "U_CARER",
            "WGS_DIAG_QALY_ADJUSTMENT",
            "familial_prop",
            "yield_wgs",
            "min_test_age",
        ]
        for key in direct_sampled_keys:
            self.assertIn(key, dask_params)
            # Raw sampled parameters use lowercase keys
            self.assertEqual(
                dask_params[key],
                raw_sampled_params[key.lower()],
                f"Mismatch for sampled param {key}",
            )

    def test_get_mean_params(self):
        means = get_mean_params(DISTRIBUTIONS)
        self.assertIn("cost_inp_mild", means)
        self.assertGreater(means["cost_inp_mild"], 0)
        self.assertAlmostEqual(
            means["severity_mild_prop"] + means["severity_severe_prop"],
            1.0,
        )


if __name__ == "__main__":
    unittest.main()
