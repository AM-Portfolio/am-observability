"""Catalog helpers for modular signal modules and bundles."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from am_obs.paths import load_yaml


def load_signal_modules(root: Path) -> dict[str, dict[str, Any]]:
    """Load `catalog/signals/*.yaml` as module_name -> module payload."""
    modules_dir = root / "catalog" / "signals"
    modules: dict[str, dict[str, Any]] = {}
    if not modules_dir.is_dir():
        return modules
    for path in sorted(modules_dir.glob("*.yaml")):
        payload = load_yaml(path) or {}
        module = str(payload.get("module") or path.stem)
        modules[module] = payload
    return modules


def load_signal_catalog(root: Path) -> dict[str, Any]:
    """Build merged SignalCatalog from module files (fallback to monolith)."""
    modules = load_signal_modules(root)
    if not modules:
        return load_yaml(root / "catalog" / "signals.yaml") or {}

    merged: dict[str, Any] = {}
    for module, payload in modules.items():
        signals = payload.get("signals") or {}
        for sid, signal in signals.items():
            if sid in merged:
                raise ValueError(f"duplicate signal id '{sid}' in module '{module}'")
            merged[sid] = signal

    return {
        "apiVersion": "am.obs/v1",
        "kind": "SignalCatalog",
        "signals": merged,
    }


def load_signal_bundles(root: Path) -> dict[str, dict[str, Any]]:
    """Load bundle files from `catalog/bundles/*.yaml` keyed by bundle id."""
    bundles_dir = root / "catalog" / "bundles"
    bundles: dict[str, dict[str, Any]] = {}
    if not bundles_dir.is_dir():
        return bundles
    for path in sorted(bundles_dir.glob("*.yaml")):
        payload = load_yaml(path) or {}
        bid = str(payload.get("id") or path.stem)
        bundles[bid] = payload
    return bundles


def expand_bundle(bundle_id: str, root: Path) -> set[str]:
    """Resolve bundle includes -> set of signal ids."""
    bundles = load_signal_bundles(root)
    bundle = bundles.get(bundle_id) or {}
    includes = list(bundle.get("includes") or [])
    modules = load_signal_modules(root)
    out: set[str] = set()
    for mod in includes:
        payload = modules.get(str(mod)) or {}
        out.update((payload.get("signals") or {}).keys())
    return out
