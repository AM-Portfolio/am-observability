"""Build catalog-index.json for service CI allow-lists."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from am_obs.loader import Context, load_context


def build_catalog_index(ctx: Context | None = None) -> dict[str, Any]:
    ctx = ctx or load_context()
    signals_out: list[dict[str, Any]] = []
    for sid, signal in sorted((ctx.signals or {}).items()):
        if not isinstance(signal, dict):
            continue
        signals_out.append(
            {
                "id": sid,
                "kind": signal.get("kind"),
                "panel_type": signal.get("panel_type"),
                "description": signal.get("description") or "",
                "dashboard": signal.get("dashboard") or _guess_dashboard(signal),
                "optional": bool(signal.get("optional")),
            }
        )

    panel_ids: list[str] = []
    row_ids: list[str] = []
    for template_name, template in (
        ("technical", ctx.technical_template),
        ("functional", ctx.functional_template),
    ):
        for panel in template.get("panels") or []:
            pid = str(panel.get("id") or "")
            if not pid:
                continue
            if (panel.get("type") or "") == "row":
                row_ids.append(pid)
            else:
                panel_ids.append(pid)

    bundles = {
        bid: {
            "id": bid,
            "tier": payload.get("tier"),
            "runtime": payload.get("runtime"),
            "includes": list(payload.get("includes") or []),
        }
        for bid, payload in sorted((ctx.signal_bundles or {}).items())
    }

    return {
        "apiVersion": "am.obs/v1",
        "kind": "CatalogIndex",
        "signals": signals_out,
        "bundles": bundles,
        "panel_ids": sorted(set(panel_ids)),
        "row_ids": sorted(set(row_ids)),
    }


def write_catalog_index(out_path: Path, ctx: Context | None = None) -> Path:
    index = build_catalog_index(ctx)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return out_path


def _guess_dashboard(signal: dict[str, Any]) -> str:
    # Signal modules set dashboard: technical|functional|platform in YAML when present
    dash = signal.get("dashboard")
    if dash:
        return str(dash)
    return "technical"
