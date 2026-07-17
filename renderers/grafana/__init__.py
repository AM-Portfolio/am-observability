"""Grafana dashboard JSON renderer — glass-friendly, theme-safe SRE panels."""

from __future__ import annotations

from typing import Any

# Grafana palette colors — readable on both dark and light themes
_GREEN = "#73BF69"
_YELLOW = "#FADE2A"
_ORANGE = "#FF9830"
_RED = "#F2495C"
_BLUE = "#5794F2"
_PURPLE = "#B877D9"
_CYAN = "#8AB8FF"
_TEAL = "#37872D"

# Template color: name → bright hex (legacy dark-* names remapped)
_FIXED_COLORS = {
    "dark-blue": _BLUE,
    "dark-green": _GREEN,
    "dark-red": _RED,
    "dark-orange": _ORANGE,
    "dark-purple": _PURPLE,
    "dark-yellow": _YELLOW,
    "blue": _BLUE,
    "green": _GREEN,
    "red": _RED,
    "orange": _ORANGE,
    "purple": _PURPLE,
    "yellow": _YELLOW,
    "cyan": _CYAN,
}


def _theme_steps(theme: str) -> list[dict[str, Any]]:
    """Shared threshold steps for stat / gauge / bargauge."""
    if theme == "restarts":
        return [
            {"color": _GREEN, "value": None},
            {"color": _YELLOW, "value": 1},
            {"color": _ORANGE, "value": 2},
            {"color": _RED, "value": 3},
        ]
    if theme == "ratio":
        return [
            {"color": _GREEN, "value": None},
            {"color": _YELLOW, "value": 0.01},
            {"color": _ORANGE, "value": 0.03},
            {"color": _RED, "value": 0.05},
        ]
    if theme == "decision":
        return [
            {"color": _RED, "value": None},
            {"color": _YELLOW, "value": 1},
            {"color": _GREEN, "value": 2},
        ]
    if theme == "neutral":
        return [{"color": _BLUE, "value": None}]
    if theme == "latency":
        return [
            {"color": _GREEN, "value": None},
            {"color": _YELLOW, "value": 1},
            {"color": _ORANGE, "value": 5},
            {"color": _RED, "value": 20},
        ]
    if theme == "slow_count":
        return [
            {"color": _GREEN, "value": None},
            {"color": _YELLOW, "value": 1},
            {"color": _RED, "value": 3},
        ]
    if theme == "success_ratio":
        return [
            {"color": _RED, "value": None},
            {"color": _ORANGE, "value": 0.85},
            {"color": _YELLOW, "value": 0.95},
            {"color": _GREEN, "value": 0.99},
        ]
    if theme == "cyan":
        return [{"color": _CYAN, "value": None}]
    if theme == "purple":
        return [{"color": _PURPLE, "value": None}]
    if theme == "teal":
        return [{"color": _GREEN, "value": None}]
    # health / up
    return [
        {"color": _RED, "value": None},
        {"color": _GREEN, "value": 1},
    ]


def _fixed_color(name: str | None) -> str:
    if not name:
        return _BLUE
    return _FIXED_COLORS.get(name, name)


def _thresholds(steps: list[dict[str, Any]]) -> dict[str, Any]:
    return {"mode": "absolute", "steps": steps}


