"""Compose dashboard IR: template ∩ manifest.signals.uses."""

from __future__ import annotations

from typing import Any

from am_obs.loader import Context
from am_obs.paths import env_from_namespace


KIND_TO_INPUT = {
    "metric": "metrics",
    "log": "logs",
    "trace": "traces",
    "link": "traces",
}


def _adapter_for_kind(ctx: Context, kind: str) -> str | None:
    input_key = KIND_TO_INPUT.get(kind)
    if not input_key:
        return None
    binding = (ctx.bindings.get("inputs") or {}).get(input_key) or {}
    return binding.get("adapter")


def _adapter_supports(ctx: Context, adapter: str, kind: str) -> bool:
    caps = (ctx.capabilities.get("adapters") or {}).get(adapter) or {}
    kinds = caps.get("kinds") or []
    # link panels ride on trace adapters
    if kind == "link":
        return "link" in kinds or "trace" in kinds
    return kind in kinds


def compose(manifest: dict[str, Any], ctx: Context) -> tuple[dict[str, Any], list[str]]:
    """Return (ir, warnings)."""
    warnings: list[str] = []
    service = manifest["service"]
    namespace = manifest["namespace"]
    app = manifest["k8s_app_label"]
    # Micrometer/Spring application label — optional override when != service id
    application = manifest.get("metrics_application") or service
    env = env_from_namespace(namespace)
    uses = set((manifest.get("signals") or {}).get("uses") or [])

    panels_out: list[dict[str, Any]] = []
    cursor_y = 0
    cursor_x = 0
    row_height = 0

    for panel in ctx.technical_template.get("panels") or []:
        signal_id = panel["signal"]
        if signal_id not in uses:
            continue

        signal = ctx.signals.get(signal_id)
        if not signal:
            warnings.append(f"drop {signal_id}: not in catalog")
            continue

        kind = signal.get("kind")
        adapter = _adapter_for_kind(ctx, kind)
        if not adapter:
            warnings.append(f"omit {signal_id}: no input binding for kind={kind}")
            continue
        if not _adapter_supports(ctx, adapter, kind):
            warnings.append(f"omit {signal_id}: adapter {adapter} lacks kind={kind}")
            continue
        if adapter not in (signal.get("adapters") or []):
            warnings.append(f"omit {signal_id}: signal does not list adapter {adapter}")
            continue

        width = int(panel.get("width") or 12)
        height = int(panel.get("height") or 8)
        if cursor_x + width > 24:
            cursor_x = 0
            cursor_y += row_height
            row_height = 0

        panels_out.append(
            {
                "id": panel.get("id") or signal_id,
                "title": panel.get("title") or signal_id,
                "signal": signal_id,
                "kind": kind,
                "type": panel.get("type") or signal.get("panel_type") or "timeseries",
                "adapter": adapter,
                "gridPos": {"h": height, "w": width, "x": cursor_x, "y": cursor_y},
            }
        )
        cursor_x += width
        row_height = max(row_height, height)

    title_tpl = ctx.technical_template.get("title") or "Technical / {{ service }}"
    title = title_tpl.replace("{{ service }}", service).replace("{{service}}", service)

    ir = {
        "apiVersion": "am.obs/v1",
        "kind": "Dashboard",
        "uid": f"tech-{service}",
        "title": title,
        "folder": ctx.technical_template.get("folder")
        or ((ctx.bindings.get("outputs") or {}).get("dashboards") or {}).get("folder")
        or "AM / Technical",
        "service": service,
        "namespace": namespace,
        "app": app,
        "application": application,
        "env": env,
        "tags": ["am", "technical", service, env],
        "panels": panels_out,
        "vars": {
            "service": service,
            "namespace": namespace,
            "app": app,
            "application": application,
            "env": env,
        },
    }

    functional = manifest.get("functional") or []
    if functional:
        warnings.append("functional KPIs requested but Phase 1 publisher skips func-* dashboards")
    # Explicit skip when empty — functional template is loaded but unused.

    return ir, warnings
