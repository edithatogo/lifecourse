# Historical prototype notebooks

These notebooks retain exploratory model editions and historical outputs. They
require their original data, hardware and scientific review for model execution.
The active package and its tested model live under `src/lifecourse`.

Repeated definitions retain the earlier function or class in
`_prototype_definition_history`, keyed by name and original cell/line. The final
public definition keeps its original name, and callers keep their original
resolution. This index supports comparing the retained editions.

An analysis fragment with absent historical inputs now defines
`run_archived_fragment_<original-cell-number>`. Supply its required keyword
arguments to execute the original analysis. It returns its resulting local
namespace so downstream fragments can receive the outputs explicitly. Inspect the
function signature and the cell's `requires_explicit_historical_inputs` metadata.
No numerical parameter values or simulation callbacks are supplied as defaults.

For example, pass the original PSA table to the relevant fragment, then pass its
returned GPU arrays to the histogram fragment. Existing model setup and imports
must also be available. Functions are not automatically executed when their cells
are defined. This changes the execution interface of the incomplete fragments.
It makes the missing dependencies explicit without inventing scientific inputs.

Cells with changed execution interfaces mark their retained outputs as historical
in metadata. Those outputs do not verify the revised source. Syntax, lint and
active-package test results do not establish archived GPU/Vivarium/JAX model
execution or numerical equivalence.
