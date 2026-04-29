from __future__ import annotations

from pathlib import Path


def test_consumer_scaffold_files_exist() -> None:
    expected = [
        "bindings/go/go.mod",
        "bindings/go/internal/contract/contract.go",
        "bindings/go/internal/contract/contract_test.go",
        "bindings/go/cmd/lifecourse-contract/main.go",
        "bindings/typescript/package.json",
        "bindings/typescript/tsconfig.json",
        "bindings/typescript/src/index.ts",
        "bindings/typescript/test/contract.test.ts",
        "bindings/typescript/types/node-shims.d.ts",
        "bindings/csharp/LifecourseContract.csproj",
        "bindings/csharp/ContractRunner.cs",
        "bindings/csharp/Program.cs",
        "bindings/csharp/tests/LifecourseContract.Tests.csproj",
        "bindings/csharp/tests/ContractRunnerTests.cs",
        "bindings/rust/Cargo.toml",
        "bindings/rust/src/lib.rs",
        "bindings/rust/src/main.rs",
        "bindings/rust/tests/contract.rs",
    ]

    for relpath in expected:
        assert Path(relpath).exists()


def test_consumer_scaffolds_reference_shared_contract_paths() -> None:
    content = Path("bindings/go/internal/contract/contract.go").read_text(
        encoding="utf-8"
    )
    assert "specs/core-api/schemas/v1" in content
    assert "specs/core-api/fixtures/v1" in content
    assert "lifecourse.model_contract" in content

    content = Path("bindings/typescript/src/index.ts").read_text(encoding="utf-8")
    assert "specs/core-api/schemas/v1" in content
    assert "specs/core-api/fixtures/v1" in content
    assert "lifecourse.model_contract" in content

    content = Path("bindings/typescript/types/node-shims.d.ts").read_text(
        encoding="utf-8"
    )
    assert "node:test" in content
    assert "node:assert/strict" in content

    content = Path("bindings/csharp/ContractRunner.cs").read_text(encoding="utf-8")
    assert "net11.0" not in content
    assert "lifecourse.model_contract" in content

    content = Path("bindings/csharp/LifecourseContract.csproj").read_text(
        encoding="utf-8"
    )
    assert "<TargetFramework>net11.0</TargetFramework>" in content

    content = Path("bindings/rust/src/lib.rs").read_text(encoding="utf-8")
    assert "specs/core-api/schemas/v1" in content
    assert "specs/core-api/fixtures/v1" in content
    assert "lifecourse.model_contract" in content
