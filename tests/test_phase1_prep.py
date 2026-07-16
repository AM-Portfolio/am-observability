"""Golden / unit tests for Phase 1 prep generator."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from am_obs.loader import load_context
from am_obs.pipeline import generate, generate_one, generate_shared
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
    assert "$uri" in joined or 'uri=~"$uri"' in joined
    assert 'application="portfolio-app"' not in joined
    # Service dropdown + derived vars (app/application hidden)
    by_name = {v["name"]: v for v in dashboard["templating"]["list"]}
    assert set(by_name) >= {
        "namespace",
        "service_pack",
        "service",
        "app",
        "application",
        "method",
        "uri",
        "mongo_command",
        "redis_command",
        "kafka_listener",
        "kafka_topic",
        "hikari_pool",
    }
    assert by_name["uri"]["type"] == "query"
    assert by_name["uri"]["includeAll"] is True
    assert by_name["method"]["includeAll"] is True
    assert by_name["uri"]["label"] == "API path"
    assert by_name["mongo_command"]["includeAll"] is True
    assert by_name["kafka_topic"]["label"] == "Kafka topic (5c)"
    assert by_name["namespace"]["type"] == "custom"
    assert by_name["service_pack"]["type"] == "custom"
    assert by_name["service_pack"]["label"] == "Service"
    assert by_name["application"]["hide"] == 2
    assert "portfolio-app" in by_name["service_pack"]["current"]["value"]
    # Section rows + API table + logs at bottom (errors before all logs)
    types = [p["type"] for p in dashboard["panels"]]
    assert "row" in types
    assert "table" in types
    assert "gauge" in types
    assert "text" in types
    # Decision strip present
    titles = [p["title"] for p in dashboard["panels"]]
    assert "Health score" in titles
    assert "Decision" in titles
    assert any("Action checklist" == t or "Action checklist" in t for t in titles)
    assert "Helm chart" in titles
    assert any("Hikari" in t for t in titles)
    # Dep filters only in dep exprs; HTTP still uses method/uri
    assert "$mongo_command" in joined or 'command=~"$mongo_command"' in joined
    assert "$kafka_topic" in joined or 'topic=~"$kafka_topic"' in joined
    log_titles = [p["title"] for p in dashboard["panels"] if p["type"] == "logs"]
    assert log_titles == ["Error logs", "Logs"]
    # Glass KPIs: color the value; Decision/Scrape keep solid wash
    pods = next(p for p in dashboard["panels"] if p["title"] == "Pods")
    assert pods["options"]["colorMode"] == "value"
    assert pods.get("transparent") is True
    decision = next(p for p in dashboard["panels"] if p["title"] == "Decision")
    assert decision["options"]["colorMode"] == "background"
    scrape = next(p for p in dashboard["panels"] if p["title"] == "Scrape up")
    assert scrape["options"]["colorMode"] == "background"
    # API table includes p75
    api = next(p for p in dashboard["panels"] if p["type"] == "table" and "API" in p["title"])
    legends = [t.get("refId") for t in api.get("targets") or []]
    assert "P75" in legends
    assert "S5xx" in legends


def test_shared_services_dashboard():
    """Default generate emits Technical + Functional Service-dropdown dashboards."""
    rc = generate()
    assert rc == 0
    report = json.loads((ROOT / "dist" / "report.json").read_text(encoding="utf-8"))
    assert "tech-am-services" in report["passed"]
    assert "func-am-services" in report["passed"]
    path = ROOT / "dist" / "grafana" / "tech-am-services.yaml"
    assert path.is_file()
    assert (ROOT / "dist" / "grafana" / "func-am-services.yaml").is_file()
    ctx = load_context()
    entries = list(ctx.registry.get("services") or [])
    dashboard, out, results = generate_shared(ctx, entries=entries, continue_on_error=True)
    assert dashboard is not None and out is not None
    assert dashboard["uid"] == "tech-am-services"
    assert dashboard["title"] == "Technical / Services"
    by_name = {v["name"]: v for v in dashboard["templating"]["list"]}
    assert by_name["service_pack"]["type"] == "custom"
    # Registry fixtures include portfolio + logging
    texts = [o["text"] for o in by_name["service_pack"]["options"]]
    assert "am-portfolio" in texts
    assert "am-logging" in texts
    # Selecting pack encodes metrics application for portfolio
    pack_by_text = {o["text"]: o["value"] for o in by_name["service_pack"]["options"]}
    assert pack_by_text["am-portfolio"] == "am-portfolio#am-portfolio#portfolio-app"
    # Functional board has avg latency (not empty-p95-only)
    ids = {r.id for r in results}
    assert "func-am-services" in ids
    func = next(r for r in results if r.id == "func-am-services")
    assert func.ok and func.path
    func_cm = (ROOT / "dist" / "grafana" / "func-am-services.yaml").read_text(encoding="utf-8")
    assert "Functional / Services" in func_cm
    assert "http_server_requests_seconds_sum" in func_cm
    assert "Worst avg" in func_cm or "worst" in func_cm.lower()


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
    # Ignore row titles / markdown blurbs — assert no HTTP/JVM *metric* panels
    metric_titles = [
        p["title"].lower()
        for p in dashboard["panels"]
        if p["type"] in ("timeseries", "stat", "gauge", "table")
    ]
    joined = " ".join(metric_titles)
    assert "request rate" not in joined
    assert "heap" not in joined
    assert any(p["type"] == "logs" for p in dashboard["panels"])


def test_functional_shared_published():
    """Shared generate publishes Functional / Services (not per-service func-*)."""
    rc = generate()
    assert rc == 0
    assert (ROOT / "dist" / "grafana" / "func-am-services.yaml").is_file()
    assert not (ROOT / "dist" / "grafana" / "func-am-portfolio.yaml").exists()


def test_platform_dashboards_generated():
    """Default generate also emits Platform / Overview + Redis."""
    rc = generate()
    assert rc == 0
    report = json.loads((ROOT / "dist" / "report.json").read_text(encoding="utf-8"))
    assert "platform-overview" in report["passed"]
    assert "platform-redis" in report["passed"]
    assert "platform-mongo" in report["passed"]
    assert "platform-postgres" in report["passed"]
    assert "platform-kafka" in report["passed"]
    overview = ROOT / "dist" / "grafana" / "platform-overview.yaml"
    redis = ROOT / "dist" / "grafana" / "platform-redis.yaml"
    assert overview.is_file()
    assert redis.is_file()
    assert (ROOT / "dist" / "grafana" / "platform-mongo.yaml").is_file()
    assert (ROOT / "dist" / "grafana" / "platform-postgres.yaml").is_file()
    kafka = ROOT / "dist" / "grafana" / "platform-kafka.yaml"
    assert kafka.is_file()
    text = overview.read_text(encoding="utf-8")
    assert 'grafana_folder: "platform"' in text
    assert "Platform / Overview" in text
    assert "container_cpu_usage_seconds_total" in text
    assert "identity" in text  # namespace dropdown includes identity
    redis_text = redis.read_text(encoding="utf-8")
    assert "redis_up" in redis_text or "redis_connected_clients" in redis_text
    assert 'grafana_folder: "platform"' in redis_text
    kafka_text = kafka.read_text(encoding="utf-8")
    assert "kafka_consumergroup_lag" in kafka_text
    assert "infra-preprod" in kafka_text
    assert '"name": "topic"' in kafka_text or "\"name\": \"topic\"" in kafka_text
    assert "consumergroup" in kafka_text


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
