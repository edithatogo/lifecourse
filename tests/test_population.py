import importlib.util
from pathlib import Path
import pytest

cupy = pytest.importorskip("cupy")
cudf = pytest.importorskip("cudf")

# Load GPU functions from archive
MODULE_PATH = Path(__file__).resolve().parents[1] / "archive" / "old_notebooks" / "LifeCourseID.py"
spec = importlib.util.spec_from_file_location("gpu_module", MODULE_PATH)
GPU = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GPU)


def test_sample_ages_gpu_shape():
    n = 5
    ages = GPU.sample_ages_gpu(n)
    assert isinstance(ages, cupy.ndarray)
    assert ages.shape == (n,)


def test_gen_population_gpu_columns():
    n = 10
    df = GPU.gen_population_gpu(n, familial_prop=0.2, arm="prospective")
    expected = {
        'age', 'sex', 'severity', 'familial', 'diagnosed', 'living',
        'employment', 'uses_respite', 'needs_mobility',
        'school', 'support', 'ses', 'annual_cost', 'annual_qaly'
    }
    assert isinstance(df, cudf.DataFrame)
    assert set(expected).issubset(set(df.columns))
    assert len(df) == n

