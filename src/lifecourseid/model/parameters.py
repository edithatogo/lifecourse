import numpy as np
from scipy.stats import beta, gamma, lognorm, norm, uniform
import math
import pandas as pd

# Global Parameters
START_YEAR, END_YEAR = 2020, 2100

DISCOUNT = 0.035  # Fixed
POP_SIZE = 62000  # Fixed

# Costs are based on 2017 values from the paper, adjust to START_YEAR (2020)
COST_REFERENCE_YEAR = 2017  # Fixed
INFLATION_RATE = 0.03  # Fixed
INFLATION_FACTOR = (1 + INFLATION_RATE) ** (START_YEAR - COST_REFERENCE_YEAR)  # Fixed

# Demographics - mostly fixed or handled by sampling
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

# NDIS Cost (fixed)
NDIS_COST = 45000 * INFLATION_FACTOR

# Carer costs (fixed)
CARER_HOURS_NP = np.array([5, 15])  # Mild, Severe
WAGE_HR = 38 * INFLATION_FACTOR

# Hospitalization costs (fixed)
HOSP_COST = 8500 * INFLATION_FACTOR
HOSP_RATE_NP = np.array(
    [0.5, 1.5, 3.0]
)  # Mild, Moderate, Severe (assuming 3 severity levels for rates)

# Other common costs (fixed)
MENTAL_HEALTH_COST = 30418 * INFLATION_FACTOR
INFORMAL_CARE_COST = 25000 * INFLATION_FACTOR

# Income parameters for log-normal distribution (mu, sigma) by severity and education
INCOME_PARAMS = {
    "mild": {"primary": (10.5, 0.5), "secondary": (10.8, 0.4), "tertiary": (11.2, 0.3)},
    "severe": {
        "primary": (10.3, 0.6),
        "secondary": (10.6, 0.5),
        "tertiary": (10.9, 0.4),
    },  # Using 'severe' for moderate/severe
}

# Education levels and age bands for demographic distributions
EDUCATION_LEVELS = ["primary", "secondary", "tertiary"]
AGE_BANDS = [(0, 14), (15, 64), (65, 100)]
AGE_BAND_P = np.array([0.19, 0.65, 0.16])  # Distribution for age bands

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
    if not (0 <= mean <= 1) or std_dev <= 0 or mean in (0, 1):
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
    "u_diag": get_beta_params(0.9, 0.002),
    "u_carer": get_beta_params(0.05, 0.005),
    "morb_qaly_epilepsy": get_beta_params(0.04, 0.005),
    "morb_qaly_asd": get_beta_params(0.03, 0.005),
    "morb_qaly_mental": get_beta_params(0.05, 0.005),
    "wgs_diag_qaly_adjustment": get_beta_params(0.5, 0.001),
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


def get_mean_params(dist_dict):
    """Return deterministic mean values for each distribution.

    Parameters defined with relative distributions are converted to their mean
    values so that deterministic scenarios can be generated easily.
    """
    mean_params = {}
    for key, info in dist_dict.items():
        if info["dist"] == "beta":
            mean_params[key] = info["alpha"] / (info["alpha"] + info["beta"])
        elif info["dist"] == "gamma":
            mean_params[key] = info["shape"] * info["scale"]
        elif info["dist"] == "lognormal":
            mean_params[key] = info["scale"] * np.exp(info["s"] ** 2 / 2)
        elif info["dist"] == "normal":
            mean_params[key] = info["loc"]
        elif info["dist"] == "uniform":
            mean_params[key] = (info["low"] + info["high"]) / 2
        elif info["dist"] == "fixed":
            mean_params[key] = info["value"]

    if "severity_mild_prop" in mean_params:
        mean_params["severity_severe_prop"] = 1.0 - mean_params["severity_mild_prop"]

    return mean_params


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
    # Build lookup table for fertility rates (base rates)
    fert_data = []
    for (s, (lo, hi)), r in FERT_AGE_SPEC.items():
        for age in range(lo, hi + 1):
            fert_data.append({"severity": s, "age": age, "rate": r})
    FERT_RATES_DF = pd.DataFrame(fert_data)

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
