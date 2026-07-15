"""Publish Grafana JSON as a labeled ConfigMap YAML."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def publish_grafana_configmap(
    dashboard: dict[str, Any],
    *,
    namespace: str = "monitoring",
    out_dir: Path,
) -> Path:
    uid = dashboard["uid"]
    cm_name = f"grafana-dashboard-{uid}"
    key = f"{uid}.json"
    dashboard_json = json.dumps(dashboard, indent=2, ensure_ascii=False) + "\n"

    # Literal block for readable diffs (matches am-infra hand-written dashboards).
    indented = "\n".join(
        ("    " + line) if line else "" for line in dashboard_json.splitlines()
    )
    text = (
        "apiVersion: v1\n"
        "kind: ConfigMap\n"
        "metadata:\n"
        f"  name: {cm_name}\n"
        f"  namespace: {namespace}\n"
        "  labels:\n"
        '    grafana_dashboard: "1"\n'
        f"    am.obs/uid: {uid}\n"
        "data:\n"
        f"  {key}: |\n"
        f"{indented}\n"
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{uid}.yaml"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path
