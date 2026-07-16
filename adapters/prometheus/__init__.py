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
    out = dict(panel)
    out["datasource"] = {"type": "prometheus", "uid": datasource_uid}

    queries = adapter_map.get("queries")
    if queries:
        targets = []
        for q in queries:
            expr_t = q.get("expr_template")
            if not expr_t:
                return None, f"omit {signal_id}: query missing expr_template"
            targets.append(
                {
                    "refId": q.get("refId") or "A",
                    "expr": subst_for_grafana(expr_t, vars_),
                    "legend": q.get("legend") or q.get("refId") or "",
                    "format": q.get("format") or "table",
                    "instant": bool(q.get("instant", True)),
                }
            )
        out["targets"] = targets
        out["column_labels"] = {
            t["refId"]: t["legend"] for t in targets if t.get("legend")
        }
        out["join_field"] = adapter_map.get("join_field") or "api"
        return out, None

    expr_t = adapter_map.get("expr_template")
    if not expr_t:
        return None, f"omit {signal_id}: missing prometheus expr_template"
    # Keep $namespace/$app/$application/$service for Grafana variables
    out["expr"] = subst_for_grafana(expr_t, vars_)
    if adapter_map.get("legend"):
        out["legend"] = adapter_map["legend"]
    # Multi-series charts use distinct colors unless template forces fixed
    if "palette" not in out:
        legend = str(adapter_map.get("legend") or "")
        out["palette"] = "classic" if "{{" in legend or "by (" in expr_t else out.get("palette") or "fixed"
    return out, None
