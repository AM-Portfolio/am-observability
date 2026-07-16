"""Tests for dashboard prefs and package-release."""

from __future__ import annotations

from pathlib import Path

from am_obs.package import package_release
from am_obs.paths import ROOT
from am_obs.prefs import apply_dashboard_prefs


def test_apply_dashboard_prefs_hide_row():
    panels = [
        {"id": "row_mongo", "type": "row", "title": "Mongo"},
        {"id": "mongo_commands", "type": "timeseries", "signal": "mongo_commands"},
        {"id": "row_redis", "type": "row", "title": "Redis"},
        {"id": "redis_commands", "type": "timeseries", "signal": "redis_commands"},
    ]
    out = apply_dashboard_prefs(
        panels, {"rows": {"hide": ["row_mongo"], "collapse": ["row_redis"]}}
    )
    ids = [p["id"] for p in out]
    assert "row_mongo" not in ids
    assert "mongo_commands" not in ids
    assert "row_redis" in ids
    assert out[0]["collapsed"] is True
    assert "redis_commands" in ids


def test_package_release_shared_only(tmp_path, monkeypatch):
    # Use real dist if present; else skip-like generate first in CI
    grafana = ROOT / "dist" / "grafana"
    if not grafana.is_dir() or not any(grafana.glob("tech-am-services.yaml")):
        import pytest

        pytest.skip("run gen.py generate first")
    zip_path = package_release("v0.0.0-test")
    assert zip_path.is_file()
    assert (ROOT / "dist" / "release" / "catalog-index.json").is_file()
    assert (ROOT / "dist" / "release" / "compat.json").is_file()
