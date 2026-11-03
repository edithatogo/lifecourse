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

This section contains drafted code, configuration, and test files that serve as a concrete specification for this new architecture.
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

# --- FIXED PARAMETERS ---
# Global constants for the simulation.
fixed_parameters:
  START_YEAR: 2020
  END_YEAR: 2100
  DISCOUNT_RATE: 0.035
  COST_REFERENCE_YEAR: 2017
  INFLATION_RATE: 0.03
  life_expectancy_by_severity:
    mild: 74
    severe: 54
  employment_costs_by_status: [0, 10000, 0]
  ndis_cost: 45000
  hospitalization_cost_per_event: 8500
  mental_health_cost: 30418
  informal_care_cost: 25000
  carer_hours_per_week_by_severity: { mild: 5, severe: 15 }
  wage_hour: 38
  education_levels: [primary, secondary, tertiary]
  age_bands_for_distribution: [[0, 14], [15, 64], [65, 100]]
  age_band_proportions: [0.19, 0.65, 0.16]
  morbidity_keys: [epilepsy, asd, mental]
  baseline_mortality_by_age_band: [0.0002, 0.0001, 0.0001, 0.0002, 0.0003, 0.0005, 0.0007, 0.0011, 0.0019, 0.0035, 0.0055, 0.0085, 0.0130, 0.0200, 0.0350, 0.0600, 0.0950, 0.1500, 0.2500]
  age_distribution_proportions: [0.064, 0.067, 0.069, 0.069, 0.071, 0.076, 0.080, 0.077, 0.080, 0.079, 0.073, 0.078, 0.077, 0.072, 0.055, 0.041, 0.031, 0.022, 0.012]

# --- UNCERTAIN PARAMETERS (for PSA) ---
distributions:
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
    # ... and so on for all education costs
  utility_base_by_severity:
    mild:   { dist: beta, mean: 0.78, std_dev: 0.02 }
    severe: { dist: beta, mean: 0.65, std_dev: 0.03 }
  # ... etc. for all other uncertain parameters
```

### 3.2. Draft: `DiseaseModel` Abstract Base Class (`drafts/disease_model.py`)

```python
"""
This file contains the draft of the DiseaseModel abstract base class.
"""

from abc import ABC, abstractmethod


class DiseaseModel(ABC):
    """
    An abstract base class that defines the interface for a cohort-specific disease model.
    """

    def __init__(self, cohort_params: dict):
        self.params = cohort_params

    @abstractmethod
    def run_diagnosis(self, population_df, year: int, sampled_params: dict, arm: str):
        pass

    @abstractmethod
    def run_progression(self, population_df, year: int, sampled_params: dict):
        pass

    @abstractmethod
    def calculate_costs_and_qalys(
        self, population_df, year: int, sampled_params: dict, arm: str
    ):
        pass
```

### 3.3. Draft: Concrete `IDDiseaseModel` Implementation (`drafts/id_model.py`)

```python
"""
This file contains the draft of the IDDiseaseModel class.
"""

import numpy as np
# from drafts.disease_model import DiseaseModel


class IDDiseaseModel(DiseaseModel):
    """
    A concrete implementation of DiseaseModel for the Intellectual Disability cohort.
    """

    def run_diagnosis(self, population_df, year: int, sampled_params: dict, arm: str):
        if arm != "prospective":
            return population_df

        def diagnosis_partition(df):
            if df.empty:
                return df
            min_test_age = sampled_params.get("min_test_age", 0)
            yield_wgs = sampled_params.get("yield_wgs", 0)
            mask = (~df["diagnosed"]) & df["familial"] & (df["age"] >= min_test_age)
            cnt = int(mask.sum())
            if cnt > 0:
                diag_outcomes = np.random.random(cnt) < yield_wgs
                df.loc[mask, "diagnosed"] = diag_outcomes
            return df

        return population_df.map_partitions(
            diagnosis_partition, meta=population_df._meta
        )

    def run_progression(self, population_df, year: int, sampled_params: dict):
        return population_df  # No progression in this model

    def calculate_costs_and_qalys(
        self, population_df, year: int, sampled_params: dict, arm: str
    ):
        # Full logic from original PopulationSystemDask._cost_qaly transposed here
        # ... (full implementation omitted for brevity in this design doc)
        return population_df  # Placeholder
```

### 3.4. Draft: Refactored `PopulationSystem` Engine (`drafts/population_system.py`)

```python
"""
This file contains the draft of the refactored PopulationSystem class.
"""

import dask.dataframe as dd
# from drafts.disease_model import DiseaseModel
# from .cohort import gen_population


class PopulationSystem:
    """
    A generalized microsimulation engine.
    """

    def __init__(
        self,
        pop_size: int,
        cohort_params: dict,
        disease_model: DiseaseModel,
        arm: str = "prospective",
    ):
        self.arm = arm
        self.params = cohort_params
        self.disease_model = disease_model
        # self.pop = gen_population(pop_size, self.params, self.arm).persist()
        self.pop = None  # Placeholder

    def _mortality(self):
        # Universal mortality logic from original implementation
        pass

    def _fertility(self):
        # Universal fertility logic from original implementation
        return None

    def step(self, year: int):
        if self.pop is None:
            return
        self._mortality()
        new_babies_dd = self._fertility()
        self.pop = self.disease_model.run_diagnosis(
            self.pop, year, self.params, self.arm
        )
        self.pop = self.disease_model.run_progression(self.pop, year, self.params)
        self.pop = self.pop.assign(age=self.pop.age + 1)
        if new_babies_dd is not None:
            self.pop = dd.concat([self.pop, new_babies_dd])
        self.pop = self.pop.persist()
        self.pop = self.disease_model.calculate_costs_and_qalys(
            self.pop, year, self.params, self.arm
        )
```

---

## 4. Drafted Test Cases

This section provides drafted unit tests that define the contract for how the new components should behave.

### 4.1. Draft: Tests for `IDDiseaseModel` (`drafts/test_id_model.py`)

```python
"""
Drafted unit tests for the drafted IDDiseaseModel class.
"""

import unittest
import pandas as pd
import numpy as np
# from drafts.disease_model import DiseaseModel
# from drafts.id_model import IDDiseaseModel


class TestIDDiseaseModel(unittest.TestCase):
    def setUp(self):
        # A mock parameter dictionary for testing
        self.mock_params = {
            "min_test_age": 0,
            "yield_wgs": 0.5,
            # ... other necessary parameters ...
        }
        # self.id_model = IDDiseaseModel(cohort_params=self.mock_params)

    def test_run_diagnosis(self):
        # Test logic with a sample pandas DataFrame
        # ...
        pass

    def test_calculate_costs_and_qalys(self):
        # Test cost/qaly logic with a sample pandas DataFrame and predictable random seeds
        # ...
        pass
```

### 4.2. Draft: Tests for Refactored `PopulationSystem` (`drafts/test_population_system_refactored.py`)

```python
"""
Drafted unit tests for the refactored PopulationSystem class.
"""

import unittest
from unittest.mock import MagicMock
import pandas as pd
# from drafts.disease_model import DiseaseModel
# from drafts.population_system import PopulationSystem


class MockDiseaseModel(DiseaseModel):
    # Mock implementation with a call log
    ...


class TestRefactoredPopulationSystem(unittest.TestCase):
    def setUp(self):
        self.mock_disease_model = MockDiseaseModel({})
        # ...

    def test_step_method_orchestration(self):
        # Test that step() calls universal and disease-specific methods in correct order
        # Use MagicMock to patch _mortality and _fertility
        # Use the call_log on the mock_disease_model to check call order
        # ...
        pass
```
