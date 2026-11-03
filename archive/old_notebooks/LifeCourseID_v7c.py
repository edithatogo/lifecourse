# --- JAX precision configuration (added in v7c) ---
import os

os.environ.setdefault("JAX_ENABLE_X64", "True")
from jax.config import config as _jax_config

_jax_config.update("jax_enable_x64", True)
# --------------------------------------------------
import gc  # Import garbage collection module
import warnings

import dask.dataframe as dd
import jax.numpy as jnp
import matplotlib.pyplot as plt
import pandas as pd
from dask.distributed import Client, LocalCluster, progress
from jax import (  # Import config for JAX settings
    config,
    device_get,  # Import device_get for converting JAX arrays to NumPy
    jit,
    random,
)

warnings.filterwarnings("ignore")

# Enable JAX to use 64-bit floating point precision globally
config.update("jax_enable_x64", True)

# Global JAX random key for reproducible random operations
# This key will be split and passed around to maintain JAX's functional randomness.
key = random.PRNGKey(42)

# Initialize Dask cluster and client globally so they are available for all simulations
cluster = LocalCluster()
client = Client(cluster)
print(
    f"Dask dashboard link: {client.dashboard_link}"
)  # Print link early for visibility

# %% [markdown]
## 2. Global Parameters & Dask Constants and Parameter Distributions

START_YEAR, END_YEAR = 2020, 2100
YEARS = list(range(START_YEAR, END_YEAR + 1))
DISCOUNT = 0.035  # Fixed
POP_SIZE = 62000  # Fixed (this is the original POP_SIZE, can be overridden in run_sim/run_scenario)

# Costs are based on 2017 values from the paper, adjust to START_YEAR (2020)
COST_REFERENCE_YEAR = 2017  # Fixed
INFLATION_RATE = 0.03  # Fixed
INFLATION_FACTOR = (1 + INFLATION_RATE) ** (START_YEAR - COST_REFERENCE_YEAR)  # Fixed