def _timeseries_panel(panel: dict[str, Any], panel_id: int) -> dict[str, Any]:
    ds = panel["datasource"]
    color = _fixed_color(panel.get("color") or _BLUE)
    fill = float(panel.get("fill_opacity", 40))
    fill = min(fill, 50)
    palette = panel.get("palette") or "classic"
    if palette == "fixed":
        color_cfg: dict[str, Any] = {"mode": "fixed", "fixedColor": color}
    else:
        color_cfg = {"mode": "palette-classic"}
    legend_fmt = panel.get("legend") or "__auto"
    draw_style = panel.get("draw_style") or "line"
    stack = panel.get("stack")
    stacking: dict[str, Any] = {"mode": "none", "group": "A"}
    if stack in (True, "normal"):
        stacking = {"mode": "normal", "group": "A"}
        fill = min(fill, 50)
    elif stack == "percent":
        stacking = {"mode": "percent", "group": "A"}

    custom: dict[str, Any] = {
        "drawStyle": draw_style,
        "lineInterpolation": "smooth",
        "barAlignment": 0,
        "lineWidth": 2 if draw_style == "line" else 1,
        "fillOpacity": fill,
        "gradientMode": "opacity",
        "showPoints": "auto",
        "pointSize": 5,
        "spanNulls": True,
        "axisBorderShow": False,
        "axisSoftMin": 0,
        "axisLabel": "",
        "axisColorMode": "text",
        "axisGridShow": True,
        "scaleDistribution": {"type": "linear"},
        "stacking": stacking,
        "thresholdsStyle": {"mode": "off"},
        "insertNulls": False,
        "hideFrom": {"tooltip": False, "viz": False, "legend": False},
    }

    legend_mode = panel.get("legend_mode") or "list"
    legend_placement = panel.get("legend_placement") or "right"
    calcs = panel.get("legend_calcs") or ["lastNotNull", "max"]

    defaults: dict[str, Any] = {
        "color": color_cfg,
        "custom": custom,
        "unit": panel.get("unit") or "short",
        "noValue": "-",
    }
    if panel.get("decimals") is not None:
        defaults["decimals"] = panel["decimals"]
    if panel.get("latency_slo"):
        defaults["thresholds"] = _thresholds(
            [
                {"color": _GREEN, "value": None},
                {"color": _YELLOW, "value": 1},
                {"color": _ORANGE, "value": 5},
                {"color": _RED, "value": 20},
            ]
        )
        custom["thresholdsStyle"] = {"mode": "line+area"}
        custom["lineWidth"] = 2

    return {
        "datasource": ds,
        "fieldConfig": {
            "defaults": defaults,
            "overrides": [],
        },
        "gridPos": panel["gridPos"],
        "id": panel_id,
        "options": {
            "legend": {
                "displayMode": legend_mode,
                "placement": legend_placement,
                "showLegend": True,
                "calcs": calcs,
                "width": 180 if legend_placement == "right" else 0,
            },
            "tooltip": {"mode": "multi", "sort": "desc"},
        },
        "targets": [
            {
                "datasource": ds,
                "editorMode": "code",
                "expr": panel["expr"],
                "legendFormat": legend_fmt,
                "range": True,
                "refId": "A",
            }
        ],
        "title": panel["title"],
        "transparent": True,
        "type": "timeseries",
    }


def _stat_panel(panel: dict[str, Any], panel_id: int) -> dict[str, Any]:
    ds = panel["datasource"]
    theme = panel.get("theme") or "health"
    mappings = list(panel.get("mappings") or [])
    steps = _theme_steps(theme)
    if theme == "decision" and not mappings:
        mappings = [
            {
                "type": "value",
                "options": {
                    "0": {"text": "ACT", "color": _RED},
                    "1": {"text": "WATCH", "color": _YELLOW},
                    "2": {"text": "GOOD", "color": _GREEN},
                },
            }
        ]

    # Glass default: color the value (+ sparkline). Solid background only for Decision / scrape.
    if panel.get("color_mode"):
        color_mode = str(panel["color_mode"])
    elif theme in ("decision", "health"):
        color_mode = "background"
    else:
        color_mode = "value"

    return {
        "datasource": ds,
        "fieldConfig": {
            "defaults": {
                "unit": panel.get("unit") or "short",
                "decimals": panel.get("decimals", 2),
                "thresholds": _thresholds(steps),
                "color": {"mode": "thresholds"},
                "mappings": mappings,
                "noValue": "0",
            },
            "overrides": [],
        },
        "gridPos": panel["gridPos"],
        "id": panel_id,
        "options": {
            "colorMode": color_mode,
            "graphMode": "none" if theme == "decision" else "area",
            "justifyMode": "center",
            "orientation": "auto",
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "textMode": "value" if theme == "decision" else "auto",
            "wideLayout": True,
            "text": {
                "titleSize": 13,
                "valueSize": 44 if theme == "decision" else 32,
            },
        },
        "targets": [
            {
                "datasource": ds,
                "editorMode": "code",
                "expr": panel["expr"],
                "legendFormat": panel.get("legend") or "__auto",
                "refId": "A",
            }
        ],
        "title": panel["title"],
        "transparent": True,
        "type": "stat",
    }


