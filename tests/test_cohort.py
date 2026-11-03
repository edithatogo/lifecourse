import unittest

import dask.dataframe as dd
import numpy as np
import pandas as pd

from lifecourse.model.cohort import FERT_RATES_DF, gen_population_dask, sample_ages
from lifecourse.model.parameters import (
    AGE_BREAKS,
    AGE_DIST,
    DISTRIBUTIONS,
    prepare_dask_params,
    sample_params_from_dist,
)


class TestCohort(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw_sampled = sample_params_from_dist(DISTRIBUTIONS, seed=42)
        cls.current_params = prepare_dask_params(raw_sampled)
        cls.N_POP = 100
        cls.N_SAMPLES_AGE_TEST = 2000

    def test_sample_ages(self):
        ages = sample_ages(self.N_SAMPLES_AGE_TEST, AGE_DIST)
        self.assertIsInstance(ages, np.ndarray)
        self.assertEqual(len(ages), self.N_SAMPLES_AGE_TEST)
        self.assertTrue(np.all(ages >= 0))
        self.assertTrue(np.all(ages <= AGE_BREAKS[-1] + 4))

        counts, _ = np.histogram(ages, bins=np.append(AGE_BREAKS, AGE_BREAKS[-1] + 5))
        self.assertTrue(counts[0] > 0, "First age bin should have samples")
        self.assertTrue(counts[-1] > 0, "Last age bin should have samples")

    def test_gen_population_dask_structure_and_types(self):
        pop_ddf = gen_population_dask(
            self.N_POP, self.current_params, arm="prospective"
        )
        self.assertIsInstance(pop_ddf, dd.DataFrame)

        expected_columns = [
            "age",
            "sex",
            "severity",
            "familial",
            "diagnosed",
            "living",
            "employment",
            "uses_respite",
            "needs_mobility",
            "support",
            "ses",
            "education",
            "age_band",
            "income",
            "school",
            "annual_cost",
            "annual_qaly",
            "cost_health",
            "cost_edu",
            "cost_respite",
            "cost_mobility",
            "cost_welfare",
            "cost_emp",
            "cost_morbidity",
            "cost_ndis",
            "cost_carer",
            "cost_hospital",
            "cost_common_other",  # Added new cost columns
        ]
        self.assertListEqual(list(pop_ddf.columns), expected_columns)

        pop_df = pop_ddf.compute()
        self.assertEqual(len(pop_df), self.N_POP)

        self.assertTrue(pd.api.types.is_integer_dtype(pop_df["age"]))
        self.assertTrue(pd.api.types.is_bool_dtype(pop_df["diagnosed"]))
        self.assertTrue(pd.api.types.is_float_dtype(pop_df["income"]))
        self.assertTrue(pd.api.types.is_float_dtype(pop_df["annual_cost"]))
        # Check new cost columns dtypes
        for new_cost_col in [
            "cost_ndis",
            "cost_carer",
            "cost_hospital",
            "cost_common_other",
        ]:
            self.assertTrue(
                pd.api.types.is_float_dtype(pop_df[new_cost_col]),
                f"Column {new_cost_col} should be float",
            )
            self.assertTrue(
                (pop_df[new_cost_col] == 0.0).all(),
                f"Column {new_cost_col} should be initialized to 0.0",
            )

    def test_gen_population_dask_values_and_logic(self):
        pop_df = gen_population_dask(
            self.N_POP, self.current_params, arm="prospective"
        ).compute()

        self.assertTrue(pop_df["age"].between(0, AGE_BREAKS[-1] + 4).all())
        self.assertTrue(pop_df["sex"].isin([0, 1]).all())
        self.assertTrue(pop_df["severity"].isin([0, 1]).all())

        self.assertTrue(
            pop_df["education"].isin(self.current_params["EDUCATION_LEVELS"]).all()
        )
        expected_age_bands_set = {
            f"{low}-{high}" for low, high in self.current_params["AGE_BANDS"]
        }
        self.assertTrue(
            set(pop_df["age_band"].unique()).issubset(expected_age_bands_set)
        )

        self.assertTrue(np.all(pop_df["income"] >= 0))
        if self.N_POP > 10:
            self.assertTrue(
                pop_df["income"].sum() > 0, "Sum of income should be positive"
            )

        self.assertTrue(pop_df.loc[pop_df["age"] < 5, "school"].eq(-1).all())
        self.assertTrue(
            pop_df.loc[(pop_df["age"] >= 5) & (pop_df["age"] < 12), "school"]
            .eq(0)
            .all()
        )
        self.assertTrue(pop_df.loc[pop_df["age"] >= 12, "school"].eq(1).all())

        cost_qaly_cols = [
            "annual_cost",
            "annual_qaly",
            "cost_health",
            "cost_edu",
            "cost_respite",
            "cost_mobility",
            "cost_welfare",
            "cost_emp",
            "cost_morbidity",
            "cost_ndis",
            "cost_carer",
            "cost_hospital",
            "cost_common_other",
        ]
        for col in cost_qaly_cols:
            self.assertTrue(
                (pop_df[col] == 0.0).all(), f"Column {col} should be initialized to 0.0"
            )

    def test_gen_population_dask_arm_diagnosis(self):
        pop_prospective_df = gen_population_dask(
            self.N_POP, self.current_params, arm="prospective"
        ).compute()
        self.assertFalse(
            pop_prospective_df["diagnosed"].any(),
            "Diagnosed should be all False for prospective arm",
        )

        test_yield_params = self.current_params.copy()

        test_yield_params["yield_wgs"] = 0.0
        pop_retro_yield_zero_df = gen_population_dask(
            self.N_POP, test_yield_params, arm="retrospective"
        ).compute()
        self.assertFalse(pop_retro_yield_zero_df["diagnosed"].any())

        test_yield_params["yield_wgs"] = 1.0
        pop_retro_yield_one_df = gen_population_dask(
            self.N_POP, test_yield_params, arm="retrospective"
        ).compute()
        if self.N_POP > 0:  # if pop is 0, diagnosed.all() is vacuously true
            # When yield_wgs = 1.0, all familial individuals should be diagnosed
            familial_mask = pop_retro_yield_one_df["familial"]
            if familial_mask.any():
                self.assertTrue(
                    pop_retro_yield_one_df.loc[familial_mask, "diagnosed"].all()
                )

        original_yield = self.current_params["yield_wgs"]
        if 0 < original_yield < 1 and self.N_POP > 50:
            pop_retro_partial_yield_df = gen_population_dask(
                self.N_POP, self.current_params, arm="retrospective"
            ).compute()
            self.assertTrue(pop_retro_partial_yield_df["diagnosed"].any())
            self.assertFalse(pop_retro_partial_yield_df["diagnosed"].all())

    def test_fert_rates_df_creation(
        self,
    ):  # FERT_RATES_DF is module global in cohort.py
        self.assertIsInstance(FERT_RATES_DF, pd.DataFrame)
        self.assertFalse(FERT_RATES_DF.empty)
        self.assertIn("severity", FERT_RATES_DF.columns)
        self.assertIn("age", FERT_RATES_DF.columns)
        self.assertIn("rate", FERT_RATES_DF.columns)
        self.assertTrue(FERT_RATES_DF["rate"].min() >= 0)


if __name__ == "__main__":
    unittest.main()
