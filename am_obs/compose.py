"""Compose dashboard IR: template ∩ manifest.signals.uses."""

from __future__ import annotations

from typing import Any

from am_obs.loader import Context
from am_obs.manifest import resolve_manifest_signals
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


def _panel_candidates(
    ctx: Context,
    *,
    template: dict[str, Any],
    uses: set[str] | None,
    warnings: list[str],
) -> list[dict[str, Any]]:
    """Build laid-out panel IR from a dashboard template."""
    panels_out: list[dict[str, Any]] = []
    cursor_y = 0
    cursor_x = 0
    row_height = 0
    pending_row: dict[str, Any] | None = None
    pending_texts: list[dict[str, Any]] = []

    def _place(width: int, height: int) -> dict[str, int]:
        nonlocal cursor_y, cursor_x, row_height
        if cursor_x + width > 24:
            cursor_x = 0
            cursor_y += row_height
            row_height = 0
        pos = {"h": height, "w": width, "x": cursor_x, "y": cursor_y}
        cursor_x += width
        row_height = max(row_height, height)
        return pos

    def _flush_row() -> None:
        nonlocal cursor_y, cursor_x, row_height, pending_row
        if pending_row is None:
            return
        if cursor_x != 0:
            cursor_x = 0
            cursor_y += row_height
            row_height = 0
        row = dict(pending_row)
        row["gridPos"] = {"h": 1, "w": 24, "x": 0, "y": cursor_y}
        panels_out.append(row)
        cursor_y += 1
        cursor_x = 0
        row_height = 0
        pending_row = None

    def _flush_texts() -> None:
        nonlocal pending_texts
        for raw in pending_texts:
            panels_out.append(
                {
                    "id": raw["id"],
                    "title": raw.get("title") or "",
                    "type": "text",
                    "kind": "text",
                    "content": raw.get("content") or "",
                    "gridPos": _place(int(raw["width"]), int(raw["height"])),
                }
            )
        pending_texts = []

    def _emit_text_now(panel: dict[str, Any]) -> None:
        panels_out.append(
            {
                "id": panel.get("id") or f"text-{cursor_y}",
                "title": panel.get("title") or "",
                "type": "text",
                "kind": "text",
                "content": panel.get("content") or "",
                "gridPos": _place(
                    int(panel.get("width") or 24),
                    int(panel.get("height") or 3),
                ),
            }
        )

    for panel in template.get("panels") or []:
        ptype = panel.get("type") or ""
        if ptype == "row":
            pending_row = {
                "id": panel.get("id") or f"row-{panel.get('title') or cursor_y}",
                "title": panel.get("title") or "Section",
                "type": "row",
                "kind": "row",
                "collapsed": bool(panel.get("collapsed") or False),
            }
            pending_texts = []
            continue

        if ptype == "text":
            raw = {
                "id": panel.get("id") or f"text-{cursor_y}",
                "title": panel.get("title") or "",
                "content": panel.get("content") or "",
                "width": int(panel.get("width") or 24),
                "height": int(panel.get("height") or 3),
            }
            if pending_row is not None:
                pending_texts.append(raw)
            else:
                _emit_text_now(panel)
            continue

        signal_id = panel["signal"]
        if uses is not None and signal_id not in uses:
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

        _flush_row()
        _flush_texts()

        panels_out.append(
            {
                "id": panel.get("id") or signal_id,
                "title": panel.get("title") or signal_id,
                "signal": signal_id,
                "kind": kind,
                "type": panel.get("type") or signal.get("panel_type") or "timeseries",
                "adapter": adapter,
                "gridPos": _place(
                    int(panel.get("width") or 12),
                    int(panel.get("height") or 8),
                ),
                **{
                    k: panel[k]
                    for k in (
                        "theme",
                        "color",
                        "color_mode",
                        "unit",
                        "decimals",
                        "fill_opacity",
                        "min",
                        "max",
                        "mappings",
                        "palette",
                        "legend",
                        "stack",
                        "draw_style",
                        "legend_mode",
                        "legend_placement",
                        "legend_calcs",
                        "transparent",
                        "latency_slo",
                        "orientation",
                        "display_mode",
                        "show_all_values",
                        "instant",
                        "pie_type",
                        "y_unit",
                    )
                    if k in panel
                },
            }
        )

    return panels_out


def target_from_manifest(manifest: dict[str, Any]) -> dict[str, str]:
    """Service dropdown row: service id + pod prefix + metrics application label."""
    service = str(manifest["service"])
    return {
        "service": service,
        "app": str(manifest["k8s_app_label"]),
        "application": str(manifest.get("metrics_application") or service),
        "namespace": str(manifest["namespace"]),
    }