# Demographics - mostly fixed or handled by sampling
# SEVERITY_DIST is now defined by a beta distribution for the proportion of mild
AGE_BREAKS = jnp.arange(0, 95, 5)  # Changed from np.arange to jnp.arange
AGE_DIST = jnp.array(
    [  # Changed from np.array to jnp.array
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
LIFE_EXP_NP = jnp.array([74, 54])  # Changed from np.array to jnp.array
ABS_MORT = jnp.array(
    [  # Changed from np.array to jnp.array
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
EMP_NP = (
    jnp.array([0, 10000, 0]) * INFLATION_FACTOR
)  # Changed from np.array to jnp.array

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
    # Ensure variance is not too large for beta distribution
    if variance >= mean * (1 - mean) and mean > 0 and mean < 1:
        variance = mean * (1 - mean) * 0.99
        std_dev = jnp.sqrt(
            variance
        )  # Changed math.sqrt to jnp.sqrt for JAX compatibility

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
    # 's' is the standard deviation of the underlying normal distribution.
    # 'scale' is exp(mean) of the underlying normal distribution.
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


# Helper function to sample from the defined distributions using JAX random
def sample_params_from_dist(
    dist_dict, seed_key=None
):  # Changed seed to seed_key for JAX compatibility
    if seed_key is None:
        seed_key = random.PRNGKey(42)  # Default key if not provided

    sampled_params = {}
    for param_name, dist_info in dist_dict.items():
        seed_key, subkey = random.split(
            seed_key
        )  # Split key for each sample to maintain randomness
        if dist_info["dist"] == "beta":
            sampled_params[param_name] = random.beta(
                subkey, dist_info["alpha"], dist_info["beta"]
            )
        elif dist_info["dist"] == "gamma":
            # JAX's random.gamma takes 'a' (shape) and then multiplies by 'scale'
            sampled_params[param_name] = (
                random.gamma(subkey, dist_info["shape"]) * dist_info["scale"]
            )
        elif dist_info["dist"] == "lognormal":
            # Convert scipy's (s, scale) to JAX's (mean_log, sigma_log)
            # scipy.stats.lognorm(s=s, scale=scale) means log(X) ~ N(log(scale), s^2)
            mean_log = jnp.log(dist_info["scale"])
            sigma_log = dist_info["s"]
            # Corrected: Generate a normal variable with specified mean_log and sigma_log, then exponentiate
            # Use shape=() for explicit scalar output from random.normal to avoid type inference issues
            sampled_params[param_name] = jnp.exp(
                random.normal(subkey, shape=()) * sigma_log + mean_log
            )
        elif dist_info["dist"] == "normal":
            sampled_params[param_name] = (
                random.normal(subkey) * dist_info["scale"] + dist_info["loc"]
            )
        elif dist_info["dist"] == "uniform":
            sampled_params[param_name] = random.uniform(
                subkey, minval=dist_info["low"], maxval=dist_info["high"]
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


# Function to prepare parameters as JAX arrays for Dask partitions
def prepare_dask_params(sampled_params):
    # Costs (converted to JAX arrays)
    COST_INP_NP_sampled = jnp.array(
        [sampled_params["cost_inp_mild"], sampled_params["cost_inp_severe"]]
    )
    COST_OUTP_NP_sampled = jnp.array(
        [sampled_params["cost_outp_mild"], sampled_params["cost_outp_severe"]]
    )
    COST_PHARM_NP_sampled = jnp.array(
        [sampled_params["cost_pharm_mild"], sampled_params["cost_pharm_severe"]]
    )
    EDU_SAMPLED = jnp.array(
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
    WELFARE_NP_sampled = jnp.array(
        [sampled_params["welfare_mild"], sampled_params["welfare_severe"]]
    )
    MORB_COST_NP_sampled = jnp.array(
        [
            sampled_params["morb_cost_epilepsy"],
            sampled_params["morb_cost_asd"],
            sampled_params["morb_cost_mental"],
        ]
    )

    # Utilities (converted to JAX arrays)
    U_BASE_NP_sampled = jnp.array(
        [sampled_params["u_base_mild"], sampled_params["u_base_severe"]]
    )
    MORB_QALY_NP_sampled = jnp.array(
        [
            sampled_params["morb_qaly_epilepsy"],
            sampled_params["morb_qaly_asd"],
            sampled_params["morb_qaly_mental"],
        ]
    )

    # Mortality HRs (converted to JAX arrays)
    MORT_HR_sampled = jnp.array(
        [sampled_params["mort_hr_mild"], sampled_params["mort_hr_severe"]]
    )

    # Morbidity Probabilities (converted to JAX-friendly dictionary/array)
    # Store as an array that can be indexed by integer, assuming order matches MORB_KEYS
    MORB_PROB_SAMPLED = {
        "epilepsy": sampled_params["morb_prob_epilepsy"],
        "asd": sampled_params["morb_prob_asd"],
        "mental": sampled_params["morb_prob_mental"],
    }

    # Severity Distribution (converted to JAX array)
    SEVERITY_DIST_SAMPLED = jnp.array(
        [sampled_params["severity_mild_prop"], sampled_params["severity_severe_prop"]]
    )

    # Fertility Rates (DataFrame remains Pandas, multiplier applied)
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
        "EMP_NP": EMP_NP,  # EMP_NP is already jnp.array global
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


# Updated to use JAX for random number generation within Dask functions for consistency and potential future JITting
def sample_ages(n, age_dist_param, key):  # Added key parameter for JAX random
    key, subkey = random.split(key)
    # random.choice in JAX needs an array for the choices, here it's implicit from len(AGE_BREAKS)
    idx = random.choice(subkey, len(AGE_BREAKS), shape=(n,), p=age_dist_param)
    key, subkey = random.split(key)
    return (
        AGE_BREAKS[idx] + random.randint(subkey, minval=0, maxval=5, shape=(n,))
    ).astype(int)


def gen_population_dask(
    n, current_params, arm="prospective", seed_key=None
):  # Added seed_key for JAX
    if seed_key is None:
        seed_key = random.PRNGKey(42)  # Default key if not provided

    # Split the main seed_key into multiple subkeys for different random operations
    (
        key_ages,
        key_sex,
        key_sev,
        key_fam,
        key_diag,
        key_liv,
        key_emp,
        key_resp,
        key_mob,
        key_sup,
        key_ses,
    ) = random.split(seed_key, 11)

    ages = sample_ages(n, AGE_DIST, key_ages)
    sev_dist = current_params["SEVERITY_DIST"]
    # Ensure sev_dist is a valid probability distribution (already JAX array from prepare_dask_params)
    sev_dist = jnp.array(sev_dist)  # Explicitly ensure it's a JAX array just in case
    sev_dist /= sev_dist.sum()

    df = pd.DataFrame(
        {
            "age": ages,
            # JAX random.choice takes a key, an array of choices, a shape, and probabilities
            "sex": random.choice(
                key_sex, jnp.array([0, 1]), shape=(n,), p=jnp.array([0.5, 0.5])
            ),
            "severity": random.choice(
                key_sev, jnp.array([0, 1]), shape=(n,), p=sev_dist
            ),
            "familial": random.uniform(key_fam, shape=(n,))
            < current_params["familial_prop"],
            "diagnosed": jnp.zeros(n, dtype=bool)
            if arm == "prospective"
            else (random.uniform(key_diag, shape=(n,)) < current_params["yield_wgs"]),
            "living": random.choice(
                key_liv,
                jnp.array([0, 1, 2, 3]),
                shape=(n,),
                p=jnp.array([0.2, 0.1, 0.3, 0.4]),
            ),  # Assuming 0 for dead, others are living states
            "employment": random.choice(
                key_emp, jnp.array([0, 1, 2]), shape=(n,), p=jnp.array([0.7, 0.2, 0.1])
            ),
            "uses_respite": random.uniform(key_resp, shape=(n,)) < 0.3,
            "needs_mobility": random.uniform(key_mob, shape=(n,)) < 0.2,
            "support": random.choice(
                key_sup, jnp.array([0, 1, 2]), shape=(n,), p=jnp.array([0.5, 0.3, 0.2])
            ),
            "ses": random.choice(key_ses, jnp.arange(5), shape=(n,)),
        }
    )
    # Convert df['age'] (Pandas Series) to JAX array for jnp.where
    df["school"] = jnp.where(
        jnp.array(df["age"]) < 5, -1, jnp.where(jnp.array(df["age"]) < 12, 0, 1)
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
        df[col] = 0.0
    return dd.from_pandas(df, npartitions=4)


# %% [markdown]
## 4. Population System (Dask)


class PopulationSystemDask:
    def __init__(
        self, pop_size, current_params, arm="prospective", seed_key=None
    ):  # Added seed_key for JAX
        self.arm = arm
        self.params = current_params
        # Initialize JAX key for this instance. If not provided, create a new one.
        self.key = seed_key if seed_key is not None else random.PRNGKey(42)
        # Initial population. We will persist it at the end of the step.
        self.pop = gen_population_dask(pop_size, self.params, arm, seed_key=self.key)
        # No initial persist here. It happens in the first step.

    def _mortality(self, current_pop):
        # Split the instance's main key for this operation
        _key, subkey_mort = random.split(self.key)
        self.key = subkey_mort  # Update the instance's key for subsequent operations

        def mortality_partition(df, abs_mort, life_exp_np, mort_hr, subkey_mort_part):
            if df.empty:
                return df
            ages = jnp.array(df["age"].values)  # Convert to JAX array
            sev = jnp.array(df["severity"].values)  # Convert to JAX array

            age_indices = jnp.clip((ages // 5).astype(int), 0, len(abs_mort) - 1)
            surv_prob = abs_mort[age_indices] * mort_hr[sev]

            # Generate random numbers within the partition using the subkey passed from the main thread
            # and further splitting it to ensure unique streams for each row or operation if needed.
            partition_key_uniform, _ = random.split(subkey_mort_part)
            # Use random.uniform for survival probability check
            mask = (
                random.uniform(partition_key_uniform, shape=(len(df),)) > surv_prob
            ) & (ages < life_exp_np[sev])

            # Convert JAX boolean array to NumPy boolean array explicitly for Pandas DataFrame filtering
            return df[device_get(mask)]

        return current_pop.map_partitions(
            mortality_partition,
            ABS_MORT,
            LIFE_EXP_NP,
            self.params["MORT_HR"],
            subkey_mort,
            meta=current_pop._meta,
        )

    def _fertility(self, current_pop):
        # Split the instance's main key for this operation
        _key, subkey_fert = random.split(self.key)
        self.key = subkey_fert  # Update the instance's key

        # Pass parameters explicitly to the partition function
        params = self.params
        fert_rates_df = self.params["FERT_RATES_DF"]  # This is a Pandas DataFrame

        def fertility_partition(
            df, params_passed, fert_rates_df_passed, subkey_fert_part, arm_passed
        ):
            if df.empty:
                return df

            # Filter for potential mothers within this partition
            moms_part = df[(df["sex"] == 0) & (df["age"].between(15, 45))]
            if moms_part.empty:
                return df

            # Merge with fertility rates (Pandas operation within partition)
            mr_part = moms_part.merge(
                fert_rates_df_passed, on=["severity", "age"], how="left"
            ).fillna(0)
            rates = mr_part["rate"].values

            # Generate births using JAX random for this partition
            birth_rand_key, _ = random.split(subkey_fert_part)
            # Convert rates to a JAX array for random.uniform comparison
            births_mask_jax = random.uniform(
                birth_rand_key, shape=(len(rates),)
            ) < jnp.array(rates)
            n_births = jnp.sum(births_mask_jax)  # Number of births in this partition

            if n_births > 0:
                # Need to convert n_births to a Python int for shape argument of JAX random functions
                n_births_int = (
                    int(n_births.item())
                    if isinstance(n_births, jnp.ndarray)
                    else int(n_births)
                )

                # Create new babies DataFrame within this partition
                # Create new babies DataFrame within this partition
                babies_df = pd.DataFrame(
                    {
                        "age": jnp.zeros(n_births_int, dtype=int),
                        "sex": device_get(
                            random.choice(
                                birth_rand_key,
                                jnp.array([0, 1]),
                                shape=(n_births_int,),
                                p=jnp.array([0.5, 0.5]),
                            )
                        ),
                        "severity": device_get(
                            random.choice(
                                birth_rand_key,
                                jnp.arange(len(params_passed["SEVERITY_DIST"])),
                                shape=(n_births_int,),
                                p=jnp.array(params_passed["SEVERITY_DIST"]),
                            )
                        ),
                        "familial": device_get(
                            random.uniform(birth_rand_key, shape=(n_births_int,))
                            < params_passed["familial_prop"]
                        ),
                        "diagnosed": device_get(
                            random.uniform(birth_rand_key, shape=(n_births_int,))
                            < params_passed["yield_wgs"]
                        ),
                        "living": device_get(
                            random.choice(
                                birth_rand_key,
                                jnp.arange(4),
                                shape=(n_births_int,),
                                p=jnp.array([0.2, 0.1, 0.3, 0.4]),
                            )
                        ),
                        "employment": device_get(
                            random.choice(
                                birth_rand_key,
                                jnp.arange(3),
                                shape=(n_births_int,),
                                p=jnp.array([0.7, 0.2, 0.1]),
                            )
                        ),
                        "uses_respite": device_get(
                            random.uniform(birth_rand_key, shape=(n_births_int,)) < 0.3
                        ),
                        "needs_mobility": device_get(
                            random.uniform(birth_rand_key, shape=(n_births_int,)) < 0.2
                        ),
                        "support": device_get(
                            random.choice(
                                birth_rand_key,
                                jnp.arange(3),
                                shape=(n_births_int,),
                                p=jnp.array([0.5, 0.3, 0.2]),
                            )
                        ),
                        "ses": device_get(
                            random.choice(
                                birth_rand_key, jnp.arange(5), shape=(n_births_int,)
                            )
                        ),
                    }
                )
                # Ensure 'familial' from mothers is passed for the new babies.
                # Use device_get for the mask to slice the Pandas DataFrame correctly.
                babies_df["familial"] = mr_part.loc[
                    device_get(births_mask_jax), "familial"
                ].values

                # Initialize new columns for babies
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
                    babies_df[col] = 0.0

                # Concatenate the original partition with the new babies
                return pd.concat([df, babies_df], ignore_index=True)
            else:
                return df

        # Call map_partitions with all necessary arguments
        return current_pop.map_partitions(
            fertility_partition,
            params,
            fert_rates_df,  # Pass the pandas DataFrame directly
            subkey_fert,
            self.arm,
            meta=current_pop._meta,
        )

    def _diagnosis(self, current_pop):
        if self.arm != "prospective":
            return current_pop

        # Split the instance's main key for this operation
        _key, subkey_diag = random.split(self.key)
        self.key = subkey_diag  # Update the instance's key

        # Use map_partitions for updating 'diagnosed' status
        def diagnosis_partition(
            df, min_test_age, yield_wgs, subkey_diag_part, arm_passed
        ):
            if df.empty:
                return df
            # Convert relevant columns to JAX arrays for JAX operations
            diagnosed_jnp = jnp.array(df["diagnosed"].values)
            familial_jnp = jnp.array(df["familial"].values)
            age_jnp = jnp.array(df["age"].values)

            # Create mask for eligible individuals using JAX
            mask = (~diagnosed_jnp) & familial_jnp & (age_jnp >= min_test_age)
            cnt = jnp.sum(mask)  # Sum using JAX for count

            if cnt > 0:
                # Generate random outcomes for diagnosis using JAX
                partition_key_diag_outcomes, _ = random.split(subkey_diag_part)
                # Generate outcomes only for the count of eligible individuals
                diag_outcomes = random.bernoulli(
                    partition_key_diag_outcomes, yield_wgs, shape=(cnt,)
                )

                # Apply updates. Need to convert JAX boolean mask to NumPy for Pandas assignment
                df.loc[device_get(mask), "diagnosed"] = device_get(diag_outcomes)
            return df

        return current_pop.map_partitions(
            diagnosis_partition,
            self.params["min_test_age"],
            self.params["yield_wgs"],
            subkey_diag,
            self.arm,
            meta=current_pop._meta,
        )

    def _cost_qaly(self, current_pop, year):
        if current_pop.npartitions == 0:
            # Return a new Dask DataFrame with the correct metadata if empty
            meta = pd.DataFrame(
                columns=current_pop.columns.tolist()
                + [
                    "cost_health",
                    "cost_edu",
                    "cost_respite",
                    "cost_mobility",
                    "cost_welfare",
                    "cost_emp",
                    "cost_morbidity",
                    "annual_cost",
                    "annual_qaly",
                ],
                dtype=float,
            )
            return dd.from_pandas(
                pd.DataFrame(), npartitions=current_pop.npartitions, meta=meta
            )

        params = self.params
        disc = 1 / ((1 + params["DISCOUNT"]) ** (year - START_YEAR))

        # Split the instance's main key for this operation
        _key, subkey_cost_qaly = random.split(self.key)
        self.key = subkey_cost_qaly  # Update the instance's key

        def cost_qaly_partition(
            df, params_passed, disc_passed, morb_keys, subkey_cost_qaly_part, arm_passed
        ):
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
            # Convert relevant columns to JAX arrays for JAX operations
            sev = jnp.array(df["severity"].values)
            ages = jnp.array(df["age"].values)
            employment_idx = jnp.array(df["employment"].values)
            school_val = jnp.array(df["school"].values)
            support_val = jnp.array(df["support"].values)
            uses_respite_val = jnp.array(df["uses_respite"].values)
            needs_mobility_val = jnp.array(df["needs_mobility"].values)
            diagnosed_val = jnp.array(df["diagnosed"].values)

            # Health Costs (using JAX arrays for parameters and indices)
            hc = (
                params_passed["COST_INP_NP"][sev]
                + params_passed["COST_OUTP_NP"][sev]
                + params_passed["COST_PHARM_NP"][sev]
            ) * disc_passed
            rc = (
                uses_respite_val.astype(jnp.float64)
                * params_passed["RESPITE"]
                * disc_passed
            )
            mc = (
                -needs_mobility_val.astype(jnp.float64)
                * params_passed["MOBILITY"]
                * disc_passed
            )
            wc = params_passed["WELFARE_NP"][sev] * disc_passed
            emp = params_passed["EMP_NP"][employment_idx] * disc_passed

            # Education Costs
            ec = jnp.zeros(n, dtype=jnp.float64)
            m0 = school_val == 0
            m1 = school_val == 1
            # Use jnp.where for conditional assignment on JAX arrays
            ec = jnp.where(m0, params_passed["EDU"][0, support_val], ec)
            ec = jnp.where(m1, params_passed["EDU"][1, support_val], ec)
            ec *= disc_passed

            # Morbidity Costs
            morb_cost = jnp.zeros(n, dtype=jnp.float64)
            partition_key_morb_cost, _ = random.split(
                subkey_cost_qaly_part
            )  # New subkey for this
            base_rand = random.uniform(partition_key_morb_cost, shape=(n,))
            for i, k in enumerate(morb_keys):  # Use passed morb_keys
                m = (
                    base_rand < params_passed["MORB_PROB"][k]
                )  # Use parameter dictionary for MORB_PROB
                morb_cost += (
                    m.astype(jnp.float64)
                    * params_passed["MORB_COST_NP"][i]
                    * disc_passed
                )

            if arm_passed == "prospective":  # Use passed arm_passed
                m = diagnosed_val
                morb_cost += (
                    m.astype(jnp.float64)
                    * params_passed["WGS_DIAG_COST_ADJUSTMENT"]
                    * disc_passed
                )

            # Morbidity QALYs
            morb_qaly = jnp.zeros(n, dtype=jnp.float64)
            partition_key_morb_qaly, _ = random.split(
                subkey_cost_qaly_part
            )  # New subkey for this
            base_rand_qaly = random.uniform(partition_key_morb_qaly, shape=(n,))
            for i, k in enumerate(morb_keys):  # Use passed morb_keys
                m = base_rand_qaly < params_passed["MORB_PROB"][k]
                morb_qaly += (
                    m.astype(jnp.float64)
                    * params_passed["MORB_QALY_NP"][i]
                    * disc_passed
                )

            # Utility (QALY) Calculation
            uq = params_passed["U_BASE_NP"][sev] * jnp.exp(
                -params_passed["U_DECAY"] * jnp.clip(ages - 20, 0, None)
            )
            total_qaly = (
                uq
                + diagnosed_val.astype(jnp.float64) * params_passed["U_DIAG"]
                + params_passed["U_CARER"]
            ) * disc_passed - morb_qaly

            if arm_passed == "prospective":  # Use passed arm_passed
                m = diagnosed_val
                total_qaly += (
                    m.astype(jnp.float64)
                    * params_passed["WGS_DIAG_QALY_ADJUSTMENT"]
                    * disc_passed
                )

            # Assign JAX array results to Pandas DataFrame columns (implicit conversion back to NumPy)
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

        return current_pop.map_partitions(
            cost_qaly_partition,
            params,
            disc,
            MORB_KEYS,
            subkey_cost_qaly,
            self.arm,
            meta=current_pop._meta,
        )

    def step(self, year):
        # Current population reference for unpersisting later

        # Chain lazy operations
        new_pop = self._mortality(self.pop)
        new_pop = self._fertility(new_pop)
        new_pop = self._diagnosis(new_pop)

        # Increment age for all individuals lazily
        new_pop = new_pop.assign(age=new_pop.age + 1)

        # Calculate costs and QALYs for the current year lazily
        new_pop = self._cost_qaly(new_pop, year)

        # Persist the new population
        self.pop = new_pop.persist()
        # Removed: client.cancel([old_pop_ref]) - Let Dask's GC handle old_pop_ref
        # Removed: del old_pop_ref
        gc.collect()  # Still good to run GC


# %% [markdown]
## 5. Run Helpers (Integrated Dask and JAX)


def run_sim(sampled_params, pop_size=POP_SIZE, seed_idx=None):
    # JAX PRNG key management for the entire simulation run
    if seed_idx is not None:
        local_key = random.PRNGKey(42 + seed_idx)
    else:
        local_key = random.PRNGKey(42)

    # Prepare parameters for Dask, ensuring JAX arrays are used internally
    dask_params = prepare_dask_params(sampled_params)

    # Split the local_key to provide distinct random streams for retrospective and prospective arms
    sim_r_key, sim_p_key, _ = random.split(local_key, 3)

    # Initialize PopulationSystemDask for both arms, passing the JAX keys
    sim_r = PopulationSystemDask(
        pop_size, dask_params, "retrospective", seed_key=sim_r_key
    )
    sim_p = PopulationSystemDask(
        pop_size, dask_params, "prospective", seed_key=sim_p_key
    )

    # These lists will now store lazy Dask Series objects
    all_r_annual_costs_lazy = []
    all_r_annual_qalys_lazy = []
    all_p_annual_costs_lazy = []
    all_p_annual_qalys_lazy = []

    # Initial population persistence for the first step
    sim_r.pop = sim_r.pop.persist()
    sim_p.pop = sim_p.pop.persist()
    gc.collect()

    for yr in YEARS:
        sim_r.step(yr)
        # Append lazy Dask Series to lists
        all_r_annual_costs_lazy.append(sim_r.pop["annual_cost"].sum())
        all_r_annual_qalys_lazy.append(sim_r.pop["annual_qaly"].sum())

        sim_p.step(yr)
        # Append lazy Dask Series to lists
        all_p_annual_costs_lazy.append(sim_p.pop["annual_cost"].sum())
        all_p_annual_qalys_lazy.append(sim_p.pop["annual_qaly"].sum())

    # NEW: Collect all Dask Scalar objects into a single list
    all_lazy_scalars_for_compute = (
        all_r_annual_costs_lazy
        + all_r_annual_qalys_lazy
        + all_p_annual_costs_lazy
        + all_p_annual_qalys_lazy
    )

    # Compute all collected lazy Dask Series (which are Dask Scalars here) at once
    computed_results_futures = client.compute(
        all_lazy_scalars_for_compute
    )  # Returns a list of Futures
    computed_results = client.gather(
        computed_results_futures
    )  # Gathers the results from Futures

    # Now, unpack the computed results from the single list
    num_years = len(YEARS)

    # Split the single list back into original four lists
    computed_r_costs = computed_results[0 * num_years : 1 * num_years]
    computed_r_qalys = computed_results[1 * num_years : 2 * num_years]
    computed_p_costs = computed_results[2 * num_years : 3 * num_years]
    computed_p_qalys = computed_results[3 * num_years : 4 * num_years]

    # Explicitly cancel the final populations after the loop is done - Removed
    # client.cancel([sim_r.pop, sim_p.pop])
    # del sim_r.pop, sim_p.pop
    gc.collect()  # Still good to run GC

    # Sum the lists directly. Each element should now be a concrete number.
    cum_r_c = sum(float(x) for x in computed_r_costs)
    cum_r_q = sum(float(x) for x in computed_r_qalys)
    cum_p_c = sum(float(x) for x in computed_p_costs)
    cum_p_q = sum(float(x) for x in computed_p_qalys)

    # These are now guaranteed to be Python floats
    dc = cum_p_c - cum_r_c
    dq = cum_p_q - cum_r_q

    # Return incremental cost and QALY (results will be Python scalars)
    return (dc, dq)


def run_scenario(sampled_params, pop_size=POP_SIZE):
    dask_params = prepare_dask_params(sampled_params)
    scenario_key = random.PRNGKey(84)  # Keep this key

    scenario_key, sim_r_key, sim_p_key = random.split(scenario_key, 3)
    sim_r = PopulationSystemDask(
        pop_size, dask_params, "retrospective", seed_key=sim_r_key
    )
    sim_p = PopulationSystemDask(
        pop_size, dask_params, "prospective", seed_key=sim_p_key
    )

    # Lists to store lazy Dask Series for each year and each arm
    # We will accumulate all the annual sums for cost and QALY categories,
    # as well as SES percentages, as Dask Series.
    # Each element in these lists will be a Dask Series representing the sum for a year.
    lazy_annual_results = []

    # Initial population persistence for the first step
    sim_r.pop = sim_r.pop.persist()
    sim_p.pop = sim_p.pop.persist()
    gc.collect()

    for yr in YEARS:
        sim_r.step(yr)
        sim_p.step(yr)

        # For each arm, create a dictionary of lazy Dask Series (sums and counts)
        # and append it to the lazy_annual_results list.
        # This prevents immediate computation within the loop.

        # Retrospective arm
        # Check if pop is empty using Dask's lazy len or by checking npartitions
        r_pop_current = sim_r.pop.assign(year=yr, arm="retrospective")
        if r_pop_current.npartitions == 0 or (
            r_pop_current.known_partitions and r_pop_current.npartitions == 0
        ):
            # If empty, append Dask Series of zeros/empty values with correct names
            lazy_r_sums = {
                col: dd.Scalar(0.0, name=f"{col}-year-{yr}-r")
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
                ]
            }
            lazy_r_ses_counts = {
                i: dd.Scalar(0, name=f"ses_q{i}_count-year-{yr}-r") for i in range(5)
            }
            lazy_r_total_pop = dd.Scalar(0, name=f"total_pop-year-{yr}-r")
        else:
            lazy_r_sums = r_pop_current[
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
            ].sum()
            lazy_r_ses_counts = r_pop_current.groupby("ses").age.count()
            lazy_r_total_pop = r_pop_current.age.count()

        lazy_annual_results.append(
            {
                "arm": "retrospective",
                "year": yr,
                "sums": lazy_r_sums,
                "ses_counts": lazy_r_ses_counts,
                "total_pop": lazy_r_total_pop,
            }
        )

        # Prospective arm
        p_pop_current = sim_p.pop.assign(year=yr, arm="prospective")
        if p_pop_current.npartitions == 0 or (
            p_pop_current.known_partitions and p_pop_current.npartitions == 0
        ):
            lazy_p_sums = {
                col: dd.Scalar(0.0, name=f"{col}-year-{yr}-p")
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
                ]
            }
            lazy_p_ses_counts = {
                i: dd.Scalar(0, name=f"ses_q{i}_count-year-{yr}-p") for i in range(5)
            }
            lazy_p_total_pop = dd.Scalar(0, name=f"total_pop-year-{yr}-p")
        else:
            lazy_p_sums = p_pop_current[
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
            ].sum()
            lazy_p_ses_counts = p_pop_current.groupby("ses").age.count()
            lazy_p_total_pop = p_pop_current.age.count()

        lazy_annual_results.append(
            {
                "arm": "prospective",
                "year": yr,
                "sums": lazy_p_sums,
                "ses_counts": lazy_p_ses_counts,
                "total_pop": lazy_p_total_pop,
            }
        )

    # Explicitly cancel the final populations after the loop is done - Removed
    # client.cancel([sim_r.pop, sim_p.pop])
    # del sim_r.pop, sim_p.pop
    gc.collect()  # Still good to run GC

    # Collect all Dask Series into a single dictionary for a final, efficient computation
    all_futures_dict = {}  # Renamed to clearly indicate it's a dict for compute
    for entry in lazy_annual_results:
        arm = entry["arm"]
        year = entry["year"]
        for col, dask_series in entry["sums"].items():
            all_futures_dict[f"{arm}_{year}_sum_{col}"] = dask_series
        for ses_q, dask_series in entry["ses_counts"].items():
            all_futures_dict[f"{arm}_{year}_ses_count_{ses_q}"] = dask_series
        all_futures_dict[f"{arm}_{year}_total_pop"] = entry["total_pop"]

    # Perform the single, large computation (compute on dict of Dask objects, then gather futures from dict)
    computed_results_futures_dict = client.compute(
        all_futures_dict
    )  # Returns a dictionary of Futures
    computed_all_results = client.gather(
        computed_results_futures_dict
    )  # Gathers the results from Futures

    # Now, reconstruct the pandas DataFrame from the computed results
    full_results_df_pd = []
    for entry in lazy_annual_results:  # Iterate through the original structure
        arm = entry["arm"]
        year = entry["year"]
        row_data = {"arm": arm, "year": year}

        # Populate sums
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
            key = f"{arm}_{year}_sum_{col}"
            # Ensure proper conversion from JAX/NumPy scalar to Python float
            value = computed_all_results[key]
            row_data[col] = (
                float(value.item()) if hasattr(value, "item") else float(value)
            )

        # Populate SES percentages
        total_pop_key = f"{arm}_{year}_total_pop"
        total_pop_val = computed_all_results[total_pop_key]
        total_pop_float = (
            float(total_pop_val.item())
            if hasattr(total_pop_val, "item")
            else float(total_pop_val)
        )

        for i in range(5):
            ses_count_key = f"{arm}_{year}_ses_count_{i}"
            ses_count_val = computed_all_results[ses_count_key]
            ses_count_float = (
                float(ses_count_val.item())
                if hasattr(ses_count_val, "item")
                else float(ses_count_val)
            )

            row_data[f"ses_q{i}_pct"] = (
                (ses_count_float / total_pop_float * 100)
                if total_pop_float > 0
                else 0.0
            )

        full_results_df_pd.append(row_data)

    full_results_df_pd = pd.DataFrame(full_results_df_pd)

    # Calculate cumulative costs and QALYs after all annual data is collected
    # These are now computed from the `full_results_df_pd`
    final_totals = {
        "retrospective": {"cost": 0.0, "qaly": 0.0},
        "prospective": {"cost": 0.0, "qaly": 0.0},
    }
    for arm in ["retrospective", "prospective"]:
        arm_df = full_results_df_pd[full_results_df_pd["arm"] == arm]
        # Sum from the already computed pandas DataFrame
        final_totals[arm]["cost"] = arm_df["annual_cost"].sum()
        final_totals[arm]["qaly"] = arm_df["annual_qaly"].sum()

    d_cost = float(
        final_totals["prospective"]["cost"] - final_totals["retrospective"]["cost"]
    )
    d_qaly = float(
        final_totals["prospective"]["qaly"] - final_totals["retrospective"]["qaly"]
    )

    return (d_cost, d_qaly), full_results_df_pd


# %% [markdown]
## 6. Deterministic Scenarios

print("--- Running Module 6: Deterministic Scenarios ---")
base_mean_params = {}
for k, v in DISTRIBUTIONS.items():
    if v["dist"] == "beta":
        base_mean_params[k] = v["alpha"] / (v["alpha"] + v["beta"])
    elif v["dist"] == "gamma":
        base_mean_params[k] = v["shape"] * v["scale"]
    elif v["dist"] == "lognormal":
        # For deterministic, use the 'scale' parameter directly from the distribution definition
        # which represents exp(mean_of_log)
        base_mean_params[k] = v["scale"]
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
# Adjusted pop_size for deterministic runs for stability
for name, specific_override_params in scenarios.items():
    current_params_for_run = base_mean_params.copy()
    current_params_for_run.update(specific_override_params)

    # dc and dq are now guaranteed to be concrete Python numbers from run_sim
    dc, dq = run_sim(current_params_for_run, pop_size=10000)

    # Ensure dq is a concrete number before the conditional check
    # The previous fix of .compute() here is no longer strictly necessary if run_sim returns floats,
    # but kept for robustness against potential future changes where Dask arrays might be passed.
    # The crucial part is that `dq` is a float before `if dq != 0`

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

# The Dask cluster and client are now initialized globally at the top of the script.
# No need to re-initialize here.
print(f"Running {psa_n} PSA simulations in parallel using Dask...")

psa_args = []
# Create a master JAX key for PSA and split it for each simulation to ensure distinct random streams
psa_master_key = random.PRNGKey(100)
for i in range(psa_n):
    psa_master_key, subkey = random.split(
        psa_master_key
    )  # Split key for each simulation
    # Pass the unique subkey to sample_params_from_dist
    sampled_params = sample_params_from_dist(DISTRIBUTIONS, seed_key=subkey)
    psa_args.append(
        (sampled_params, 5000, i)
    )  # Reduced pop_size for PSA runs from 8000


def _run_sim_job(args):
    """Wrapper so Dask can pickle the function. args=(params, pop_size, iter_id)"""
    sampled_params, pop_size, iter_id = args
    return run_sim(sampled_params, pop_size, iter_id)


futures = client.map(_run_sim_job, psa_args)
progress(futures)

results = client.gather(futures)

# After gathering futures, cancel them to release resources - Removed
# client.cancel(futures)
gc.collect()

for i, (dc, dq) in enumerate(results):
    original_sampled_params = psa_args[i][0]
    row_data = {"run": i, "dCost": dc, "dQALY": dq}
    # Convert JAX array results to Python scalars for Pandas DataFrame
    for k, v in original_sampled_params.items():
        if isinstance(v, jnp.ndarray):
            row_data[k] = v.item()
        else:
            row_data[k] = v
    psa_out.append(row_data)

# Create a Pandas DataFrame first, then convert to Dask for large-scale analysis
psa_df_pd = pd.DataFrame(psa_out)
psa_df_pd.to_csv("psa_samples.csv", index=False)
print("PSA results saved to psa_samples.csv")

# Convert to Dask DataFrame for subsequent modules
psa_df = dd.from_pandas(psa_df_pd, npartitions=4)


# Close the Dask client and cluster (moved to end of script)


# %% [markdown]
## 8. CE-Plane, CEAC, EVPI & ENMB

print("\n--- Running Module 8: CE-Plane, CEAC, EVPI & ENMB ---")
wtp = jnp.linspace(
    0, 150000, 40
)  # Changed np.linspace to jnp.linspace for JAX compatibility
# Compute the dask series to get NumPy arrays (which JAX can then convert to its own arrays)
dcost = jnp.array(psa_df["dCost"].compute().to_numpy())  # Convert to JAX array
dqaly = jnp.array(psa_df["dQALY"].compute().to_numpy())  # Convert to JAX array

valid_psa = dqaly > 0
# Use jnp.newaxis for broadcasting instead of None
nb = dqaly[valid_psa, jnp.newaxis] * wtp[jnp.newaxis, :] - dcost[valid_psa, jnp.newaxis]

plt.figure()
# Plotting with NumPy arrays for Matplotlib compatibility
plt.scatter(jnp.array(dqaly), jnp.array(dcost), alpha=0.6)
plt.axvline(x=0, color="grey", linestyle="--", linewidth=0.8)
plt.axhline(y=0, color="grey", linestyle="--", linewidth=0.8)
plt.plot(
    jnp.array(wtp),
    jnp.array(wtp * 20000),
    color="green",
    linestyle=":",
    label="WTP £20,000/QALY",
)
plt.plot(
    jnp.array(wtp),
    jnp.array(wtp * 30000),
    color="red",
    linestyle=":",
    label="WTP £30,000/QALY",
)

plt.xlabel("Incremental QALYs (Delta QALY)")
plt.ylabel("Incremental Cost (Delta Cost)")
plt.title("Cost-Effectiveness Plane with WTP Thresholds")
plt.grid(True)
plt.legend()
plt.show()

prob = jnp.mean(nb > 0, axis=0)  # Use jnp.mean for JAX array
plt.figure()
plt.plot(
    jnp.array(wtp), jnp.array(prob)
)  # Plotting with NumPy arrays for Matplotlib compatibility
plt.title("Cost-Effectiveness Acceptability Curve (CEAC)")
plt.xlabel("Willingness-to-Pay per QALY")
plt.ylabel("Probability Cost-Effective")
plt.ylim(0, 1)
plt.grid(True)
plt.show()

evpi = jnp.mean(jnp.maximum(0, nb), axis=0) - jnp.maximum(
    0, jnp.mean(nb, axis=0)
)  # Use jnp.mean, jnp.maximum
plt.figure()
plt.plot(
    jnp.array(wtp), jnp.array(evpi)
)  # Plotting with NumPy arrays for Matplotlib compatibility
plt.title("Expected Value of Perfect Information (EVPI)")
plt.xlabel("Willingness-to-Pay per QALY")
plt.ylabel("EVPPI")
plt.grid(True)
plt.show()

enmb = jnp.mean(nb, axis=0)  # Use jnp.mean
plt.figure()
plt.plot(
    jnp.array(wtp), jnp.array(enmb)
)  # Plotting with NumPy arrays for Matplotlib compatibility
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
base_params = base_mean_params  # From Module 6 (Python dictionary of scalars)

if "severity_mild_prop" in base_params:
    base_params["severity_severe_prop"] = 1.0 - base_params["severity_mild_prop"]

# dc and dq are now guaranteed to be concrete Python numbers from run_sim
base_dc, base_dq = run_sim(base_params, pop_size=10000)
# Ensure base_dq is a concrete number before the conditional check
base_icer = (base_dc / base_dq) if base_dq != 0 else 0

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
        std_dev = jnp.sqrt(variance)  # Changed math.sqrt to jnp.sqrt
        low_val, high_val = (
            max(0, mean_val - 2 * std_dev),
            min(1, mean_val + 2 * std_dev),
        )
    elif dist_info["dist"] == "gamma":
        mean_val = dist_info["shape"] * dist_info["scale"]
        std_dev = jnp.sqrt(
            dist_info["shape"] * dist_info["scale"] ** 2
        )  # Changed math.sqrt to jnp.sqrt
        low_val, high_val = max(0, mean_val - 2 * std_dev), mean_val + 2 * std_dev
    elif dist_info["dist"] == "lognormal":
        # For deterministic sensitivity, use a percentage change around the 'scale' (exp(mean_log))
        mean_val = dist_info["scale"]
        low_val, high_val = mean_val * 0.90, mean_val * 1.10
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

    for val in [low_val, high_val]:
        p_temp = base_params.copy()
        p_temp[param_name] = val
        # dc and dq are now guaranteed to be concrete Python numbers from run_sim
        dc, dq = run_sim(p_temp, pop_size=10000)
        # Ensure dq is a concrete number before the conditional check
        icer = (dc / dq) if dq != 0 else 0
        change_type = "Low" if val < mean_val else "High"
        tornado.append({"param": param_name, "change_type": change_type, "ICER": icer})

tor_df = pd.DataFrame(tornado)
tor_df["ICER_diff"] = tor_df["ICER"] - base_icer
tor_df["abs_diff"] = (
    tor_df["ICER_diff"].abs().astype(float)
)  # Ensure abs_diff is float for sorting
tor_df = tor_df.sort_values(by="abs_diff", ascending=True)

plt.figure(figsize=(10, len(tornado_params_to_vary) * 0.8))
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
mean_params_for_subgroup = base_mean_params  # from Module 6

if "severity_mild_prop" in mean_params_for_subgroup:
    mean_params_for_subgroup["severity_severe_prop"] = (
        1.0 - mean_params_for_subgroup["severity_mild_prop"]
    )

for sev_prop, label in [(1.0, "Mild Only"), (0.0, "Severe Only")]:
    p_temp = mean_params_for_subgroup.copy()
    p_temp["severity_mild_prop"] = sev_prop
    p_temp["severity_severe_prop"] = 1.0 - sev_prop
    # dc and dq are now guaranteed to be concrete Python numbers from run_sim
    dc, dq = run_sim(p_temp, pop_size=15000)
    # Ensure dq is a concrete number before the conditional check
    icer_val = (
        (dc / dq) if dq != 0 else (jnp.inf if dq < 0 else -jnp.inf)
    )  # Handle division by zero
    sg.append(
        {
            "group": f"Severity: {label}",
            "ICER": icer_val.item() if isinstance(icer_val, jnp.ndarray) else icer_val,
        }
    )  # Convert JAX scalar to Python float

for age in [0, 18, 30]:
    p_temp = mean_params_for_subgroup.copy()
    p_temp["min_test_age"] = age
    # dc and dq are now guaranteed to be concrete Python numbers from run_sim
    dc, dq = run_sim(p_temp, pop_size=15000)
    # Ensure dq is a concrete number before the conditional check
    icer_val = (
        (dc / dq) if dq != 0 else (jnp.inf if dq < 0 else -jnp.inf)
    )  # Handle division by zero
    sg.append(
        {
            "group": f"Min Test Age: {age}",
            "ICER": icer_val.item() if isinstance(icer_val, jnp.ndarray) else icer_val,
        }
    )  # Convert JAX scalar to Python float

# Note: The 'Horizon' part of the subgroup analysis relies on annual data
# from `run_scenario`, which generates Pandas DataFrames. This section remains
# using Pandas/NumPy results for now. If this also needs JAX acceleration for
# the data collection, `run_scenario` would need to be re-designed to return
# JAX arrays of annual results.
(_, int_full) = run_scenario(
    mean_params_for_subgroup, pop_size=15000
)  # Using a consistent pop_size
dfp = int_full[int_full["arm"] == "prospective"]
dfr = int_full[int_full["arm"] == "retrospective"]
for yrs_n in [10, 20, len(YEARS)]:
    yr = START_YEAR + yrs_n - 1
    # Ensure the year exists in both prospective and retrospective dataframes before accessing
    if yr in dfp["year"].values and yr in dfr["year"].values:
        c1 = float(
            dfp.loc[dfp["year"] == yr, "annual_cost"].values[0]
        )  # Use annual_cost from aggregated data
        c0 = float(
            dfr.loc[dfr["year"] == yr, "annual_cost"].values[0]
        )  # Use annual_cost from aggregated data
        q1 = float(
            dfp.loc[dfp["year"] == yr, "annual_qaly"].values[0]
        )  # Use annual_qaly from aggregated data
        q0 = float(
            dfr.loc[dfr["year"] == yr, "annual_qaly"].values[0]
        )  # Use annual_qaly from aggregated data
        dc, dq = (c1 - c0), (q1 - q0)
        sg.append(
            {"group": f"Horizon: {yrs_n} yrs", "ICER": (dc / dq) if dq != 0 else 0}
        )

sg_df = pd.DataFrame(sg)
# dc and dq are now guaranteed to be concrete Python numbers from run_sim
base_dc_subgroup, base_dq_subgroup = run_sim(mean_params_for_subgroup, pop_size=10000)
# Ensure base_dq_subgroup is a concrete number before the conditional check
base_icer_subgroup = (
    (base_dc_subgroup / base_dq_subgroup) if base_dq_subgroup != 0 else 0
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

# %% [markdown]
## 11. Cost-Mix Stacked Area (Prospective)

print("\n--- Running Module 11: Cost-Mix Stacked Area (Prospective) ---")
# This module relies on the detailed annual outputs from `run_scenario`,
# which currently generates Pandas DataFrames.
(_, mix_data) = run_scenario(
    mean_params_for_subgroup, pop_size=20000
)  # Re-run run_scenario to get the updated mix_data structure
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
# Re-use the data from the previous scenario run
dfp = mix_data[mix_data["arm"] == "prospective"]
dfr = mix_data[dfr["arm"] == "retrospective"]

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
        sub["year"], sub["budget_impact"], label=f"Uptake {int(u * 100)}%", marker="o"
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
    labels = [f"Quintile {i + 1}" for i in range(5)]

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
# 'prob' was calculated in module 8 as a JAX array
ceaf = jnp.maximum.accumulate(prob)  # Use jnp.maximum.accumulate

plt.figure()
plt.plot(
    jnp.array(wtp), jnp.array(prob), label="CEAC"
)  # Plotting with NumPy arrays for Matplotlib compatibility
plt.plot(
    jnp.array(wtp), jnp.array(ceaf), label="CEAF", linestyle="--"
)  # Plotting with NumPy arrays for Matplotlib compatibility
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
        summary_str += f", s (std_log): {dist_info['s']:.2f}, Scale (exp(mean_log)): {dist_info['scale']:.2f}"
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
familial_prevalence_range = jnp.linspace(
    0.10, 0.23, 10
)  # Changed np.linspace to jnp.linspace
familial_sens_results = []
for f_prop in familial_prevalence_range:
    # dc and dq are now guaranteed to be concrete Python numbers from run_sim
    # Need to make sure p_temp is defined for each iteration. It should be copied from mean_params_for_sens.
    p_temp = mean_params_for_sens.copy()
    p_temp["familial_prop"] = f_prop
    dc, dq = run_sim(p_temp, pop_size=10000)
    icer = (dc / dq) if dq != 0 else 0
    familial_sens_results.append(
        {"familial_prop": f_prop, "dCost": dc, "dQALY": dq, "ICER": icer}
    )

familial_sens_df = pd.DataFrame(familial_sens_results)
print("Familial ID Prevalence Sensitivity Results:")
print(familial_sens_df.to_string())

plt.figure(figsize=(8, 6))
plt.plot(
    jnp.array(familial_sens_df["familial_prop"]),
    jnp.array(familial_sens_df["ICER"]),
    marker="o",
    linestyle="-",
)  # Plotting with NumPy arrays for Matplotlib compatibility
plt.xlabel("Familial ID Prevalence")
plt.ylabel("ICER (£/QALY)")
plt.title("Sensitivity to Familial ID Prevalence")
plt.grid(True)
plt.show()

# %% [markdown]
## 19. EVPPI Analysis

print("\n--- Running Module 19: EVPPI Analysis ---")


# JIT compile the core EVPPI calculation for performance
@jit
def calculate_evppi_curve_jax_core(
    dcost_jnp, dqaly_jnp, param_values_jnp, wtp_range_jnp
):
    evppi_values = []

    # Construct design matrix X for linear regression
    X = jnp.vstack([jnp.ones(len(dcost_jnp)), param_values_jnp]).T

    # Loop over WTP values
    for wtp_val in wtp_range_jnp:
        nmb_jnp = dqaly_jnp * wtp_val - dcost_jnp

        # Linear regression to get predicted NMB based on parameter
        # JAX's jnp.linalg.lstsq is differentiable and GPU compatible
        coeffs = jnp.linalg.lstsq(X, nmb_jnp, rcond=None)[0]
        nmb_predicted = X @ coeffs

        # Calculate EVPPI for this WTP value
        evppi_val = jnp.mean(jnp.maximum(0, nmb_jnp)) - jnp.maximum(
            0, jnp.mean(nmb_predicted)
        )
        evppi_values.append(evppi_val)
    return jnp.array(evppi_values)  # Return JAX array


parameters_for_evppi_new = ["familial_prop", "yield_wgs", "u_diag", "cost_inp_severe"]
evppi_results = {}
# Use the pandas version of the PSA results, then convert to JAX arrays for calculation
print("Calculating EVPPI for key parameters...")
for param in parameters_for_evppi_new:
    if param in psa_df_pd.columns:
        dcost_jnp_val = jnp.array(psa_df_pd["dCost"].values)
        dqaly_jnp_val = jnp.array(psa_df_pd["dQALY"].values)
        param_values_jnp_val = jnp.array(psa_df_pd[param].values)
        wtp_jnp_val = jnp.array(wtp)  # Ensure wtp is JAX array

        # Call the JIT-compiled function
        evppi_curve = calculate_evppi_curve_jax_core(
            dcost_jnp_val, dqaly_jnp_val, param_values_jnp_val, wtp_jnp_val
        )
        evppi_results[param] = evppi_curve  # Store the JAX array

if evppi_results:
    plt.figure(figsize=(10, 6))
    for param, evppi_curve_host in evppi_results.items():
        # Plotting with NumPy arrays for Matplotlib compatibility
        plt.plot(
            jnp.array(wtp),
            jnp.array(evppi_curve_host),
            label=f"EVPPI ({param.replace('_', ' ').title()})",
        )
    plt.title("Expected Value of Partial Perfect Information (EVPPI) Curves")
    plt.xlabel("Willingness-to-Pay per QALY")
    plt.ylabel("EVPPI (£)")
    plt.legend()
    plt.grid(True)
    plt.show()

# %% [markdown]
## 20. PSA Histograms

print("\n--- Running Module 20: PSA Histograms (dCost, dQALY) ---")
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
    rm["year"], *data_r, labels=[c.replace("cost_", "").capitalize() for c in cost_cols]
)
plt.legend(loc="upper left")
plt.title("Cost Mix Over Time (Retrospective Arm - Discounted Annual Costs)")
plt.xlabel("Year")
plt.ylabel("Annual Cost")
plt.show()

print("Retrospective Cost Mix analysis complete.")

# Close the Dask client and cluster at the very end of the script
client.close()
cluster.close()
