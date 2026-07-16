"""JSON Schema validation for catalog, bindings, registry, manifests."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from am_obs.catalog import expand_bundle
from am_obs.loader import Context, load_context
from am_obs.manifest import resolve_manifest_signals
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
    resolved = resolve_manifest_signals(manifest, ctx)
    for sid in sorted(resolved.technical | resolved.functional):
        if sid not in known:
            errors.append(f"{source}: unknown signal id '{sid}'")
    sig = manifest.get("signals") or {}
    bundle = sig.get("bundle")
    if bundle:
        bundle_cfg = (ctx.signal_bundles or {}).get(str(bundle))
        if not bundle_cfg:
            errors.append(f"{source}: unknown bundle '{bundle}'")
        else:
            expected_tier = bundle_cfg.get("tier")
            expected_runtime = bundle_cfg.get("runtime")
            if expected_tier and manifest.get("tier") != expected_tier:
                errors.append(
                    f"{source}: bundle '{bundle}' tier mismatch "
                    f"(manifest={manifest.get('tier')} bundle={expected_tier})"
                )
            if expected_runtime and manifest.get("runtime") != expected_runtime:
                errors.append(
                    f"{source}: bundle '{bundle}' runtime mismatch "
                    f"(manifest={manifest.get('runtime')} bundle={expected_runtime})"
                )
    for bundle_id in sig.get("include") or []:
        if str(bundle_id) not in (ctx.signal_bundles or {}):
            errors.append(f"{source}: unknown bundle '{bundle_id}'")
    return errors


def validate_all(ctx: Context | None = None) -> list[str]:
    ctx = ctx or load_context()
    root = ctx.root
    errors: list[str] = []

    errors.extend(
        _check(
            Draft202012Validator(_schema(root, "signal-catalog.schema.json")),
            ctx.catalog,
            "catalog/signals",
        )
    )
    # Validate module files and duplicate IDs
    seen: set[str] = set()
    for module, payload in sorted((ctx.signal_modules or {}).items()):
        errors.extend(
            _check(
                Draft202012Validator(_schema(root, "signal-module.schema.json")),
                payload,
                f"catalog/signals/{module}.yaml",
            )
        )
        signals = payload.get("signals")
        if not isinstance(signals, dict):
            errors.append(f"catalog/signals/{module}.yaml: missing 'signals' mapping")
            continue
        for sid, signal in signals.items():
            if sid in seen:
                errors.append(f"catalog/signals/{module}.yaml: duplicate signal id '{sid}'")
            seen.add(sid)
            if isinstance(signal, dict) and signal.get("id") != sid:
                errors.append(
                    f"catalog/signals/{module}.yaml: key '{sid}' id mismatch "
                    f"('{signal.get('id')}')"
                )
    for bundle_id, payload in sorted((ctx.signal_bundles or {}).items()):
        errors.extend(
            _check(
                Draft202012Validator(_schema(root, "signal-bundle.schema.json")),
                payload,
                f"catalog/bundles/{bundle_id}.yaml",
            )
        )
        includes = payload.get("includes") or []
        if not isinstance(includes, list):
            errors.append(f"catalog/bundles/{bundle_id}.yaml: includes must be a list")
            continue
        for mod in includes:
            if str(mod) not in (ctx.signal_modules or {}):
                errors.append(
                    f"catalog/bundles/{bundle_id}.yaml: unknown module '{mod}'"
                )
        expanded = expand_bundle(bundle_id, root)
        if not expanded:
            errors.append(f"catalog/bundles/{bundle_id}.yaml: expands to zero signals")
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
