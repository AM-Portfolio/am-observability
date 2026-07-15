"""Golden / unit tests for Phase 1 prep generator."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from am_obs.loader import load_context
from am_obs.pipeline import generate, generate_one
from am_obs.validate import validate_all, validate_manifest

ROOT = Path(__file__).resolve().parents[1]
GOLDENS = ROOT / "testdata" / "goldens"
FIXTURES = ROOT / "testdata" / "fixtures"


def test_metrics_application_as_grafana_var():
    """application stays a Grafana $var (not baked) so the Metrics application filter works."""
    ctx = load_context()
    manifest = yaml.safe_load((FIXTURES / "am-portfolio.yaml").read_text(encoding="utf-8"))
    dashboard, _, _, err = generate_one(manifest, ctx, source="fixture")
    assert err is None and dashboard is not None
    exprs = []
    for panel in dashboard["panels"]:
        for t in panel.get("targets") or []:
            if "expr" in t:
                exprs.append(t["expr"])
    joined = "\n".join(exprs)
    assert "$application" in joined or "${application}" in joined
    assert 'application="portfolio-app"' not in joined
    # Visible filter variables present
    names = {v["name"] for v in dashboard["templating"]["list"]}
    assert names >= {"namespace", "service", "app", "application"}
    assert all(v.get("hide", 0) == 0 for v in dashboard["templating"]["list"])


def test_validate_platform_ok():
    assert validate_all(load_context()) == []


def test_unknown_signal_fails():
    ctx = load_context()
    manifest = yaml.safe_load((FIXTURES / "am-portfolio.yaml").read_text(encoding="utf-8"))
    manifest["signals"]["uses"] = ["not_a_real_signal"]
    errors = validate_manifest(manifest, ctx, source="fixture")
    assert any("unknown signal" in e for e in errors)


def test_compose_intersection_tier_b_no_red():
    ctx = load_context()
    manifest = yaml.safe_load((FIXTURES / "am-logging.yaml").read_text(encoding="utf-8"))
    dashboard, path, warnings, err = generate_one(manifest, ctx, source="fixture")
    assert err is None
    assert path is not None
    assert dashboard is not None
    titles = [p["title"] for p in dashboard["panels"]]
    joined = " ".join(titles).lower()
    assert "request rate" not in joined
    assert "jvm" not in joined
    assert any(p["type"] == "logs" for p in dashboard["panels"])


def test_functional_empty_skips_func_publish():
    ctx = load_context()
    manifest = yaml.safe_load((FIXTURES / "am-portfolio.yaml").read_text(encoding="utf-8"))
    generate_one(manifest, ctx, source="fixture")
    assert not (ROOT / "dist" / "grafana" / "func-am-portfolio.yaml").exists()


def test_goldens_match(request):
    """Compare generated ConfigMaps to checked-in goldens."""
    update = request.config.getoption("--update-goldens")
    ctx = load_context()
    for name in ("am-portfolio", "am-logging"):
        manifest = yaml.safe_load((FIXTURES / f"{name}.yaml").read_text(encoding="utf-8"))
        dashboard, path, _, err = generate_one(manifest, ctx, source=f"fixture:{name}")
        assert err is None and path is not None and dashboard is not None

        golden_path = GOLDENS / f"tech-{name}.json"
        if update or not golden_path.exists():
            golden_path.parent.mkdir(parents=True, exist_ok=True)
            golden_path.write_text(
                json.dumps(dashboard, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        expected = json.loads(golden_path.read_text(encoding="utf-8"))
        assert dashboard == expected, f"golden mismatch for {name}; re-run with --update-goldens"


def test_generate_only_fixture_cli(tmp_path, monkeypatch):
    # Use real ROOT; ensure --only works with fixtures while enabled=false
    rc = generate(only="am-logging", continue_on_error=False)
    assert rc == 0
    report = json.loads((ROOT / "dist" / "report.json").read_text(encoding="utf-8"))
    assert "am-logging" in report["passed"]
