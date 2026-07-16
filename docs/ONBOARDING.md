# Onboard a service (zero coupling — Planes A / B / C)

Service deploy registers the app in shared Grafana. You do **not** edit am-observability or am-infra to add a service.

## Planes (read once)

| Plane | What | Who acts |
|-------|------|----------|
| **A** Registration | Scrape → Prometheus → appears in `tech-am-services` dropdown | Service deploy only |
| **B** Shared dashboards | New panels for everyone | am-obs release → am-infra `obs-upgrade` |
| **C** Panel visibility (optional) | Filtered `tech-view-{service}` | Service `dashboard:` prefs + `gen.py compose-view` |

## Prerequisites

- [ ] Tier: **A** (Java Prom+OTEL) or **B** (logs+k8s)
- [ ] Know `k8s_app_label` and `spring.application.name` → `metrics_application`
- [ ] Shared dashboards already live in cluster (`tech-am-services`)

## Steps (Plane A — required)

### 1. Manifest in the service repo

Monorepo: one file per workload, e.g. `services/am-analysis/observability.yaml`.

```yaml
apiVersion: am.obs/v1
kind: ServiceObservability
service: am-example
tier: A
runtime: java
k8s_app_label: am-example
metrics_application: am-example   # must match spring.application.name
namespace: am-apps-preprod
owners: [your-team]
signals:
  bundle: tier-a-java-core   # or tier-b-python
  domain: []                 # optional business KPI signal ids
  include: []                # optional extra signal ids (or bundle ids)
# Optional Plane C — omit to use shared dashboard only:
# dashboard:
#   technical:
#     rows:
#       hide: [row_mongo]
```

### 2. Prometheus scrape (Helm)

```yaml
podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8080"
  prometheus.io/path: "/actuator/prometheus"
```

Ensure Micrometer Prometheus registry + Actuator expose `prometheus`.

### 3. Deploy any env

Wait 1–2 scrape intervals. Open **AM / Technical → Technical / Services**, pick your `application` label.

### 4. Optional CI

```bash
# from am-observability checkout, or download schema/catalog-index from a release
python gen.py doctor path/to/observability.yaml
```

**Do not** add the service to `am-observability/services/registry.yaml` for onboard.
**Do not** generate `tech-am-example.yaml` as the product path.

## Custom KPIs (`domain`)

1. Prefer an existing catalog signal id, or request one in am-obs (sets `panel_type`: stat/timeseries/…).
2. List under `signals.domain`.
3. Emit the Micrometer meter.
4. Visual type comes from the **catalog**, not from the service yaml.

## Plane C (optional visibility)

```bash
python gen.py compose-view --manifest services/am-gateway/observability.yaml
kubectl apply -f dist/grafana/tech-view-am-gateway.yaml
```

Or omit `dashboard:` and use the shared dropdown only.

## Plane B (platform — not per service)

When shared panels change: tag am-observability → am-infra workflow **obs-upgrade** (`pr-only` then `apply`). No Grafana restart.

## Verify

| Check | Pass |
|-------|------|
| In Application dropdown | Yes |
| Scrape up | 1 |
| HTTP after real traffic | Lines move (not only actuator) |
| Unused Redis/Kafka empty | OK if app does not use them |
