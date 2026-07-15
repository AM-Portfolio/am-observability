# Verification reference

Run these checks before marking a phase `[x]` in [TRACKING.md](TRACKING.md). Prefer preprod: namespace **`am-apps-preprod`**, Grafana folder **`AM / Technical`**.

---

## Conventions under test

| Item | Expected |
|------|----------|
| Dashboard UID | `tech-{service}` |
| ConfigMap | `grafana-dashboard-{uid}` label `grafana_dashboard: "1"` |
| Pin path | `am-infra/k8s/grafana/dashboards/` |
| Version file | `am-infra/.../OBSERVABILITY_VERSION` or sibling |
| Binding | `bindings/preprod.yaml` |

---

## V0 — Bootstrap

1. [x] `make validate` (or stub) runs without traceback
2. [x] `make test` collects at least an empty/placeholder suite
3. [ ] CI green on a no-op PR
4. [x] Schemas exist and are referenced from README or Makefile
5. [x] `services/registry.yaml` parses as YAML

---

## V1-prep — Generator

1. [x] Invalid catalog/manifest fails validate with clear error
2. [x] Unknown signal ID in manifest fails CI
3. [x] Compose drops panels whose signals are not in `signals.uses`
4. [x] Unsupported adapter capability omits panel + warning (no empty PromQL lie)
5. [x] Golden test updates intentionally (`make test`)

---

## V1a — am-portfolio

1. [ ] ConfigMap `grafana-dashboard-tech-am-portfolio` exists in `monitoring`
2. [ ] Dashboard visible: Grafana → `AM / Technical` → Technical / am-portfolio
3. [ ] Log panel returns lines for `namespace=am-apps-preprod` + calibrated `app` label
4. [ ] Metrics: at least one timeseries with data **or** documented omit+warn + scrape follow-up ticket
5. [ ] Tempo/trace `link` panel opens Explore (or is omitted with warn if Tempo unavailable)
6. [ ] No hand-edited Grafana JSON committed as source of truth in am-observability
7. [ ] `OBSERVABILITY_VERSION` matches released/pinned generator output

---

## V1b — am-logging

1. [ ] ConfigMap `grafana-dashboard-tech-am-logging` exists in `monitoring`
2. [ ] Dashboard visible under `AM / Technical`
3. [ ] Log panels show logging service workload logs
4. [ ] **Zero** empty RED/JVM panels (those signals must not appear)
5. [ ] k8s CPU/mem/restarts present **or** omit+warn if kube metrics missing
6. [ ] Functional ConfigMap **not** published

---

## V2 — Alerts

1. [ ] Alert definitions generated from catalog signal IDs (no hardcodes for pilots only without schema)
2. [ ] Test alert can fire in preprod (or recording rule visible)
3. [ ] Runbook URL / severity fields present on pilot alert
4. [ ] Rollback: previous alert artifact re-applicable

---

## V3 — Switch proof

1. [ ] Alternate binding selects stub adapter/publisher without template edits
2. [ ] Documents list am-infra datasource steps for a foreign log feed
3. [ ] Templates still contain **no** vendor query dialects

---

## Failure conditions (any phase)

Mark phase **failed** (do not check complete) if:

- [ ] LogQL/PromQL pasted into templates
- [ ] Fake functional KPI panels with invented metrics
- [ ] Python dashboard full of blank Prom charts
- [ ] Artifacts not applied by am-infra deploy path
- [ ] Dashboards only exist as manual Grafana UI edits
