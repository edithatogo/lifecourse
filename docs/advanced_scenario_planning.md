# Advanced Scenario Planning for Genomic Testing

This document outlines detailed considerations for implementing more sophisticated scenarios related to diagnostic genetic/genomic testing in the lifecourse microsimulation model. These plans are conceptual and intended for future development when the execution environment is stable and allows for coding and testing.

## Scenario 1: Modeling Different Genomic Test Types

**Concept:** Allow the model to simulate different types of genomic tests (e.g., Targeted Panel, Exome Sequencing, Genome Sequencing). These tests would have distinct costs, diagnostic yields for the primary condition, and potentially different probabilities and impacts of secondary findings like Variants of Uncertain Significance (VUS) or Incidental Findings (IFs).

**1. New Parameters Needed (Examples):**

For each test type (e.g., identifiers: `panel`, `exome`, `genome`):

*   **Cost of Test:**
    *   `cost_test_panel`: Cost of the targeted panel. (Type: float, e.g., `500 * INFLATION_FACTOR`)
    *   `cost_test_exome`: Cost of exome sequencing. (Type: float, e.g., `1200 * INFLATION_FACTOR`)
    *   `cost_test_genome`: Cost of genome sequencing. (Type: float, e.g., `2000 * INFLATION_FACTOR`)
*   **Diagnostic Yield (Primary Finding):**
    *   `yield_test_panel`: Probability of pathogenic variant detection for the primary condition with panel. (Type: float, Range: 0-1, e.g., 0.25)
    *   `yield_test_exome`: Probability for exome. (Type: float, Range: 0-1, e.g., 0.40)
    *   `yield_test_genome`: Probability for genome. (Type: float, Range: 0-1, e.g., 0.50)
        *   *Note:* The current `yield_wgs` parameter might serve as a baseline or be mapped to one of these specific test types.
*   **Probability of VUS:**
    *   `prob_vus_panel`: Probability of detecting at least one VUS. (Type: float, Range: 0-1, e.g., 0.10)
    *   `prob_vus_exome`: (e.g., 0.30)
    *   `prob_vus_genome`: (e.g., 0.40)
*   **Cost Associated with VUS Follow-up:**
    *   `cost_vus_follow_up`: Average cost for VUS management (e.g., further analysis, parental testing). (Type: float, e.g., `300 * INFLATION_FACTOR`)
*   **QALY Impact of VUS (e.g., anxiety, uncertainty):**
    *   `qaly_decrement_vus`: QALY decrement due to a VUS finding, possibly temporary. (Type: float, e.g., 0.01 for 1 year).
*   **Probability of Actionable Incidental Finding (IF):**
    *   `prob_if_panel`: (e.g., 0.005, potentially very low/zero for targeted panels)
    *   `prob_if_exome`: (e.g., 0.02)
    *   `prob_if_genome`: (e.g., 0.03)
*   **Cost Associated with IF Follow-up:**
    *   `cost_if_follow_up`: Average cost for managing/acting on an actionable IF. (Type: float, e.g., `1000 * INFLATION_FACTOR`)
*   **QALY Impact of Actionable IF (e.g., benefit from early intervention for the IF):**
    *   `qaly_gain_if`: QALY gain associated with an actionable IF. (Type: float, e.g., 0.05, one-time or ongoing).

**2. Logic Changes in `PopulationSystemDask`:**

*   **Parameter Access:** `prepare_dask_params` would incorporate these new parameters into the `params` dictionary.
*   **`_diagnosis()` Method:**
    *   A new parameter like `current_params['active_test_type']` (e.g., 'panel', 'exome') would indicate the test being used in a given scenario.
    *   The diagnostic yield applied would be selected based on `active_test_type` (e.g., `params['yield_test_' + active_test_type]`).
    *   After determining the primary diagnosis, additional random draws based on `prob_vus_...` and `prob_if_...` for the active test type would determine VUS/IF findings.
    *   New boolean columns on the person DataFrame (e.g., `has_vus`, `has_if`) might be needed to track these secondary findings.
*   **`_cost_qaly()` Method:**
    *   Apply the cost of the `active_test_type` in the year of diagnosis.
    *   If `has_vus` is true, apply `cost_vus_follow_up` and `qaly_decrement_vus`.
    *   If `has_if` is true, apply `cost_if_follow_up` and `qaly_gain_if`.
    *   The existing `WGS_DIAG_COST_ADJUSTMENT` and `WGS_DIAG_QALY_ADJUSTMENT` might need to be re-evaluated: are they general diagnosis effects, or specific to a comprehensive test like WGS, or should they be made test-type specific?