def _gauge_panel(panel: dict[str, Any], panel_id: int) -> dict[str, Any]:
    ds = panel["datasource"]
    unit = panel.get("unit") or "percentunit"
    gmin = panel.get("min", 0)
    gmax = panel.get("max", 1)
    if panel.get("theme") == "score":
        steps = [
            {"color": _RED, "value": None},
            {"color": _ORANGE, "value": 40},
            {"color": _YELLOW, "value": 50},
            {"color": _GREEN, "value": 80},
        ]
        unit = panel.get("unit") or "none"
        gmin = 0
        gmax = 100
    else:
        steps = [
            {"color": _GREEN, "value": None},
            {"color": _YELLOW, "value": 0.7},
            {"color": _ORANGE, "value": 0.85},
            {"color": _RED, "value": 0.9},
        ]
    mappings = panel.get("mappings") or []
    return {
        "datasource": ds,
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "min": gmin,
                "max": gmax,
                "decimals": panel.get("decimals", 0),
                "thresholds": _thresholds(steps),
                "color": {"mode": "thresholds"},
                "mappings": mappings,
                "noValue": "0",
            },
            "overrides": [],
        },
        "gridPos": panel["gridPos"],
        "id": panel_id,
        "options": {
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "needle": False,
            "showThresholdLabels": False,
            "showThresholdMarkers": True,
        },
        "targets": [
            {
                "datasource": ds,
                "editorMode": "code",
                "expr": panel["expr"],
                "legendFormat": panel.get("legend") or "__auto",
                "refId": "A",
            }
        ],
        "title": panel["title"],
        "transparent": True,
        "type": "gauge",
    }


def _bargauge_panel(panel: dict[str, Any], panel_id: int) -> dict[str, Any]:
    ds = panel["datasource"]
    theme = panel.get("theme") or "latency"
    steps = _theme_steps(theme)
    orientation = panel.get("orientation") or "horizontal"
    display_mode = panel.get("display_mode") or "gradient"
    legend_fmt = panel.get("legend") or "__auto"
    defaults: dict[str, Any] = {
        "unit": panel.get("unit") or "short",
        "decimals": panel.get("decimals", 2),
        "thresholds": _thresholds(steps),
        "color": {"mode": "thresholds"},
        "noValue": "0",
    }
    if panel.get("min") is not None:
        defaults["min"] = panel["min"]
    if panel.get("max") is not None:
        defaults["max"] = panel["max"]
    return {
        "datasource": ds,
        "fieldConfig": {
            "defaults": defaults,
            "overrides": [],
        },
        "gridPos": panel["gridPos"],
        "id": panel_id,
        "options": {
            "displayMode": display_mode,
            "orientation": orientation,
            "reduceOptions": {
                "calcs": ["lastNotNull"],
                "fields": "",
                "values": bool(panel.get("show_all_values", False)),
            },
            "showUnfilled": True,
            "minVizHeight": 16,
            "minVizWidth": 8,
            "namePlacement": "auto",
            "sizing": "auto",
            "valueMode": "color",
            "text": {"titleSize": 13, "valueSize": 18},
        },
        "targets": [
            {
                "datasource": ds,
                "editorMode": "code",
                "expr": panel["expr"],
                "legendFormat": legend_fmt,
                "range": not bool(panel.get("instant", True)),
                "instant": bool(panel.get("instant", True)),
                "refId": "A",
            }
        ],
        "title": panel["title"],
        "transparent": True,
        "type": "bargauge",
    }


def _piechart_panel(panel: dict[str, Any], panel_id: int) -> dict[str, Any]:
    ds = panel["datasource"]
    legend_fmt = panel.get("legend") or "__auto"
    return {
        "datasource": ds,
        "fieldConfig": {
            "defaults": {
                "unit": panel.get("unit") or "short",
                "decimals": panel.get("decimals", 2),
                "color": {"mode": "palette-classic"},
                "noValue": "0",
            },
            "overrides": [],
        },
        "gridPos": panel["gridPos"],
        "id": panel_id,
        "options": {
            "reduceOptions": {
                "calcs": ["lastNotNull"],
                "fields": "",
                "values": False,
            },
            "pieType": panel.get("pie_type") or "donut",
            "tooltip": {"mode": "single", "sort": "desc"},
            "legend": {
                "displayMode": "table",
                "placement": "right",
                "showLegend": True,
                "values": ["value", "percent"],
            },
            "displayLabels": ["percent"],
        },
        "targets": [
            {
                "datasource": ds,
                "editorMode": "code",
                "expr": panel["expr"],
                "legendFormat": legend_fmt,
                "instant": True,
                "refId": "A",
            }
        ],
        "title": panel["title"],
        "transparent": True,
        "type": "piechart",
    }


