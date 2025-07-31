import numpy as np
import pandas as pd
import dask.dataframe as dd
from .cohort import gen_population_dask
from .parameters import START_YEAR, ABS_MORT, LIFE_EXP_NP, EMP_NP


class PopulationSystemDask:
    def __init__(self, pop_size, current_params, arm="prospective"):
        self.arm = arm
        self.params = current_params
        self.pop = gen_population_dask(pop_size, self.params, arm).persist()

    def _mortality(self):
        params = self.params

        def mortality_partition(df):
            if df.empty:
                return df
            ages = df["age"].values
            sev = df["severity"].values
            age_indices = np.clip((ages // 5).astype(int), 0, len(ABS_MORT) - 1)
            surv_prob = ABS_MORT[age_indices] * params["MORT_HR"][sev]
            mask = (np.random.random(len(df)) > surv_prob) & (ages < LIFE_EXP_NP[sev])
            return df[mask]

        self.pop = self.pop.map_partitions(
            mortality_partition, meta=self.pop._meta
        ).persist()

    def _fertility(self):
        moms_dd = self.pop[(self.pop["sex"] == 0) & (self.pop["age"].between(15, 45))]

        if moms_dd.npartitions == 0:
            return dd.from_pandas(pd.DataFrame(columns=self.pop.columns), npartitions=1)

        moms_merged_dd = moms_dd.merge(
            self.params["FERT_RATES_DF"], on=["severity", "age"], how="left"
        )
        moms_merged_dd["rate"] = moms_merged_dd["rate"].fillna(0)

        def determine_births_and_familial_status(df_partition):
            if df_partition.empty:
                return pd.DataFrame(
                    columns=["has_birth", "familial_parent"], dtype=bool, index=[]
                )

            rates = df_partition["rate"].values
            has_birth = np.random.random(len(df_partition)) < rates
            familial_parent = df_partition["familial"].values

            return pd.DataFrame(
                {"has_birth": has_birth, "familial_parent": familial_parent},
                index=df_partition.index,
            )

        birth_info_dd = moms_merged_dd.map_partitions(
            determine_births_and_familial_status,
            meta=pd.DataFrame({"has_birth": bool, "familial_parent": bool}, index=[]),
        )

        actual_births_info_dd = birth_info_dd[birth_info_dd["has_birth"]]

        if actual_births_info_dd.npartitions == 0:
            return dd.from_pandas(pd.DataFrame(columns=self.pop.columns), npartitions=1)

        def generate_babies_for_partition(
            partition_of_birth_info, params, arm, pop_meta
        ):
            n_babies_in_partition = len(partition_of_birth_info)
            if n_babies_in_partition == 0:
                return pop_meta.copy()

            babies_df_part = gen_population_dask(
                n_babies_in_partition, params, arm
            ).compute()

            babies_df_part["age"] = 0
            babies_df_part["familial"] = partition_of_birth_info[
                "familial_parent"
            ].values

            return babies_df_part

        babies_dd = actual_births_info_dd.map_partitions(
            generate_babies_for_partition,
            self.params,
            self.arm,
            self.pop._meta,
            meta=self.pop._meta,
        )
        return babies_dd

    def _diagnosis(self):
        if self.arm != "prospective":
            return

        def diagnosis_partition(df):
            if df.empty:
                return df
            mask = (
                (~df["diagnosed"])
                & df["familial"]
                & (df["age"] >= self.params["min_test_age"])
            )
            cnt = int(mask.sum())
            if cnt > 0:
                diag_outcomes = np.random.random(cnt) < self.params["yield_wgs"]
                df.loc[mask, "diagnosed"] = diag_outcomes
            return df

        self.pop = self.pop.map_partitions(
            diagnosis_partition, meta=self.pop._meta
        ).persist()

    def _cost_qaly(self, year):
        if self.pop.npartitions == 0:
            return

        params = self.params
        disc = 1 / ((1 + params["DISCOUNT"]) ** (year - START_YEAR))

        def cost_qaly_partition(df):
            if df.empty:
                return df.assign(
                    cost_health=0.0,
                    cost_edu=0.0,
                    cost_respite=0.0,
                    cost_mobility=0.0,
                    cost_welfare=0.0,
                    cost_emp=0.0,
                    cost_morbidity=0.0,
                    annual_cost=0.0,
                    annual_qaly=0.0,
                    cost_ndis=0.0,
                    cost_carer=0.0,
                    cost_hospital=0.0,
                    cost_common_other=0.0,
                    income=0.0,
                )

            n = len(df)
            sev = df["severity"].values
            ages = df["age"].values

            # Existing costs
            hc = (
                params["COST_INP_NP"][sev]
                + params["COST_OUTP_NP"][sev]
                + params["COST_PHARM_NP"][sev]
            ) * disc
            rc = df["uses_respite"].values.astype(int) * params["RESPITE"] * disc
            mc = -df["needs_mobility"].values.astype(int) * params["MOBILITY"] * disc
            wc = params["WELFARE_NP"][sev] * disc
            emp = EMP_NP[df["employment"].values] * disc

            # Hospitalization costs (poisson distributed events)
            hosp_events = np.random.poisson(params["HOSP_RATE_NP"][sev], size=n)
            cost_hospital = hosp_events * params["HOSP_COST"] * disc

            # Other common costs
            cost_common_other = (
                params["MENTAL_HEALTH_COST"] + params["INFORMAL_CARE_COST"]
            ) * disc

            ec = np.zeros(n, dtype=np.float64)
            m0 = df["school"] == 0
            m1 = df["school"] == 1
            if m0.any():
                ec[m0] = params["EDU"][0, df.loc[m0, "support"].values] * disc
            if m1.any():
                ec[m1] = params["EDU"][1, df.loc[m1, "support"].values] * disc

            morb_cost = np.zeros(n, dtype=np.float64)
            base_rand = np.random.random(n)
            for i, k in enumerate(params["MORB_KEYS"]):
                m = base_rand < params["MORB_PROB"][k]
                morb_cost += m.astype(np.float64) * params["MORB_COST_NP"][i] * disc

            if self.arm == "prospective":
                m = df["diagnosed"].values
                morb_cost += (
                    m.astype(np.float64) * params["WGS_DIAG_COST_ADJUSTMENT"] * disc
                )

            morb_qaly = np.zeros(n, dtype=np.float64)
            for i, k in enumerate(params["MORB_KEYS"]):
                m = base_rand < params["MORB_PROB"][k]
                morb_qaly += m.astype(np.float64) * params["MORB_QALY_NP"][i] * disc

            uq = params["U_BASE_NP"][sev] * np.exp(
                -params["U_DECAY"] * np.clip(ages - 20, 0, None)
            )
            total_qaly = (
                uq + params["U_CARER"]
            ) * disc - morb_qaly  # U_CARER applied universally

            if self.arm == "prospective":
                m = df["diagnosed"].values
                total_qaly += (
                    m.astype(np.float64)
                    * (params["U_DIAG"] + params["WGS_DIAG_QALY_ADJUSTMENT"])
                    * disc
                )

            df["annual_cost"] = hc + ec + rc + mc + wc + emp + morb_cost
            df["cost_health"] = hc
            df["cost_respite"] = rc
            df["annual_qaly"] = total_qaly
            df["cost_ndis"] = (
                df["diagnosed"].values.astype(int) * params["NDIS_COST"] * disc
            )
            df["cost_carer"] = params["CARER_HOURS_NP"][sev] * params["WAGE_HR"] * disc
            df["cost_mobility"] = mc
            df["cost_welfare"] = wc
            df["cost_emp"] = emp

            # Impute income based on severity and education
            income = np.zeros(n, dtype=np.float64)
            for i, sev_label in enumerate(
                ["mild", "severe"]
            ):  # Assuming 0:mild, 1:severe
                for edu_label in params["EDUCATION_LEVELS"]:
                    mask = (df["severity"] == i) & (df["education"] == edu_label)
                    if mask.any():
                        mu, sigma = params["INCOME_PARAMS"][sev_label][edu_label]
                        income[mask] = np.exp(
                            np.random.normal(mu, sigma, size=mask.sum())
                        )
            df["income"] = income
            df["cost_hospital"] = cost_hospital
            df["cost_common_other"] = cost_common_other
            return df

        self.pop = self.pop.map_partitions(
            cost_qaly_partition, meta=self.pop._meta
        ).persist()

    def step(self, year):
        self._mortality()
        new_babies_dd = self._fertility()
        self._diagnosis()
        self.pop = self.pop.assign(age=self.pop.age + 1)
        if new_babies_dd.npartitions > 0:
            self.pop = dd.concat([self.pop, new_babies_dd], interleave_partitions=True)
        self.pop = self.pop.persist()
        self._cost_qaly(year)
