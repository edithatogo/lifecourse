import dask.array as da
import dask.dataframe as dd
import pandas as pd
import matplotlib.pyplot as plt
import warnings
import numpy as np
import math
import os
from dask.distributed import LocalCluster, Client, progress, performance_report
import dask
from dask.diagnostics import Profiler, ResourceProfiler, CacheProfiler

warnings.filterwarnings("ignore")

# %% [markdown]
## 2. Global Parameters & Dask Constants and Parameter Distributions

START_YEAR, END_YEAR = 2020, 2100
YEARS = list(range(START_YEAR, END_YEAR + 1))
DISCOUNT = 0.035
POP_SIZE = 62000

# Costs are based on 2017 values from the paper, adjust to START_YEAR (2020)
COST_REFERENCE_YEAR = 2017
INFLATION_RATE = 0.03
INFLATION_FACTOR = (1 + INFLATION_RATE) ** (START_YEAR - COST_REFERENCE_YEAR)

# Demographics
AGE_BREAKS = np.arange(0, 95, 5)
AGE_DIST = np.array(
    [
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
LIFE_EXP_NP = np.array([74, 54])
ABS_MORT = np.array(
    [
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

# Fertility bands
FERT_AGE_SPEC = {
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

# Employment costs
EMP_NP = np.array([0, 10000, 0]) * INFLATION_FACTOR

# Morbidity Keys
MORB_KEYS = ["epilepsy", "asd", "mental"]


# Helper function to get Gamma parameters from mean and standard deviation
def get_gamma_params(mean, std_dev):
    if mean <= 0 or std_dev <= 0:
        return {"dist": "fixed", "value": mean}
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
        # Adjust variance slightly to ensure valid beta parameters if std_dev is too high
        variance = mean * (1 - mean) * 0.99
        std_dev = math.sqrt(variance)

    alpha = mean * (mean * (1 - mean) / variance - 1)
    beta_param = (1 - mean) * (mean * (1 - mean) / variance - 1)

    if alpha <= 0 or beta_param <= 0:
        # Fallback for invalid beta parameters (e.g., mean too close to 0 or 1 with large std_dev)
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
        rng = np.random.default_rng(seed)
    else:
        rng = np.random.default_rng()
    sampled_params = {}
    for param_name, dist_info in dist_dict.items():
        if dist_info["dist"] == "beta":
            sampled_params[param_name] = rng.beta(dist_info["alpha"], dist_info["beta"])
        elif dist_info["dist"] == "gamma":
            sampled_params[param_name] = rng.gamma(
                shape=dist_info["shape"], scale=dist_info["scale"]
            )
        elif dist_info["dist"] == "lognormal":
            sampled_params[param_name] = rng.lognormal(
                sigma=dist_info["s"], mean=np.log(dist_info["scale"])
            )
        elif dist_info["dist"] == "normal":
            sampled_params[param_name] = rng.normal(
                loc=dist_info["loc"], scale=dist_info["scale"]
            )
        elif dist_info["dist"] == "uniform":
            sampled_params[param_name] = rng.uniform(
                low=dist_info["low"], high=dist_info["high"]
            )
        elif dist_info["dist"] == "fixed":
            sampled_params[param_name] = dist_info["value"]
        else:
            raise ValueError(f"Unknown distribution type: {dist_info['dist']}")
    return sampled_params


def prepare_dask_params(sampled_params):
    if (
        "severity_mild_prop" in sampled_params
        and "severity_severe_prop" not in sampled_params
    ):
        sampled_params["severity_severe_prop"] = (
            1.0 - sampled_params["severity_mild_prop"]
        )

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

    # Morbidity Probabilities - Keep as dict for clarity in MORB_KEYS lookup
    MORB_PROB_SAMPLED = {
        "epilepsy": sampled_params["morb_prob_epilepsy"],
        "asd": sampled_params["morb_prob_asd"],
        "mental": sampled_params["morb_prob_mental"],
    }

    # Severity Distribution
    SEVERITY_DIST_SAMPLED = np.array(
        [sampled_params["severity_mild_prop"], sampled_params["severity_severe_prop"]]
    )

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
        "FERTILITY_MULTIPLIER": sampled_params["fertility_multiplier"],
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

# Client initialization moved before other operations to ensure it's available
try:
    if "client" not in locals() or not client.is_connected():
        cluster = LocalCluster(n_workers=os.cpu_count(), threads_per_worker=1)
        client = Client(cluster)
        print(f"Dask dashboard link: {client.dashboard_link}")
except Exception:
    cluster = LocalCluster(n_workers=os.cpu_count(), threads_per_worker=1)
    client = Client(cluster)
    print(f"Dask dashboard link: {client.dashboard_link}")

# Publish the fertility DataFrame to the Dask cluster
client.publish_dataset(fert=FERT_RATES_DF)

# Scatter constant objects to workers once
scattered_distributions = client.scatter(DISTRIBUTIONS, broadcast=True)
scattered_age_dist = client.scatter(AGE_DIST, broadcast=True)
scattered_abs_mort = client.scatter(ABS_MORT, broadcast=True)
scattered_life_exp_np = client.scatter(LIFE_EXP_NP, broadcast=True)
scattered_emp_np = client.scatter(EMP_NP, broadcast=True)
scattered_morb_keys = client.scatter(MORB_KEYS, broadcast=True)
scattered_fert_rates_df = client.scatter(FERT_RATES_DF, broadcast=True)

# Global Dask RandomState for pre-generating random numbers
global_rng_dask = da.random.RandomState(42)  # Use a fixed seed for reproducibility

# Pre-generate large Dask arrays for random numbers, sized to handle max possible population over time
# A rough estimate: POP_SIZE * len(YEARS) * 2 (for prospective/retrospective) * some buffer
total_sim_steps = len(YEARS) * 2  # Number of steps per simulation (r and p)
max_pop_per_step = POP_SIZE * 2  # Max population can grow due to births
estimated_max_elements = (
    max_pop_per_step * total_sim_steps
)  # Total elements needed over all steps

# Define chunks for random arrays to match Dask DataFrame partitions
# This ensures that when we slice these arrays by index, the chunks align with DataFrame partitions
# We'll use a chunk size roughly equivalent to a partition size
random_array_chunk_size = POP_SIZE // os.cpu_count()  # Example: POP_SIZE / num_cores

mortality_rand_global = global_rng_dask.random(
    size=estimated_max_elements, chunks=random_array_chunk_size
)
fertility_rand_global = global_rng_dask.random(
    size=estimated_max_elements, chunks=random_array_chunk_size
)
diag_rand_global = global_rng_dask.random(
    size=estimated_max_elements, chunks=random_array_chunk_size
)
morb_rand_base_global = global_rng_dask.random(
    size=estimated_max_elements, chunks=random_array_chunk_size
)

_POPULATION_META = pd.DataFrame(
    {
        "age": pd.Series([], dtype="int64"),
        "sex": pd.Series([], dtype="int64"),
        "severity": pd.Series([], dtype="int64"),
        "familial": pd.Series([], dtype="bool"),
        "diagnosed": pd.Series([], dtype="bool"),
        "living": pd.Series([], dtype="int64"),
        "employment": pd.Series([], dtype="int64"),
        "uses_respite": pd.Series([], dtype="bool"),
        "needs_mobility": pd.Series([], dtype="bool"),
        "support": pd.Series([], dtype="int64"),
        "ses": pd.Series([], dtype="int64"),
        "school": pd.Series([], dtype="int64"),
        "annual_cost": pd.Series([], dtype="float64"),
        "annual_qaly": pd.Series([], dtype="float64"),
        "cost_health": pd.Series([], dtype="float64"),
        "cost_edu": pd.Series([], dtype="float64"),
        "cost_respite": pd.Series([], dtype="float64"),
        "cost_mobility": pd.Series([], dtype="float64"),
        "cost_welfare": pd.Series([], dtype="float64"),
        "cost_emp": pd.Series([], dtype="float64"),
        "cost_morbidity": pd.Series([], dtype="float64"),
    }
)


# %% [markdown]
## 3. Cohort Generator (Dask-compatible) - Helper Functions (Module Scope)


def gen_population_dask(
    n,
    current_params,
    arm="prospective",
    seed=None,
    n_partitions=1,
    age_dist_scattered_func=None,
):
    rng = da.random.RandomState(seed)

    # Generate random data using Dask arrays
    ages_rand = rng.choice(
        len(age_dist_scattered_func), size=n, p=age_dist_scattered_func
    )
    ages = (ages_rand * 5) + rng.randint(0, 5, size=n)

    sev_dist = np.array(current_params["SEVERITY_DIST"])
    sev_dist /= sev_dist.sum()

    # Create a Dask DataFrame from Dask arrays
    ddf = dd.from_dask_array(
        da.stack(
            [
                ages,
                rng.choice(2, size=n),
                rng.choice(2, size=n, p=sev_dist),
                (rng.random(n) < current_params["familial_prop"]).astype(bool),
                (rng.random(n) < current_params["yield_wgs"]).astype(bool)
                if arm != "prospective"
                else np.zeros(n, dtype=bool),
                rng.choice(4, size=n, p=[0.2, 0.1, 0.3, 0.4]),
                rng.choice(3, size=n, p=[0.7, 0.2, 0.1]),
                (rng.random(n) < 0.3).astype(bool),
                (rng.random(n) < 0.2).astype(bool),
                rng.choice(3, size=n, p=[0.5, 0.3, 0.2]),
                rng.choice(5, size=n),
            ],
            axis=1,
        ),
        columns=[
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
        ],
    )

    # Add remaining columns
    ddf["school"] = ddf["age"].map_partitions(
        lambda s: np.where(s < 5, -1, np.where(s < 12, 0, 1))
    )
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
        ddf[col] = 0.0

    return ddf.repartition(npartitions=n_partitions)


# Unified partition processing function (combining mortality, fertility, diagnosis, cost/QALY)
# Moved to module scope to avoid closure overhead.
def process_population_partition(
    df,
    params,
    arm,
    year,
    seed_offset,
    partition_info,
    abs_mort_scattered_func,
    life_exp_np_scattered_func,
    emp_np_scattered_func,
    morb_keys_scattered_func,
    age_dist_scattered_func,
    fert_rates_df_scattered_func,
    mortality_rand_dask_slice,
    fertility_rand_dask_slice,
    diag_rand_dask_slice,
    morb_rand_base_dask_slice,
):
    if df.empty:
        return _POPULATION_META.iloc[0:0]

    # --- 1. Mortality ---
    ages = df["age"].values.astype(np.int64)
    sev = df["severity"].values.astype(np.int64)
    age_indices = np.clip((ages // 5).astype(int), 0, len(abs_mort_scattered_func) - 1)

    # Correctly calculate survival probability
    death_prob = abs_mort_scattered_func[age_indices] * params["MORT_HR"][sev]

    # Use the sliced random array for this partition
    mortality_mask = mortality_rand_dask_slice < death_prob

    # Additional condition for life expectancy
    life_exp_mask = ages >= life_exp_np_scattered_func[sev]

    # Combine masks: a person dies if the random draw is less than the death probability OR they are past their life expectancy
    combined_mortality_mask = mortality_mask | life_exp_mask

    # Keep individuals who are NOT in the combined_mortality_mask
    df = df[~combined_mortality_mask].copy()

    if df.empty:
        return _POPULATION_META.iloc[0:0]

    # --- 2. Fertility (Baby Generation) ---
    moms_partition = df[(df["sex"] == 0) & (df["age"].between(15, 45))]
    babies_df_part = pd.DataFrame(columns=_POPULATION_META.columns)

    if not moms_partition.empty:
        fert_rates_df_actual = fert_rates_df_scattered_func.copy()
        fert_rates_df_actual["rate"] *= params["FERTILITY_MULTIPLIER"]

        mr = moms_partition.merge(
            fert_rates_df_actual, on=["severity", "age"], how="left"
        ).fillna(0)

        if len(mr) > 0:
            # Use the sliced fertility random array
            birth_mask = (
                fertility_rand_dask_slice.loc[moms_partition.index] < mr["rate"].values
            )
            n_births_this_partition = birth_mask.sum()

            if n_births_this_partition > 0:
                # Generate babies directly into a DataFrame
                babies_data = {
                    "age": np.zeros(n_births_this_partition, dtype="int64"),
                    "sex": np.random.choice([0, 1], size=n_births_this_partition),
                    "severity": np.random.choice(
                        [0, 1], size=n_births_this_partition, p=params["SEVERITY_DIST"]
                    ),
                    "familial": mr["familial"].values[birth_mask],
                    "diagnosed": np.zeros(n_births_this_partition, dtype="bool"),
                    "living": np.random.choice(
                        [0, 1, 2, 3],
                        size=n_births_this_partition,
                        p=[0.2, 0.1, 0.3, 0.4],
                    ),
                    "employment": np.random.choice(
                        [0, 1, 2], size=n_births_this_partition, p=[0.7, 0.2, 0.1]
                    ),
                    "uses_respite": np.random.random(n_births_this_partition) < 0.3,
                    "needs_mobility": np.random.random(n_births_this_partition) < 0.2,
                    "support": np.random.choice(
                        [0, 1, 2], size=n_births_this_partition, p=[0.5, 0.3, 0.2]
                    ),
                    "ses": np.random.choice(5, size=n_births_this_partition),
                    "school": -1,  # Babies start at age 0, so school is -1
                }

                # Initialize cost/QALY columns to 0.0
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
                    babies_data[col] = 0.0

                babies_df_part = pd.DataFrame(
                    babies_data, columns=_POPULATION_META.columns
                )

    if not babies_df_part.empty:
        df = pd.concat([df, babies_df_part], ignore_index=True)

    # --- 3. Diagnosis ---
    if arm == "prospective":
        mask_undiagnosed_familial = (
            (~df["diagnosed"]) & df["familial"] & (df["age"] >= params["min_test_age"])
        )
        if mask_undiagnosed_familial.any():
            # Use the sliced diagnosis random array
            df.loc[mask_undiagnosed_familial, "diagnosed"] = (
                diag_rand_dask_slice[mask_undiagnosed_familial] < params["yield_wgs"]
            )

    # --- 4. Age Increment ---
    df["age"] += 1

    # --- 5. Cost and QALY Calculation ---
    n = len(df)
    disc = 1 / ((1 + params["DISCOUNT"]) ** (year - START_YEAR))
    sev = df["severity"].values.astype(np.int64)
    ages = df["age"].values.astype(np.float64)

    hc = (
        params["COST_INP_NP"][sev]
        + params["COST_OUTP_NP"][sev]
        + params["COST_PHARM_NP"][sev]
    ) * disc
    rc = df["uses_respite"].values.astype(int) * params["RESPITE"] * disc
    mc = -df["needs_mobility"].values.astype(int) * params["MOBILITY"] * disc
    wc = params["WELFARE_NP"][sev] * disc
    emp_idx = df["employment"].values.astype(np.int64)
    emp = emp_np_scattered_func[emp_idx] * disc

    ec = np.zeros(n, dtype=np.float64)
    m0 = df["school"] == 0
    m1 = df["school"] == 1
    if m0.any():
        ec[m0] = params["EDU"][0, df.loc[m0, "support"].values.astype(np.int64)] * disc
    if m1.any():
        ec[m1] = params["EDU"][1, df.loc[m1, "support"].values.astype(np.int64)] * disc

    morb_probs_array = np.array(
        [params["MORB_PROB"][k] for k in morb_keys_scattered_func]
    )
    # Use the sliced morbidity random array
    morbid_mat = morb_rand_base_dask_slice.values[:, None] < morb_probs_array[None, :]
    morb_cost_base = (morbid_mat * params["MORB_COST_NP"]).sum(axis=1) * disc

    if arm == "prospective":
        morb_cost_wgs_adj = (
            df["diagnosed"].values.astype(np.float64)
            * params["WGS_DIAG_COST_ADJUSTMENT"]
            * disc
        )
    else:
        morb_cost_wgs_adj = np.zeros(n, dtype=np.float64)
    df["cost_morbidity"] = morb_cost_base + morb_cost_wgs_adj

    morb_qaly_base = (morbid_mat * params["MORB_QALY_NP"]).sum(axis=1) * disc
    uq = params["U_BASE_NP"][sev] * np.exp(
        -params["U_DECAY"] * np.clip(ages - 20, 0, None)
    )
    diag_qaly_adj = df["diagnosed"].values.astype(np.float64) * params["U_DIAG"]
    carer_qaly_adj = params["U_CARER"]
    total_qaly = (uq + diag_qaly_adj + carer_qaly_adj) * disc - morb_qaly_base

    if arm == "prospective":
        total_qaly_wgs_adj = (
            df["diagnosed"].values.astype(np.float64)
            * params["WGS_DIAG_QALY_ADJUSTMENT"]
            * disc
        )
    else:
        total_qaly_wgs_adj = np.zeros(n, dtype=np.float64)
    df["annual_qaly"] = total_qaly + total_qaly_wgs_adj

    df["cost_health"] = hc
    df["cost_edu"] = ec
    df["cost_respite"] = rc
    df["cost_mobility"] = mc
    df["cost_welfare"] = wc
    df["cost_emp"] = emp
    df["annual_cost"] = hc + ec + rc + mc + wc + emp + df["cost_morbidity"]

    return df


# %% [markdown]
## 4. Population System (Dask)


class PopulationSystemDask:
    def __init__(
        self,
        pop_size,
        current_params,
        arm="prospective",
        seed_offset=0,
        n_partitions=1,
        abs_mort_scattered=None,
        life_exp_np_scattered=None,
        emp_np_scattered=None,
        morb_keys_scattered=None,
        age_dist_scattered=None,
        fert_rates_df_scattered=None,
    ):
        self.arm = arm
        self.params = current_params
        self.seed_offset = seed_offset
        self.abs_mort_scattered = abs_mort_scattered
        self.life_exp_np_scattered = life_exp_np_scattered
        self.emp_np_scattered = emp_np_scattered
        self.morb_keys_scattered = morb_keys_scattered
        self.age_dist_scattered = age_dist_scattered
        self.fert_rates_df_scattered = fert_rates_df_scattered

        self.pop = gen_population_dask(
            pop_size,
            self.params,
            arm,
            seed=self.seed_offset,
            n_partitions=n_partitions,
            age_dist_scattered_func=self.age_dist_scattered,
        ).persist()
        _ = self.pop.head(0)

    def step(
        self,
        year,
        mortality_rand_dask,
        fertility_rand_dask,
        diag_rand_dask,
        morb_rand_base_dask,
    ):
        # Pass slices of the global random arrays to map_partitions
        self.pop = self.pop.map_partitions(
            process_population_partition,
            self.params,
            self.arm,
            year,
            self.seed_offset,
            abs_mort_scattered_func=self.abs_mort_scattered,
            life_exp_np_scattered_func=self.life_exp_np_scattered,
            emp_np_scattered_func=self.emp_np_scattered,
            morb_keys_scattered_func=self.morb_keys_scattered,
            age_dist_scattered_func=self.age_dist_scattered,
            fert_rates_df_scattered_func=self.fert_rates_df_scattered,
            mortality_rand_dask_slice=mortality_rand_dask,
            fertility_rand_dask_slice=fertility_rand_dask,
            diag_rand_dask_slice=diag_rand_dask,
            morb_rand_base_dask_slice=morb_rand_base_dask,
            meta=self.pop._meta,
        ).persist()

        annual_cost_sum = self.pop["annual_cost"].sum()
        annual_qaly_sum = self.pop["annual_qaly"].sum()
        cost_health_sum = self.pop["cost_health"].sum()
        cost_edu_sum = self.pop["cost_edu"].sum()
        cost_respite_sum = self.pop["cost_respite"].sum()
        cost_mobility_sum = self.pop["cost_mobility"].sum()
        cost_welfare_sum = self.pop["cost_welfare"].sum()
        cost_emp_sum = self.pop["cost_emp"].sum()
        cost_morbidity_sum = self.pop["cost_morbidity"].sum()
        pop_size_current = self.pop.age.count()
        ses_qs_delayed = {
            f"ses_q{i}_pct": (self.pop["ses"] == i).mean() * 100 for i in range(5)
        }

        return {
            "annual_sums": {
                "annual_cost": annual_cost_sum,
                "annual_qaly": annual_qaly_sum,
                "cost_health": cost_health_sum,
                "cost_edu": cost_edu_sum,
                "cost_respite": cost_respite_sum,
                "cost_mobility": cost_mobility_sum,
                "cost_welfare": cost_welfare_sum,
                "cost_emp": cost_emp_sum,
                "cost_morbidity": cost_morbidity_sum,
            },
            "ses_qs": ses_qs_delayed,
            "population_size": pop_size_current,
        }


# %% [markdown]
## 5. Run Helpers


def run_sim(
    sampled_params,
    pop_size,
    seed_idx,
    n_partitions_per_sim,
    abs_mort_scattered_func,
    life_exp_np_scattered_func,
    emp_np_scattered_func,
    morb_keys_scattered_func,
    age_dist_scattered_func,
    fert_rates_df_scattered_func,
    mortality_rand_dask_global,
    fertility_rand_dask_global,
    diag_rand_dask_global,
    morb_rand_base_dask_global,
):
    dask_params = prepare_dask_params(sampled_params)

    sim_r = PopulationSystemDask(
        pop_size,
        dask_params,
        "retrospective",
        seed_offset=seed_idx,
        n_partitions=n_partitions_per_sim,
        abs_mort_scattered=abs_mort_scattered_func,
        life_exp_np_scattered=life_exp_np_scattered_func,
        emp_np_scattered=emp_np_scattered_func,
        morb_keys_scattered=morb_keys_scattered_func,
        age_dist_scattered=age_dist_scattered_func,
        fert_rates_df_scattered=fert_rates_df_scattered_func,
    )
    sim_p = PopulationSystemDask(
        pop_size,
        dask_params,
        "prospective",
        seed_offset=seed_idx + 100000,
        n_partitions=n_partitions_per_sim,
        abs_mort_scattered=abs_mort_scattered_func,
        life_exp_np_scattered=life_exp_np_scattered_func,
        emp_np_scattered=emp_np_scattered_func,
        morb_keys_scattered=morb_keys_scattered_func,
        age_dist_scattered=age_dist_scattered_func,
        fert_rates_df_scattered=fert_rates_df_scattered_func,
    )

    total_cost_r_delayed = 0.0
    total_qaly_r_delayed = 0.0
    total_cost_p_delayed = 0.0
    total_qaly_p_delayed = 0.0

    for i, yr in enumerate(YEARS):
        # Calculate slice for the current year
        start_idx = i * pop_size
        end_idx = (i + 1) * pop_size

        yearly_data_r_delayed = sim_r.step(
            yr,
            mortality_rand_dask_global[start_idx:end_idx],
            fertility_rand_dask_global[start_idx:end_idx],
            diag_rand_dask_global[start_idx:end_idx],
            morb_rand_base_dask_global[start_idx:end_idx],
        )
        total_cost_r_delayed += yearly_data_r_delayed["annual_sums"]["annual_cost"]
        total_qaly_r_delayed += yearly_data_r_delayed["annual_sums"]["annual_qaly"]

        yearly_data_p_delayed = sim_p.step(
            yr,
            mortality_rand_dask_global[start_idx:end_idx],
            fertility_rand_dask_global[start_idx:end_idx],
            diag_rand_dask_global[start_idx:end_idx],
            morb_rand_base_dask_global[start_idx:end_idx],
        )
        total_cost_p_delayed += yearly_data_p_delayed["annual_sums"]["annual_cost"]
        total_qaly_p_delayed += yearly_data_p_delayed["annual_sums"]["annual_qaly"]

    return (
        total_cost_p_delayed - total_cost_r_delayed,
        total_qaly_p_delayed - total_qaly_r_delayed,
    )


def run_scenario(
    sampled_params,
    pop_size,
    seed_offset,
    n_partitions_per_sim,
    abs_mort_scattered_func,
    life_exp_np_scattered_func,
    emp_np_scattered_func,
    morb_keys_scattered_func,
    age_dist_scattered_func,
    fert_rates_df_scattered_func,
    mortality_rand_dask_global,
    fertility_rand_dask_global,
    diag_rand_dask_global,
    morb_rand_base_dask_global,
):
    dask_params = prepare_dask_params(sampled_params)

    sim_r = PopulationSystemDask(
        pop_size,
        dask_params,
        "retrospective",
        seed_offset=seed_offset,
        n_partitions=n_partitions_per_sim,
        abs_mort_scattered=abs_mort_scattered_func,
        life_exp_np_scattered=life_exp_np_scattered_func,
        emp_np_scattered=emp_np_scattered_func,
        morb_keys_scattered=morb_keys_scattered_func,
        age_dist_scattered=age_dist_scattered_func,
        fert_rates_df_scattered=fert_rates_df_scattered_func,
    )
    sim_p = PopulationSystemDask(
        pop_size,
        dask_params,
        "prospective",
        seed_offset=seed_offset + 200000,
        n_partitions=n_partitions_per_sim,
        abs_mort_scattered=abs_mort_scattered_func,
        life_exp_np_scattered=life_exp_np_scattered_func,
        emp_np_scattered=emp_np_scattered_func,
        morb_keys_scattered=morb_keys_scattered_func,
        age_dist_scattered=age_dist_scattered_func,
        fert_rates_df_scattered=fert_rates_df_scattered_func,
    )

    yearly_data_delayed_list = []
    final_cost_r_delayed = 0.0
    final_qaly_r_delayed = 0.0
    final_cost_p_delayed = 0.0
    final_qaly_p_delayed = 0.0
    cumulative_cost_r_delayed = 0.0
    cumulative_qaly_r_delayed = 0.0
    cumulative_cost_p_delayed = 0.0
    cumulative_qaly_p_delayed = 0.0

    for i, yr in enumerate(YEARS):
        start_idx = i * pop_size
        end_idx = (i + 1) * pop_size

        yearly_info_r_delayed = sim_r.step(
            yr,
            mortality_rand_dask_global[start_idx:end_idx],
            fertility_rand_dask_global[start_idx:end_idx],
            diag_rand_dask_global[start_idx:end_idx],
            morb_rand_base_dask_global[start_idx:end_idx],
        )
        yearly_info_p_delayed = sim_p.step(
            yr,
            mortality_rand_dask_global[start_idx:end_idx],
            fertility_rand_dask_global[start_idx:end_idx],
            diag_rand_dask_global[start_idx:end_idx],
            morb_rand_base_dask_global[start_idx:end_idx],
        )

        final_cost_r_delayed += yearly_info_r_delayed["annual_sums"]["annual_cost"]
        final_qaly_r_delayed += yearly_info_r_delayed["annual_sums"]["annual_qaly"]
        final_cost_p_delayed += yearly_info_p_delayed["annual_sums"]["annual_cost"]
        final_qaly_p_delayed += yearly_info_p_delayed["annual_sums"]["annual_qaly"]

        cumulative_cost_r_delayed += yearly_info_r_delayed["annual_sums"]["annual_cost"]
        cumulative_qaly_r_delayed += yearly_info_r_delayed["annual_sums"]["annual_qaly"]
        cumulative_cost_p_delayed += yearly_info_p_delayed["annual_sums"]["annual_cost"]
        cumulative_qaly_p_delayed += yearly_info_p_delayed["annual_sums"]["annual_qaly"]

        yearly_data_delayed_list.append(
            dask.delayed(
                {
                    "arm": "retrospective",
                    "year": yr,
                    "annual_cost": yearly_info_r_delayed["annual_sums"]["annual_cost"],
                    "cost_health": yearly_info_r_delayed["annual_sums"]["cost_health"],
                    "cost_edu": yearly_info_r_delayed["annual_sums"]["cost_edu"],
                    "cost_respite": yearly_info_r_delayed["annual_sums"][
                        "cost_respite"
                    ],
                    "cost_mobility": yearly_info_r_delayed["annual_sums"][
                        "cost_mobility"
                    ],
                    "cost_welfare": yearly_info_r_delayed["annual_sums"][
                        "cost_welfare"
                    ],
                    "cost_emp": yearly_info_r_delayed["annual_sums"]["cost_emp"],
                    "cost_morbidity": yearly_info_r_delayed["annual_sums"][
                        "cost_morbidity"
                    ],
                    "annual_qaly": yearly_info_r_delayed["annual_sums"]["annual_qaly"],
                    "population_size": yearly_info_r_delayed["population_size"],
                    "costs": cumulative_cost_r_delayed,
                    "qalys": cumulative_qaly_r_delayed,
                    **yearly_info_r_delayed["ses_qs"],
                }
            )
        )

        yearly_data_delayed_list.append(
            dask.delayed(
                {
                    "arm": "prospective",
                    "year": yr,
                    "annual_cost": yearly_info_p_delayed["annual_sums"]["annual_cost"],
                    "cost_health": yearly_info_p_delayed["annual_sums"]["cost_health"],
                    "cost_edu": yearly_info_p_delayed["annual_sums"]["cost_edu"],
                    "cost_respite": yearly_info_p_delayed["annual_sums"][
                        "cost_respite"
                    ],
                    "cost_mobility": yearly_info_p_delayed["annual_sums"][
                        "cost_mobility"
                    ],
                    "cost_welfare": yearly_info_p_delayed["annual_sums"][
                        "cost_welfare"
                    ],
                    "cost_emp": yearly_info_p_delayed["annual_sums"]["cost_emp"],
                    "cost_morbidity": yearly_info_p_delayed["annual_sums"][
                        "cost_morbidity"
                    ],
                    "annual_qaly": yearly_info_p_delayed["annual_sums"]["annual_qaly"],
                    "population_size": yearly_info_p_delayed["population_size"],
                    "costs": cumulative_cost_p_delayed,
                    "qalys": cumulative_qaly_p_delayed,
                    **yearly_info_p_delayed["ses_qs"],
                }
            )
        )

    results_df = dask.delayed(pd.DataFrame)(yearly_data_delayed_list)

    return (
        final_cost_p_delayed - final_cost_r_delayed,
        final_qaly_p_delayed - final_qaly_r_delayed,
        results_df,
    )


# %% [markdown]
## 6. Deterministic Scenarios

print("--- Running Module 6: Deterministic Scenarios ---")
# Retrieve DISTRIBUTIONS from scattered object
local_distributions = client.gather(scattered_distributions)

base_mean_params = {}
for k, v in local_distributions.items():  # Use local_distributions
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

# Scatter base_mean_params as it's used frequently and is constant
scattered_base_mean_params = client.scatter(base_mean_params, broadcast=True)

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

# 1) Parallelize the three scenarios
scenario_args = []
for name, specific_override_params in scenarios.items():
    p = base_mean_params.copy()
    p.update(specific_override_params)
    seed = hash(name) % (2**32 - 1)
    # For deterministic runs, a single partition is often sufficient or optimal,
    # or can be set to `n_workers` for better load balancing for larger populations.
    scenario_args.append((p, 20000, seed, 1))

# 2) Kick them off in parallel without profiling
# Unpack arguments for client.map
params, pop_sizes, seeds, parts = zip(*scenario_args)
# Pass scattered constant objects to run_sim using keyword arguments
futures = client.map(
    run_sim,
    params,
    pop_sizes,
    seeds,
    parts,
    abs_mort_scattered_func=scattered_abs_mort,
    life_exp_np_scattered_func=scattered_life_exp_np,
    emp_np_scattered_func=scattered_emp_np,
    morb_keys_scattered_func=scattered_morb_keys,
    age_dist_scattered_func=scattered_age_dist,
    fert_rates_df_scattered_func=scattered_fert_rates_df,
    mortality_rand_dask_global=mortality_rand_global,
    fertility_rand_dask_global=fertility_rand_global,
    diag_rand_dask_global=diag_rand_global,
    morb_rand_base_dask_global=morb_rand_base_global,
)
deterministic_results_raw = client.gather(futures)

# 3) Build your DataFrame
deterministic_results = []
for i, (dc, dq) in enumerate(deterministic_results_raw):
    scenario_name = list(scenarios.keys())[i]
    deterministic_results.append(
        {
            "scenario": scenario_name,
            "dCost": dc,
            "dQALY": dq,
            "ICER": dc / dq if dq else np.nan,
        }
    )

det_df = pd.DataFrame(deterministic_results)


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

print(f"Dask dashboard link: {client.dashboard_link}")
print(f"Running {psa_n} PSA simulations in parallel using Dask...")

# Dynamic number of partitions based on client's total threads
n_workers = len(client.scheduler_info()["workers"])
# Experiment with psa_n_partitions. The "sweet spot" is often 2x, 4x, or even 8x `n_workers`.
# Consider trying: `2 * n_workers`, `4 * n_workers`, `8 * n_workers`.
psa_n_partitions = n_workers  # Default to n_workers, adjust for tuning

with performance_report(
    filename="psa_sim_report.html"
), Profiler() as prof_psa, ResourceProfiler() as rprof_psa, CacheProfiler() as cprof_psa:
    psa_args = []
    # Retrieve DISTRIBUTIONS from scattered object
    local_distributions_for_psa = client.gather(scattered_distributions)
    for i in range(psa_n):
        sampled_params = sample_params_from_dist(local_distributions_for_psa, seed=i)
        psa_args.append((sampled_params, 8000, i, psa_n_partitions))

    # Unpack arguments for client.map
    psa_params, psa_sizes, psa_seeds, psa_parts = zip(*psa_args)
    # Pass scattered constant objects to run_sim using keyword arguments
    futures = client.map(
        run_sim,
        psa_params,
        psa_sizes,
        psa_seeds,
        psa_parts,
        abs_mort_scattered_func=scattered_abs_mort,
        life_exp_np_scattered_func=scattered_life_exp_np,
        emp_np_scattered_func=scattered_emp_np,
        morb_keys_scattered_func=scattered_morb_keys,
        age_dist_scattered_func=scattered_age_dist,
        fert_rates_df_scattered_func=scattered_fert_rates_df,
        mortality_rand_dask_global=mortality_rand_global,
        fertility_rand_dask_global=fertility_rand_global,
        diag_rand_dask_global=diag_rand_global,
        morb_rand_base_dask_global=morb_rand_base_global,
    )
    progress(futures)

    results = client.gather(futures)

print("\nGenerating Dask diagnostic plots for PSA...")
try:
    prof_psa.visualize(filename="profiler_plot_psa.html", format="html")
    rprof_psa.visualize(filename="resource_profiler_plot_psa.html", format="html")
    cprof_psa.visualize(filename="cache_profiler_plot_psa.html", format="html")
    print("Profiler plots for PSA saved as HTML files.")
except Exception as e:
    print(
        f"Error generating diagnostic plots for PSA: {e}. Ensure graphviz is installed for full functionality."
    )

psa_out = []
for i, (dc, dq) in enumerate(results):
    original_sampled_params = psa_args[i][0]
    row_data = {"run": i, "dCost": dc, "dQALY": dq}
    row_data.update(original_sampled_params)
    psa_out.append(row_data)

psa_df_pd = pd.DataFrame(psa_out)
psa_df_pd.to_csv("psa_samples.csv", index=False)
print("PSA results saved to psa_samples.csv")

psa_df = dd.from_pandas(psa_df_pd, npartitions=n_workers)  # Also make this dynamic


# %% [markdown]
## 8. CE-Plane, CEAC, EVPI & ENMB

print("\n--- Running Module 8: CE-Plane, CEAC, EVPI & ENMB ---")
wtp = np.linspace(0, 150000, 40)
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
# Retrieve base_mean_params from scattered object
base_params = client.gather(scattered_base_mean_params)
local_distributions_for_tornado = client.gather(scattered_distributions)

# Experiment with tornado_n_partitions. The "sweet spot" is often 2x, 4x, or even 8x `n_workers`.
# Consider trying: `2 * n_workers`, `4 * n_workers`, `8 * n_workers`.
tornado_n_partitions = n_workers  # Default to n_workers, adjust for tuning

with performance_report(
    filename="tornado_sim_report.html"
), Profiler() as prof_tornado, ResourceProfiler() as rprof_tornado, CacheProfiler() as cprof_tornado:
    # run_sim is called directly, not via client.map/starmap here
    # This single run will compute immediately as its final compute is inside run_sim
    base_dc, base_dq = dask.compute(
        run_sim(
            base_params,
            pop_size=10000,
            seed_idx=1,
            n_partitions_per_sim=tornado_n_partitions,
            abs_mort_scattered_func=scattered_abs_mort,
            life_exp_np_scattered_func=scattered_life_exp_np,
            emp_np_scattered_func=scattered_emp_np,
            morb_keys_scattered_func=scattered_morb_keys,
            age_dist_scattered_func=scattered_age_dist,
            fert_rates_df_scattered_func=scattered_fert_rates_df,
            mortality_rand_dask_global=mortality_rand_global,
            fertility_rand_dask_global=fertility_rand_global,
            diag_rand_dask_global=diag_rand_global,
            morb_rand_base_dask_global=morb_rand_base_global,
        )
    )
    base_icer = base_dc / base_dq if base_dq != 0 else 0

    tornado_params_to_vary = ["familial_prop", "yield_wgs", "u_diag", "cost_inp_severe"]

    tornado_sim_args = []
    for i, param_name in enumerate(tornado_params_to_vary):
        p_temp_low = base_params.copy()
        p_temp_high = base_params.copy()

        dist_info = local_distributions_for_tornado[
            param_name
        ]  # Use local_distributions
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
        elif dist_info["dist"] == "lognormal":
            mean_val = dist_info["scale"] * np.exp(dist_info["s"] ** 2 / 2)
            low_val, high_val = (
                mean_val * 0.90,
                mean_val * 1.10,
            )  # Using arbitrary 10% variation for lognormal for now
        elif dist_info["dist"] == "normal":
            mean_val = dist_info["loc"]
            std_dev = dist_info["scale"]
            low_val, high_val = mean_val - 2 * std_dev, mean_val + 2 * std_dev
        elif dist_info["dist"] == "uniform":
            mean_val = (dist_info["low"] + dist_info["high"]) / 2
            low_val, high_val = dist_info["low"], dist_info["high"]
        elif dist_info["dist"] == "fixed":
            mean_val = dist_info["value"]
            low_val, high_val = mean_val, mean_val
        else:
            continue

        p_temp_low[param_name] = low_val
        tornado_sim_args.append((p_temp_low, 10000, 100 + i * 2, tornado_n_partitions))

        p_temp_high[param_name] = high_val
        tornado_sim_args.append(
            (p_temp_high, 10000, 100 + i * 2 + 1, tornado_n_partitions)
        )

    # Unpack arguments for client.map
    tornado_params, tornado_sizes, tornado_seeds, tornado_parts = zip(*tornado_sim_args)
    # Pass scattered constant objects to run_sim using keyword arguments
    futures_tornado = client.map(
        run_sim,
        tornado_params,
        tornado_sizes,
        tornado_seeds,
        tornado_parts,
        abs_mort_scattered_func=scattered_abs_mort,
        life_exp_np_scattered_func=scattered_life_exp_np,
        emp_np_scattered_func=scattered_emp_np,
        morb_keys_scattered_func=scattered_morb_keys,
        age_dist_scattered_func=scattered_age_dist,
        fert_rates_df_scattered_func=scattered_fert_rates_df,
        mortality_rand_dask_global=mortality_rand_global,
        fertility_rand_dask_global=fertility_rand_global,
        diag_rand_dask_global=diag_rand_global,
        morb_rand_base_dask_global=morb_rand_base_global,
    )
    tornado_results = client.gather(futures_tornado)

    result_idx = 0
    for i, param_name in enumerate(tornado_params_to_vary):
        dc_low, dq_low = tornado_results[result_idx]
        icer_low = (dc_low / dq_low) if dq_low != 0 else 0
        tornado.append({"param": param_name, "change_type": "Low", "ICER": icer_low})
        result_idx += 1

        dc_high, dq_high = tornado_results[result_idx]
        icer_high = (dc_high / dq_high) if dq_high != 0 else 0
        tornado.append({"param": param_name, "change_type": "High", "ICER": icer_high})
        result_idx += 1

print("\nGenerating Dask diagnostic plots for Tornado Analysis...")
try:
    prof_tornado.visualize(filename="profiler_plot_tornado.html", format="html")
    rprof_tornado.visualize(
        filename="resource_profiler_plot_tornado.html", format="html"
    )
    cprof_tornado.visualize(filename="cache_profiler_plot_tornado.html", format="html")
    print("Profiler plots for Tornado Analysis saved as HTML files.")
except Exception as e:
    print(
        f"Error generating diagnostic plots for Tornado Analysis: {e}. Ensure graphviz is installed for full functionality."
    )


tor_df = pd.DataFrame(tornado)
tor_df["ICER_diff"] = tor_df["ICER"] - base_icer
tor_df["abs_diff"] = tor_df["ICER_diff"].abs()
tor_df = tor_df.sort_values(by="abs_diff", ascending=True)

plt.figure(figsize=(10, 8))  # Increased figure size for better readability
labels = [f"{row['param']} ({row['change_type']})" for idx, row in tor_df.iterrows()]
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
# Retrieve mean_params_for_subgroup from scattered object
mean_params_for_subgroup = client.gather(scattered_base_mean_params)

# Experiment with subgroup_n_partitions. The "sweet spot" is often 2x, 4x, or even 8x `n_workers`.
# Consider trying: `2 * n_workers`, `4 * n_workers`, `8 * n_workers`.
subgroup_n_partitions = n_workers  # Default to n_workers, adjust for tuning

with performance_report(
    filename="subgroup_sim_report.html"
), Profiler() as prof_subgroup, ResourceProfiler() as rprof_subgroup, CacheProfiler() as cprof_subgroup:
    # Execute the full scenario run once to get the mix_data for horizons
    # This will compute yearly results for plotting horizon effects
    _, _, mix_data_for_subgroup = dask.compute(
        run_scenario(
            mean_params_for_subgroup,
            pop_size=15000,
            seed_offset=400,
            n_partitions_per_sim=subgroup_n_partitions,
            abs_mort_scattered_func=scattered_abs_mort,
            life_exp_np_scattered_func=scattered_life_exp_np,
            emp_np_scattered_func=scattered_emp_np,
            morb_keys_scattered_func=scattered_morb_keys,
            age_dist_scattered_func=scattered_age_dist,
            fert_rates_df_scattered_func=scattered_fert_rates_df,
            mortality_rand_dask_global=mortality_rand_global,
            fertility_rand_dask_global=fertility_rand_global,
            diag_rand_dask_global=diag_rand_global,
            morb_rand_base_dask_global=morb_rand_base_global,
        )
    )

    dfp = mix_data_for_subgroup[mix_data_for_subgroup["arm"] == "prospective"]
    dfr = mix_data_for_subgroup[mix_data_for_subgroup["arm"] == "retrospective"]
    for yrs_n in [10, 20, len(YEARS)]:
        yr = START_YEAR + yrs_n - 1
        if yr in dfp["year"].values and yr in dfr["year"].values:
            c1 = float(dfp.loc[dfp["year"] == yr, "costs"].item())
            c0 = float(dfr.loc[dfr["year"] == yr, "costs"].item())
            q1 = float(dfp.loc[dfp["year"] == yr, "qalys"].item())
            q0 = float(dfr.loc[dfr["year"] == yr, "qalys"].item())
            dc, dq = (c1 - c0), (q1 - q0)
            sg.append(
                {"group": f"Horizon: {yrs_n} yrs", "ICER": (dc / dq) if dq != 0 else 0}
            )

    subgroup_sim_args = []
    for i, (sev_prop, label) in enumerate([(1.0, "Mild Only"), (0.0, "Severe Only")]):
        p_temp = mean_params_for_subgroup.copy()
        p_temp["severity_mild_prop"] = sev_prop
        # Ensure 'severity_severe_prop' is also set correctly when 'severity_mild_prop' is overridden
        p_temp["severity_severe_prop"] = (
            1.0 - sev_prop
            if sev_prop >= 0 and sev_prop <= 1
            else (1.0 - p_temp.get("severity_mild_prop", 0.7))
        )
        subgroup_sim_args.append(
            (
                p_temp,
                15000,
                200 + i,
                subgroup_n_partitions,
                abs_mort_scattered_func,
                life_exp_np_scattered_func,
                emp_np_scattered_func,
                morb_keys_scattered_func,
                age_dist_scattered_func,
                fert_rates_df_scattered_func,
                mortality_rand_global,
                fertility_rand_global,
                diag_rand_global,
                morb_rand_base_dask_global,
            )
        )

    for i, age in enumerate([0, 18, 30]):
        p_temp = mean_params_for_subgroup.copy()
        p_temp["min_test_age"] = age
        subgroup_sim_args.append(
            (
                p_temp,
                15000,
                300 + i,
                subgroup_n_partitions,
                abs_mort_scattered_func,
                life_exp_np_scattered_func,
                emp_np_scattered_func,
                morb_keys_scattered_func,
                age_dist_scattered_func,
                fert_rates_df_scattered_func,
                mortality_rand_global,
                fertility_rand_global,
                diag_rand_global,
                morb_rand_base_dask_global,
            )
        )

    # Execute the run_sim calls for severity and min_test_age
    subgroup_params, subgroup_sizes, subgroup_seeds, subgroup_parts = zip(
        *subgroup_sim_args
    )
    futures_subgroup = client.map(
        run_sim,
        subgroup_params,
        subgroup_sizes,
        subgroup_seeds,
        subgroup_parts,
        abs_mort_scattered_func=scattered_abs_mort,
        life_exp_np_scattered_func=scattered_life_exp_np,
        emp_np_scattered_func=scattered_emp_np,
        morb_keys_scattered_func=scattered_morb_keys,
        age_dist_scattered_func=scattered_age_dist,
        fert_rates_df_scattered_func=scattered_fert_rates_df,
        mortality_rand_dask_global=mortality_rand_global,
        fertility_rand_dask_global=fertility_rand_global,
        diag_rand_dask_global=diag_rand_global,
        morb_rand_base_dask_global=morb_rand_base_global,
    )
    subgroup_results_sims = client.gather(futures_subgroup)

    # Populate sg list with results from run_sim calls
    sim_idx = 0
    for i, (sev_prop, label) in enumerate([(1.0, "Mild Only"), (0.0, "Severe Only")]):
        dc, dq = subgroup_results_sims[sim_idx]
        icer = (dc / dq) if dq != 0 else 0
        sg.append({"group": f"Severity: {label}", "ICER": icer})
        sim_idx += 1

    for i, age in enumerate([0, 18, 30]):
        dc, dq = subgroup_results_sims[sim_idx]
        icer = (dc / dq) if dq != 0 else 0
        sg.append({"group": f"Min Test Age: {age}", "ICER": icer})
        sim_idx += 1


print("\nGenerating Dask diagnostic plots for Sub-group Analysis...")
try:
    prof_subgroup.visualize(filename="profiler_plot_subgroup.html", format="html")
    rprof_subgroup.visualize(
        filename="resource_profiler_plot_subgroup.html", format="html"
    )
    cprof_subgroup.visualize(
        filename="cache_profiler_plot_subgroup.html", format="html"
    )
    print("Profiler plots for Sub-group Analysis saved as HTML files.")
except Exception as e:
    print(
        f"Error generating diagnostic plots for Sub-group Analysis: {e}. Ensure graphviz is installed for full functionality."
    )

# Use the scattered base_mean_params directly
base_dc_subgroup, base_dq_subgroup = dask.compute(
    run_sim(
        client.gather(scattered_base_mean_params),
        pop_size=10000,
        seed_idx=1,
        n_partitions_per_sim=subgroup_n_partitions,
        abs_mort_scattered_func=scattered_abs_mort,
        life_exp_np_scattered_func=scattered_life_exp_np,
        emp_np_scattered_func=scattered_emp_np,
        morb_keys_scattered_func=scattered_morb_keys,
        age_dist_scattered_func=scattered_age_dist,
        fert_rates_df_scattered_func=scattered_fert_rates_df,
        mortality_rand_dask_global=mortality_rand_global,
        fertility_rand_dask_global=fertility_rand_global,
        diag_rand_dask_global=diag_rand_global,
        morb_rand_base_dask_global=morb_rand_base_global,
    )
)
base_icer_subgroup = base_dc_subgroup / base_dq_subgroup if base_dq_subgroup != 0 else 0

sg_df = pd.DataFrame(sg)

plt.figure(figsize=(10, 6))  # Increased figure size for better readability
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


# %% [markdown]
## 11. Cost-Mix Stacked Area (Prospective)

print("\n--- Running Module 11: Cost-Mix Stacked Area (Prospective) ---")

# Experiment with costmix_n_partitions. The "sweet spot" is often 2x, 4x, or even 8x `n_workers`.
# Consider trying: `2 * n_workers`, `4 * n_workers`, `8 * n_workers`.
costmix_n_partitions = n_workers  # Default to n_workers, adjust for tuning

with performance_report(
    filename="costmix_prospective_report.html"
), Profiler() as prof_cm_p, ResourceProfiler() as rprof_cm_p, CacheProfiler() as cprof_cm_p:
    # run_scenario is called directly, not via client.map/starmap here
    # Use the scattered base_mean_params directly
    # This will generate `mix_data` with yearly computed results needed for plotting
    _, _, mix_data = dask.compute(
        run_scenario(
            client.gather(scattered_base_mean_params),
            pop_size=20000,
            seed_offset=500,
            n_partitions_per_sim=costmix_n_partitions,
            abs_mort_scattered_func=scattered_abs_mort,
            life_exp_np_scattered_func=scattered_life_exp_np,
            emp_np_scattered_func=scattered_emp_np,
            morb_keys_scattered_func=scattered_morb_keys,
            age_dist_scattered_func=scattered_age_dist,
            fert_rates_df_scattered_func=scattered_fert_rates_df,
            mortality_rand_dask_global=mortality_rand_global,
            fertility_rand_dask_global=fertility_rand_global,
            diag_rand_dask_global=diag_rand_global,
            morb_rand_base_dask_global=morb_rand_base_global,
        )
    )

print("\nGenerating Dask diagnostic plots for Prospective Cost-Mix...")
try:
    prof_cm_p.visualize(
        filename="profiler_plot_costmix_prospective.html", format="html"
    )
    rprof_cm_p.visualize(
        filename="resource_profiler_plot_costmix_prospective.html", format="html"
    )
    cprof_cm_p.visualize(
        filename="cache_profiler_plot_costmix_prospective.html", format="html"
    )
    print("Profiler plots for Prospective Cost-Mix saved as HTML files.")
except Exception as e:
    print(
        f"Error generating diagnostic plots for Prospective Cost-Mix: {e}. Ensure graphviz is installed for full functionality."
    )


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
    pm["year"], *data, labels=[c.replace("cost_", "").capitalize() for c in cost_cols]
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
bas = mix_data[mix_data["arm"] == "prospective"]
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
# Retrieve DISTRIBUTIONS from scattered object
local_distributions_for_summary = client.gather(scattered_distributions)
for param_name, dist_info in local_distributions_for_summary.items():
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
        summary_str += f", Loc: {dist_info['loc']:.2f}, Scale: {dist_info['scale']:.2f}"
    elif dist_info["dist"] == "uniform":
        summary_str += f", Low: {dist_info['low']:.2f}, High: {dist_info['high']:.2f}"
    elif dist_info["dist"] == "fixed":
        summary_str += f", Value: {dist_info['value']:.2f}"

    param_summary_list.append(
        {"parameter": param_name, "distribution_details": summary_str}
    )

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

df_cmp = det_df.merge(pub_df, on="scenario", how="left")
df_cmp = df_cmp.rename(
    columns={"dCost": "dCost_sim", "dQALY": "dQALY_sim", "ICER": "ICER_sim"}
)  # Corrected column name here
print("Comparison of Simulation vs. Published Data:")
print(df_cmp.to_string())
df_cmp.to_csv("publication_comparison.csv", index=False)


# %% [markdown]
## 18. Familial ID Prevalence Sensitivity Analysis

print("\n--- Running Module 18: Familial ID Prevalence Sensitivity Analysis ---")
# Retrieve mean_params_for_sens from scattered object
mean_params_for_sens = client.gather(scattered_base_mean_params)
familial_prevalence_range = np.linspace(0.10, 0.23, 10)
familial_sens_results = []

# Experiment with familial_sens_n_partitions. The "sweet spot" is often 2x, 4x, or even 8x `n_workers`.
# Consider trying: `2 * n_workers`, `4 * n_workers`, `8 * n_workers`.
familial_sens_n_partitions = n_workers  # Default to n_workers, adjust for tuning

with performance_report(
    filename="familial_sens_sim_report.html"
), Profiler() as prof_fam_sens, ResourceProfiler() as rprof_fam_sens, CacheProfiler() as cprof_fam_sens:
    familial_sens_args = []
    for i, f_prop in enumerate(familial_prevalence_range):
        p_temp = mean_params_for_sens.copy()
        p_temp["familial_prop"] = f_prop
        familial_sens_args.append((p_temp, 10000, 600 + i, familial_sens_n_partitions))

    # Unpack arguments for client.map
    familial_params, familial_sizes, familial_seeds, familial_parts = zip(
        *familial_sens_args
    )
    # Pass scattered constant objects to run_sim using keyword arguments
    futures_familial_sens = client.map(
        run_sim,
        familial_params,
        familial_sizes,
        familial_seeds,
        familial_parts,
        abs_mort_scattered_func=scattered_abs_mort,
        life_exp_np_scattered_func=scattered_life_exp_np,
        emp_np_scattered_func=scattered_emp_np,
        morb_keys_scattered_func=scattered_morb_keys,
        age_dist_scattered_func=scattered_age_dist,
        fert_rates_df_scattered_func=scattered_fert_rates_df,
        mortality_rand_dask_global=mortality_rand_global,
        fertility_rand_dask_global=fertility_rand_global,
        diag_rand_dask_global=diag_rand_global,
        morb_rand_base_dask_global=morb_rand_base_global,
    )
    familial_sens_raw_results = client.gather(futures_familial_sens)

    for i, (dc, dq) in enumerate(familial_sens_raw_results):
        f_prop = familial_prevalence_range[i]
        icer = (dc / dq) if dq != 0 else 0
        familial_sens_results.append(
            {"familial_prop": f_prop, "dCost": dc, "dQALY": dq, "ICER": icer}
        )

print(
    "\nGenerating Dask diagnostic plots for Familial ID Prevalence Sensitivity Analysis..."
)
try:
    prof_fam_sens.visualize(filename="profiler_plot_familial_sens.html", format="html")
    rprof_fam_sens.visualize(
        filename="resource_profiler_plot_familial_sens.html", format="html"
    )
    cprof_fam_sens.visualize(
        filename="cache_profiler_plot_familial_sens.html", format="html"
    )
    print(
        "Profiler plots for Familial ID Prevalence Sensitivity Analysis saved as HTML files."
    )
except Exception as e:
    print(
        f"Error generating diagnostic plots for Familial ID Prevalence Sensitivity Analysis: {e}. Ensure graphviz is installed for full functionality."
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
        coeffs, residuals, rank, s = np.linalg.lstsq(X, nmb_np, rcond=None)
        nmb_predicted = X @ coeffs
        evppi_val = np.mean(np.maximum(0, nmb_np)) - np.mean(
            np.maximum(0, nmb_predicted)
        )
        evppi_values.append(evppi_val)
    return np.array(evppi_values)


parameters_for_evppi_new = ["familial_prop", "yield_wgs", "u_diag", "cost_inp_severe"]
evppi_results = {}
print("Calculating EVPPI for key parameters...")

with performance_report(
    filename="evppi_sim_report.html"
), Profiler() as prof_evppi, ResourceProfiler() as rprof_evppi, CacheProfiler() as cprof_evppi:
    # We need the full pandas DataFrame for EVPPI calculation as it uses linear regression
    # over the entire PSA dataset, not just partitions.
    dcost = psa_df["dCost"].compute().to_numpy()
    dqaly = psa_df["dQALY"].compute().to_numpy()

    for param in parameters_for_evppi_new:
        if param in psa_df_pd.columns:
            # calculate_evppi_curve is a regular function call, not via client.map/starmap
            evppi_curve = calculate_evppi_curve(psa_df_pd, param, wtp)
            evppi_results[param] = evppi_curve

print("\nGenerating Dask diagnostic plots for EVPPI Analysis...")
try:
    prof_evppi.visualize(filename="profiler_plot_evppi.html", format="html")
    rprof_evppi.visualize(filename="resource_profiler_plot_evppi.html", format="html")
    cprof_evppi.visualize(filename="cache_profiler_plot_evppi.html", format="html")
    print("Profiler plots for EVPPI Analysis saved as HTML files.")
except Exception as e:
    print(
        f"Error generating diagnostic plots for EVPPI Analysis: {e}. Ensure graphviz is installed for full functionality."
    )


if evppi_results:
    plt.figure(figsize=(10, 6))
    for param, evppi_curve_host in evppi_results.items():
        plt.plot(
            wtp, evppi_curve_host, label=f'EVPPI ({param.replace("_", " ").title()})'
        )
    plt.title("Expected Value of Partial Perfect Information (EVPPI) Curves")
    plt.xlabel("Willingness-to-Pay per QALY")
    plt.ylabel("EVPPI (£)")
    plt.legend()
    plt.grid(True)
    plt.show()

# %% [markdown]
## 20. PSA Histograms (Re-run from Module 14, consolidating)

print("\n--- Running Module 20: PSA Histograms (dCost, dQALY) ---")
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
## 21. Cost-Mix Stacked Area (Retrospective)

print("\n--- Running Module 21: Cost-Mix Stacked Area (Retrospective) ---")
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
    rm["year"], *data_r, labels=[c.replace("cost_", "").capitalize() for c in cost_cols]
)
plt.legend(loc="upper left")
plt.title("Cost Mix Over Time (Retrospective Arm - Discounted Annual Costs)")
plt.xlabel("Year")
plt.ylabel("Annual Cost")
plt.show()

print("Retrospective Cost Mix analysis complete.")

if "client" in locals():
    client.close()
    print("Dask client closed.")
if "cluster" in locals():
    cluster.close()
    print("Dask cluster closed.")
