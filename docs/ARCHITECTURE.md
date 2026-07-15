# Architecture (locked)

## Goal

Switch **feeds** (logs/metrics/traces) and **dashboard UI** independently — same provider or mixed — without rewriting templates.

## Repos

| Concern | Owns it |
|---------|---------|
| Catalog, templates, adapters, renderers, bindings, registry | **am-observability** |
| Prometheus, Grafana, Loki, Tempo, OTEL, Traefik, datasource secrets | **am-infra** |
| Per-service KPIs / tier / `k8s_app_label` | **Each service** → `observability.yaml` |

## Pipeline

```text
registry.yaml → load service observability.yaml
    → validate (JSON Schema)
    → compose IR (template ∩ signals.uses)
    → adapt (PromQL / LogQL / Trace link + datasource_uid)
    → render (Grafana JSON)
    → publish (ConfigMap)
    → pin copy into am-infra/k8s/grafana/dashboards/
```

## Bindings (inputs ≠ outputs)

```yaml
inputs:
  metrics: { adapter: prometheus, datasource_uid: prometheus }
  logs:    { adapter: loki,       datasource_uid: loki }
  traces:  { adapter: tempo,      datasource_uid: tempo }
outputs:
  dashboards: { renderer: grafana, publisher: grafana_configmap }
```

Changing log provider while keeping Grafana still requires an **am-infra Grafana datasource** for that provider.

## Pilots

| Order | Service | Tier | Expectation |
|-------|---------|------|-------------|
| 1a | am-portfolio | A (Java) | RED + JVM + logs + k8s + Tempo link |
| 1b | am-logging | B (Python) | logs + health/k8s only — no blank Prom charts |

Acceptance env: **`am-apps-preprod`**.

## Scale (50+)

- Source of truth: `{service-repo}/observability.yaml`
- Discovery: `services/registry.yaml` (pointers only)
- Partial generate: `--only <id>`
- Wave rollout — do not enable all 50 at once

## Non-goals (Phase 1)

Alertmanager cluster, notebooks, inventing functional KPIs, publishing `func-*` dashboards, production Datadog adapter, dialects inside templates.
