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
    def run_diagnosis(self, population_df, year: int, sampled_params: dict):
        """
        Applies cohort-specific diagnosis logic to the population.

        Args:
            population_df (dd.DataFrame): The Dask DataFrame representing the population.
            year (int): The current simulation year.
            sampled_params (dict): The dictionary of parameters for the current simulation run
                                   (e.g., mean parameters for deterministic, or a PSA sample).

        Returns:
            dd.DataFrame: The population DataFrame with updated diagnosis states.
        """

    @abstractmethod
    def run_progression(self, population_df, year: int, sampled_params: dict):
        """
        Applies cohort-specific disease progression logic (e.g., cancer onset,
        changes in severity, etc.).

        Args:
            population_df (dd.DataFrame): The Dask DataFrame representing the population.
            year (int): The current simulation year.
            sampled_params (dict): The dictionary of parameters for the current simulation run.

        Returns:
            dd.DataFrame: The population DataFrame with updated health states.
        """

    @abstractmethod
    def calculate_costs_and_qalys(self, population_df, year: int, sampled_params: dict):
        """
        Calculates and assigns all cohort-specific costs and QALYs for the given year.

        Args:
            population_df (dd.DataFrame): The Dask DataFrame representing the population.
            year (int): The current simulation year.
            sampled_params (dict): The dictionary of parameters for the current simulation run.

        Returns:
            dd.DataFrame: The population DataFrame with all annual cost and QALY columns populated.
        """