def _heatmap_panel(panel: dict[str, Any], panel_id: int) -> dict[str, Any]:
    """Prometheus histogram buckets → Grafana heatmap (format=heatmap)."""
    ds = panel["datasource"]
    legend_fmt = panel.get("legend") or "{{le}}"
    return {
        "datasource": ds,
        "fieldConfig": {
            "defaults": {
                "custom": {
                    "scaleDistribution": {"type": "linear"},
                    "hideFrom": {"legend": False, "tooltip": False, "viz": False},
                },
                "unit": panel.get("unit") or "short",
            },
            "overrides": [],
        },
        "gridPos": panel["gridPos"],
        "id": panel_id,
        "options": {
            "calculate": False,
            "cellGap": 1,
            "cellValues": {"decimals": 1},
            "color": {
                "exponent": 0.5,
                "fill": _BLUE,
                "mode": "scheme",
                "reverse": False,
                "scale": "exponential",
                "scheme": "Spectral",
                "steps": 64,
            },
            "exemplars": {"color": _RED},
            "filterValues": {"le": 1e-9},
            "legend": {"show": True},
            "rowsFrame": {"layout": "auto"},
            "tooltip": {"mode": "single", "showColorScale": True, "yHistogram": False},
            "yAxis": {
                "axisPlacement": "left",
                "reverse": False,
                "unit": panel.get("y_unit") or "s",
            },
        },
        "targets": [
            {
                "datasource": ds,
                "editorMode": "code",
                "expr": panel["expr"],
                "format": "heatmap",
                "legendFormat": legend_fmt,
                "range": True,
                "refId": "A",
            }
        ],
        "title": panel["title"],
        "transparent": True,
        "type": "heatmap",
    }


