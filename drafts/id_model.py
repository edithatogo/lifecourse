"""
This file contains the draft of the IDDiseaseModel class.
NOTE: This code is a draft, has not been integrated, and has not been tested.
It is part of a design exercise to refactor the model for multi-cohort support.
"""

import numpy as np
from src.model.parameters import START_YEAR

# This draft assumes it will be used within a new PopulationSystem that handles
# the Dask execution. The logic is transposed from the original PopulationSystemDask.
# It would also need access to global constants like START_YEAR, EMP_NP, etc.
# A full implementation would need to decide how these are passed or imported.
from drafts.disease_model import DiseaseModel
# Assuming draft of disease_model.py is in the same directory for this conceptual exercise.


class IDDiseaseModel(DiseaseModel):
    """
    A concrete implementation of DiseaseModel for the Intellectual Disability cohort.
    This class encapsulates the specific logic for diagnosis and cost/QALY calculations
    for the ID model.
    """

    def run_diagnosis(self, population_df, year: int, sampled_params: dict, arm: str):
        """
        Applies diagnosis logic for the ID cohort. Logic is transposed from the original
        PopulationSystemDask._diagnosis method.
        """
        if arm != "prospective":
            return population_df

        def diagnosis_partition(df):
            if df.empty:
                return df

            # Use .get() for safety in case param is not in this cohort's config
            min_test_age = sampled_params.get("min_test_age", 0)
            yield_wgs = sampled_params.get("yield_wgs", 0)

            mask = (~df["diagnosed"]) & df["familial"] & (df["age"] >= min_test_age)
            cnt = int(mask.sum())
            if cnt > 0:
                diag_outcomes = np.random.random(cnt) < yield_wgs
                df.loc[mask, "diagnosed"] = diag_outcomes
            return df

        # The new PopulationSystem would handle the Dask execution.
        # This function just defines the logic to be applied.
        # For drafting, we assume a mechanism like map_partitions exists.
        # return population_df.map_partitions(diagnosis_partition, meta=population_df._meta)

        # For a pure draft, we just show the logic.
        print("[Draft] Applying ID-specific diagnosis logic.")
        # The actual application (map_partitions) would be handled by the main PopulationSystem engine.
        # This class just provides the function to be mapped.
        return diagnosis_partition  # Returning the function to be mapped

    def run_progression(self, population_df, year: int, sampled_params: dict):
        """
        The current ID model does not have an explicit disease progression step
        (e.g., changes in severity over time). This method is a placeholder.
        """
        print("[Draft] No disease progression logic for ID model.")
        return population_df  # Return the population unchanged

    def calculate_costs_and_qalys(
        self, population_df, year: int, sampled_params: dict, arm: str
    ):
        """
        Calculates and assigns all costs and QALYs for the ID cohort for the given year.
        Logic is transposed from the original PopulationSystemDask._cost_qaly method.
        """

        # These would ideally be passed via sampled_params from the cohort config
        DISCOUNT = sampled_params.get("DISCOUNT", 0.035)
        EMP_NP = sampled_params.get("EMP_NP", np.array([0, 10000, 0]))
        MORB_KEYS = sampled_params.get("MORB_KEYS", ["epilepsy", "asd", "mental"])

        disc = 1 / ((1 + DISCOUNT) ** (year - START_YEAR))

        def cost_qaly_partition(df):
            if df.empty:
                # In a real implementation, this would need to ensure all columns exist
                return df

            n = len(df)
            sev = df["severity"].values
            ages = df["age"].values

            # Costs
            hc = (
                sampled_params["COST_INP_NP"][sev]
                + sampled_params["COST_OUTP_NP"][sev]
                + sampled_params["COST_PHARM_NP"][sev]
            ) * disc
            rc = (
                df["uses_respite"].values.astype(int) * sampled_params["RESPITE"] * disc
            )
            mc = (
                -df["needs_mobility"].values.astype(int)
                * sampled_params["MOBILITY"]
                * disc
            )
            wc = sampled_params["WELFARE_NP"][sev] * disc
            emp = EMP_NP[df["employment"].values] * disc

            ec = np.zeros(n, dtype=np.float64)
            m0 = df["school"] == 0
            m1 = df["school"] == 1
            if m0.any():
                ec[m0] = sampled_params["EDU"][0, df.loc[m0, "support"].values] * disc
            if m1.any():
                ec[m1] = sampled_params["EDU"][1, df.loc[m1, "support"].values] * disc

            cost_ndis = (
                np.where(
                    df["diagnosed"].values & (sev == 1), sampled_params["NDIS_COST"], 0
                )
                * disc
            )
            cost_carer = (
                sampled_params["CARER_HOURS_NP"][sev] * sampled_params["WAGE_HR"] * disc
            )

            hosp_events = np.random.poisson(sampled_params["HOSP_RATE_NP"][sev], size=n)
            cost_hospital = hosp_events * sampled_params["HOSP_COST"] * disc

            cost_common_other = (
                sampled_params["MENTAL_HEALTH_COST"]
                + sampled_params["INFORMAL_CARE_COST"]
            ) * disc

            morb_cost = np.zeros(n, dtype=np.float64)
            base_rand = np.random.random(n)
            for i, k in enumerate(MORB_KEYS):
                m = base_rand < sampled_params["MORB_PROB"][k]
                morb_cost += (
                    m.astype(np.float64) * sampled_params["MORB_COST_NP"][i] * disc
                )

            if arm == "prospective":
                m = df["diagnosed"].values
                morb_cost += (
                    m.astype(np.float64)
                    * sampled_params["WGS_DIAG_COST_ADJUSTMENT"]
                    * disc
                )

            annual_cost = (
                hc
                + ec
                + rc
                + mc
                + wc
                + emp
                + morb_cost
                + cost_ndis
                + cost_carer
                + cost_hospital
                + cost_common_other
            )

            # QALYs
            morb_qaly = np.zeros(n, dtype=np.float64)
            for i, k in enumerate(MORB_KEYS):
                m = base_rand < sampled_params["MORB_PROB"][k]
                morb_qaly += m.astype(np.float64) * sampled_params["MORB_QALY_NP"][i]

            uq = sampled_params["U_BASE_NP"][sev] * np.exp(
                -sampled_params["U_DECAY"] * np.clip(ages - 20, 0, None)
            )
            total_qaly = (
                uq
                + df["diagnosed"].values.astype(int) * sampled_params["U_DIAG"]
                + sampled_params["U_CARER"]
            ) * disc - morb_qaly

            if arm == "prospective":
                m = df["diagnosed"].values
                total_qaly += (
                    m.astype(np.float64)
                    * sampled_params["WGS_DIAG_QALY_ADJUSTMENT"]
                    * disc
                )

            return df.assign(
                cost_health=hc,
                cost_edu=ec,
                cost_respite=rc,
                cost_mobility=mc,
                cost_welfare=wc,
                cost_emp=emp,
                cost_morbidity=morb_cost,
                cost_ndis=cost_ndis,
                cost_carer=cost_carer,
                cost_hospital=cost_hospital,
                cost_common_other=cost_common_other,
                annual_cost=annual_cost,
                annual_qaly=total_qaly,
            )

        print("[Draft] Applying ID-specific cost/QALY logic.")
        # Again, the PopulationSystem engine would handle the map_partitions call.
        # This class just provides the function to be mapped.
        return cost_qaly_partition
