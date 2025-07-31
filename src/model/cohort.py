import numpy as np
import pandas as pd
import dask.dataframe as dd
from .parameters import AGE_BREAKS, AGE_DIST, FERT_AGE_SPEC, EDUCATION_LEVELS, AGE_BANDS, AGE_BAND_P

# Build lookup table for fertility rates (base rates)
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

    df = pd.DataFrame({
        'age': ages,
        'sex': np.random.choice(2, n),
        'severity': np.random.choice(2, n, p=sev_dist),
        'familial': np.random.random(n) < current_params['familial_prop'],
        'diagnosed': np.zeros(n, bool),
        'living': np.random.choice(4, n, p=[0.2,0.1,0.3,0.4]),
        'employment': np.random.choice(3, n, p=[0.7,0.2,0.1]),
        'uses_respite': np.random.random(n) < 0.3,
        'needs_mobility': np.random.random(n) < 0.2,
        'support': np.random.choice(3, n, p=[0.5,0.3,0.2]),
        'ses': np.random.choice(5, n)
    })

    if arm == 'retrospective':
        df['diagnosed'] = np.random.random(n) < current_params['yield_wgs']

    df['education'] = np.random.choice(EDUCATION_LEVELS, n)
    df['age_band'] = pd.cut(df['age'], bins=[-1] + [b[1] for b in AGE_BANDS], labels=[f"{low}-{high}" for low, high in AGE_BANDS])
    df['income'] = np.where(df['employment'] == 0, 50000.0, 0.0) # Placeholder: 50k for employed, 0 otherwise
    df['school'] = np.where(df['age'] < 5, -1, np.where(df['age'] < 12, 0, 1))

    for col in ['annual_cost', 'annual_qaly', 'cost_health', 'cost_edu',
                'cost_respite', 'cost_mobility', 'cost_welfare',
                'cost_emp', 'cost_morbidity', 'cost_ndis', 'cost_carer', 'cost_hospital', 'cost_common_other']:
        df[col] = 0.0
    return dd.from_pandas(df, npartitions=4)