# Phase 1a — Pilot `am-portfolio` (Java Tier A)

**Goal:** First end-to-end path: service manifest → generate → pin in am-infra → dashboard visible in Grafana preprod.

**Depends on:** Phase 0 + Phase 1 prep (catalog + working generator)  
**Unlocks:** Phase 1b

Do **not** enable am-logging until this phase verifies.

---

## Detailed steps

### 1a.0 Phase 1 prep (if not done)

- [x] Land frozen signals + adapter maps in `catalog/signals.yaml` (see plan / ARCHITECTURE)
- [x] `bindings/preprod.yaml` with datasource UIDs matching am-infra
- [x] `templates/technical/service-overview.yaml`
- [x] Adapters: prometheus, loki, tempo (+ capabilities)
- [x] Renderer + `grafana_configmap` publisher
- [x] Goldens for a fixture manifest green

### 1a.1 Service manifest

- [x] Create [`am-portfolio/observability.yaml`](../../am-portfolio/observability.yaml) (path relative once repo sits next to portfolio):

```yaml
apiVersion: am.obs/v1
kind: ServiceObservability
service: am-portfolio
tier: A
runtime: java
k8s_app_label: am-portfolio   # calibrate after cluster check
metrics_application: portfolio-app   # spring.application.name
namespace: am-apps-preprod
owners: [portfolio]
signals:
  uses:
    - http_request_rate
    - http_error_rate
    - http_latency_p95
    - jvm_heap_used
    - jvm_gc_pause
    - k8s_cpu_usage
    - k8s_memory_usage
    - k8s_restarts
    - service_logs_all
    - service_error_logs
    - service_health_up
    - trace_latency_p95
functional: []
```

- [ ] Commit in **am-portfolio** repo (service-owned)

### 1a.2 Registry

- [x] In `services/registry.yaml`:

```yaml
  - id: am-portfolio
    repo: am-portfolio
    path: observability.yaml
    ref: main
    enabled: true
```

### 1a.3 Calibrate on cluster

- [ ] `kubectl -n am-apps-preprod get pods -l app=am-portfolio -o wide` (or discover real label) — **blocked: local API server down**
- [ ] Update `k8s_app_label` if live label differs
- [x] Prom label names: use `metrics_application` (`portfolio-app`) for `application="$application"` maps
- [ ] Confirm Loki streams: `{namespace="am-apps-preprod", app="<label>"}`

### 1a.4 Generate

- [x] From am-observability: `make generate --only am-portfolio`
- [x] Confirm `dist/grafana/tech-am-portfolio.yaml` (ConfigMap)
- [x] Review: no dialects in templates; queries only after adapt
- [x] Update golden if intentional

### 1a.5 am-infra wire

- [x] Confirm Grafana sidecar/provider loads `grafana_dashboard: "1"` ConfigMaps
- [x] If missing: add dashboardProviders ConfigMap / fix deploy
- [x] Copy artifact → `am-infra/k8s/grafana/dashboards/tech-am-portfolio.yaml`
- [x] Write `OBSERVABILITY_VERSION` (tag or commit SHA)
- [x] Ensure `deploy-monitoring.sh` (or docs) applies `dashboards/*.yaml`
- [ ] Apply to cluster `monitoring` namespace — **blocked: cluster offline**

### 1a.6 Optional scrape follow-up

- [ ] If no HTTP/JVM series: file ticket to add `prometheus.io/scrape` on portfolio Helm
- [ ] Acceptance still OK with omit+warn + logs working (document in PR)

---

## Verification {#verification}

1. [ ] `kubectl -n monitoring get cm grafana-dashboard-tech-am-portfolio`
2. [ ] Grafana UI: folder **AM / Technical**, dashboard UID **tech-am-portfolio**
3. [ ] Variables include service/namespace/env (or defaults)
4. [ ] **Logs** panel shows portfolio lines in last 1h (preprod)
5. [ ] **Errors** log panel filters error-like levels (or documented fallback)
6. [ ] At least one **metrics** panel has data **OR** PR lists omit+warn + scrape ticket ID
7. [ ] Trace **link** works or omitted with warn
8. [ ] Source of truth remains YAML in repos — not a Grafana UI export checked into am-observability as template
9. [ ] Rollback test: re-apply previous ConfigMap (if prior version exists) still applies cleanly

### Exit criteria

| Criterion | Pass? |
|-----------|-------|
| E2E generate → Grafana works | [ ] |
| am-infra pin path proven | [ ] |
| Safe to start Phase 1b | [ ] |

**Signed off by:** _______________ **Date:** _______________
