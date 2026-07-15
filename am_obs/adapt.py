"""Adapt IR panels with vendor queries + datasource_uid from bindings."""

from __future__ import annotations

from string import Template
from typing import Any

from am_obs.loader import Context

KIND_TO_INPUT = {
    "metric": "metrics",
    "log": "logs",
    "trace": "traces",
    "link": "traces",
}

DATASOURCE_TYPE = {
    "prometheus": "prometheus",
    "loki": "loki",
    "tempo": "tempo",
}


def _subst(template: str, vars_: dict[str, str]) -> str:
    # Use safe_substitute so unknown $tokens remain (Grafana vars later).
    return Template(template).safe_substitute(**vars_)


def adapt(ir: dict[str, Any], ctx: Context) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    vars_ = {k: str(v) for k, v in (ir.get("vars") or {}).items()}
    adapted_panels: list[dict[str, Any]] = []

    for panel in ir.get("panels") or []:
        signal_id = panel["signal"]
        signal = ctx.signals[signal_id]
        kind = signal["kind"]
        adapter = panel["adapter"]
        input_key = KIND_TO_INPUT[kind]
        binding = (ctx.bindings.get("inputs") or {})[input_key]
        datasource_uid = binding["datasource_uid"]
        ds_type = DATASOURCE_TYPE.get(adapter, adapter)

        adapter_map = (signal.get("adapter_map") or {}).get(adapter) or {}
        panel_out = dict(panel)
        panel_out["datasource"] = {"type": ds_type, "uid": datasource_uid}

        if kind == "metric":
            expr_t = adapter_map.get("expr_template")
            if not expr_t:
                warnings.append(f"omit {signal_id}: missing prometheus expr_template")
                continue
            panel_out["expr"] = _subst(expr_t, vars_)
        elif kind == "log":
            expr_t = adapter_map.get("expr_template")
            if not expr_t:
                warnings.append(f"omit {signal_id}: missing loki expr_template")
                continue
            panel_out["expr"] = _subst(expr_t, vars_)
        elif kind in ("trace", "link"):
            search = adapter_map.get("search") or f'service.name="{vars_["service"]}"'
            panel_out["search"] = _subst(search, vars_)
            link_t = adapter_map.get("link_template")
            if link_t:
                panel_out["url"] = _subst(link_t, vars_)
            else:
                panel_out["url"] = (
                    f'/explore?orgId=1&left=%5B"now-1h","now","Tempo",'
                    f'%7B"query":"{panel_out["search"]}"%7D%5D'
                )
        else:
            warnings.append(f"omit {signal_id}: unsupported kind {kind}")
            continue

        adapted_panels.append(panel_out)

    out = dict(ir)
    out["panels"] = adapted_panels
    return out, warnings
