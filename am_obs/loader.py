"""Load catalog, bindings, capabilities, templates, registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from am_obs.catalog import load_signal_bundles, load_signal_catalog, load_signal_modules
from am_obs.paths import ROOT, load_yaml


@dataclass
class Context:
    root: Path = ROOT
    catalog: dict[str, Any] = field(default_factory=dict)
    signal_modules: dict[str, Any] = field(default_factory=dict)
    signal_bundles: dict[str, Any] = field(default_factory=dict)
    labels: dict[str, Any] = field(default_factory=dict)
    capabilities: dict[str, Any] = field(default_factory=dict)
    bindings: dict[str, Any] = field(default_factory=dict)
    technical_template: dict[str, Any] = field(default_factory=dict)
    functional_template: dict[str, Any] = field(default_factory=dict)
    registry: dict[str, Any] = field(default_factory=dict)
    platform_registry: dict[str, Any] = field(default_factory=dict)

    @property
    def signals(self) -> dict[str, Any]:
        return self.catalog.get("signals") or {}


def load_context(
    *,
    binding: Path | None = None,
    root: Path | None = None,
) -> Context:
    root = root or ROOT
    binding = binding or (root / "bindings" / "platform.yaml")
    return Context(
        root=root,
        catalog=load_signal_catalog(root) or {},
        signal_modules=load_signal_modules(root),
        signal_bundles=load_signal_bundles(root),
        labels=load_yaml(root / "catalog" / "labels.yaml") or {},
        capabilities=load_yaml(root / "adapters" / "capabilities.yaml") or {},
        bindings=load_yaml(binding) or {},
        technical_template=load_yaml(root / "templates" / "technical" / "service-overview.yaml")
        or {},
        functional_template=load_yaml(root / "templates" / "functional" / "domain-kpi.yaml") or {},
        registry=load_yaml(root / "services" / "registry.yaml") or {},
        platform_registry=load_yaml(root / "infra" / "registry.yaml") or {},
    )
