import pytest
import numpy as np
from importlib.machinery import SourceFileLoader
from pathlib import Path

cupy = pytest.importorskip('cupy')
cudf = pytest.importorskip('cudf')

# Load module containing GPU functions
module_path = Path(__file__).resolve().parents[1] / 'archive' / 'old_notebooks' / 'LifeCourseID.py'
LifeCourseID_gpu = SourceFileLoader('LifeCourseID_gpu', str(module_path)).load_module()

sample_ages_gpu = LifeCourseID_gpu.sample_ages_gpu
gen_population_gpu = LifeCourseID_gpu.gen_population_gpu


def test_sample_ages_gpu_shape():
    n = 5
    ages = sample_ages_gpu(n)
    assert isinstance(ages, cupy.ndarray)
    assert ages.shape == (n,)


def test_gen_population_gpu_output():
    n = 10
    df = gen_population_gpu(n, 0.2, arm='prospective')
    assert isinstance(df, cudf.DataFrame)
    assert len(df) == n
    expected_cols = {
        'age', 'sex', 'severity', 'familial', 'diagnosed',
        'living', 'employment', 'uses_respite', 'needs_mobility',
        'school', 'support', 'ses', 'annual_cost', 'annual_qaly'
    }
    assert expected_cols.issubset(set(df.columns))
