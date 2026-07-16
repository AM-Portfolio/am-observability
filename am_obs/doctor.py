"""Doctor: validate a service observability.yaml against catalog + optional live checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from am_obs.catalog_index import build_catalog_index
from am_obs.loader import load_context
from am_obs.paths import load_yaml
from am_obs.prefs import collect_pref_ids
from am_obs.validate import validate_manifest


def doctor_manifest(manifest_path: Path, *, index_path: Path | None = None) -> list[str]:
    """Return list of problems (empty = healthy)."""
    problems: list[str] = []
    path = Path(manifest_path)
    if not path.is_file():
        return [f"manifest not found: {path}"]

    manifest = load_yaml(path)
    if not isinstance(manifest, dict):
        return [f"invalid YAML: {path}"]

    ctx = load_context()
    problems.extend(validate_manifest(manifest, ctx, source=str(path)))

    index: dict[str, Any]
    if index_path and index_path.is_file():
        index = json.loads(index_path.read_text(encoding="utf-8"))
    else:
        index = build_catalog_index(ctx)

    known_panels = set(index.get("panel_ids") or [])
    known_rows = set(index.get("row_ids") or [])
    known_signals = {s["id"] for s in (index.get("signals") or []) if isinstance(s, dict)}

    dash = manifest.get("dashboard") or {}
    for section in ("technical", "functional"):
        prefs = dash.get(section) or {}
        for pid in collect_pref_ids(prefs):
            if pid not in known_panels and pid not in known_rows and pid not in known_signals:
                problems.append(
                    f"{path}: dashboard.{section} unknown id '{pid}' "
                    f"(not in panel_ids/row_ids/signals)"
                )

    sig = manifest.get("signals") or {}
    for sid in sig.get("domain") or []:
        if str(sid) not in known_signals:
            problems.append(f"{path}: domain signal '{sid}' not in catalog index")

    return problems


def cmd_doctor(manifest: Path, index: Path | None = None) -> int:
    problems = doctor_manifest(manifest, index_path=index)
    if not problems:
        print(f"doctor OK: {manifest}")
        return 0
    print(f"doctor FAILED: {manifest}", file=sys.stderr)
    for p in problems:
        print(f"  - {p}", file=sys.stderr)
    return 1
