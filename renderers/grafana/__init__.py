"""Grafana dashboard JSON renderer (output side)."""

from __future__ import annotations

from typing import Any


def _timeseries_panel(panel: dict[str, Any], panel_id: int) -> dict[str, Any]:
    ds = panel["datasource"]
    return {
        "datasource": ds,
        "fieldConfig": {"defaults": {}, "overrides": []},
        "gridPos": panel["gridPos"],
        "id": panel_id,
        "options": {"legend": {"displayMode": "list", "placement": "bottom", "showLegend": True}},
        "targets": [
            {
                "datasource": ds,
                "editorMode": "code",
                "expr": panel["expr"],
                "legendFormat": "__auto",
                "range": True,
                "refId": "A",
            }
        ],
        "title": panel["title"],
        "type": "timeseries",
    }


def _stat_panel(panel: dict[str, Any], panel_id: int) -> dict[str, Any]:
    ds = panel["datasource"]
    return {
        "datasource": ds,
        "fieldConfig": {"defaults": {"unit": "short"}, "overrides": []},
        "gridPos": panel["gridPos"],
        "id": panel_id,
        "options": {
            "colorMode": "value",
            "graphMode": "none",
            "justifyMode": "auto",
            "orientation": "auto",
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "textMode": "auto",
        },
        "targets": [
            {
                "datasource": ds,
                "editorMode": "code",
                "expr": panel["expr"],
                "refId": "A",
            }
        ],
        "title": panel["title"],
        "type": "stat",
    }


def _logs_panel(panel: dict[str, Any], panel_id: int) -> dict[str, Any]:
    ds = panel["datasource"]
    return {
        "datasource": ds,
        "gridPos": panel["gridPos"],
        "id": panel_id,
        "options": {
            "dedupStrategy": "none",
            "enableLogDetails": True,
            "prettifyLogMessage": False,
            "showCommonLabels": False,
            "showLabels": False,
            "showTime": True,
            "sortOrder": "Descending",
            "wrapLogMessage": True,
        },
        "targets": [
            {
                "datasource": ds,
                "editorMode": "code",
                "expr": panel["expr"],
                "queryType": "range",
                "refId": "A",
            }
        ],
        "title": panel["title"],
        "type": "logs",
    }


def _link_panel(panel: dict[str, Any], panel_id: int) -> dict[str, Any]:
    """Text panel with Tempo explore link (not a fake Prom timeseries)."""
    url = panel.get("url") or "#"
    search = panel.get("search") or ""
    return {
        "gridPos": panel["gridPos"],
        "id": panel_id,
        "options": {
            "code": {"language": "markdown", "showLineNumbers": False, "showMiniMap": False},
            "content": (
                f"**Open traces in Tempo** for `{search}` — "
                f"[Explore Tempo]({url})"
            ),
            "mode": "markdown",
        },
        "title": panel["title"],
        "type": "text",
    }


_RENDERERS = {
    "timeseries": _timeseries_panel,
    "stat": _stat_panel,
    "logs": _logs_panel,
    "link": _link_panel,
}


def _var_custom(name: str, label: str, value: str, options: list[str]) -> dict[str, Any]:
    opts = [{"selected": v == value, "text": v, "value": v} for v in options]
    if value not in options:
        opts.insert(0, {"selected": True, "text": value, "value": value})
    return {
        "name": name,
        "label": label,
        "type": "custom",
        "hide": 0,
        "multi": False,
        "includeAll": False,
        "query": ",".join(dict.fromkeys([value, *options])),
        "current": {"selected": True, "text": value, "value": value},
        "options": opts,
    }


def _var_textbox(name: str, label: str, value: str) -> dict[str, Any]:
    return {
        "name": name,
        "label": label,
        "type": "textbox",
        "hide": 0,
        "query": value,
        "current": {"selected": True, "text": value, "value": value},
        "options": [{"selected": True, "text": value, "value": value}],
    }


def render(ir: dict[str, Any]) -> dict[str, Any]:
    """Render adapted IR → Grafana dashboard JSON."""
    panels = []
    for idx, panel in enumerate(ir.get("panels") or [], start=1):
        renderer = _RENDERERS.get(panel.get("type") or "timeseries", _timeseries_panel)
        panels.append(renderer(panel, idx))

    ns = ir["namespace"]
    service = ir["service"]
    app = ir["app"]
    application = ir.get("application") or service

    return {
        "annotations": {"list": []},
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 0,
        "id": None,
        "links": [],
        "liveNow": False,
        "panels": panels,
        "refresh": "30s",
        "schemaVersion": 38,
        "style": "dark",
        "tags": list(ir.get("tags") or []),
        "templating": {
            "list": [
                _var_custom(
                    "namespace",
                    "Namespace",
                    ns,
                    ["am-apps-preprod", "am-apps-prod", "am-apps-dev"],
                ),
                _var_textbox("service", "Service", service),
                _var_textbox("app", "App (pod prefix)", app),
                _var_textbox("application", "Metrics application", application),
            ]
        },
        "time": {"from": "now-1h", "to": "now"},
        "timepicker": {},
        "timezone": "",
        "title": ir["title"],
        "uid": ir["uid"],
        "version": 1,
    }


# Binding / CLI alias used by pipeline
render_grafana = render
