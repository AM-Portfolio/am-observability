"""JSON Schema validation for catalog, bindings, registry, manifests."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from am_obs.loader import Context, load_context
from am_obs.paths import ROOT, load_json, load_yaml


class ValidationError(Exception):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


def _schema(root: Path, name: str) -> dict[str, Any]:
    return load_json(root / "schema" / name)


def _check(validator: Draft202012Validator, data: Any, source: str) -> list[str]:
    return [
        f"{source}: {err.message}"
        for err in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    ]


def validate_manifest(manifest: dict[str, Any], ctx: Context, source: str = "manifest") -> list[str]:
    errors = _check(
        Draft202012Validator(_schema(ctx.root, "service-observability.schema.json")),
        manifest,
        source,
    )
    known = set(ctx.signals)
    uses = (manifest.get("signals") or {}).get("uses") or []
    for sid in uses:
        if sid not in known:
            errors.append(f"{source}: unknown signal id '{sid}'")
    return errors


def validate_all(ctx: Context | None = None) -> list[str]:
    ctx = ctx or load_context()
    root = ctx.root
    errors: list[str] = []

    errors.extend(
        _check(
            Draft202012Validator(_schema(root, "signal-catalog.schema.json")),
            ctx.catalog,
            "catalog/signals.yaml",
        )
    )
    errors.extend(
        _check(
            Draft202012Validator(_schema(root, "bindings.schema.json")),
            ctx.bindings,
            "bindings",
        )
    )
    errors.extend(
        _check(
            Draft202012Validator(_schema(root, "registry.schema.json")),
            ctx.registry,
            "services/registry.yaml",
        )
    )

    # Additional binding YAML files (if any)
    for path in sorted((root / "bindings").glob("*.yaml")):
        if path.name == "platform.yaml" and ctx.bindings:
            continue
        data = load_yaml(path)
        if data:
            errors.extend(
                _check(
                    Draft202012Validator(_schema(root, "bindings.schema.json")),
                    data,
                    str(path.relative_to(root)),
                )
            )

    return errors


def cmd_validate(binding: Path | None = None) -> int:
    ctx = load_context(binding=binding)
    errors = validate_all(ctx)
    if errors:
        for msg in errors:
            print(msg, file=sys.stderr)
        return 1
    print("validate OK")
    return 0