def compose(manifest: dict[str, Any], ctx: Context) -> tuple[dict[str, Any], list[str]]:
    """Per-service dashboard IR (template ∩ manifest.signals.uses)."""
    warnings: list[str] = []
    service = manifest["service"]
    namespace = manifest["namespace"]
    app = manifest["k8s_app_label"]
    application = manifest.get("metrics_application") or service
    env = env_from_namespace(namespace)
    resolved = resolve_manifest_signals(manifest, ctx)
    uses = set(resolved.technical)

    panels_out = _panel_candidates(
        ctx, template=ctx.technical_template, uses=uses, warnings=warnings
    )

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
        "service_targets": [target_from_manifest(manifest)],
        "vars": {
            "service": service,
            "namespace": namespace,
            "app": app,
            "application": application,
            "env": env,
        },
    }

    return ir, warnings


def compose_shared(
    targets: list[dict[str, str]],
    ctx: Context,
    *,
    default: dict[str, str] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """One technical dashboard for all registry services (Service dropdown)."""
    warnings: list[str] = []
    if not targets:
        return {}, ["no service targets for shared dashboard"]

    default = default or targets[0]
    namespace = default["namespace"]
    env = env_from_namespace(namespace)

    panels_out = _panel_candidates(
        ctx, template=ctx.technical_template, uses=None, warnings=warnings
    )

    ir = {
        "apiVersion": "am.obs/v1",
        "kind": "Dashboard",
        "uid": "tech-am-services",
        "title": "Technical / Services",
        "folder": ctx.technical_template.get("folder")
        or ((ctx.bindings.get("outputs") or {}).get("dashboards") or {}).get("folder")
        or "AM / Technical",
        "service": default["service"],
        "namespace": namespace,
        "app": default["app"],
        "application": default["application"],
        "env": env,
        "tags": ["am", "technical", "shared", env],
        "panels": panels_out,
        "service_targets": targets,
        "vars": {
            "service": default["service"],
            "namespace": namespace,
            "app": default["app"],
            "application": default["application"],
            "env": env,
        },
    }
    return ir, warnings


def compose_shared_functional(
    targets: list[dict[str, str]],
    ctx: Context,
    *,
    default: dict[str, str] | None = None,
    uses: set[str] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """One Functional / Services product dashboard (Service dropdown)."""
    warnings: list[str] = []
    if not targets:
        return {}, ["no service targets for functional dashboard"]

    default = default or targets[0]
    namespace = default["namespace"]
    env = env_from_namespace(namespace)

    panels_out = _panel_candidates(ctx, template=ctx.functional_template, uses=uses, warnings=warnings)

    ir = {
        "apiVersion": "am.obs/v1",
        "kind": "Dashboard",
        "uid": "func-am-services",
        "title": "Functional / Services",
        "folder": ctx.functional_template.get("folder") or "AM / Functional",
        "service": default["service"],
        "namespace": namespace,
        "app": default["app"],
        "application": default["application"],
        "env": env,
        "tags": ["am", "functional", "shared", env],
        "panels": panels_out,
        "service_targets": targets,
        "vars": {
            "service": default["service"],
            "namespace": namespace,
            "app": default["app"],
            "application": default["application"],
            "env": env,
        },
    }
    return ir, warnings


PLATFORM_NAMESPACES = [
    "infra",
    "infra-preprod",
    "infra-prod",
    "infra-dev",
    "identity",
    "billing",
    "notification",
    "vault",
    "monitoring",
]


def compose_platform(
    template: dict[str, Any],
    ctx: Context,
    *,
    namespace: str = "infra",
    pod: str = ".*",
    namespaces: list[str] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Platform / infra dashboard IR (no service dropdown; namespace + pod vars)."""
    warnings: list[str] = []
    ns_opts = namespaces or PLATFORM_NAMESPACES
    if namespace not in ns_opts:
        ns_opts = [namespace, *ns_opts]

    panels_out = _panel_candidates(ctx, template=template, uses=None, warnings=warnings)

    uid = str(template.get("uid") or template.get("id") or "platform")
    title = str(template.get("title") or f"Platform / {uid}")
    folder = str(template.get("folder") or "AM / Platform")
    platform_filters = list(template.get("platform_filters") or [])

    ir = {
        "apiVersion": "am.obs/v1",
        "kind": "Dashboard",
        "dashboard_kind": "platform",
        "uid": uid,
        "title": title,
        "folder": folder,
        "grafana_folder_path": "platform",
        "service": "platform",
        "namespace": namespace,
        "app": "platform",
        "application": "platform",
        "env": "platform",
        "tags": ["am", "platform", uid],
        "panels": panels_out,
        "namespace_options": ns_opts,
        "platform_filters": platform_filters,
        "vars": {
            "service": "platform",
            "namespace": namespace,
            "app": "platform",
            "application": "platform",
            "env": "platform",
            "pod": pod,
            "topic": ".*",
            "consumergroup": ".*",
        },
    }
    return ir, warnings
