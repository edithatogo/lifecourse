import numpy as np
import pandas as pd
import dask.dataframe as dd
from .parameters import AGE_BREAKS, AGE_DIST, FERT_AGE_SPEC, EDUCATION_LEVELS, AGE_BANDS, AGE_BAND_P

# Build lookup table for fertility rates (base rates) - moved here as it's used by gen_population_dask
fert_data = []
for (s, (lo, hi)), r in FERT_AGE_SPEC.items():
    for age in range(lo, hi+1):
        fert_data.append({'severity': s, 'age': age, 'rate': r})
FERT_RATES_DF = pd.DataFrame(fert_data)

def sample_ages(n, age_dist_param):
    idx = np.random.choice(len(AGE_BREAKS), n, p=age_dist_param)
    return (AGE_BREAKS[idx] + np.random.randint(0, 5, n)).astype(int)

def gen_population_dask(n, current_params, arm='prospective'):
    ages = sample_ages(n, AGE_DIST)
    sev_dist = current_params['SEVERITY_DIST']
    # Ensure sev_dist is a valid probability distribution
    sev_dist = np.array(sev_dist)
    sev_dist /= sev_dist.sum()

    # Assign education levels
    education = np.random.choice(current_params['EDUCATION_LEVELS'], n)

    # Assign age bands
    age_band = np.empty(n, dtype=object)
    for i, (low, high) in enumerate(current_params['AGE_BANDS']):
        mask = (ages >= low) & (ages <= high)
        age_band[mask] = f"{low}-{high}"

    df = pd.DataFrame({
        'age': ages,
        'sex': np.random.choice(2, n),
        'severity': np.random.choice(2, n, p=sev_dist),
        'familial': np.random.random(n) < current_params['familial_prop'],
        'diagnosed': np.zeros(n, bool) if arm == 'prospective' else (np.random.random(n) < current_params['yield_wgs']),
        'living': np.random.choice(4, n, p=[0.2,0.1,0.3,0.4]),
        'employment': np.random.choice(3, n, p=[0.7,0.2,0.1]),
        'uses_respite': np.random.random(n) < 0.3,
        'needs_mobility': np.random.random(n) < 0.2,
        'support': np.random.choice(3, n, p=[0.5,0.3,0.2]),
        'ses': np.random.choice(5, n),
        'education': education, # Add education
        'age_band': age_band # Add age band
    })

    # Impute income based on severity and education
    income = np.zeros(n, dtype=np.float64)
    for i, sev_label in enumerate(['mild', 'severe']): # Assuming 0:mild, 1:severe
        for edu_label in current_params['EDUCATION_LEVELS']:
            mask = (df['severity'] == i) & (df['education'] == edu_label)
            if mask.any():
                mu, sigma = current_params['INCOME_PARAMS'][sev_label][edu_label]
                income[mask] = np.exp(np.random.normal(mu, sigma, size=mask.sum()))
    df['income'] = income # Add imputed income

    df['school'] = np.where(df['age'] < 5, -1, np.where(df['age'] < 12, 0, 1))

    for col in ['annual_cost', 'annual_qaly', 'cost_health', 'cost_edu',
                'cost_respite', 'cost_mobility', 'cost_welfare',
                'cost_emp', 'cost_morbidity']:
        df[col] = 0.0
    return dd.from_pandas(df, npartitions=4)
