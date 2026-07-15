"""Render adapted IR to Grafana dashboard JSON."""

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


def render_grafana(ir: dict[str, Any]) -> dict[str, Any]:
    panels = []
    for idx, panel in enumerate(ir.get("panels") or [], start=1):
        renderer = _RENDERERS.get(panel.get("type") or "timeseries", _timeseries_panel)
        panels.append(renderer(panel, idx))

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
                {
                    "current": {"text": ir["namespace"], "value": ir["namespace"]},
                    "hide": 2,
                    "name": "namespace",
                    "query": ir["namespace"],
                    "type": "constant",
                },
                {
                    "current": {"text": ir["service"], "value": ir["service"]},
                    "hide": 2,
                    "name": "service",
                    "query": ir["service"],
                    "type": "constant",
                },
                {
                    "current": {"text": ir["app"], "value": ir["app"]},
                    "hide": 2,
                    "name": "app",
                    "query": ir["app"],
                    "type": "constant",
                },
            ]
        },
        "time": {"from": "now-1h", "to": "now"},
        "timepicker": {},
        "timezone": "",
        "title": ir["title"],
        "uid": ir["uid"],
        "version": 1,
    }
