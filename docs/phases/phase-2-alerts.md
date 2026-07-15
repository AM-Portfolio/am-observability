# Phase 2 — Alerts, monitors, SLOs

**Goal:** Same catalog drives alerts/monitors/SLOs; no separate hand-managed Prom rules for pilots.

**Depends on:** Phase 1 complete  
**Unlocks:** Phase 3 (optional parallel)

---

## Detailed steps

### 2.1 Schema + IR

- [ ] Define alert schema (signal id, threshold, severity, for, runbook URL)
- [ ] Extend generator: `alerts/` templates or manifest `alerts:` section
- [ ] Keep signal IDs from catalog only

### 2.2 Publisher

- [ ] Choose Phase 2 target: PrometheusRule and/or Grafana unified alerting
- [ ] Implement publisher → artifacts under `dist/alerts/`
- [ ] Pin path in am-infra (new folder e.g. `k8s/prometheus/rules/` or Grafana provisioning)

### 2.3 Alertmanager (if PrometheusRule path)

- [ ] Deploy/configure Alertmanager in am-infra if missing
- [ ] Wire receivers (email/Slack/etc.) via existing secrets patterns — no secrets in am-observability

### 2.4 Pilot alerts

- [ ] Add 1–2 alerts for am-portfolio (e.g. error rate, restart spike)
- [ ] Add 1 alert for am-logging (e.g. pod restarts or process down)
- [ ] SLO optional: one objective on portfolio availability/error ratio

### 2.5 Docs

- [ ] Binding/ops checklist for alert rollback
- [ ] Update TRACKING / VERIFICATION V2

---

## Verification {#verification}

1. [ ] Generated alert artifact applied in preprod
2. [ ] Alert appears in Prometheus/Grafana Alerting UI
3. [ ] Can force a harmless test fire **or** show pending/firing with synthetic threshold in a PR preview env
4. [ ] Runbook link opens
5. [ ] Disable/rollback previous alert version works
6. [ ] No alert queries hardcoded outside catalog/adapter layer

### Exit criteria

| Criterion | Pass? |
|-----------|-------|
| Catalog-driven alerts for pilots | [ ] |
| am-infra apply path for alerts exists | [ ] |

**Signed off by:** _______________ **Date:** _______________
