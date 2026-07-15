"""Loki input adapter — binds log signals to LogQL + datasource_uid."""

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
        return None, f"omit {signal_id}: missing loki expr_template"
    out = dict(panel)
    out["datasource"] = {"type": "loki", "uid": datasource_uid}
    out["expr"] = subst_for_grafana(expr_t, vars_)
    return out, None
