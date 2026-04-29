from __future__ import annotations

from pathlib import Path

EXPECTED = {
    "bindings/README.md": "experimental, smoke-tested scaffold",
    "bindings/r/README.md": "experimental, smoke-tested scaffold",
    "bindings/julia/README.md": "experimental, smoke-tested scaffold",
    "bindings/go/README.md": "experimental, smoke-tested scaffold",
    "bindings/typescript/README.md": "experimental, smoke-tested scaffold",
    "bindings/csharp/README.md": "experimental, smoke-tested scaffold targeting .NET 11",
    "bindings/rust/README.md": "experimental, smoke-tested scaffold and future contract consumer",
}


def test_bindings_readmes_state_support_tiers() -> None:
    for relpath, expected in EXPECTED.items():
        content = Path(relpath).read_text(encoding="utf-8")
        assert expected in content


def test_bindings_versioning_doc_states_semver_rules() -> None:
    content = Path("docs/bindings_versioning.md").read_text(encoding="utf-8")

    assert (
        "`MAJOR` changes for incompatible request or response shape changes." in content
    )
    assert (
        "`MINOR` changes for backward-compatible additions to the contract or new"
        in content
    )
    assert "`PATCH` changes for documentation fixes" in content
    assert (
        "generated clients and wrapper adapters should align their `major` version"
        in content.lower()
    )
