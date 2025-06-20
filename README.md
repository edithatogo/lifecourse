# LifeCourseID
Lifecourse Dynamic Population Microsimulation of Intellectual Disability


## Important Components
Key sections from the notebook:

* Global parameters – defines constants such as start/end years, population size, demographic distributions, mortality tables, fertility rates, utilities, and cost parameters.
* Cohort generator – gen_population_gpu creates an initial population with random attributes stored in a GPU-backed dataframe.
* Simulation engine – PopulationSystemGPU manages annual transitions for mortality, fertility, diagnosis, and cost/QALY accumulation. The class methods use cupy and cudf to perform computations on the GPU.
* Run helpers – run_sim and run_scenario run the model for prospective and retrospective arms, aggregating costs and QALYs or returning detailed yearly outputs.

The rest of the notebook runs deterministic scenarios, probabilistic sensitivity analyses, and produces numerous plots summarizing results (ICER tables, CEAC/EVPI, tornado charts, etc.).

## What to Know
* GPU environment – The entire simulation relies on CUDA-based libraries (cupy and cudf). Running the notebook requires a GPU-enabled Python setup.
* Health-economic concepts – The model calculates QALYs and costs, computing incremental cost-effectiveness ratios (ICERs) and related metrics typical in health economics.
* Notebook-centric – All code and analyses reside in this single notebook. There is no package structure or external modules.

## Pointers for Further Learning
* Follow each notebook section in order to see how the population is initialized and simulated year by year.
* Understand the PopulationSystemGPU class—its _mortality, _fertility, _diagnosis, and _cost_qaly methods implement the yearly dynamics.
* Review health-economic methods: deterministic vs probabilistic simulation, cost-effectiveness planes, CEAC/EVPI calculations, and budget impact analysis.
* Explore GPU data libraries (cupy and cudf) if unfamiliar, since they replace NumPy and pandas functionality with GPU acceleration.

Because there are only three files and the entire logic is in the notebook, reading the notebook end-to-end provides a complete understanding of the project.
