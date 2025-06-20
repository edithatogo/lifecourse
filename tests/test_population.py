import json
import sys
import types
import numpy as np
import pandas as pd


def load_population_functions():
    """Load functions from the notebook using numpy/pandas as cupy/cudf."""
    with open("LifeCourseID - v1, 20250620.ipynb") as f:
        nb = json.load(f)

    code_blocks = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        if "## 2. Global Parameters" in src:
            code_blocks.append(src)
        elif "def sample_ages_gpu" in src:
            code_blocks.append(src)
            break
    module = types.ModuleType("nb_funcs")
    sys.modules['cupy'] = np
    sys.modules['cudf'] = pd
    module.__dict__['cp'] = np
    module.__dict__['cudf'] = pd
    for block in code_blocks:
        exec(block, module.__dict__)
    return module.sample_ages_gpu, module.gen_population_gpu

sample_ages_gpu, gen_population_gpu = load_population_functions()


def test_sample_ages_gpu_shape():
    n = 10
    ages = sample_ages_gpu(n)
    assert isinstance(ages, np.ndarray)
    assert ages.shape == (n,)


def test_gen_population_gpu_structure():
    n = 5
    df = gen_population_gpu(n, 0.3)
    expected_cols = [
        'age', 'sex', 'severity', 'familial', 'diagnosed', 'living',
        'employment', 'uses_respite', 'needs_mobility', 'school',
        'support', 'ses', 'annual_cost', 'annual_qaly'
    ]
    assert list(df.columns) == expected_cols
    assert df.shape == (n, len(expected_cols))
