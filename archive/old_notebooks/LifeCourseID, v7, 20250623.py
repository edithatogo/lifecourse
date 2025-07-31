#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# In[12]:


import dask.array as da
import dask.dataframe as dd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import numpy as np
from scipy.stats import beta, gamma, lognorm, norm, uniform
import math
from dask.distributed import LocalCluster, Client, progress

warnings.filterwarnings("ignore")
np.random.seed(42)

# %% [markdown]
## 2. Global Parameters & Dask Constants and Parameter Distributions

START_YEAR, END_YEAR = 2020, 2100
YEARS = list(range(START_YEAR, END_YEAR + 1))
DISCOUNT = 0.035  # Fixed
POP_SIZE = 62000  # Fixed

# Costs are based on 2017 values from the paper, adjust to START_YEAR (2020)
COST_REFERENCE_YEAR = 2017  # Fixed
INFLATION_RATE = 0.03  # Fixed
INFLATION_FACTOR = (1 + INFLATION_RATE) ** (START_YEAR - COST_REFERENCE_YEAR)  # Fixed

# Demographics - mostly fixed or handled by sampling
# SEVERITY_DIST is now defined by a beta distribution for the proportion of mild
AGE_BREAKS = np.arange(0, 95, 5)  # Fixed
AGE_DIST = np.array(
    [  # Fixed demographic distribution
        0.064,
        0.067,
        0.069,
        0.069,
        0.071,
        0.076,
        0.080,
        0.077,
        0.080,
        0.079,
        0.073,
        0.078,
        0.077,
        0.072,
        0.055,
        0.041,
        0.031,
        0.022,
        0.012,
    ]
)
AGE_DIST /= AGE_DIST.sum()

# Mortality
LIFE_EXP_NP = np.array([74, 54])  # Fixed life expectancy for severe/mild
ABS_MORT = np.array(
    [  # Fixed baseline mortality rates
        0.0002,
        0.0001,
        0.0001,
        0.0002,
        0.0003,
        0.0005,
        0.0007,
        0.0011,
        0.0019,
        0.0035,
        0.0055,
        0.0085,
        0.0130,
        0.0200,
        0.0350,
        0.0600,
        0.0950,
        0.1500,
        0.2500,
    ]
)

# Fertility bands - rates will be scaled by a sampled multiplier
FERT_AGE_SPEC = {  # Base fertility rates (fixed means, scaled in PSA)
    (0, (15, 19)): 0.003,
    (0, (20, 24)): 0.008,
    (0, (25, 29)): 0.010,
    (0, (30, 34)): 0.007,
    (0, (35, 45)): 0.002,
    (1, (15, 19)): 0.001,
    (1, (20, 24)): 0.003,
    (1, (25, 29)): 0.004,
    (1, (30, 34)): 0.003,
    (1, (35, 45)): 0.001,
}

# Employment costs (assumed fixed structural values)
EMP_NP = np.array([0, 10000, 0]) * INFLATION_FACTOR

# Morbidity Keys (Globally defined and fixed list of categories)
MORB_KEYS = [
    "epilepsy",
    "asd",
    "mental",
]  # Based on previous code, not the paper's full list of costs


# Helper function to get Gamma parameters from mean and standard deviation
def get_gamma_params(mean, std_dev):
    if mean <= 0 or std_dev <= 0:
        return {"dist": "fixed", "value": mean}  # Handle fixed or zero values
    variance = std_dev**2
    shape = mean**2 / variance
    scale = variance / mean
    return {"dist": "gamma", "shape": shape, "scale": scale}


# Helper function to get Beta parameters from mean and standard deviation
def get_beta_params(mean, std_dev):
    if not (0 <= mean <= 1) or std_dev <= 0:
        return {"dist": "fixed", "value": mean}
    variance = std_dev**2
    if variance >= mean * (1 - mean) and mean > 0 and mean < 1:
        variance = mean * (1 - mean) * 0.99
        std_dev = math.sqrt(variance)

    alpha = mean * (mean * (1 - mean) / variance - 1)
    beta_param = (1 - mean) * (mean * (1 - mean) / variance - 1)

    if alpha <= 0 or beta_param <= 0:
        return {
            "dist": "uniform",
            "low": max(0, mean - 0.01),
            "high": min(1, mean + 0.01),
        }
    return {"dist": "beta", "alpha": alpha, "beta": beta_param}


