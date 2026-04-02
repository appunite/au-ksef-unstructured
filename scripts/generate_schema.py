"""Generate default_invoice_schema.json from the Pydantic InvoiceSchema model.

Inlines $ref definitions and strips Pydantic-specific keys (title, default,
$defs, examples) to produce a clean, human-readable JSON Schema.

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
    return _strip_keys(resolved, {"title", "default", "examples"})


def main() -> None:
    schema = generate()
    SCHEMA_PATH.write_text(json.dumps(schema, indent=2) + "\n")
    print(f"Written to {SCHEMA_PATH}")


if __name__ == "__main__":
    main()
