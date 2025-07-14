# Design Plan: Multi-Cohort Model Architecture

This document outlines a proposed architecture for refactoring the LifeCourseID microsimulation model to support multiple, distinct disease cohorts in a modular and extensible way. This plan addresses the limitations of the current architecture, which is tightly coupled to a single disease model.

## 1. Goals

*   **Decouple** simulation logic from disease-specific parameters and rules.
*   **Enable** the addition of new disease models (e.g., Lynch Syndrome, Cystic Fibrosis) with minimal changes to the core simulation engine.
*   **Improve** maintainability and clarity by co-locating all parameters and logic for a specific cohort.
*   **Enhance** testability by allowing disease models to be tested in isolation.

## 2. Proposed Architecture

The proposed architecture is based on two main changes:
1.  A **data-driven parameter structure** using cohort-specific configuration files.
2.  A **Composition/Strategy pattern** for the core simulation logic, separating the universal simulation engine from pluggable disease-specific modules.

---

## 3. Implementation Drafts

This section contains drafted code and configuration files that serve as a concrete specification for this new architecture.
**NOTE: This code is a draft, has not been integrated, and has not been tested.**

### 3.1. Draft: Cohort-Specific Parameter File (`drafts/id_cohort.yaml`)

This YAML file defines all parameters for the Intellectual Disability cohort, moving them out of `src/model/parameters.py`.