# Define all uncertain parameters with their distributions
DISTRIBUTIONS = {
    # Costs (Gamma distributions)
    "cost_inp_mild": get_gamma_params(
        5000 * INFLATION_FACTOR, 5000 * INFLATION_FACTOR * 0.20
    ),
    "cost_inp_severe": get_gamma_params(
        15000 * INFLATION_FACTOR, 15000 * INFLATION_FACTOR * 0.20
    ),
    "cost_outp_mild": get_gamma_params(
        1000 * INFLATION_FACTOR, 1000 * INFLATION_FACTOR * 0.20
    ),
    "cost_outp_severe": get_gamma_params(
        3000 * INFLATION_FACTOR, 3000 * INFLATION_FACTOR * 0.20
    ),
    "cost_pharm_mild": get_gamma_params(
        200 * INFLATION_FACTOR, 200 * INFLATION_FACTOR * 0.20
    ),
    "cost_pharm_severe": get_gamma_params(
        500 * INFLATION_FACTOR, 500 * INFLATION_FACTOR * 0.20
    ),
    "edu0_sup0": get_gamma_params(
        16107 * INFLATION_FACTOR, 16107 * INFLATION_FACTOR * 0.15
    ),
    "edu0_sup1": get_gamma_params(
        27903 * INFLATION_FACTOR, 27903 * INFLATION_FACTOR * 0.15
    ),
    "edu0_sup2": get_gamma_params(
        46733 * INFLATION_FACTOR, 46733 * INFLATION_FACTOR * 0.15
    ),
    "edu1_sup0": get_gamma_params(
        18958 * INFLATION_FACTOR, 18958 * INFLATION_FACTOR * 0.15
    ),
    "edu1_sup1": get_gamma_params(
        30789 * INFLATION_FACTOR, 30789 * INFLATION_FACTOR * 0.15
    ),
    "edu1_sup2": get_gamma_params(
        49604 * INFLATION_FACTOR, 49604 * INFLATION_FACTOR * 0.15
    ),
    "respite": get_gamma_params(
        13024 * INFLATION_FACTOR, 13024 * INFLATION_FACTOR * 0.20
    ),
    "mobility": get_gamma_params(
        2493 * INFLATION_FACTOR, 2493 * INFLATION_FACTOR * 0.20
    ),
    "welfare_mild": get_gamma_params(
        3000 * INFLATION_FACTOR, 3000 * INFLATION_FACTOR * 0.20
    ),
    "welfare_severe": get_gamma_params(
        8000 * INFLATION_FACTOR, 8000 * INFLATION_FACTOR * 0.20
    ),
    "morb_cost_epilepsy": get_gamma_params(
        2000 * INFLATION_FACTOR, 2000 * INFLATION_FACTOR * 0.20
    ),
    "morb_cost_asd": get_gamma_params(
        1500 * INFLATION_FACTOR, 1500 * INFLATION_FACTOR * 0.20
    ),
    "morb_cost_mental": get_gamma_params(
        1000 * INFLATION_FACTOR, 1000 * INFLATION_FACTOR * 0.20
    ),
    "wgs_diag_cost_adjustment": {
        "dist": "normal",
        "loc": -1000 * INFLATION_FACTOR,
        "scale": 100 * INFLATION_FACTOR,
    },
    # Utilities (Beta distributions)
    "u_base_mild": get_beta_params(0.78, 0.02),
    "u_base_severe": get_beta_params(0.65, 0.03),
    "u_decay": get_beta_params(0.0005, 0.00005),
    "u_diag": get_beta_params(0.02, 0.002),
    "u_carer": get_beta_params(0.05, 0.005),
    "morb_qaly_epilepsy": get_beta_params(0.04, 0.005),
    "morb_qaly_asd": get_beta_params(0.03, 0.005),
    "morb_qaly_mental": get_beta_params(0.05, 0.005),
    "wgs_diag_qaly_adjustment": get_beta_params(0.01, 0.001),
    # Probabilities / Rates
    "mort_hr_mild": {"dist": "lognormal", "s": 0.1, "scale": 2.0},
    "mort_hr_severe": {"dist": "lognormal", "s": 0.1, "scale": 4.0},
    "morb_prob_epilepsy": get_beta_params(0.25, 0.03),
    "morb_prob_asd": get_beta_params(0.30, 0.03),
    "morb_prob_mental": get_beta_params(0.35, 0.04),
    "familial_prop": {"dist": "beta", "alpha": 30, "beta": 150},
    "yield_wgs": {"dist": "beta", "alpha": 45, "beta": 55},
    "severity_mild_prop": get_beta_params(0.70, 0.03),
    "fertility_multiplier": {"dist": "lognormal", "s": 0.1, "scale": 1.0},
    # Fixed parameters
    "min_test_age": {"dist": "fixed", "value": 0},
}


# Helper function to sample from the defined distributions
def sample_params_from_dist(dist_dict, seed=None):
    if seed is not None:
        np.random.seed(seed)
    sampled_params = {}
    for param_name, dist_info in dist_dict.items():
        if dist_info["dist"] == "beta":
            sampled_params[param_name] = beta.rvs(dist_info["alpha"], dist_info["beta"])
        elif dist_info["dist"] == "gamma":
            sampled_params[param_name] = gamma.rvs(
                a=dist_info["shape"], scale=dist_info["scale"]
            )
        elif dist_info["dist"] == "lognormal":
            sampled_params[param_name] = lognorm.rvs(
                s=dist_info["s"], scale=dist_info["scale"]
            )
        elif dist_info["dist"] == "normal":
            sampled_params[param_name] = norm.rvs(
                loc=dist_info["loc"], scale=dist_info["scale"]
            )
        elif dist_info["dist"] == "uniform":
            sampled_params[param_name] = uniform.rvs(
                loc=dist_info["low"], scale=dist_info["high"] - dist_info["low"]
            )
        elif dist_info["dist"] == "fixed":
            sampled_params[param_name] = dist_info["value"]
        else:
            raise ValueError(f"Unknown distribution type: {dist_info['dist']}")
    if "severity_mild_prop" in sampled_params:
        sampled_params["severity_severe_prop"] = (
            1.0 - sampled_params["severity_mild_prop"]
        )
    return sampled_params


def prepare_dask_params(sampled_params):
    # Costs
    COST_INP_NP_sampled = np.array(
        [sampled_params["cost_inp_mild"], sampled_params["cost_inp_severe"]]
    )
    COST_OUTP_NP_sampled = np.array(
        [sampled_params["cost_outp_mild"], sampled_params["cost_outp_severe"]]
    )
    COST_PHARM_NP_sampled = np.array(
        [sampled_params["cost_pharm_mild"], sampled_params["cost_pharm_severe"]]
    )
    EDU_SAMPLED = np.array(
        [
            [
                sampled_params["edu0_sup0"],
                sampled_params["edu0_sup1"],
                sampled_params["edu0_sup2"],
            ],
            [
                sampled_params["edu1_sup0"],
                sampled_params["edu1_sup1"],
                sampled_params["edu1_sup2"],
            ],
        ]
    )
    WELFARE_NP_sampled = np.array(
        [sampled_params["welfare_mild"], sampled_params["welfare_severe"]]
    )
    MORB_COST_NP_sampled = np.array(
        [
            sampled_params["morb_cost_epilepsy"],
            sampled_params["morb_cost_asd"],
            sampled_params["morb_cost_mental"],
        ]
    )

    # Utilities
    U_BASE_NP_sampled = np.array(
        [sampled_params["u_base_mild"], sampled_params["u_base_severe"]]
    )
    MORB_QALY_NP_sampled = np.array(
        [
            sampled_params["morb_qaly_epilepsy"],
            sampled_params["morb_qaly_asd"],
            sampled_params["morb_qaly_mental"],
        ]
    )

    # Mortality HRs
    MORT_HR_sampled = np.array(
        [sampled_params["mort_hr_mild"], sampled_params["mort_hr_severe"]]
    )

    # Morbidity Probabilities
    MORB_PROB_SAMPLED = {
        "epilepsy": sampled_params["morb_prob_epilepsy"],
        "asd": sampled_params["morb_prob_asd"],
        "mental": sampled_params["morb_prob_mental"],
    }

    # Severity Distribution
    SEVERITY_DIST_SAMPLED = np.array(
        [sampled_params["severity_mild_prop"], sampled_params["severity_severe_prop"]]
    )

    # Fertility Rates
    FERT_RATES_DF_SAMPLED = FERT_RATES_DF.copy()
    FERT_RATES_DF_SAMPLED["rate"] *= sampled_params["fertility_multiplier"]

    return {
        "COST_INP_NP": COST_INP_NP_sampled,
        "COST_OUTP_NP": COST_OUTP_NP_sampled,
        "COST_PHARM_NP": COST_PHARM_NP_sampled,
        "EDU": EDU_SAMPLED,
        "RESPITE": sampled_params["respite"],
        "MOBILITY": sampled_params["mobility"],
        "WELFARE_NP": WELFARE_NP_sampled,
        "EMP_NP": EMP_NP,
        "MORB_COST_NP": MORB_COST_NP_sampled,
        "WGS_DIAG_COST_ADJUSTMENT": sampled_params["wgs_diag_cost_adjustment"],
        "U_BASE_NP": U_BASE_NP_sampled,
        "U_DECAY": sampled_params["u_decay"],
        "U_DIAG": sampled_params["u_diag"],
        "U_CARER": sampled_params["u_carer"],
        "MORB_QALY_NP": MORB_QALY_NP_sampled,
        "WGS_DIAG_QALY_ADJUSTMENT": sampled_params["wgs_diag_qaly_adjustment"],
        "MORT_HR": MORT_HR_sampled,
        "MORB_PROB": MORB_PROB_SAMPLED,
        "familial_prop": sampled_params["familial_prop"],
        "yield_wgs": sampled_params["yield_wgs"],
        "min_test_age": sampled_params["min_test_age"],
        "SEVERITY_DIST": SEVERITY_DIST_SAMPLED,
        "FERT_RATES_DF": FERT_RATES_DF_SAMPLED,
        "DISCOUNT": DISCOUNT,
        "INFLATION_FACTOR": INFLATION_FACTOR,
        "MORB_KEYS": MORB_KEYS,
    }


