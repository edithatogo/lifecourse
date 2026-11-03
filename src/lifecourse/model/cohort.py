import numpy as np
import pandas as pd

from .parameters import AGE_BANDS, AGE_BREAKS, AGE_DIST, EDUCATION_LEVELS, FERT_AGE_SPEC
from .rng_utils import bernoulli, categorical

# Build lookup table for fertility rates (base rates)
fert_data = []
for (s, (lo, hi)), r in FERT_AGE_SPEC.items():
    for age in range(lo, hi + 1):
        fert_data.append({"severity": s, "age": age, "rate": r})
FERT_RATES_DF = pd.DataFrame(fert_data)


def sample_ages_from_uids(person_uids, age_dist_param):
    # categorical draw for age bucket then small uniform offset 0-4
    idx = categorical(
        person_uids,
        list(range(len(AGE_BREAKS))),
        probs=age_dist_param,
        tag="age_bucket",
    )
    offsets = categorical(person_uids, list(range(5)), probs=None, tag="age_offset")
    ages = np.array([AGE_BREAKS[i] for i in idx]) + offsets
    return ages.astype(int)


def gen_person_uids(n):
    """Generate stable, deterministic person_uids for initial populations.

    Use a simple sequential 64-bit integer series. This ensures uniqueness and
    stability across runs in tests and avoids relying on the global RNG.
    """
    return np.arange(1, n + 1, dtype=np.int64)


def sample_ages(n, age_dist_param):
    """Backward-compatible wrapper used by tests: sample n ages using global RNG.
    Internally approximate previous behaviour by creating temporary person_uids.
    """
    temp_uids = np.random.randint(0, 2**63, size=n, dtype=np.int64)
    return sample_ages_from_uids(temp_uids, age_dist_param)


def gen_population_dask(n, current_params, arm="prospective", person_uids=None):
    # Create deterministic per-person unique id (64-bit int) drawn from the RNG state
    # if none provided. Downstream stateless draws are keyed by person_uid.
    if person_uids is None:
        person_uids = np.random.randint(0, 2**63, size=n, dtype=np.int64)
    ages = sample_ages_from_uids(person_uids, AGE_DIST)
    sev_dist = current_params["SEVERITY_DIST"]
    # Ensure sev_dist is a valid probability distribution
    sev_dist = np.array(sev_dist)
    sev_dist /= sev_dist.sum()

    df = pd.DataFrame({"age": ages})
    df["person_uid"] = person_uids

    df["sex"] = categorical(person_uids, [0, 1], probs=None, tag="sex")
    df["severity"] = categorical(person_uids, [0, 1], probs=sev_dist, tag="severity")
    df["familial"] = bernoulli(
        person_uids, current_params["familial_prop"], tag="familial"
    )
    df["diagnosed"] = np.zeros(n, bool)
    df["living"] = categorical(
        person_uids, list(range(4)), probs=[0.2, 0.1, 0.3, 0.4], tag="living"
    )
    df["employment"] = categorical(
        person_uids, list(range(3)), probs=[0.7, 0.2, 0.1], tag="employment"
    )
    df["uses_respite"] = bernoulli(person_uids, 0.3, tag="uses_respite")
    df["needs_mobility"] = bernoulli(person_uids, 0.2, tag="needs_mobility")
    df["support"] = categorical(
        person_uids, list(range(3)), probs=[0.5, 0.3, 0.2], tag="support"
    )
    df["ses"] = categorical(person_uids, list(range(5)), probs=None, tag="ses")

    # For retrospective arm, assign diagnosed status only to familial individuals
    if arm == "retrospective":
        familial_mask = df["familial"].to_numpy()
        if familial_mask.any():
            fam_uids = df.loc[familial_mask, "person_uid"].to_numpy()
            df.loc[familial_mask, "diagnosed"] = bernoulli(
                fam_uids, current_params["yield_wgs"], tag="retrospective_diag"
            )

    df["education"] = [
        EDUCATION_LEVELS[i]
        for i in categorical(
            person_uids, list(range(len(EDUCATION_LEVELS))), probs=None, tag="education"
        )
    ]
    df["age_band"] = pd.cut(
        df["age"],
        bins=[-1] + [b[1] for b in AGE_BANDS],
        labels=[f"{low}-{high}" for low, high in AGE_BANDS],
    )
    df["income"] = np.where(df["employment"] == 0, 50000.0, 0.0)
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
        "cost_ndis",
        "cost_carer",
        "cost_hospital",
        "cost_common_other",
    ]:
        df[col] = 0.0
    # Backwards-compatible: older tests expect `person_uid` not be present
    # in the cohort output and expect a specific column order. Remove the
    # internal `person_uid` column before returning while keeping the
    # ability to accept `person_uids` as input (used by callers that set
    # UIDs explicitly, e.g., newborn generation).
    if "person_uid" in df.columns:
        df = df.drop(columns=["person_uid"])
    # Return a dask dataframe with explicit known divisions to avoid
    # warnings when callers concatenate these frames later.
    from .dask_utils import safe_from_pandas

    return safe_from_pandas(df, npartitions=4)
