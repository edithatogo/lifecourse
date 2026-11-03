"""Keep incomplete historical analyses from running with assumed model inputs."""

import ast
import inspect
import json
import types
from pathlib import Path

import pytest

ARCHIVE = Path(__file__).resolve().parents[1] / "archive" / "old_notebooks"


def fragments():
    for path in sorted(ARCHIVE.glob("*.ipynb")):
        notebook = json.loads(path.read_text())
        for cell in notebook["cells"]:
            required = cell.get("metadata", {}).get(
                "requires_explicit_historical_inputs"
            )
            if not required:
                continue
            tree = ast.parse("".join(cell["source"]))
            node = next(
                item
                for item in tree.body
                if isinstance(item, ast.FunctionDef)
                and item.name.startswith("run_archived_fragment_")
            )
            yield pytest.param(
                node, required, cell["metadata"], id=f"{path.stem}-{node.name}"
            )


@pytest.mark.parametrize(("node", "required", "metadata"), list(fragments()))
def test_historical_inputs_cannot_be_inferred_from_globals(node, required, metadata):
    # A stale interactive kernel must not silently supply a missing model input.
    namespace = dict.fromkeys(required, object())
    compiled = compile(ast.Module(body=[node], type_ignores=[]), "<fragment>", "exec")
    code = next(
        value for value in compiled.co_consts if isinstance(value, types.CodeType)
    )
    function = types.FunctionType(code, namespace)
    signature = inspect.signature(function)
    assert set(signature.parameters) == set(required)
    assert metadata["retained_outputs_are_historical"] is True
    supplied = dict.fromkeys(required, object())
    supplied.pop(required[0])
    with pytest.raises(TypeError, match=required[0]):
        function(**supplied)
