"""Placeholder suite so Phase 0 `make test` is green."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_registry_loads_and_pilots():
    data = yaml.safe_load((ROOT / "services" / "registry.yaml").read_text(encoding="utf-8"))
    assert "services" in data
    ids = {entry["id"]: entry for entry in data["services"]}
    assert "am-portfolio" in ids
    assert "am-logging" in ids
    assert ids["am-portfolio"]["enabled"] is True
    assert ids["am-logging"]["enabled"] is False


def test_schemas_exist():
    schema_dir = ROOT / "schema"
    expected = [
        "service-observability.schema.json",
        "signal-catalog.schema.json",
        "bindings.schema.json",
        "dashboard-ir.schema.json",
        "registry.schema.json",
    ]
    for name in expected:
        assert (schema_dir / name).is_file(), name