def _status_history_panel(panel: dict[str, Any], panel_id: int) -> dict[str, Any]:
    ds = panel["datasource"]
    theme = panel.get("theme") or "health"
    steps = _theme_steps(theme)
    legend_fmt = panel.get("legend") or "__auto"
    return {
        "datasource": ds,
        "fieldConfig": {
            "defaults": {
                "custom": {
                    "fillOpacity": 85,
                    "lineWidth": 0,
                    "hideFrom": {"legend": False, "tooltip": False, "viz": False},
                },
                "thresholds": _thresholds(steps),
                "color": {"mode": "thresholds"},
                "noValue": "0",
            },
            "overrides": [],
        },
        "gridPos": panel["gridPos"],
        "id": panel_id,
        "options": {
            "colWidth": 0.9,
            "legend": {
                "displayMode": "list",
                "placement": "bottom",
                "showLegend": True,
            },
            "rowHeight": 0.9,
            "showValue": "auto",
            "tooltip": {"mode": "single", "sort": "none"},
        },
        "targets": [
            {
                "datasource": ds,
                "editorMode": "code",
                "expr": panel["expr"],
                "legendFormat": legend_fmt,
                "range": True,
                "refId": "A",
            }
        ],
        "title": panel["title"],
        "transparent": True,
        "type": "status-history",
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


def _text_panel(panel: dict[str, Any], panel_id: int) -> dict[str, Any]:
    """Markdown description / action guidance panel."""
    return {
        "gridPos": panel["gridPos"],
        "id": panel_id,
        "options": {
            "code": {"language": "markdown", "showLineNumbers": False, "showMiniMap": False},
            "content": panel.get("content") or "",
            "mode": "markdown",
        },
        "title": panel.get("title") or "",
        "transparent": True,
        "type": "text",
    }


def _row_panel(panel: dict[str, Any], panel_id: int) -> dict[str, Any]:
    return {
        "collapsed": bool(panel.get("collapsed") or False),
        "gridPos": panel["gridPos"],
        "id": panel_id,
        "panels": [],
        "title": panel["title"],
        "type": "row",
    }


def _table_panel(panel: dict[str, Any], panel_id: int) -> dict[str, Any]:
    """Multi-query Prometheus table (API SLO or image inventory)."""
    ds = panel["datasource"]
    column_labels: dict[str, str] = dict(panel.get("column_labels") or {})
    join_field = panel.get("join_field") or "api"
    targets = []
    join_labels = {
        "api": "API",
        "image": "Image",
        "helm_sh_chart": "Helm chart",
        "label_helm_sh_chart": "Helm chart",
        "app_kubernetes_io_version": "App version",
        "label_app_kubernetes_io_version": "App version",
    }
    join_title = join_labels.get(join_field, join_field.replace("_", " ").title())
    rename: dict[str, str] = {join_field: join_title}
    exclude: dict[str, bool] = {"Time": True, "method": True, "uri": True}

    for t in panel.get("targets") or []:
        ref = t.get("refId") or "A"
        label = column_labels.get(ref) or t.get("legend") or ref
        targets.append(
            {
                "datasource": ds,
                "editorMode": "code",
                "expr": t["expr"],
                "format": t.get("format") or "table",
                "instant": bool(t.get("instant", True)),
                "refId": ref,
            }
        )
        rename[f"Value #{ref}"] = label
        exclude[f"Time #{ref}"] = True

    is_api = join_field == "api"
    overrides: list[dict[str, Any]] = []
    index_by: dict[str, int] = {}

    if is_api:
        index_by = {
            "API": 0,
            "Total": 1,
            "2xx": 2,
            "4xx": 3,
            "5xx": 4,
            "Fail": 5,
            "avg": 6,
            "p50": 7,
            "p75": 8,
            "p90": 9,
            "p95": 10,
        }
        overrides = [
            {
                "matcher": {"id": "byName", "options": "API"},
                "properties": [
                    {"id": "custom.width", "value": 260},
                    {"id": "decimals", "value": 0},
                ],
            },
            {
                "matcher": {"id": "byName", "options": "2xx"},
                "properties": [
                    {"id": "decimals", "value": 0},
                    {"id": "unit", "value": "short"},
                    {
                        "id": "thresholds",
                        "value": _thresholds(
                            [{"color": _GREEN, "value": None}, {"color": "#56A64B", "value": 1}]
                        ),
                    },
                    {"id": "color", "value": {"mode": "thresholds"}},
                    {"id": "custom.cellOptions", "value": {"type": "color-background", "mode": "gradient"}},
                ],
            },
            {
                "matcher": {"id": "byRegexp", "options": "/^(4xx)$/"},
                "properties": [
                    {"id": "decimals", "value": 0},
                    {
                        "id": "thresholds",
                        "value": _thresholds(
                            [
                                {"color": _GREEN, "value": None},
                                {"color": _YELLOW, "value": 1},
                                {"color": _ORANGE, "value": 10},
                            ]
                        ),
                    },
                    {"id": "color", "value": {"mode": "thresholds"}},
                    {"id": "custom.cellOptions", "value": {"type": "color-background", "mode": "gradient"}},
                ],
            },
            {
                "matcher": {"id": "byRegexp", "options": "/^(5xx|Fail)$/"},
                "properties": [
                    {"id": "decimals", "value": 0},
                    {
                        "id": "thresholds",
                        "value": _thresholds(
                            [
                                {"color": _GREEN, "value": None},
                                {"color": _YELLOW, "value": 1},
                                {"color": _RED, "value": 5},
                            ]
                        ),
                    },
                    {"id": "color", "value": {"mode": "thresholds"}},
                    {"id": "custom.cellOptions", "value": {"type": "color-background", "mode": "gradient"}},
                ],
            },
            {
                "matcher": {"id": "byRegexp", "options": "/^(avg|p50|p75|p90|p95)$/"},
                "properties": [
                    {"id": "unit", "value": "s"},
                    {"id": "decimals", "value": 3},
                    {
                        "id": "thresholds",
                        "value": _thresholds(
                            [
                                {"color": _GREEN, "value": None},
                                {"color": _YELLOW, "value": 0.2},
                                {"color": _ORANGE, "value": 1},
                                {"color": _RED, "value": 5},
                            ]
                        ),
                    },
                    {"id": "color", "value": {"mode": "thresholds"}},
                    {"id": "custom.cellOptions", "value": {"type": "color-background", "mode": "gradient"}},
                ],
            },
            {
                "matcher": {"id": "byName", "options": "Total"},
                "properties": [{"id": "decimals", "value": 0}, {"id": "unit", "value": "short"}],
            },
        ]
    else:
        value_col = column_labels.get((panel.get("targets") or [{}])[0].get("refId") or "A") or "pods"
        # After rename, Value #Ref becomes legend
        index_by = {join_title: 0, value_col: 1}
        overrides = [
            {
                "matcher": {"id": "byName", "options": join_title},
                "properties": [{"id": "custom.width", "value": 420}],
            }
        ]

    transforms: list[dict[str, Any]] = []
    if len(targets) > 1:
        transforms.append(
            {"id": "joinByField", "options": {"byField": join_field, "mode": "outer"}}
        )
    transforms.append(
        {
            "id": "organize",
            "options": {
                "excludeByName": exclude,
                "renameByName": rename,
                "indexByName": index_by,
            },
        }
    )

    return {
        "datasource": ds,
        "fieldConfig": {
            "defaults": {
                "custom": {"align": "auto", "filterable": True},
                "decimals": 3,
            },
            "overrides": overrides,
        },
        "gridPos": panel["gridPos"],
        "id": panel_id,
        "options": {
            "showHeader": True,
            "cellHeight": "sm",
            "footer": {"show": False, "reducer": ["sum"], "countRows": False, "fields": ""},
        },
        "targets": targets,
        "title": panel["title"],
        "transformations": transforms,
        "transparent": True,
        "type": "table",
    }


_RENDERERS = {
    "timeseries": _timeseries_panel,
    "stat": _stat_panel,
    "gauge": _gauge_panel,
    "bargauge": _bargauge_panel,
    "piechart": _piechart_panel,
    "heatmap": _heatmap_panel,
    "status-history": _status_history_panel,
    "logs": _logs_panel,
    "link": _link_panel,
    "text": _text_panel,
    "row": _row_panel,
    "table": _table_panel,
}


def _var_custom(name: str, label: str, value: str, options: list[str]) -> dict[str, Any]:
    def _opt_text(v: str) -> str:
        if name == "section" and v == ".*":
            return "All"
        return v

    opts = [
        {"selected": v == value, "text": _opt_text(v), "value": v} for v in options
    ]
    if value not in options:
        opts.insert(0, {"selected": True, "text": _opt_text(value), "value": value})
    return {
        "name": name,
        "label": label,
        "type": "custom",
        "hide": 0,
        "multi": False,
        "includeAll": False,
        "query": ",".join(dict.fromkeys([value, *options])),
        "current": {"selected": True, "text": _opt_text(value), "value": value},
        "options": opts,
    }


def _var_prom_label(
    name: str,
    label: str,
    *,
    query: str,
    datasource_uid: str = "prometheus",
    all_value: str | None = ".*",
    multi: bool = False,
    hide: int = 0,
    include_all: bool = True,
    current: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Prometheus label_values dropdown.

    When include_all and all_value is None, Grafana joins all option values with `|`
    (needed for pod=~"$pod" scoped to the selected application).
    """
    var: dict[str, Any] = {
        "name": name,
        "label": label,
        "type": "query",
        "hide": hide,
        "multi": multi,
        "includeAll": include_all,
        "datasource": {"type": "prometheus", "uid": datasource_uid},
        "definition": query,
        "query": query,
        "refresh": 2,
        "sort": 1,
        "regex": "",
        "options": [],
    }
    if include_all and all_value is not None:
        var["allValue"] = all_value
    if current is not None:
        var["current"] = current
    elif include_all:
        var["current"] = {"selected": True, "text": "All", "value": "$__all"}
    else:
        var["current"] = {"selected": False, "text": "", "value": ""}
    return var


def _templating_platform(ir: dict[str, Any]) -> dict[str, Any]:
    """Namespace (+ optional pod / topic / consumergroup) vars for Platform dashboards."""
    ns = ir["namespace"]
    ns_opts = list(ir.get("namespace_options") or [ns])
    pod = str((ir.get("vars") or {}).get("pod") or ".*")
    filters = set(ir.get("platform_filters") or [])
    ds_uid = "prometheus"
    inputs = ir.get("bindings_inputs") or {}
    metrics = inputs.get("metrics") or {}
    if metrics.get("datasource_uid"):
        ds_uid = str(metrics["datasource_uid"])

    variables: list[dict[str, Any]] = [
        _var_custom("namespace", "Namespace", ns, ns_opts),
    ]
    # Only show pod filter when not "match all"
    if pod and pod != ".*":
        variables.append(
            {
                "name": "pod",
                "label": "Pod",
                "type": "textbox",
                "hide": 0,
                "query": pod,
                "current": {"selected": True, "text": pod, "value": pod},
                "options": [{"selected": True, "text": pod, "value": pod}],
            }
        )
    else:
        variables.append(
            {
                "name": "pod",
                "label": "Pod",
                "type": "textbox",
                "hide": 2,
                "query": ".*",
                "current": {"selected": True, "text": ".*", "value": ".*"},
                "options": [{"selected": True, "text": ".*", "value": ".*"}],
            }
        )

    if "topic" in filters:
        variables.append(
            _var_prom_label(
                "topic",
                "Topic",
                query=(
                    "label_values("
                    'kafka_topic_partitions{namespace="$namespace"}, topic)'
                ),
                datasource_uid=ds_uid,
            )
        )
    if "consumergroup" in filters:
        variables.append(
            _var_prom_label(
                "consumergroup",
                "Consumer group",
                query=(
                    "label_values("
                    'kafka_consumergroup_lag{namespace="$namespace"}, consumergroup)'
                ),
                datasource_uid=ds_uid,
            )
        )
    return {"list": variables}


def _var_loki_label(
    name: str,
    label: str,
    *,
    query: str,
    datasource_uid: str = "loki",
    all_value: str | None = ".+",
    multi: bool = True,
    hide: int = 0,
    include_all: bool = True,
    current: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Loki label_values dropdown for product telemetry filters."""
    var: dict[str, Any] = {
        "name": name,
        "label": label,
        "type": "query",
        "hide": hide,
        "multi": multi,
        "includeAll": include_all,
        "datasource": {"type": "loki", "uid": datasource_uid},
        "definition": query,
        "query": query,
        "refresh": 2,
        "sort": 1,
        "regex": "",
        "options": [],
    }
    if include_all and all_value is not None:
        var["allValue"] = all_value
    if current is not None:
        var["current"] = current
    elif include_all:
        var["current"] = {"selected": True, "text": "All", "value": "$__all"}
    else:
        var["current"] = {"selected": False, "text": "", "value": ""}
    return var


def _templating_product(ir: dict[str, Any]) -> dict[str, Any]:
    """Env + Platform + Section + User + Portfolio filters for Product boards."""
    env = str((ir.get("vars") or {}).get("env") or ir.get("env") or "prod")
    ds_uid = "loki"
    inputs = ir.get("bindings_inputs") or {}
    logs = inputs.get("logs") or {}
    if logs.get("datasource_uid"):
        ds_uid = str(logs["datasource_uid"])

    return {
        "list": [
            _var_custom(
                "env",
                "Env",
                env if env in {"dev", "preprod", "prod"} else "prod",
                ["dev", "preprod", "prod"],
            ),
            _var_loki_label(
                "platform",
                "Platform",
                query='label_values({job="am-product-telemetry"}, platform)',
                datasource_uid=ds_uid,
                multi=True,
                include_all=True,
                all_value=".*",
            ),
            # Default "All" must be .* (match empty too). .+ excluded events
            # without user_id / portfolio_id / section and zeroed Auth + dwell panels.
            _var_custom(
                "section",
                "Section",
                ".*",
                [
                    ".*",
                    "portfolio",
                    "trade",
                    "market",
                    "docs",
                    "ai",
                    "auth",
                    "subscription",
                    "dashboard",
                    "profile",
                    "analysis",
                ],
            ),
            {
                "name": "user_id",
                "label": "User (user_id)",
                "type": "textbox",
                "hide": 0,
                "query": ".*",
                "current": {"selected": True, "text": ".*", "value": ".*"},
                "options": [{"selected": True, "text": ".*", "value": ".*"}],
            },
            {
                "name": "portfolio_id",
                "label": "Portfolio",
                "type": "textbox",
                "hide": 0,
                "query": ".*",
                "current": {"selected": True, "text": ".*", "value": ".*"},
                "options": [{"selected": True, "text": ".*", "value": ".*"}],
            },
        ]
    }


def _templating(ir: dict[str, Any]) -> dict[str, Any]:
    if ir.get("dashboard_kind") == "platform":
        return _templating_platform(ir)
    if ir.get("dashboard_kind") == "product":
        return _templating_product(ir)

    ns = ir["namespace"]
    application = str(ir.get("application") or ir.get("service") or "")

    ds_uid = "prometheus"
    inputs = ir.get("bindings_inputs") or {}
    metrics = inputs.get("metrics") or {}
    if metrics.get("datasource_uid"):
        ds_uid = str(metrics["datasource_uid"])

    # Plane A: Service = any series that carries application= (Java JVM + Python
    # Plane A metrics). Prefer a label selector over JVM-only discovery so
    # am-logging / am-asrax-proxy appear alongside portfolio-app.
    app_current = (
        {"selected": True, "text": application, "value": application}
        if application
        else {"selected": False, "text": "", "value": ""}
    )

    return {
        "list": [
            _var_custom(
                "namespace",
                "Namespace",
                ns,
                ["am-apps-preprod", "am-apps-prod", "am-apps-dev"],
            ),
            _var_prom_label(
                "application",
                "Service",
                query=(
                    "label_values("
                    '{namespace="$namespace",application=~".+"}, application)'
                ),
                datasource_uid=ds_uid,
                include_all=False,
                multi=False,
                hide=0,
                all_value=None,
                current=app_current,
            ),
            # Hidden: expands to this application's pods (pipe-joined when All).
            _var_prom_label(
                "pod",
                "Pod",
                query=(
                    "label_values("
                    '{namespace="$namespace",application="$application"}, pod)'
                ),
                datasource_uid=ds_uid,
                multi=True,
                hide=2,
                include_all=True,
                all_value=None,
            ),
            # HTTP only — Method / API path (Java Micrometer + Python Plane A)
            _var_prom_label(
                "method",
                "HTTP method",
                query=(
                    "label_values("
                    '{__name__=~"http_server_requests_seconds_count|http_requests_total",'
                    'application="$application",namespace="$namespace"}, method)'
                ),
                datasource_uid=ds_uid,
            ),
            _var_prom_label(
                "uri",
                "API path",
                query=(
                    "label_values("
                    'http_server_requests_seconds_count{application="$application",'
                    'namespace="$namespace",method=~"$method",uri!~".*actuator.*"}, uri)'
                ),
                datasource_uid=ds_uid,
            ),
            # Dep filters — only wired into section 5a–5d PromQL (not HTTP/JVM/K8s)
            _var_prom_label(
                "mongo_command",
                "Mongo cmd (5a)",
                query=(
                    "label_values("
                    'mongodb_driver_commands_seconds_count{application="$application",'
                    'namespace="$namespace"}, command)'
                ),
                datasource_uid=ds_uid,
            ),
            _var_prom_label(
                "redis_command",
                "Redis cmd (5b)",
                query=(
                    "label_values("
                    'lettuce_command_completion_seconds_count{application="$application",'
                    'namespace="$namespace"}, command)'
                ),
                datasource_uid=ds_uid,
            ),
            _var_prom_label(
                "kafka_listener",
                "Kafka listener (5c)",
                query=(
                    "label_values("
                    'spring_kafka_listener_seconds_count{application="$application",'
                    'namespace="$namespace"}, name)'
                ),
                datasource_uid=ds_uid,
            ),
            _var_prom_label(
                "kafka_topic",
                "Kafka topic (5c)",
                query=(
                    "label_values("
                    'kafka_consumer_fetch_manager_records_lag{application="$application",'
                    'namespace="$namespace"}, topic)'
                ),
                datasource_uid=ds_uid,
            ),
            _var_prom_label(
                "hikari_pool",
                "Hikari pool (5d)",
                query=(
                    "label_values("
                    'hikaricp_connections_active{application="$application",'
                    'namespace="$namespace"}, pool)'
                ),
                datasource_uid=ds_uid,
            ),
        ]
    }


def render(ir: dict[str, Any]) -> dict[str, Any]:
    """Render adapted IR → Grafana dashboard JSON."""
    panels = []
    for idx, panel in enumerate(ir.get("panels") or [], start=1):
        ptype = panel.get("type") or "timeseries"
        renderer = _RENDERERS.get(ptype, _timeseries_panel)
        # Pass optional viz hints from template through unchanged
        panels.append(renderer(panel, idx))

    tags = list(ir.get("tags") or [])
    if ir.get("dashboard_kind") == "platform":
        default_tags = ("am", "sre", "platform")
    elif ir.get("dashboard_kind") == "product":
        default_tags = ("am", "product", "users")
    else:
        default_tags = ("am", "sre", "technical")
    for t in default_tags:
        if t not in tags:
            tags.append(t)

    return {
        "annotations": {"list": []},
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 1,  # shared crosshair
        "id": None,
        "links": [],
        "liveNow": False,
        "panels": panels,
        "refresh": "30s",
        "schemaVersion": 38,
        "tags": tags,
        "templating": _templating(ir),
        "time": {"from": "now-1h", "to": "now"},
        "timepicker": {},
        "timezone": "browser",
        "title": ir["title"],
        "uid": ir["uid"],
        "version": 1,
    }


render_grafana = render
