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

### 2.1. Cohort-Specific Parameter Structure

#### Directory and File Structure
All cohort-specific parameters will be moved from `src/model/parameters.py` into individual YAML files within a new `config/cohorts/` directory.

```
config/
├── scenarios.yaml
└── cohorts/
    ├── _base_params.yaml      # (Optional) For parameters shared across all models (e.g., DISCOUNT rate)
    ├── id_cohort.yaml         # Parameters for the current Intellectual Disability model
    └── lynch_cohort.yaml      # Future: Parameters for a Lynch Syndrome model
```

#### Content of Cohort YAML Files
Each file (e.g., `id_cohort.yaml`) will contain all necessary parameters for that model.

*   **Metadata:** `cohort_name`, `version`, `description`.
*   **Health States:** Explicitly define the states used by the model (e.g., `severity: [mild, severe]`).
*   **Parameter Distributions:** Define all uncertain parameters in a structured way. Names should be generic to allow for abstract logic (e.g., `utility_by_state` instead of `u_base_mild`).
    ```yaml
    distributions:
      utility_by_severity:
        mild: {dist: beta, mean: 0.78, std_dev: 0.02}
        severe: {dist: beta, mean: 0.65, std_dev: 0.03}

      cost_inpatient_by_severity:
        mild: {dist: gamma, mean: 5000, std_dev_mult: 0.20}
        severe: {dist: gamma, mean: 15000, std_dev_mult: 0.20}

      diagnostic_yield: {dist: beta, mean: 0.45, std_dev: 0.05}
    ```
*   **Fixed Parameters:** Define all fixed values (e.g., `life_expectancy_by_severity`, `ndis_cost`).
*   **Data Tables:** Define data like fertility rates in a structured list format.

#### Loading Logic
A new function in `src/data_loader.py`, `load_cohort_parameters(cohort_name: str)`, will read the appropriate YAML file(s), process the contents (e.g., create distribution dicts for sampling), and return a comprehensive cohort parameter object.

### 2.2. Core Simulation Logic Abstraction (Composition/Strategy Pattern)

#### The `DiseaseModel` Interface
A new abstract base class will define the interface for any disease-specific logic.

```python
# In a new file, e.g., src/model/disease_model.py
from abc import ABC, abstractmethod

class DiseaseModel(ABC):
    """Defines the interface for a pluggable, cohort-specific disease model."""
    def __init__(self, cohort_params):
        self.params = cohort_params

    @abstractmethod
    def run_diagnosis(self, population_df, year, current_params):
        """Applies cohort-specific diagnosis logic."""
        pass

    @abstractmethod
    def run_progression(self, population_df, year, current_params):
        """Applies cohort-specific disease progression logic."""
        pass

    @abstractmethod
    def calculate_costs_and_qalys(self, population_df, year, current_params):
        """Calculates cohort-specific costs and QALYs."""
        pass
```

#### Concrete Implementations
For each cohort YAML file, there will be a corresponding concrete class.

*   `IDDiseaseModel(DiseaseModel)`: Contains the diagnosis and cost/QALY logic from the current `PopulationSystemDask`. Its `run_progression` method would likely be empty as the current model has no explicit progression logic.
*   `LynchDiseaseModel(DiseaseModel)`: A future implementation would contain logic for cancer onset in `run_progression`, carrier identification in `run_diagnosis`, and costs of surveillance/cancer treatment in `calculate_costs_and_qalys`.

#### The Refactored `PopulationSystem`
The main simulation engine becomes a composer that uses a `DiseaseModel` object.

```python
# In src/model/population_system.py
class PopulationSystem:
    def __init__(self, pop_size, cohort_params, disease_model: DiseaseModel, arm='prospective'):
        self.params = cohort_params
        self.disease_model = disease_model # The configured disease model object
        self.pop = gen_population(pop_size, self.params, arm).persist() # gen_population also generalized

    def _mortality(self):
        # Universal mortality logic (uses cohort-specific MORT_HR from self.params)
        ...

    def _fertility(self):
        # Universal fertility logic (uses cohort-specific FERT_AGE_SPEC from self.params)
        ...

    def step(self, year):
        # 1. Universal events
        self._mortality()
        new_babies_dd = self._fertility()

        # 2. Delegate cohort-specific logic
        self.pop = self.disease_model.run_diagnosis(self.pop, year, self.params)
        self.pop = self.disease_model.run_progression(self.pop, year, self.params)

        # 3. Universal updates
        self.pop = self.pop.assign(age=self.pop.age + 1)
        if new_babies_dd.npartitions > 0:
            self.pop = dd.concat([self.pop, new_babies_dd])
        self.pop = self.pop.persist()

        # 4. Delegate final cohort-specific calculation
        self.pop = self.disease_model.calculate_costs_and_qalys(self.pop, year, self.params)
```

#### Generalizing `gen_population`
The `gen_population` function would be modified to use the `cohort_params` object to define initial population characteristics rather than using hardcoded logic/probabilities.

## 3. Benefits of Proposed Architecture

*   **Extensibility:** Adding a new disease model is a clean process: create a parameter YAML and a `DiseaseModel` implementation.
*   **Maintainability:** Code is better organized. Changes to the ID model logic won't risk breaking a future Lynch Syndrome model.
*   **Testability:** The core engine (`PopulationSystem`) and each `DiseaseModel` can be unit tested independently.
*   **Clarity:** Parameters are explicitly tied to the cohort they describe.

This architecture provides a robust and scalable foundation for the future development of the LifeCourseID project.
