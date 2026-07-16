"""Compose a filtered service-view ConfigMap from observability.yaml (Plane C)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from am_obs.adapt import adapt
from am_obs.compose import compose, target_from_manifest
from am_obs.loader import Context, load_context
from am_obs.paths import load_yaml
from am_obs.prefs import apply_dashboard_prefs
from am_obs.publish import publish_grafana_configmap
from am_obs.render import render_grafana
from am_obs.validate import validate_manifest


def compose_service_view(
    manifest_path: Path,
    *,
    out_dir: Path | None = None,
    ctx: Context | None = None,
) -> Path:
    """Generate tech-view-{service} ConfigMap applying dashboard.technical prefs."""
    ctx = ctx or load_context()
    manifest = load_yaml(manifest_path)
    if not isinstance(manifest, dict):
        raise ValueError(f"invalid manifest: {manifest_path}")

    errors = validate_manifest(manifest, ctx, source=str(manifest_path))
    if errors:
        raise ValueError("; ".join(errors))

    ir, warnings = compose(manifest, ctx)
    for w in warnings:
        print(f"  warn: {w}")

    prefs = ((manifest.get("dashboard") or {}).get("technical")) or {}
    ir["panels"] = apply_dashboard_prefs(ir.get("panels") or [], prefs)

    service = str(manifest.get("service") or "service")
    ir["uid"] = f"tech-view-{service}"
    ir["title"] = f"Technical / {service} (view)"
    ir["tags"] = list(ir.get("tags") or []) + ["service-view", "plane-c"]

    adapted, w2 = adapt(ir, ctx)
    for w in w2:
        print(f"  warn: {w}")

    dashboard = render_grafana(adapted)
    out_ns = (
        ((ctx.bindings.get("outputs") or {}).get("dashboards") or {}).get("namespace")
        or "monitoring"
    )
    dest = out_dir or (ctx.root / "dist" / "grafana")
    path = publish_grafana_configmap(
        dashboard,
        namespace=out_ns,
        out_dir=dest,
        folder_path="technical",
    )
    print(f"[OK] service view -> {path}")
    return path
