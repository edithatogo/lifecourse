import pandas as pd
import numpy as np
import yaml

def load_scenarios_from_yaml(file_path):
    with open(file_path, 'r') as f:
        config = yaml.safe_load(f)
    return config['scenarios']

def load_nz_population_distribution(url=None): # For New Zealand data
    """
    Load NZ population distribution by age and sex from Stats NZ public CSV.
    Returns a DataFrame with columns ['age', 'sex', 'count'].
    """
    if url is None:
        url = (
            'https://www.stats.govt.nz/assets/Uploads/Population-estimates-at-'
            'year-end-March-2024/Download-data/population-estimates-at-year-end-'
            'march-2024-csv.csv'
        )
    pop = pd.read_csv(url)
    if 'Geography' in pop.columns:
        pop = pop[pop['Geography'] == 'New Zealand']
    pop = pop.rename(columns={'Age': 'age', 'Sex': 'sex', 'Population': 'count'})
    pop['age'] = (
        pop['age'].astype(str)
           .str.extract(r"(\d+)")[0]
           .astype(int)
    )
    return pop[['age', 'sex', 'count']]


def load_nz_life_table_hazards(url=None): # For New Zealand data
    """
    Load NZ life table hazards (central mortality rates) from Stats NZ CSV.
    Returns dict hazards[sex] = array of hazard per age index.
    """
    if url is None:
        url = (
            'https://www.stats.govt.nz/assets/Uploads/Life-tables-Year-ended-'
            'December-2020/Life-tables-year-ended-December-2020.csv'
        )
    lt = pd.read_csv(url)
    lt = lt.rename(columns={'Sex': 'sex', 'Age': 'age', 'nMx': 'hazard'})
    hazards = {sex: group.sort_values('age')['hazard'].values
               for sex, group in lt.groupby('sex')}
    return hazards


