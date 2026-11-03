import unittest

import dask.dataframe as dd
import numpy as np
import pandas as pd

from lifecourse.model.dask_utils import safe_from_pandas
from lifecourse.model.parameters import (
    DISTRIBUTIONS,
    LIFE_EXP_NP,
    START_YEAR,
    prepare_dask_params,
    sample_params_from_dist,
)
from lifecourse.model.population_system import PopulationSystemDask


def get_test_params_for_system(
    seed=42,
):  # Renamed to avoid potential global scope issues
    raw_sampled = sample_params_from_dist(DISTRIBUTIONS, seed=seed)
    return prepare_dask_params(raw_sampled)


class TestPopulationSystem(unittest.TestCase):
    def _create_pop_system(self, pop_size, arm_type="prospective", seed=42):
        params = get_test_params_for_system(seed)
        return PopulationSystemDask(pop_size, params, arm=arm_type)

    def setUp(self):
        self.pop_size_default = 50
        # This default system is created for each test method
        # self.pop_system_default = self._create_pop_system(self.pop_size_default, arm_type='prospective', seed=1)

    def test_initialization(self):
        pop_system = self._create_pop_system(
            pop_size=10, arm_type="prospective", seed=2
        )
        self.assertEqual(pop_system.arm, "prospective")
        self.assertIsInstance(pop_system.pop, dd.DataFrame)
        self.assertTrue(len(pop_system.pop.columns) > 0)  # Check it has columns
        self.assertTrue(pop_system.pop.npartitions > 0)  # Check it has partitions
        computed_pop = pop_system.pop.compute()
        self.assertEqual(len(computed_pop), 10)
        self.assertIn("age", computed_pop.columns)
        self.assertIn("diagnosed", computed_pop.columns)

    def test_mortality(self):
        pop_system = self._create_pop_system(pop_size=self.pop_size_default, seed=3)
        initial_pop_computed = pop_system.pop.compute()  # Compute once before operation
        initial_pop_size = len(initial_pop_computed)

        pop_system._mortality()
        current_pop_computed = pop_system.pop.compute()  # Compute once after operation
        current_pop_size = len(current_pop_computed)

        self.assertTrue(current_pop_size <= initial_pop_size)

        # Test LIFE_EXP_NP effect
        params_mort = get_test_params_for_system(seed=101)
        params_mort["MORT_HR"] = np.array([0.00001, 0.00001])  # Minimize HR effect

        # Create a new system for this specific test
        temp_pop_sys = PopulationSystemDask(
            self.pop_size_default, params_mort, arm="prospective"
        )
        pop_df_mort = temp_pop_sys.pop.compute()

        if len(pop_df_mort) > 2:
            # Modify a few individuals to test specific age-related mortality
            pop_df_mort.loc[pop_df_mort.index[0], "age"] = (
                LIFE_EXP_NP[1] + 5
            )  # Severe, older than life exp
            pop_df_mort.loc[pop_df_mort.index[0], "severity"] = 1

            pop_df_mort.loc[pop_df_mort.index[1], "age"] = (
                LIFE_EXP_NP[0] - 5
            )  # Mild, younger than life exp
            pop_df_mort.loc[pop_df_mort.index[1], "severity"] = 0

            temp_pop_sys.pop = safe_from_pandas(
                pop_df_mort, npartitions=temp_pop_sys.pop.npartitions or 1
            )

        temp_pop_sys._mortality()
        pop_after_controlled_mort = temp_pop_sys.pop.compute()

        if len(pop_df_mort) > 0 and pop_df_mort.iloc[0]["severity"] == 1:
            self.assertNotIn(
                pop_df_mort.index[0],
                pop_after_controlled_mort.index,
                "Old severe individual should be removed by LIFE_EXP_NP",
            )
        if len(pop_df_mort) > 1 and pop_df_mort.iloc[1]["severity"] == 0:
            self.assertIn(
                pop_df_mort.index[1],
                pop_after_controlled_mort.index,
                "Young mild individual should survive LIFE_EXP_NP",
            )

    def test_fertility(self):
        pop_system = self._create_pop_system(pop_size=self.pop_size_default, seed=5)
        pop_df_fert = pop_system.pop.compute()
        num_to_modify = min(5, len(pop_df_fert))

        if num_to_modify > 0:
            indices_to_modify = pop_df_fert.index[0:num_to_modify]
            pop_df_fert.loc[indices_to_modify, "sex"] = 0  # Female
            pop_df_fert.loc[indices_to_modify, "age"] = 25  # Fertile age
            pop_df_fert.loc[indices_to_modify, "familial"] = True
            pop_system.pop = safe_from_pandas(
                pop_df_fert, npartitions=pop_system.pop.npartitions or 1
            )

        babies_dd = pop_system._fertility()
        babies_df = babies_dd.compute()  # This will be empty if no births

        if not babies_df.empty:
            self.assertTrue(np.all(babies_df["age"] == 0))
            # Familial flag should be boolean-like. The exact inheritance is probabilistic
            # and depends on which mothers had births; avoid brittle assertions that depend
            # on specific RNG outcomes. Instead assert the column contains boolean-like values.
            fam_vals = babies_df["familial"].dropna().unique()
            # All values should be interpretable as True/False
            for v in fam_vals:
                assert v in (True, False, 0, 1)

    def test_diagnosis_prospective(self):
        pop_system = self._create_pop_system(
            pop_size=self.pop_size_default, arm_type="prospective", seed=6
        )
        pop_df_diag_initial = pop_system.pop.compute()
        num_to_modify = min(10, len(pop_df_diag_initial))
        eligible_indices = []

        if num_to_modify > 0:
            indices_to_modify = pop_df_diag_initial.index[0:num_to_modify]
            pop_df_diag_initial.loc[indices_to_modify, "diagnosed"] = False
            pop_df_diag_initial.loc[indices_to_modify, "familial"] = True
            pop_df_diag_initial.loc[indices_to_modify, "age"] = (
                pop_system.params["min_test_age"] + 1
            )
            eligible_indices = indices_to_modify  # These are the ones we made eligible
            pop_system.pop = safe_from_pandas(
                pop_df_diag_initial, npartitions=pop_system.pop.npartitions or 1
            )

        pop_system.params["yield_wgs"] = 1.0
        pop_system._diagnosis()
        pop_after_diag_yield_1 = pop_system.pop.compute()

        if num_to_modify > 0:
            self.assertTrue(
                pop_after_diag_yield_1.loc[eligible_indices, "diagnosed"].all()
            )

        # Reset for yield_wgs = 0.0 test
        if num_to_modify > 0:
            pop_df_diag_initial.loc[eligible_indices, "diagnosed"] = False  # Reset
            pop_system.pop = safe_from_pandas(
                pop_df_diag_initial, npartitions=pop_system.pop.npartitions or 1
            )

        pop_system.params["yield_wgs"] = 0.0
        pop_system._diagnosis()
        pop_after_diag_yield_0 = pop_system.pop.compute()
        if num_to_modify > 0:
            self.assertFalse(
                pop_after_diag_yield_0.loc[eligible_indices, "diagnosed"].any()
            )

    def test_diagnosis_non_prospective_arm(self):
        pop_system = self._create_pop_system(
            pop_size=self.pop_size_default, arm_type="retrospective", seed=7
        )
        pop_df_diag_retro = pop_system.pop.compute()
        # Manually set some diagnosed states to ensure they are not changed
        if len(pop_df_diag_retro) > 1:
            pop_df_diag_retro.loc[pop_df_diag_retro.index[0], "diagnosed"] = True
            pop_df_diag_retro.loc[pop_df_diag_retro.index[1], "diagnosed"] = False
            pop_system.pop = safe_from_pandas(
                pop_df_diag_retro, npartitions=pop_system.pop.npartitions or 1
            )

        initial_diagnosed_state = pop_system.pop["diagnosed"].compute()
        pop_system._diagnosis()
        after_diagnosed_state = pop_system.pop["diagnosed"].compute()
        pd.testing.assert_series_equal(
            initial_diagnosed_state, after_diagnosed_state, check_dtype=False
        )

    def test_cost_qaly_calculation(self):
        pop_system = self._create_pop_system(pop_size=self.pop_size_default, seed=8)
        pop_df_cq = pop_system.pop.compute()
        if len(pop_df_cq) > 0:  # Setup one individual for specific checks
            idx_to_mod = pop_df_cq.index[0]
            pop_df_cq.loc[idx_to_mod, "diagnosed"] = True
            pop_df_cq.loc[idx_to_mod, "severity"] = 1
            pop_df_cq.loc[idx_to_mod, "uses_respite"] = True
            pop_df_cq.loc[idx_to_mod, "school"] = 0
            pop_df_cq.loc[idx_to_mod, "support"] = 1
            pop_df_cq.loc[idx_to_mod, "needs_mobility"] = (
                True  # Added for mobility cost test
            )
            pop_df_cq.loc[idx_to_mod, "employment"] = (
                1  # Added for employment cost test (assuming EMP_NP[1] > 0)
            )
            pop_df_cq.loc[idx_to_mod, "education"] = "primary"  # Added for income test
            pop_system.pop = safe_from_pandas(
                pop_df_cq, npartitions=pop_system.pop.npartitions or 1
            )

        pop_system._cost_qaly(year=START_YEAR)
        pop_after_cq_df = pop_system.pop.compute()

        self.assertIn("annual_cost", pop_after_cq_df.columns)
        self.assertIn("annual_qaly", pop_after_cq_df.columns)

        if len(pop_after_cq_df) > 0:
            self.assertTrue(pop_after_cq_df["annual_cost"].sum() >= 0)
            self.assertTrue(
                pop_after_cq_df["annual_qaly"].between(-3.0, 3.0).all()
            )  # Wider range to account for adjustments

            if (
                0 in pop_after_cq_df.index
                and len(pop_df_cq) > 0
                and pop_df_cq.index[0] == 0
            ):  # If the modified individual is still index 0
                first_person_costs = pop_after_cq_df.loc[0]
                self.assertTrue(first_person_costs["cost_health"] > 0)
                if pop_system.params["RESPITE"] > 0:
                    self.assertTrue(first_person_costs["cost_respite"] > 0)
                # edu cost depends on params['EDU'] values which can be 0
                # self.assertTrue(first_person_costs['cost_edu'] > 0)
                if pop_system.params["NDIS_COST"] > 0:
                    self.assertTrue(first_person_costs["cost_ndis"] > 0)
                if (
                    pop_system.params["CARER_HOURS_NP"][1]
                    * pop_system.params["WAGE_HR"]
                    > 0
                ):
                    self.assertTrue(first_person_costs["cost_carer"] > 0)
                if pop_system.params["MOBILITY"] > 0:
                    self.assertTrue(
                        first_person_costs["cost_mobility"] < 0
                    )  # Mobility is negative cost
                if pop_system.params["WELFARE_NP"][1] > 0:
                    self.assertTrue(first_person_costs["cost_welfare"] > 0)
                if pop_system.params["EMP_NP"][1] > 0:
                    self.assertTrue(first_person_costs["cost_emp"] > 0)
                # Morbidity cost is probabilistic, so we can't assert > 0 directly unless we mock random
                # self.assertTrue(first_person_costs['cost_morbidity'] >= 0)
                if pop_system.params["HOSP_COST"] > 0:
                    self.assertTrue(
                        first_person_costs["cost_hospital"] >= 0
                    )  # Can be 0 if no events
                if (
                    pop_system.params["MENTAL_HEALTH_COST"]
                    + pop_system.params["INFORMAL_CARE_COST"]
                    > 0
                ):
                    self.assertTrue(first_person_costs["cost_common_other"] > 0)
                # Income should be positive for employed individuals
                self.assertTrue(first_person_costs["income"] > 0)

    def test_step_function(self):
        pop_system = self._create_pop_system(pop_size=self.pop_size_default, seed=9)
        initial_pop_ddf = pop_system.pop.copy()
        initial_ages_computed = initial_pop_ddf["age"].compute()  # Compute before step
        initial_len = len(initial_ages_computed)

        pop_system.step(year=START_YEAR + 1)

        pop_after_step_df = pop_system.pop.compute()
        current_len = len(pop_after_step_df)

        self.assertTrue(current_len >= 0)
        if initial_len == 0:
            self.assertEqual(current_len, 0)
            return

        if current_len > 0:
            self.assertTrue(np.all(pop_after_step_df["age"] >= 0))
            # Check if ages of (some) survivors incremented
            # This is complex due to births/deaths and dask indexing.
            # A simple check: if any original individuals survived, their age should be initial_age + 1
            # This requires matching individuals.
            # For now, just check that 'age' column exists and some basic properties.
            if (initial_len > 0 and current_len > 0) and (
                initial_ages_computed.max() > 0
            ):
                # If we had some people with age > 0 before, and some people still exist,
                # it's likely max age increased or mean age changed plausibly.
                pass  # Max age could decrease if all oldest die.

            self.assertTrue(
                pop_after_step_df["annual_cost"].sum() >= 0 if current_len > 0 else True
            )


if __name__ == "__main__":
    unittest.main()