# Build lookup table for fertility rates (base rates)
fert_data = []
for (s, (lo, hi)), r in FERT_AGE_SPEC.items():
    for age in range(lo, hi + 1):
        fert_data.append({"severity": s, "age": age, "rate": r})
FERT_RATES_DF = pd.DataFrame(fert_data)

# %% [markdown]
## 3. Cohort Generator (Dask-compatible)


def sample_ages(n, age_dist_param):
    idx = np.random.choice(len(AGE_BREAKS), n, p=age_dist_param)
    return (AGE_BREAKS[idx] + np.random.randint(0, 5, n)).astype(int)


def gen_population_dask(n, current_params, arm="prospective"):
    ages = sample_ages(n, AGE_DIST)
    sev_dist = current_params["SEVERITY_DIST"]
    # Ensure sev_dist is a valid probability distribution
    sev_dist = np.array(sev_dist)
    sev_dist /= sev_dist.sum()

    df = pd.DataFrame(
        {
            "age": ages,
            "sex": np.random.choice(2, n),
            "severity": np.random.choice(2, n, p=sev_dist),
            "familial": np.random.random(n) < current_params["familial_prop"],
            "diagnosed": np.zeros(n, bool)
            if arm == "prospective"
            else (np.random.random(n) < current_params["yield_wgs"]),
            "living": np.random.choice(4, n, p=[0.2, 0.1, 0.3, 0.4]),
            "employment": np.random.choice(3, n, p=[0.7, 0.2, 0.1]),
            "uses_respite": np.random.random(n) < 0.3,
            "needs_mobility": np.random.random(n) < 0.2,
            "support": np.random.choice(3, n, p=[0.5, 0.3, 0.2]),
            "ses": np.random.choice(5, n),
        }
    )
    df["school"] = np.where(df["age"] < 5, -1, np.where(df["age"] < 12, 0, 1))

    for col in [
        "annual_cost",
        "annual_qaly",
        "cost_health",
        "cost_edu",
        "cost_respite",
        "cost_mobility",
        "cost_welfare",
        "cost_emp",
        "cost_morbidity",
    ]:
        df[col] = 0.0
    return dd.from_pandas(df, npartitions=4)


# %% [markdown]
## 4. Population System (Dask)


class PopulationSystemDask:
    def __init__(self, pop_size, current_params, arm="prospective"):
        self.arm = arm
        self.params = current_params
        self.pop = gen_population_dask(pop_size, self.params, arm).persist()

    def _mortality(self):
        params = self.params

        # map_partitions is suitable for complex row-wise logic
        def mortality_partition(df):
            if df.empty:
                return df
            ages = df["age"].values
            sev = df["severity"].values
            age_indices = np.clip((ages // 5).astype(int), 0, len(ABS_MORT) - 1)
            surv_prob = ABS_MORT[age_indices] * params["MORT_HR"][sev]
            # Create a mask for survivors
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
        ).fillna(0)

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

        # Define a function to generate babies for each partition of actual_births_info_dd
        def generate_babies_for_partition(
            partition_of_birth_info, params, arm, pop_meta
        ):
            n_babies_in_partition = len(partition_of_birth_info)
            if n_babies_in_partition == 0:
                return pop_meta.copy()  # Return empty DataFrame with correct metadata

            # Generate base baby population for this partition
            # gen_population_dask returns a Dask DataFrame, so we need to compute it here
            # as this function operates on a Pandas partition.
            babies_df_part = gen_population_dask(
                n_babies_in_partition, params, arm
            ).compute()

            # Set age to 0 and assign familial status from the parent
            babies_df_part["age"] = 0
            babies_df_part["familial"] = partition_of_birth_info[
                "familial_parent"
            ].values

            return babies_df_part

        # Apply this function to each partition of actual_births_info_dd
        # The meta should match the schema of the main population DataFrame (self.pop)
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

        # Use map_partitions for updating 'diagnosed' status
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
                # Generate random outcomes for diagnosis
                diag_outcomes = np.random.random(cnt) < self.params["yield_wgs"]
                # Update the 'diagnosed' column where the mask is True
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
                )

            n = len(df)
            sev = df["severity"].values
            ages = df["age"].values

            hc = (
                params["COST_INP_NP"][sev]
                + params["COST_OUTP_NP"][sev]
                + params["COST_PHARM_NP"][sev]
            ) * disc
            rc = df["uses_respite"].values.astype(int) * params["RESPITE"] * disc
            mc = -df["needs_mobility"].values.astype(int) * params["MOBILITY"] * disc
            wc = params["WELFARE_NP"][sev] * disc
            emp = params["EMP_NP"][df["employment"].values] * disc

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
                uq
                + df["diagnosed"].values.astype(int) * params["U_DIAG"]
                + params["U_CARER"]
            ) * disc - morb_qaly

            if self.arm == "prospective":
                m = df["diagnosed"].values
                total_qaly += (
                    m.astype(np.float64) * params["WGS_DIAG_QALY_ADJUSTMENT"] * disc
                )

            return df.assign(
                cost_health=hc,
                cost_edu=ec,
                cost_respite=rc,
                cost_mobility=mc,
                cost_welfare=wc,
                cost_emp=emp,
                cost_morbidity=morb_cost,
                annual_cost=hc + ec + rc + mc + wc + emp + morb_cost,
                annual_qaly=total_qaly,
            )

        self.pop = self.pop.map_partitions(
            cost_qaly_partition, meta=self.pop._meta
        ).persist()

    def step(self, year):
        self._mortality()
        new_babies_dd = self._fertility()
        self._diagnosis()
        self.pop = self.pop.assign(age=self.pop.age + 1)
        # Concatenate new babies lazily
        if new_babies_dd.npartitions > 0:
            self.pop = dd.concat([self.pop, new_babies_dd], interleave_partitions=True)
        self.pop = self.pop.persist()
        self._cost_qaly(year)


