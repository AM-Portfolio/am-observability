"""Tempo input adapter — binds trace/link panels to Explore URLs + datasource_uid."""

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
    out["datasource"] = {"type": "tempo", "uid": datasource_uid}
    search = adapter_map.get("search") or 'service.name="$service"'
    out["search"] = subst_for_grafana(search, vars_)
    link_t = adapter_map.get("link_template")
    if link_t:
        out["url"] = subst_for_grafana(link_t, vars_)
    else:
        out["url"] = (
            f'/explore?orgId=1&left=%5B"now-1h","now","tempo",'
            f'%7B"query":"{out["search"]}"%7D%5D'
        )
    return out, None