```yaml
# Parameter Configuration for the Intellectual Disability (ID) Cohort Model
# NOTE: This is a draft file for a proposed multi-cohort architecture.

# --- METADATA ---
cohort_name: "Intellectual Disability Model"
version: 1.0
description: "Parameters for a microsimulation of a specific health condition with mild/severe states, focused on an intervention of genomic testing."

# --- HEALTH STATES ---
# Defines the discrete health states used in this model's logic.
states:
  severity: [mild, severe]
  # In a more complex model, could add more states like:
  # cancer_status: [none, colorectal_pre, colorectal_local, colorectal_distal]

# --- FIXED PARAMETERS ---
# Global constants for the simulation.
fixed_parameters:
  # Simulation Horizon & Discounting
  START_YEAR: 2020
  END_YEAR: 2100
  DISCOUNT_RATE: 0.035

  # Cost Inflation
  COST_REFERENCE_YEAR: 2017
  INFLATION_RATE: 0.03

  # Mortality
  life_expectancy_by_severity:
    mild: 74
    severe: 54

  # Employment Costs (per year)
  employment_costs_by_status: # Indexed by 0:unemployed, 1:employed, 2:not_in_labour_force
    - 0
    - 10000
    - 0

  # Specific Fixed Costs (annual, pre-inflation)
  ndis_cost: 45000
  hospitalization_cost_per_event: 8500
  mental_health_cost: 30418
  informal_care_cost: 25000

  # Carer Costs
  carer_hours_per_week_by_severity:
    mild: 5
    severe: 15
  wage_hour: 38

  # Demographics
  education_levels: [primary, secondary, tertiary]
  age_bands_for_distribution: [[0, 14], [15, 64], [65, 100]]
  age_band_proportions: [0.19, 0.65, 0.16]

  # Morbidity
  morbidity_keys: [epilepsy, asd, mental]

  # Base Demographic Data (Placeholder - currently NZ data)
  # In a real run, this would point to a file path. For this draft, values are illustrative.
  # A data loader would read these.
  baseline_mortality_by_age_band: [0.0002, 0.0001, 0.0001, 0.0002, 0.0003, 0.0005, 0.0007, 0.0011, 0.0019, 0.0035, 0.0055, 0.0085, 0.0130, 0.0200, 0.0350, 0.0600, 0.0950, 0.1500, 0.2500]
  age_distribution_proportions: [0.064, 0.067, 0.069, 0.069, 0.071, 0.076, 0.080, 0.077, 0.080, 0.079, 0.073, 0.078, 0.077, 0.072, 0.055, 0.041, 0.031, 0.022, 0.012]


# --- UNCERTAIN PARAMETERS (for PSA) ---
# Defines the distributions for parameters sampled in PSA.
# Helper functions (get_beta_params, etc.) would be used by the data loader to parse this.
distributions:
  # Using more generic names where possible
  # Cost Parameters (Gamma Distributions)
  cost_inpatient_by_severity:
    mild:   { dist: gamma, mean: 5000,  std_dev_mult: 0.20 }
    severe: { dist: gamma, mean: 15000, std_dev_mult: 0.20 }
  cost_outpatient_by_severity:
    mild:   { dist: gamma, mean: 1000,  std_dev_mult: 0.20 }
    severe: { dist: gamma, mean: 3000,  std_dev_mult: 0.20 }
  cost_pharmacy_by_severity:
    mild:   { dist: gamma, mean: 200,   std_dev_mult: 0.20 }
    severe: { dist: gamma, mean: 500,   std_dev_mult: 0.20 }

  cost_education_support:
    primary_low:    { dist: gamma, mean: 16107, std_dev_mult: 0.15 }
    primary_medium: { dist: gamma, mean: 27903, std_dev_mult: 0.15 }
    primary_high:   { dist: gamma, mean: 46733, std_dev_mult: 0.15 }
    secondary_low:    { dist: gamma, mean: 18958, std_dev_mult: 0.15 }
    secondary_medium: { dist: gamma, mean: 30789, std_dev_mult: 0.15 }
    secondary_high:   { dist: gamma, mean: 49604, std_dev_mult: 0.15 }

  cost_respite: { dist: gamma, mean: 13024, std_dev_mult: 0.20 }
  cost_mobility: { dist: gamma, mean: 2493, std_dev_mult: 0.20 }

  cost_welfare_by_severity:
    mild:   { dist: gamma, mean: 3000, std_dev_mult: 0.20 }
    severe: { dist: gamma, mean: 8000, std_dev_mult: 0.20 }

  cost_morbidity:
    epilepsy: { dist: gamma, mean: 2000, std_dev_mult: 0.20 }
    asd:      { dist: gamma, mean: 1500, std_dev_mult: 0.20 }
    mental:   { dist: gamma, mean: 1000, std_dev_mult: 0.20 }

  cost_adjustment_wgs_diagnosis: { dist: normal, mean: -1000, std_dev: 100 }

  # Utility Parameters (Beta Distributions)
  utility_base_by_severity:
    mild:   { dist: beta, mean: 0.78, std_dev: 0.02 }
    severe: { dist: beta, mean: 0.65, std_dev: 0.03 }

  utility_decay_rate: { dist: beta, mean: 0.0005, std_dev: 0.00005 }
  utility_gain_diagnosis: { dist: beta, mean: 0.02, std_dev: 0.002 }
  utility_gain_carer: { dist: beta, mean: 0.05, std_dev: 0.005 }
  utility_adjustment_wgs_diagnosis: { dist: beta, mean: 0.01, std_dev: 0.001 }

  utility_decrement_morbidity:
    epilepsy: { dist: beta, mean: 0.04, std_dev: 0.005 }
    asd:      { dist: beta, mean: 0.03, std_dev: 0.005 }
    mental:   { dist: beta, mean: 0.05, std_dev: 0.005 }

  # Probability / Rate Parameters
  mortality_hazard_ratio_by_severity:
    mild:   { dist: lognormal, s: 0.1, scale: 2.0 }
    severe: { dist: lognormal, s: 0.1, scale: 4.0 }

  probability_morbidity:
    epilepsy: { dist: beta, mean: 0.25, std_dev: 0.03 }
    asd:      { dist: beta, mean: 0.30, std_dev: 0.03 }
    mental:   { dist: beta, mean: 0.35, std_dev: 0.04 }

  proportion_familial: { dist: beta, alpha: 30, beta: 150 }
  diagnostic_yield_wgs: { dist: beta, alpha: 45, beta: 55 }
  proportion_severity_mild: { dist: beta, mean: 0.70, std_dev: 0.03 }
  fertility_rate_multiplier: { dist: lognormal, s: 0.1, scale: 1.0 }

  # Fixed Value Parameters within Distributions section
  min_test_age: { dist: fixed, value: 0 }

  # Hospitalization rates (Poisson mean)
  hospitalization_rate_by_severity:
    mild: { dist: fixed, value: 0.5 }
    moderate: { dist: fixed, value: 1.5 } # Note: Model uses 3 levels here
    severe: { dist: fixed, value: 3.0 }

  # Income Parameters (Log-normal) - could be structured under distributions or as a separate table
  income_distribution_params:
    mild_primary:   { dist: lognormal, mu: 10.5, sigma: 0.5 }
    mild_secondary: { dist: lognormal, mu: 10.8, sigma: 0.4 }
    mild_tertiary:  { dist: lognormal, mu: 11.2, sigma: 0.3 }
    severe_primary:   { dist: lognormal, mu: 10.3, sigma: 0.6 }
    severe_secondary: { dist: lognormal, mu: 10.6, sigma: 0.5 }
    severe_tertiary:  { dist: lognormal, mu: 10.9, sigma: 0.4 }

```

