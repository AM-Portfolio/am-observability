"""Adapt IR panels via input adapters selected by bindings."""

from __future__ import annotations

from typing import Any

from adapters import loki, prometheus, tempo
from am_obs.loader import Context

KIND_TO_INPUT = {
    "metric": "metrics",
    "log": "logs",
    "trace": "traces",
    "link": "traces",
}

ADAPTERS = {
    "prometheus": prometheus,
    "loki": loki,
    "tempo": tempo,
}


def adapt(ir: dict[str, Any], ctx: Context) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    vars_ = {k: str(v) for k, v in (ir.get("vars") or {}).items()}
    adapted_panels: list[dict[str, Any]] = []

    for panel in ir.get("panels") or []:
        signal_id = panel["signal"]
        signal = ctx.signals[signal_id]
        kind = signal["kind"]
        adapter_name = panel["adapter"]
        input_key = KIND_TO_INPUT[kind]
        binding = (ctx.bindings.get("inputs") or {})[input_key]
        datasource_uid = binding["datasource_uid"]
        adapter_map = (signal.get("adapter_map") or {}).get(adapter_name) or {}

        mod = ADAPTERS.get(adapter_name)
        if mod is None:
            warnings.append(f"omit {signal_id}: unknown adapter {adapter_name}")
            continue

        panel_out, err = mod.adapt_panel(
            panel,
            adapter_map=adapter_map,
            datasource_uid=datasource_uid,
            vars_=vars_,
            signal_id=signal_id,
        )
        if err:
            warnings.append(err)
            continue
        if panel_out is None:
            continue
        adapted_panels.append(panel_out)

    out = dict(ir)
    out["panels"] = adapted_panels
    return out, warnings
