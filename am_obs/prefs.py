"""Apply service dashboard visibility prefs (Plane C)."""

from __future__ import annotations

from typing import Any


def apply_dashboard_prefs(
    panels: list[dict[str, Any]],
    prefs: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Filter/collapse panels using observability.yaml dashboard.*.prefs.

    prefs shape (technical or functional block):
      panels:
        include: [panel_id, ...]
        exclude: [panel_id, ...]
      rows:
        hide: [row_id, ...]
        collapse: [row_id, ...]
    """
    if not prefs:
        return panels

    panel_cfg = prefs.get("panels") or {}
    row_cfg = prefs.get("rows") or {}
    include = set(panel_cfg.get("include") or [])
    exclude = set(panel_cfg.get("exclude") or [])
    hide_rows = set(row_cfg.get("hide") or [])
    collapse_rows = set(row_cfg.get("collapse") or [])

    if not (include or exclude or hide_rows or collapse_rows):
        return panels

    # Walk panels in order; drop hidden rows and their following section until next row
    out: list[dict[str, Any]] = []
    skipping_section = False
    for panel in panels:
        pid = str(panel.get("id") or "")
        ptype = panel.get("type") or panel.get("kind") or ""

        if ptype == "row":
            if pid in hide_rows:
                skipping_section = True
                continue
            skipping_section = False
            row = dict(panel)
            if pid in collapse_rows:
                row["collapsed"] = True
            out.append(row)
            continue

        if skipping_section:
            continue

        # Text panels without signal: keep if in include mode only when listed, else keep
        if include:
            # Always keep row text immediately after kept rows — text ids must be included
            # or we keep text that has no signal when preceding row was kept.
            signal = panel.get("signal")
            if signal and signal not in include and pid not in include:
                continue
            if not signal and pid and pid not in include and ptype != "text":
                continue
            if ptype == "text" and include and pid not in include:
                # keep section blurbs that belong to included content: keep all text if any
                # panel in section might be included — simpler: keep text panels always when
                # include is set (section headers).
                pass
        if exclude and (pid in exclude or (panel.get("signal") in exclude)):
            continue

        out.append(panel)

    return out


def collect_pref_ids(prefs: dict[str, Any] | None) -> set[str]:
    """All panel/row ids referenced by prefs (for validation)."""
    if not prefs:
        return set()
    ids: set[str] = set()
    panel_cfg = prefs.get("panels") or {}
    row_cfg = prefs.get("rows") or {}
    for key in ("include", "exclude"):
        ids.update(str(x) for x in (panel_cfg.get(key) or []))
    for key in ("hide", "collapse"):
        ids.update(str(x) for x in (row_cfg.get(key) or []))
    return ids
