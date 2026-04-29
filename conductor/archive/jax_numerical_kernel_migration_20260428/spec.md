# JAX Numerical Kernel Migration

## Overview
Identify and migrate selected pure numerical kernels to optional JAX execution
where benchmark evidence supports acceleration or clearer vectorization.

## Initial Candidate Areas
- Net-benefit and EVPI/EVSI vector calculations.
- PSA array transforms that do not depend on pandas objects.
- Cost/QALY kernels only after their data dependencies are isolated.

## Acceptance Criteria
- JAX remains optional.
- Each JAX path has numpy equivalence tests.
- Missing JAX failures remain clear.