**3. Configuration (`config/scenarios.yaml`):**

*   A scenario could specify the `active_test_type`:
    ```yaml
    scenarios:
      run_with_panel:
        active_test_type: 'panel'
        # Other parameters can still override the defaults for 'panel' if needed
        # For example, to model an "improved panel":
        # yield_test_panel: 0.30
      run_with_exome:
        active_test_type: 'exome'
    ```
*   The base definitions for each test type's characteristics (`cost_test_panel`, `yield_test_panel`, etc.) would reside in `src/model/parameters.py::DISTRIBUTIONS` or as global constants.

---

## Scenario 2: Incorporating Pre- and Post-Test Genetic Counseling

**Concept:** Model the costs and potential QALY impacts of genetic counseling sessions provided before and/or after genomic testing.

**1. New Parameters Needed (Examples):**

*   **Costs:**
    *   `cost_pre_test_counseling`: (Type: float, e.g., `150 * INFLATION_FACTOR`)
    *   `cost_post_test_counseling`: (Type: float, e.g., `150 * INFLATION_FACTOR`)
*   **Uptake Probabilities:**
    *   `prob_pre_test_counseling`: Probability of attending pre-test counseling if eligible for testing. (Type: float, Range: 0-1, e.g., 0.80)
    *   `prob_post_test_counseling_if_tested`: Probability of attending post-test counseling if a test was performed. (Type: float, Range: 0-1, e.g., 0.90)
    *   `prob_post_test_counseling_if_positive`: (Optional) Higher probability if test is positive. (Type: float, Range: 0-1, e.g., 0.95)
    *   `prob_post_test_counseling_if_vus`: (Optional) Probability of specific/additional counseling if a VUS is found. (Type: float, Range: 0-1, e.g., 0.75)
*   **QALY Impact (Optional):**
    *   `qaly_adj_counseling`: One-time or short-term QALY gain from counseling (e.g., reduced anxiety, improved coping). (Type: float, e.g., 0.005 for 1 year).

**2. Logic Changes in `PopulationSystemDask`:**

*   **Parameter Access:** New parameters included in `params` via `prepare_dask_params`.
*   **Individual Attributes (Tracking):**
    *   Consider adding `df['received_pre_counseling']` (boolean) and `df['received_post_counseling']` (boolean or count).
*   **Timing & Logic:**
    *   **Pre-Test Counseling:**
        *   In `_diagnosis()` (or a preceding dedicated method), for individuals eligible for testing: apply `prob_pre_test_counseling`.
        *   If they receive it, flag them and accrue `cost_pre_test_counseling` in `_cost_qaly()` for that year. Apply `qaly_adj_counseling` if modeled.
        *   *Advanced:* Pre-test counseling could potentially modify a *test uptake probability* if testing itself is not assumed to be 100% for eligibles.
    *   **Post-Test Counseling:**
        *   In `_diagnosis()` or `_cost_qaly()`, after test results are known:
        *   For those tested, apply `prob_post_test_counseling_if_tested` (or more specific probabilities like `_if_positive`, `_if_vus`).
        *   If they receive it, flag them and accrue `cost_post_test_counseling`. Apply `qaly_adj_counseling`.
*   **`_cost_qaly()` Method:**
    *   Add logic to sum counseling costs to `annual_cost` based on flags/counts.
    *   Add logic to apply `qaly_adj_counseling` to `annual_qaly`.

**3. Configuration (`config/scenarios.yaml`):**

*   Scenarios could enable/disable counseling or set its parameters:
    ```yaml
    scenarios:
      intervention_with_counseling:
        # Parameters for the main intervention (e.g., test type)
        active_test_type: 'exome'
        # Counseling parameters
        prob_pre_test_counseling: 0.90
        cost_pre_test_counseling: 160 # Override default if needed
        prob_post_test_counseling_if_tested: 0.95
        cost_post_test_counseling: 160
        qaly_adj_counseling: 0.005

      intervention_no_counseling:
        active_test_type: 'exome'
        prob_pre_test_counseling: 0.0
        prob_post_test_counseling_if_tested: 0.0
    ```
*   Base values for counseling costs and probabilities would be in `src/model/parameters.py` (either fixed or as distributions).

---

These outlines provide a starting point for enhancing the scenario analysis capabilities of the lifecourse model concerning genomic testing. Implementation would require careful consideration of interactions with existing model logic and thorough testing (once the environment permits).