# %% [markdown]
## 5. Run Helpers


def run_sim(sampled_params, pop_size=POP_SIZE, seed_idx=None):
    if seed_idx is not None:
        np.random.seed(42 + seed_idx)
    else:
        np.random.seed(42)

    dask_params = prepare_dask_params(sampled_params)

    sim_r = PopulationSystemDask(pop_size, dask_params, "retrospective")
    sim_p = PopulationSystemDask(pop_size, dask_params, "prospective")

    # Accumulate Dask Series for costs and QALYs
    annual_costs_r = []
    annual_qalys_r = []
    annual_costs_p = []
    annual_qalys_p = []

    for yr in YEARS:
        sim_r.step(yr)
        if sim_r.pop.npartitions > 0:  # Check if population is not empty
            annual_costs_r.append(sim_r.pop["annual_cost"].sum())
            annual_qalys_r.append(sim_r.pop["annual_qaly"].sum())
        else:
            annual_costs_r.append(da.from_array(np.array(0.0)))
            annual_qalys_r.append(da.from_array(np.array(0.0)))

        sim_p.step(yr)
        if sim_p.pop.npartitions > 0:  # Check if population is not empty
            annual_costs_p.append(sim_p.pop["annual_cost"].sum())
            annual_qalys_p.append(sim_p.pop["annual_qaly"].sum())
        else:
            annual_costs_p.append(da.from_array(np.array(0.0)))
            annual_qalys_p.append(da.from_array(np.array(0.0)))

    # Sum the lists of Dask Series/Arrays directly within dd.compute
    # This will create a single Dask graph for all sums and then compute them
    cum_r_c_dask = sum(annual_costs_r)
    cum_r_q_dask = sum(annual_qalys_r)
    cum_p_c_dask = sum(annual_costs_p)
    cum_p_q_dask = sum(annual_qalys_p)

    cum_r_c, cum_r_q, cum_p_c, cum_p_q = dd.compute(
        cum_r_c_dask, cum_r_q_dask, cum_p_c_dask, cum_p_q_dask
    )

    return (cum_p_c - cum_r_c, cum_p_q - cum_r_q)


def run_scenario(sampled_params, pop_size=POP_SIZE):
    dask_params = prepare_dask_params(sampled_params)

    sim_r = PopulationSystemDask(pop_size, dask_params, "retrospective")
    sim_p = PopulationSystemDask(pop_size, dask_params, "prospective")

    # Lists to hold Dask objects for later computation
    annual_data_r_dask_list = []
    annual_data_p_dask_list = []
    ses_r_dask_list = []
    ses_p_dask_list = []

    for yr in YEARS:
        sim_r.step(yr)
        if sim_r.pop.npartitions > 0:
            annual_data_r_dask_list.append(
                sim_r.pop[
                    [
                        "annual_cost",
                        "annual_qaly",
                        "cost_health",
                        "cost_edu",
                        "cost_respite",
                        "cost_mobility",
                        "cost_welfare",
                        "cost_emp",
                        "cost_morbidity",
                    ]
                ]
                .sum()
                .to_frame(name=yr)
                .T
            )
            # Store Dask Series for SES distribution
            ses_r_dask_list.append(sim_r.pop["ses"])
        else:
            empty_df = pd.DataFrame(
                [[0.0] * 9],
                columns=[
                    "annual_cost",
                    "annual_qaly",
                    "cost_health",
                    "cost_edu",
                    "cost_respite",
                    "cost_mobility",
                    "cost_welfare",
                    "cost_emp",
                    "cost_morbidity",
                ],
                index=[yr],
            )
            annual_data_r_dask_list.append(dd.from_pandas(empty_df, npartitions=1))
            ses_r_dask_list.append(
                dd.from_pandas(pd.Series([0] * pop_size, dtype=int), npartitions=1)
            )  # Placeholder for SES if pop is empty

        sim_p.step(yr)
        if sim_p.pop.npartitions > 0:
            annual_data_p_dask_list.append(
                sim_p.pop[
                    [
                        "annual_cost",
                        "annual_qaly",
                        "cost_health",
                        "cost_edu",
                        "cost_respite",
                        "cost_mobility",
                        "cost_welfare",
                        "cost_emp",
                        "cost_morbidity",
                    ]
                ]
                .sum()
                .to_frame(name=yr)
                .T
            )
            # Store Dask Series for SES distribution
            ses_p_dask_list.append(sim_p.pop["ses"])
        else:
            empty_df = pd.DataFrame(
                [[0.0] * 9],
                columns=[
                    "annual_cost",
                    "annual_qaly",
                    "cost_health",
                    "cost_edu",
                    "cost_respite",
                    "cost_mobility",
                    "cost_welfare",
                    "cost_emp",
                    "cost_morbidity",
                ],
                index=[yr],
            )
            annual_data_p_dask_list.append(dd.from_pandas(empty_df, npartitions=1))
            ses_p_dask_list.append(
                dd.from_pandas(pd.Series([0] * pop_size, dtype=int), npartitions=1)
            )  # Placeholder for SES if pop is empty

    # Concatenate all annual Dask DataFrames and compute once
    # Also compute all SES distributions once
    all_dask_objects = (
        annual_data_r_dask_list
        + annual_data_p_dask_list
        + ses_r_dask_list
        + ses_p_dask_list
    )
    computed_results = dd.compute(*all_dask_objects)

    # Separate the computed results
    num_years = len(YEARS)
    all_annual_r_computed = computed_results[0:num_years]
    all_annual_p_computed = computed_results[num_years : 2 * num_years]
    ses_r_computed_list = computed_results[2 * num_years : 3 * num_years]
    ses_p_computed_list = computed_results[3 * num_years : 4 * num_years]

    outputs = []
    final_totals = {}

    for arm_idx, (arm, annual_computed_list, ses_computed_list) in enumerate(
        [
            ("retrospective", all_annual_r_computed, ses_r_computed_list),
            ("prospective", all_annual_p_computed, ses_p_computed_list),
        ]
    ):
        cum_c = 0.0
        cum_q = 0.0
        for yr_idx, yr in enumerate(YEARS):
            annual_sums = annual_computed_list[yr_idx].iloc[
                0
            ]  # .iloc[0] because .T makes it a 1-row DataFrame
            ses_series = ses_computed_list[yr_idx]

            cum_c += annual_sums["annual_cost"]
            cum_q += annual_sums["annual_qaly"]

            ses_q_pct = {
                f"ses_q{i}_pct": (ses_series == i).mean() * 100 for i in range(5)
            }

            row_data = {
                "arm": arm,
                "year": yr,
                "annual_cost": annual_sums["annual_cost"],
                "cost_health": annual_sums["cost_health"],
                "cost_edu": annual_sums["cost_edu"],
                "cost_respite": annual_sums["cost_respite"],
                "cost_mobility": annual_sums["cost_mobility"],
                "cost_welfare": annual_sums["cost_welfare"],
                "cost_emp": annual_sums["cost_emp"],
                "cost_morbidity": annual_sums["cost_morbidity"],
                "costs": cum_c,
                "qalys": cum_q,
                **ses_q_pct,
            }
            outputs.append(row_data)

        final_totals[arm] = {"cost": cum_c, "qaly": cum_q}

    d_cost = final_totals["prospective"]["cost"] - final_totals["retrospective"]["cost"]
    d_qaly = final_totals["prospective"]["qaly"] - final_totals["retrospective"]["qaly"]

    return (d_cost, d_qaly), pd.DataFrame(outputs)


