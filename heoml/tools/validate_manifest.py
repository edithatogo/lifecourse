#!/usr/bin/env python3
"""Validate a HEOML manifest against the local v0.1 schema.

This keeps HEOML validation usable without adding a dedicated JSON Schema
dependency. The validator implements the subset of JSON Schema used by the
current v0.1 manifest schema.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ValidationError(Exception):
    path: str
    message: str

    def __str__(self) -> str:
        location = self.path or "$"
        return f"{location}: {self.message}"


def _path_join(base: str, segment: str) -> str:
    if not base:
        return segment
    if segment.startswith("["):
        return f"{base}{segment}"
    return f"{base}.{segment}"


def _validate(schema: dict[str, Any], instance: Any, path: str = "") -> None:
    if "const" in schema and instance != schema["const"]:
        raise ValidationError(path, f"expected const value {schema['const']!r}")

    if "enum" in schema and instance not in schema["enum"]:
        raise ValidationError(
            path, f"value {instance!r} is not in enum {schema['enum']!r}"
        )

    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        if instance is None and "null" in schema_type:
            return
        allowed = [item for item in schema_type if item != "null"]
        if not any(_type_matches(item, instance) for item in allowed):
            raise ValidationError(path, f"expected one of types {schema_type!r}")
    elif schema_type is not None and not _type_matches(schema_type, instance):
        raise ValidationError(path, f"expected type {schema_type!r}")

    if schema_type == "object" or (
        isinstance(schema_type, list)
        and "object" in schema_type
        and isinstance(instance, dict)
    ):
        _validate_object(schema, instance, path)
    elif schema_type == "array" or (
        isinstance(schema_type, list)
        and "array" in schema_type
        and isinstance(instance, list)
    ):
        _validate_array(schema, instance, path)


def _type_matches(schema_type: str, instance: Any) -> bool:
    return {
        "object": isinstance(instance, dict),
        "array": isinstance(instance, list),
        "string": isinstance(instance, str),
        "number": isinstance(instance, int | float) and not isinstance(instance, bool),
        "integer": isinstance(instance, int) and not isinstance(instance, bool),
        "boolean": isinstance(instance, bool),
        "null": instance is None,
    }.get(schema_type, False)


def _validate_object(
    schema: dict[str, Any], instance: dict[str, Any], path: str
) -> None:
    required = schema.get("required", [])
    for key in required:
        if key not in instance:
            raise ValidationError(_path_join(path, key), "missing required property")

    properties = schema.get("properties", {})
    for key, value in instance.items():
        if key in properties:
            _validate(properties[key], value, _path_join(path, key))
        elif not schema.get("additionalProperties", True):
            raise ValidationError(
                _path_join(path, key), "additional properties are not allowed"
            )


def _validate_array(schema: dict[str, Any], instance: list[Any], path: str) -> None:
    if "minItems" in schema and len(instance) < schema["minItems"]:
        raise ValidationError(path, f"expected at least {schema['minItems']} items")

    item_schema = schema.get("items")
    if item_schema is None:
        return

    for index, item in enumerate(instance):
        _validate(item_schema, item, _path_join(path, f"[{index}]"))


def validate_manifest(schema_path: Path, manifest_path: Path) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    _validate(schema, manifest)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifest",
        nargs="?",
        default="heoml/specs/v0.1/examples/minimal-run-bundle.manifest.json",
        help="Path to a HEOML manifest to validate.",
    )
    parser.add_argument(
        "--schema",
        default="heoml/specs/v0.1/schemas/manifest.schema.json",
        help="Path to the HEOML manifest schema.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    schema_path = Path(args.schema)
    manifest_path = Path(args.manifest)

    try:
        validate_manifest(schema_path, manifest_path)
    except ValidationError as exc:
        print(f"Validation failed: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - defensive CLI guard
        print(f"Validation failed: {exc}")
        return 1

    print(f"Validation passed: {manifest_path} matches {schema_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
