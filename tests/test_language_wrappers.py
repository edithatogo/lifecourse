from __future__ import annotations

from pathlib import Path


def test_r_wrapper_scaffold_points_at_python_contract() -> None:
    content = Path("bindings/r/R/lifecourse_contract.R").read_text(encoding="utf-8")

    assert "lifecourse.model_contract" in content
    assert "specs/core-api/fixtures/v1/model-run-request.fixture.json" not in content
    assert "python3" in content


def test_julia_wrapper_scaffold_points_at_python_contract() -> None:
    content = Path("bindings/julia/src/LifecourseContract.jl").read_text(
        encoding="utf-8"
    )

    assert "lifecourse.model_contract" in content
    assert "python3" in content


def test_wrapper_package_metadata_exists() -> None:
    expected = [
        "bindings/r/DESCRIPTION",
        "bindings/r/NAMESPACE",
        "bindings/r/R/lifecourse_contract.R",
        "bindings/r/tests/testthat.R",
        "bindings/r/tests/testthat/test-contract.R",
        "bindings/julia/Project.toml",
        "bindings/julia/src/LifecourseContract.jl",
        "bindings/julia/test/runtests.jl",
    ]

    for relpath in expected:
        assert Path(relpath).exists()
