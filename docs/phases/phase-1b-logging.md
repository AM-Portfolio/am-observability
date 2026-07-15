# Phase 1b — Pilot `am-logging` (Python Tier B)

**Goal:** Second pilot proving Tier B degrade path (logs + k8s, no blank Prom RED charts).

**Depends on:** Phase 1a verified  
**Unlocks:** Wave rollout / Phase 2

---

## Detailed steps

### 1b.1 Service manifest

- [ ] Create `am-logging/observability.yaml`:

```yaml
apiVersion: am.obs/v1
kind: ServiceObservability
service: am-logging
tier: B
runtime: python
k8s_app_label: am-logging   # calibrate
namespace: am-apps-preprod
owners: [platform]
signals:
  uses:
    - k8s_cpu_usage
    - k8s_memory_usage
    - k8s_restarts
    - service_logs_all
    - service_error_logs
    - service_health_up
functional: []
```

- [ ] Confirm this dashboard targets the **logging service workload**, not every CLS client

### 1b.2 Registry

- [ ] Enable in `services/registry.yaml`:

```yaml
  - id: am-logging
    repo: am-logging
    path: observability.yaml
    ref: main
    enabled: true
```

### 1b.3 Calibrate

- [ ] Confirm pod labels in `am-apps-preprod`
- [ ] Loki query `{namespace="am-apps-preprod", app="<label>"}` returns logging service logs

### 1b.4 Generate + pin

- [ ] `make generate --only am-logging`
- [ ] Inspect JSON: **must not** include http_request_rate / jvm_* panels
- [ ] Pin `tech-am-logging.yaml` into am-infra dashboards
- [ ] Bump `OBSERVABILITY_VERSION`
- [ ] Apply deploy

### 1b.5 Docs

- [ ] Update ONBOARDING examples if labels differed from defaults
- [ ] Mark Phase 1b in TRACKING after verification

---

## Verification {#verification}

1. [ ] ConfigMap `grafana-dashboard-tech-am-logging` in `monitoring`
2. [ ] Grafana: **AM / Technical** / UID **tech-am-logging**
3. [ ] Log panels show data for logging pods
4. [ ] **No** empty RED/JVM timeseries panels at all
5. [ ] k8s panels work **or** omit+warn documented
6. [ ] `func-am-logging` ConfigMap **does not** exist
7. [ ] `make generate` (both enabled pilots) succeeds; `dist/report.json` (if implemented) shows both pass
8. [ ] Phase 1a dashboard still healthy after 1b deploy (no overwrite clash)

### Exit criteria

| Criterion | Pass? |
|-----------|-------|
| Tier B path proven | [ ] |
| Phase 1 (both pilots) done | [ ] |
| Safe to onboard wave 2 | [ ] |

**Signed off by:** _______________ **Date:** _______________
