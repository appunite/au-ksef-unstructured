"""Generate default_invoice_schema.json from the Pydantic InvoiceSchema model.

Produces a flat, human-readable JSON Schema by inlining $ref definitions
and stripping Pydantic-specific keys (title, default, $defs, examples).

Usage:
    uv run python -m scripts.generate_schema
"""

import json
from pathlib import Path
from typing import Any

from src.app.schemas.invoice import InvoiceSchema

SCHEMA_PATH = Path("src/app/schemas/default_invoice_schema.json")


def _resolve_refs(node: Any, defs: dict[str, Any]) -> Any:
    """Recursively resolve $ref pointers and inline definitions."""
    if isinstance(node, dict):
        if "$ref" in node:
            ref_name = node["$ref"].rsplit("/", 1)[-1]
            return _resolve_refs(defs[ref_name], defs)
        return {k: _resolve_refs(v, defs) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve_refs(item, defs) for item in node]
    return node


def _simplify_any_of(node: Any) -> Any:
    """Convert anyOf: [{type: X}, {type: null}] to type: [X, null]."""
    if isinstance(node, dict):
        if "anyOf" in node:
            types = node["anyOf"]
            if (
                len(types) == 2
                and all(isinstance(t, dict) and set(t.keys()) == {"type"} for t in types)
            ):
                merged_type = [t["type"] for t in types]
                result = {k: v for k, v in node.items() if k != "anyOf"}
                result["type"] = merged_type
                return {k: _simplify_any_of(v) for k, v in result.items()}

            if len(types) == 2:
                null_types = [t for t in types if isinstance(t, dict) and t.get("type") == "null"]
                obj_types = [t for t in types if t not in null_types]
                if len(null_types) == 1 and len(obj_types) == 1:
                    obj = _simplify_any_of(obj_types[0])
                    if isinstance(obj, dict) and "type" in obj:
                        obj["type"] = [obj["type"], "null"]
                    return {**{k: _simplify_any_of(v) for k, v in node.items() if k != "anyOf"}, **obj}

        return {k: _simplify_any_of(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_simplify_any_of(item) for item in node]
    return node


def _strip_keys(node: Any, keys: set[str]) -> Any:
    """Remove unwanted keys recursively."""
    if isinstance(node, dict):
        return {k: _strip_keys(v, keys) for k, v in node.items() if k not in keys}
    if isinstance(node, list):
        return [_strip_keys(item, keys) for item in node]
    return node


def generate() -> dict:
    raw = InvoiceSchema.model_json_schema()
    defs = raw.pop("$defs", {})
    resolved = _resolve_refs(raw, defs)
    simplified = _simplify_any_of(resolved)
    cleaned = _strip_keys(simplified, {"title", "default", "examples"})
    return cleaned


def main() -> None:
    schema = generate()
    SCHEMA_PATH.write_text(json.dumps(schema, indent=2) + "\n")
    print(f"Written to {SCHEMA_PATH}")


if __name__ == "__main__":
    main()