# %% [markdown]
## 6. Deterministic Scenarios

if __name__ == "__main__":
    print("--- Running Module 6: Deterministic Scenarios ---")
    base_mean_params = {}
    for k, v in DISTRIBUTIONS.items():
        if v["dist"] == "beta":
            base_mean_params[k] = v["alpha"] / (v["alpha"] + v["beta"])
        elif v["dist"] == "gamma":
            base_mean_params[k] = v["shape"] * v["scale"]
        elif v["dist"] == "lognormal":
            base_mean_params[k] = v["scale"] * np.exp(v["s"] ** 2 / 2)
        elif v["dist"] == "normal":
            base_mean_params[k] = v["loc"]
        elif v["dist"] == "uniform":
            base_mean_params[k] = (v["low"] + v["high"]) / 2
        elif v["dist"] == "fixed":
            base_mean_params[k] = v["value"]

    if "severity_mild_prop" in base_mean_params:
        base_mean_params["severity_severe_prop"] = (
            1.0 - base_mean_params["severity_mild_prop"]
        )

    scenarios = {
        "low": {
            "familial_prop": base_mean_params["familial_prop"] - 0.05,
            "yield_wgs": base_mean_params["yield_wgs"] - 0.05,
        },
        "base": {
            "familial_prop": base_mean_params["familial_prop"],
            "yield_wgs": base_mean_params["yield_wgs"],
        },
        "high": {
            "familial_prop": base_mean_params["familial_prop"] + 0.05,
            "yield_wgs": base_mean_params["yield_wgs"] + 0.05,
        },
    }

    results = []
    for name, specific_override_params in scenarios.items():
        current_params_for_run = base_mean_params.copy()
        current_params_for_run.update(specific_override_params)

        dc, dq = run_sim(
            current_params_for_run, pop_size=100
        )  # Smaller population for testing
        icer = (dc / dq) if dq != 0 else 0
        results.append({"scenario": name, "dCost": dc, "dQALY": dq, "ICER": icer})

    det_df = pd.DataFrame(results)
    det_df.to_csv("deterministic_summary.csv", index=False)
    print(det_df)

    plt.figure()
    plt.bar(det_df["scenario"], det_df["ICER"])
    plt.title("Deterministic ICERs (£/QALY)")
    plt.ylabel("ICER (£/QALY)")
    plt.show()

    # %% [markdown]
    ## 7. Probabilistic Sensitivity Analysis (PSA)

    print("\n--- Running Module 7: Probabilistic Sensitivity Analysis ---")
    psa_n = 300
    psa_out = []

    # Initialize Dask cluster for parallel processing
    cluster = LocalCluster()
    client = Client(cluster)

    try:
        print(f"Dask dashboard link: {client.dashboard_link}")
        print(f"Running {psa_n} PSA simulations in parallel using Dask...")

        psa_args = []
        for i in range(psa_n):
            sampled_params = sample_params_from_dist(DISTRIBUTIONS, seed=i)
            psa_args.append((sampled_params, 100, i))  # Smaller population for testing

        futures = client.map(lambda args: run_sim(args[0], args[1], args[2]), psa_args)
        progress(futures)

        results = client.gather(futures)

        for i, (dc, dq) in enumerate(results):
            original_sampled_params = psa_args[i][0]
            row_data = {"run": i, "dCost": dc, "dQALY": dq}
            row_data.update(original_sampled_params)
            psa_out.append(row_data)

        # Create a Pandas DataFrame first, then convert to Dask for large-scale analysis
        psa_df_pd = pd.DataFrame(psa_out)
        psa_df_pd.to_csv("psa_samples.csv", index=False)
        print("PSA results saved to psa_samples.csv")

        # Convert to Dask DataFrame for subsequent modules
        psa_df = dd.from_pandas(psa_df_pd, npartitions=4)

    finally:
        # Close the Dask client and cluster
        client.close()
        cluster.close()
        print("Dask cluster closed.")

    # %% [markdown]
    ## 8. CE-Plane, CEAC, EVPI & ENMB

    print("\n--- Running Module 8: CE-Plane, CEAC, EVPI & ENMB ---")
    wtp = np.linspace(0, 150000, 40)
    # Compute the dask series to get numpy arrays for calculation
    dcost = psa_df["dCost"].compute().to_numpy()
    dqaly = psa_df["dQALY"].compute().to_numpy()

    valid_psa = dqaly > 0
    nb = dqaly[valid_psa, None] * wtp[None, :] - dcost[valid_psa, None]

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
    plt.show()

    prob = (nb > 0).mean(axis=0)
    plt.figure()
    plt.plot(wtp, prob)
    plt.title("Cost-Effectiveness Acceptability Curve (CEAC)")
    plt.xlabel("Willingness-to-Pay per QALY")
    plt.ylabel("Probability Cost-Effective")
    plt.ylim(0, 1)
    plt.grid(True)
    plt.show()

    evpi = np.mean(np.maximum(0, nb), axis=0) - np.maximum(0, np.mean(nb, axis=0))
    plt.figure()
    plt.plot(wtp, evpi)
    plt.title("Expected Value of Perfect Information (EVPI)")
    plt.xlabel("Willingness-to-Pay per QALY")
    plt.ylabel("EVPI")
    plt.grid(True)
    plt.show()

    enmb = np.mean(nb, axis=0)
    plt.figure()
    plt.plot(wtp, enmb)
    plt.axhline(y=0, color="grey", linestyle="--", linewidth=0.8)
    plt.title("Expected Net Monetary Benefit (ENMB) Curve")
    plt.xlabel("Willingness-to-Pay per QALY")
    plt.ylabel("Expected Net Monetary Benefit (£)")
    plt.grid(True)
    plt.show()

    # %% [markdown]
    ## 9. One-Way Sensitivity (Tornado)

    print("\n--- Running Module 9: One-Way Sensitivity (Tornado) ---")
    tornado = []
    base_params = base_mean_params  # From Module 6

    if "severity_mild_prop" in base_params:
        base_params["severity_severe_prop"] = 1.0 - base_params["severity_mild_prop"]

    base_dc, base_dq = run_sim(
        base_params, pop_size=100
    )  # Smaller population for testing
    base_icer = base_dc / base_dq if base_dq != 0 else 0

    tornado_params_to_vary = ["familial_prop", "yield_wgs", "u_diag", "cost_inp_severe"]

    for param_name in tornado_params_to_vary:
        dist_info = DISTRIBUTIONS[param_name]
        low_val, high_val, mean_val = 0, 0, 0
        if dist_info["dist"] == "beta":
            mean_val = dist_info["alpha"] / (dist_info["alpha"] + dist_info["beta"])
            variance = (dist_info["alpha"] * dist_info["beta"]) / (
                (dist_info["alpha"] + dist_info["beta"]) ** 2
                * (dist_info["alpha"] + dist_info["beta"] + 1)
            )
            std_dev = math.sqrt(variance)
            low_val, high_val = (
                max(0, mean_val - 2 * std_dev),
                min(1, mean_val + 2 * std_dev),
            )
        elif dist_info["dist"] == "gamma":
            mean_val = dist_info["shape"] * dist_info["scale"]
            std_dev = math.sqrt(dist_info["shape"] * dist_info["scale"] ** 2)
            low_val, high_val = max(0, mean_val - 2 * std_dev), mean_val + 2 * std_dev
        # ... (rest of the conditions remain the same, using numpy where needed)
        elif dist_info["dist"] == "lognormal":
            mean_val = dist_info["scale"] * np.exp(dist_info["s"] ** 2 / 2)
            low_val, high_val = mean_val * 0.90, mean_val * 1.10
        else:
            continue

        for val in [low_val, high_val]:
            p_temp = base_params.copy()
            p_temp[param_name] = val
            dc, dq = run_sim(p_temp, pop_size=100)  # Smaller population for testing
            icer = (dc / dq) if dq != 0 else 0
            change_type = "Low" if val < mean_val else "High"
            tornado.append(
                {"param": param_name, "change_type": change_type, "ICER": icer}
            )

    tor_df = pd.DataFrame(tornado)
    tor_df["ICER_diff"] = tor_df["ICER"] - base_icer
    tor_df["abs_diff"] = tor_df["ICER_diff"].abs()
    tor_df = tor_df.sort_values(by="abs_diff", ascending=True)

    plt.figure(figsize=(10, len(tornado_params_to_vary) * 0.8))
    labels = [
        f"{row['param']} ({row['change_type']})" for idx, row in tor_df.iterrows()
    ]
    colors = ["red" if x < 0 else "green" for x in tor_df["ICER_diff"]]
    plt.barh(labels, tor_df["ICER_diff"], color=colors)
    plt.axvline(0, color="black", lw=0.8)
    plt.xlabel("Change in ICER from base (£/QALY)")
    plt.title("Tornado Sensitivity Analysis (Selected Parameters)")
    plt.tight_layout()
    plt.show()

    # %% [markdown]
    ## 10. Sub-group Analyses

    print("\n--- Running Module 10: Sub-group Analyses ---")
    sg = []
    mean_params_for_subgroup = base_mean_params  # from Module 6

    if "severity_mild_prop" in mean_params_for_subgroup:
        mean_params_for_subgroup["severity_severe_prop"] = (
            1.0 - mean_params_for_subgroup["severity_mild_prop"]
        )

    for sev_prop, label in [(1.0, "Mild Only"), (0.0, "Severe Only")]:
        p_temp = mean_params_for_subgroup.copy()
        p_temp["severity_mild_prop"] = sev_prop
        p_temp["severity_severe_prop"] = 1.0 - sev_prop
        dc, dq = run_sim(p_temp, pop_size=100)  # Smaller population for testing
        sg.append({"group": f"Severity: {label}", "ICER": (dc / dq) if dq != 0 else 0})

    for age in [0, 18, 30]:
        p_temp = mean_params_for_subgroup.copy()
        p_temp["min_test_age"] = age
        dc, dq = run_sim(p_temp, pop_size=100)  # Smaller population for testing
        sg.append(
            {"group": f"Min Test Age: {age}", "ICER": (dc / dq) if dq != 0 else 0}
        )

    (_, int_full_df) = run_scenario(
        mean_params_for_subgroup, pop_size=100
    )  # Smaller population for testing
    dfp = int_full_df[int_full_df["arm"] == "prospective"]
    dfr = int_full_df[int_full_df["arm"] == "retrospective"]
    for yrs_n in [10, 20, len(YEARS)]:
        yr = START_YEAR + yrs_n - 1
        if yr in dfp["year"].values and yr in dfr["year"].values:
            c1 = float(dfp.loc[dfp["year"] == yr, "costs"].values[0])
            c0 = float(dfr.loc[dfr["year"] == yr, "costs"].values[0])
            q1 = float(dfp.loc[dfp["year"] == yr, "qalys"].values[0])
            q0 = float(dfr.loc[dfr["year"] == yr, "qalys"].values[0])
            dc, dq = (c1 - c0), (q1 - q0)
            sg.append(
                {"group": f"Horizon: {yrs_n} yrs", "ICER": (dc / dq) if dq != 0 else 0}
            )

    sg_df = pd.DataFrame(sg)
    base_dc_subgroup, base_dq_subgroup = run_sim(
        mean_params_for_subgroup, pop_size=10000
    )  # Smaller population for testing
    base_icer_subgroup = (
        base_dc_subgroup / base_dq_subgroup if base_dq_subgroup != 0 else 0
    )

    plt.figure()
    plt.scatter(sg_df["ICER"], sg_df["group"], marker="o")
    plt.axvline(
        base_icer_subgroup,
        color="grey",
        linestyle="--",
        label=f"Base Case ICER ({base_icer_subgroup:,.0f})",
    )
    plt.xlabel("ICER (£/QALY)")
    plt.title("Sub-group Analyses")
    plt.legend()
    plt.tight_layout()
    plt.grid(axis="x")
    plt.show()

    # ... The rest of the modules follow a similar pattern of replacing cudf/cupy with pandas/numpy
    # and using .compute() where necessary.

    # %% [markdown]
    ## 11. Cost-Mix Stacked Area (Prospective)

    print("\n--- Running Module 11: Cost-Mix Stacked Area (Prospective) ---")
    (_, mix_data) = run_scenario(
        mean_params_for_subgroup, pop_size=100
    )  # Smaller population for testing
    pm = mix_data[mix_data["arm"] == "prospective"]
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
    plt.title("Cost Mix Over Time (Prospective Arm - Discounted Annual Costs)")
    plt.xlabel("Year")
    plt.ylabel("Annual Cost")
    plt.show()

    # %% [markdown]
    ## 12. 5-Year Budget Impact

    print("\n--- Running Module 12: 5-Year Budget Impact ---")
    budg = []
    uptakes = [0.2, 0.5, 0.8]
    yrs = YEARS[:5]
    # Re-use the data from the previous scenario run
    # mix_data is already a pandas DataFrame from Module 11
    dfp = mix_data[mix_data["arm"] == "prospective"]
    dfr = mix_data[mix_data["arm"] == "retrospective"]

    for u in uptakes:
        for yr in yrs:
            if yr in dfp["year"].values and yr in dfr["year"].values:
                c1 = float(dfp.loc[dfp["year"] == yr, "annual_cost"].item())
                c0 = float(dfr.loc[dfr["year"] == yr, "annual_cost"].item())
                incremental_cost = c1 - c0
                budg.append(
                    {"uptake": u, "year": yr, "budget_impact": incremental_cost * u}
                )

    budg_df = pd.DataFrame(budg)
    plt.figure()
    for u in uptakes:
        sub = budg_df[budg_df["uptake"] == u]
        plt.plot(
            sub["year"], sub["budget_impact"], label=f"Uptake {int(u*100)}%", marker="o"
        )
    plt.title("5-Year Budget Impact")
    plt.xlabel("Year")
    plt.ylabel("Incremental Budget Impact")
    plt.legend()
    plt.grid(True)
    plt.show()

    # %% [markdown]
    ## 13. Equity by SES Quintile

    print("\n--- Running Module 13: Equity by SES Quintile ---")
    bas = mix_data[
        mix_data["arm"] == "prospective"
    ]  # mix_data is already a pandas DataFrame
    if YEARS[-1] in bas["year"].values:
        row_series = bas[bas["year"] == YEARS[-1]].iloc[0]
        ses_cols = [f"ses_q{i}_pct" for i in range(5)]
        ses_vals = [float(row_series[col]) for col in ses_cols]
        labels = [f"Quintile {i+1}" for i in range(5)]

        plt.figure()
        plt.bar(labels, ses_vals)
        plt.title(f"SES Distribution of Population in Final Year ({YEARS[-1]})")
        plt.xlabel("SES Quintile")
        plt.ylabel("Percentage of Population (%)")
        plt.tight_layout()
        plt.show()

    # %% [markdown]
    ## 14. PSA Histograms

    print("\n--- Running Module 14: PSA Histograms (dCost, dQALY) ---")
    # psa_df_pd was created in module 7
    cost_list = psa_df_pd["dCost"].tolist()
    qaly_list = psa_df_pd["dQALY"].tolist()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    ax1.hist(cost_list, bins=30, color="skyblue", edgecolor="black")
    ax1.set_title("PSA Distribution of Incremental Cost")
    ax1.set_xlabel("Delta Cost")
    ax1.set_ylabel("Frequency")

    ax2.hist(qaly_list, bins=30, color="salmon", edgecolor="black")
    ax2.set_title("PSA Distribution of Incremental QALYs")
    ax2.set_xlabel("Delta QALY")
    ax2.set_ylabel("Frequency")

    plt.tight_layout()
    plt.show()

    # %% [markdown]
    ## 15. CEAF (Cost-Effectiveness Acceptability Frontier)

    print("\n--- Running Module 15: CEAF ---")
    # 'prob' was calculated in module 8 from numpy arrays
    ceaf = np.maximum.accumulate(prob)

    plt.figure()
    plt.plot(wtp, prob, label="CEAC")
    plt.plot(wtp, ceaf, label="CEAF", linestyle="--")
    plt.title("CEAC and CEAF")
    plt.xlabel("Willingness-to-Pay per QALY")
    plt.ylabel("Probability")
    plt.legend()
    plt.grid(True)
    plt.show()

    # %% [markdown]
    ## 16. Input Parameter Summary (Updated for Distributions)

    print("\n--- Running Module 16: Saving Input Parameter Summary ---")

    param_summary_list = []
    for param_name, dist_info in DISTRIBUTIONS.items():
        # ... This module's logic remains the same, as it deals with dicts and strings
        summary_str = f"Distribution: {dist_info['dist']}"
        if dist_info["dist"] == "beta":
            summary_str += (
                f", Alpha: {dist_info['alpha']:.2f}, Beta: {dist_info['beta']:.2f}"
            )
        elif dist_info["dist"] == "gamma":
            summary_str += (
                f", Shape: {dist_info['shape']:.2f}, Scale: {dist_info['scale']:.2f}"
            )
        elif dist_info["dist"] == "lognormal":
            summary_str += f", S: {dist_info['s']:.2f}, Scale: {dist_info['scale']:.2f}"
        elif dist_info["dist"] == "normal":
            summary_str += (
                f", Loc: {dist_info['loc']:.2f}, Scale: {dist_info['scale']:.2f}"
            )
        elif dist_info["dist"] == "uniform":
            summary_str += (
                f", Low: {dist_info['low']:.2f}, High: {dist_info['high']:.2f}"
            )
        elif dist_info["dist"] == "fixed":
            summary_str += f", Value: {dist_info['value']:.2f}"
        param_summary_list.append(
            {"parameter": param_name, "distribution_details": summary_str}
        )

    # ... Add fixed parameters
    param_df = pd.DataFrame(param_summary_list)
    param_df.to_csv("input_parameters_with_distributions.csv", index=False)
    print(
        "Input parameters with distributions saved to input_parameters_with_distributions.csv"
    )

    # %% [markdown]
    ## 17. Publication Comparison

    print("\n--- Running Module 17: Publication Comparison ---")
    published = {"base": {"dCost": 480000, "dQALY": 6.5, "ICER": 73846}}
    pub_df = (
        pd.DataFrame.from_dict(published, orient="index")
        .reset_index()
        .rename(columns={"index": "scenario"})
    )
    pub_df = pub_df.rename(
        columns={"dCost": "dCost_pub", "dQALY": "dQALY_pub", "ICER": "ICER_pub"}
    )

    # det_df is the pandas dataframe from Module 6
    df_cmp = det_df.merge(pub_df, on="scenario", how="left")
    df_cmp = df_cmp.rename(
        columns={"dCost": "dCost_sim", "dQALY": "dQALY_sim", "ICER": "ICER_sim"}
    )
    print("Comparison of Simulation vs. Published Data:")
    print(df_cmp.to_string())
    df_cmp.to_csv("publication_comparison.csv", index=False)

    # %% [markdown]
    ## 18. Familial ID Prevalence Sensitivity Analysis

    print("\n--- Running Module 18: Familial ID Prevalence Sensitivity Analysis ---")
    mean_params_for_sens = base_mean_params  # from Module 6
    familial_prevalence_range = np.linspace(0.10, 0.23, 10)
    familial_sens_results = []
    for f_prop in familial_prevalence_range:
        p_temp = mean_params_for_sens.copy()
        p_temp["familial_prop"] = f_prop
        dc, dq = run_sim(p_temp, pop_size=10000)  # Smaller population for testing
        icer = (dc / dq) if dq != 0 else 0
        familial_sens_results.append(
            {"familial_prop": f_prop, "dCost": dc, "dQALY": dq, "ICER": icer}
        )

    familial_sens_df = pd.DataFrame(familial_sens_results)
    print("Familial ID Prevalence Sensitivity Results:")
    print(familial_sens_df.to_string())

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
    plt.show()

    # %% [markdown]
    ## 19. EVPPI Analysis

    print("\n--- Running Module 19: EVPPI Analysis ---")

    def calculate_evppi_curve(psa_df_local, param_name, wtp_range):
        evppi_values = []
        dcost_np = psa_df_local["dCost"].values
        dqaly_np = psa_df_local["dQALY"].values
        param_values_np = psa_df_local[param_name].values
        X = np.vstack([np.ones(len(psa_df_local)), param_values_np]).T

        for wtp_val in wtp_range:
            nmb_np = dqaly_np * wtp_val - dcost_np
            coeffs = np.linalg.lstsq(X, nmb_np, rcond=None)[0]
            nmb_predicted = X @ coeffs
            evppi_val = np.mean(np.maximum(0, nmb_np)) - np.mean(
                np.maximum(0, nmb_predicted)
            )
            evppi_values.append(evppi_val)
        return np.array(evppi_values)

    parameters_for_evppi_new = [
        "familial_prop",
        "yield_wgs",
        "u_diag",
        "cost_inp_severe",
    ]
    evppi_results = {}
    # Use the pandas version of the PSA results
    print("Calculating EVPPI for key parameters...")
    for param in parameters_for_evppi_new:
        if param in psa_df_pd.columns:
            evppi_curve = calculate_evppi_curve(psa_df_pd, param, wtp)
            evppi_results[param] = evppi_curve

    if evppi_results:
        plt.figure(figsize=(10, 6))
        for param, evppi_curve_host in evppi_results.items():
            plt.plot(
                wtp,
                evppi_curve_host,
                label=f'EVPPI ({param.replace("_", " ").title()})',
            )
        plt.title("Expected Value of Partial Perfect Information (EVPPI) Curves")
        plt.xlabel("Willingness-to-Pay per QALY")
        plt.ylabel("EVPPI (£)")
        plt.legend()
        plt.grid(True)
        plt.show()

    # %% [markdown]
    ## 20. PSA ICER Distribution

    print("\n--- Running Module 20: PSA ICER Distribution ---")
    # Use the pandas dataframe for this calculation
    dc = psa_df_pd["dCost"]
    dq = psa_df_pd["dQALY"]
    psa_icers_np = (dc / dq).replace([np.inf, -np.inf], np.nan).dropna()

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
        sns.histplot(
            finite_icers_capped, bins=50, kde=True, color="purple", edgecolor="black"
        )
        plt.title("PSA Distribution of ICERs (Capped at 1st and 99th Percentiles)")
        plt.xlabel("ICER (£/QALY)")
        plt.ylabel("Frequency")
        plt.grid(True)
    plt.show()

    # %% [markdown]
    ## 21. Cost-Mix Stacked Area (Retrospective)

    print("\n--- Running Module 21: Cost-Mix Stacked Area (Retrospective) ---")
    # mix_data was generated in module 11
    rm = mix_data[mix_data["arm"] == "retrospective"]
    cost_cols = [
        "cost_health",
        "cost_edu",
        "cost_respite",
        "cost_mobility",
        "cost_welfare",
        "cost_emp",
        "cost_morbidity",
    ]
    data_r = [rm[col] for col in cost_cols]

    plt.figure(figsize=(10, 6))
    plt.stackplot(
        rm["year"],
        *data_r,
        labels=[c.replace("cost_", "").capitalize() for c in cost_cols],
    )
    plt.legend(loc="upper left")
    plt.title("Cost Mix Over Time (Retrospective Arm - Discounted Annual Costs)")
    plt.xlabel("Year")
    plt.ylabel("Annual Cost")
    plt.show()

    print("Retrospective Cost Mix analysis complete.")
