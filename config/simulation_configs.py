# config/simulation_configs.py

DEFAULT_CONFIG = {
    "POP_SIZE": 62000,
    "PSA_N": 300,
    "SIMULATION_YEARS": 81,
    "CALIBRATION_POP_SIZE": 10000,
    "STRUCTURAL_UNCERTAINTY_POP_SIZE": 10000,
}

MINIMAL_TEST_CONFIG = {
    "POP_SIZE": 100,
    "PSA_N": 0, # No PSA runs for minimal test
    "SIMULATION_YEARS": 5,
    "CALIBRATION_POP_SIZE": 100,
    "STRUCTURAL_UNCERTAINTY_POP_SIZE": 100,
}

# You can add other configurations here, e.g., for medium runs, specific scenarios, etc.
# MEDIUM_TEST_CONFIG = {
#     "POP_SIZE": 100,
#     "PSA_N": 10,
#     "SIMULATION_YEARS": 10,
#     "CALIBRATION_POP_SIZE": 100,
#     "STRUCTURAL_UNCERTAINTY_POP_SIZE": 100,
# }
