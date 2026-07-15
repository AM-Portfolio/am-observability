"""Prometheus input adapter — binds metric signals to PromQL + datasource_uid."""

from __future__ import annotations

from typing import Any

from adapters._subst import subst_for_grafana


def adapt_panel(
    panel: dict[str, Any],
    *,
    adapter_map: dict[str, Any],
    datasource_uid: str,
    vars_: dict[str, str],
    signal_id: str,
) -> tuple[dict[str, Any] | None, str | None]:
    expr_t = adapter_map.get("expr_template")
    if not expr_t:
        return None, f"omit {signal_id}: missing prometheus expr_template"
    out = dict(panel)
    out["datasource"] = {"type": "prometheus", "uid": datasource_uid}
    # Keep $namespace/$app/$application/$service for Grafana variables
    out["expr"] = subst_for_grafana(expr_t, vars_)
    return out, None