### 3.2. Draft: `DiseaseModel` Abstract Base Class (`drafts/disease_model.py`)

```python
"""
This file contains the draft of the DiseaseModel abstract base class.
NOTE: This code is a draft, has not been integrated, and has not been tested.
It is part of a design exercise to refactor the model for multi-cohort support.
"""
from abc import ABC, abstractmethod

class DiseaseModel(ABC):
    """
    An abstract base class that defines the interface for a cohort-specific disease model.
    It encapsulates the unique logic for disease progression, diagnosis, costs, and QALYs.

    Each concrete implementation of this class will represent the specific logic
    for a particular disease or cohort (e.g., Intellectual Disability, Lynch Syndrome).
    """
    def __init__(self, cohort_params: dict):
        """
        Initializes the disease model with a dictionary of cohort-specific parameters.

        Args:
            cohort_params (dict): A dictionary containing all parameters (fixed,
                                  distributions, data tables) needed for this cohort's model.
        """
        self.params = cohort_params

    @abstractmethod
    def run_diagnosis(self, population_df, year: int, sampled_params: dict, arm: str):
        """
        Applies cohort-specific diagnosis logic to the population.
        """
        pass

    @abstractmethod
    def run_progression(self, population_df, year: int, sampled_params: dict):
        """
        Applies cohort-specific disease progression logic (e.g., cancer onset,
        changes in severity, etc.).
        """
        pass

    @abstractmethod
    def calculate_costs_and_qalys(self, population_df, year: int, sampled_params: dict, arm: str):
        """
        Calculates and assigns all cohort-specific costs and QALYs for the given year.
        """
        pass
```

### 3.3. Draft: Concrete `IDDiseaseModel` Implementation (`drafts/id_model.py`)

```python
"""
This file contains the draft of the IDDiseaseModel class.
NOTE: This code is a draft, has not been integrated, and has not been tested.
It is part of a design exercise to refactor the model for multi-cohort support.
"""
import numpy as np
import pandas as pd
import dask.dataframe as dd

# from drafts.disease_model import DiseaseModel # Assumes this is available

class IDDiseaseModel(DiseaseModel):
    """
    A concrete implementation of DiseaseModel for the Intellectual Disability cohort.
    """

    def run_diagnosis(self, population_df, year: int, sampled_params: dict, arm: str):
        if arm != 'prospective':
            return population_df # Return unchanged population if not prospective arm

        def diagnosis_partition(df):
            if df.empty:
                return df
            min_test_age = sampled_params.get('min_test_age', 0)
            yield_wgs = sampled_params.get('diagnostic_yield_wgs', 0) # Using generic name

            mask = (~df['diagnosed']) & df['familial'] & (df['age'] >= min_test_age)
            cnt = int(mask.sum())
            if cnt > 0:
                diag_outcomes = np.random.random(cnt) < yield_wgs
                df.loc[mask, 'diagnosed'] = diag_outcomes
            return df

        # The engine would run this map_partitions call
        return population_df.map_partitions(diagnosis_partition, meta=population_df._meta)


    def run_progression(self, population_df, year: int, sampled_params: dict):
        # The current ID model has no explicit disease progression logic.
        return population_df

    def calculate_costs_and_qalys(self, population_df, year: int, sampled_params: dict, arm: str):
        # This function would contain the detailed cost/qaly logic from the original
        # PopulationSystemDask._cost_qaly, using the generic parameter names from the
        # new YAML structure. The logic is extensive and is transposed from the original.
        # For brevity in this design doc, the full implementation is omitted but would
        # be a direct translation of the existing logic.

        # --- Example Snippet ---
        # START_YEAR = sampled_params.get('START_YEAR')
        # DISCOUNT = sampled_params.get('DISCOUNT_RATE')
        # disc = 1 / ((1 + DISCOUNT)**(year - START_YEAR))
        # ... and so on for all costs and qaly calculations.

        # The function must return the dataframe with all cost/qaly columns assigned.
        # return population_df.map_partitions(cost_qaly_partition_func, meta=...)
        return population_df # Placeholder for draft
```

### 3.4. Draft: Refactored `PopulationSystem` Engine (`drafts/population_system.py`)

```python
"""
This file contains the draft of the refactored PopulationSystem class.
NOTE: This code is a draft, has not been integrated, and has not been tested.
"""
import numpy as np
import pandas as pd
import dask.dataframe as dd
# from drafts.disease_model import DiseaseModel
# from .cohort import gen_population

class PopulationSystem:
    """
    A generalized microsimulation engine that handles universal simulation events
    and delegates cohort-specific logic to a provided DiseaseModel object.
    """
    def __init__(self, pop_size: int, cohort_params: dict, disease_model: DiseaseModel, arm: str = 'prospective'):
        self.arm = arm
        self.params = cohort_params
        self.disease_model = disease_model
        # self.pop = gen_population(pop_size, self.params, self.arm).persist() # gen_population would be generalized
        self.pop = None # Placeholder for draft

    def _mortality(self):
        # Universal mortality logic (transposed from original)
        # Uses cohort-specific parameters like ABS_MORT, MORT_HR, LIFE_EXP_NP from self.params
        ...
        pass

    def _fertility(self):
        # Universal fertility logic (transposed from original)
        # Uses cohort-specific FERT_RATES_DF, fertility_multiplier from self.params
        ...
        return None # Placeholder return for draft

    def step(self, year: int):
        if self.pop is None: return

        # 1. Universal events
        self._mortality()
        new_babies_dd = self._fertility()

        # 2. Delegate cohort-specific logic
        self.pop = self.disease_model.run_diagnosis(self.pop, year, self.params, self.arm)
        self.pop = self.disease_model.run_progression(self.pop, year, self.params)

        # 3. Universal updates
        self.pop = self.pop.assign(age=self.pop.age + 1)
        if new_babies_dd is not None and new_babies_dd.npartitions > 0:
            self.pop = dd.concat([self.pop, new_babies_dd])
        self.pop = self.pop.persist()

        # 4. Delegate final cohort-specific calculation
        self.pop = self.disease_model.calculate_costs_and_qalys(self.pop, year, self.params, self.arm)
```

### 3.5. Loading and Orchestration (Conceptual)

`main.py` would be updated to:
1.  Load a specific cohort's parameters: `id_params = load_cohort_parameters("id_cohort")`.
2.  Instantiate the corresponding disease model: `id_model = IDDiseaseModel(id_params)`.
3.  Instantiate the simulation engine with the parameters and disease model: `sim_p = PopulationSystem(pop_size, id_params, id_model, arm='prospective')`.
4.  Run the simulation loop as it does now.
```
