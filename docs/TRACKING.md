# Master tracking checklist

Mark items `[x]` only after the **verification** for that step passes (see [VERIFICATION.md](VERIFICATION.md) and the phase doc).

**How to use:** work phases in order. Do not start Phase 1b until Phase 1a verification is green. Update this file in the same PR that completes work.

---

## Phase 0 — Bootstrap repo

- [x] Repo `am-observability` initialized (git remote if/when ready)
- [x] Folder layout created (`catalog/`, `bindings/`, `templates/`, `adapters/`, `renderers/`, `publishers/`, `schema/`, `testdata/`, `services/`)
- [x] `requirements.txt` / `pyproject.toml` with `PyYAML`, `jsonschema`, `pytest`
- [x] JSON Schemas stubbed (`service-observability`, `signal-catalog`, `bindings`, `dashboard-ir`, `registry`)
- [x] `Makefile` targets: `validate`, `test`, `generate`, `release` (stubs OK)
- [x] `gen.py` stub that exits non-zero with "not implemented" or no-op validate
- [x] CI workflow: validate + test on PR
- [x] `services/registry.yaml` exists (pilots listed, `enabled: false` until Phase 1)
- [x] README links to docs accurate
- [x] **VERIFY:** [Phase 0 verification](phases/phase-0-bootstrap.md#verification)

**Phase 0 complete:** [x]

---

## Phase 1 prep — Catalog + generator core

- [x] Frozen Phase 1 signals landed in `catalog/signals.yaml` with adapter maps
- [x] `catalog/labels.yaml` + `adapters/capabilities.yaml`
- [x] `bindings/preprod.yaml` with prometheus/loki/tempo datasource UIDs
- [x] Technical template `templates/technical/service-overview.yaml`
- [x] Functional template present but skipped when `functional: []`
- [x] Pipeline: validate → compose → adapt → render → publish
- [x] Golden test harness under `testdata/goldens/`
- [x] `make generate --only <id>` supported
- [x] Generate continues/report for failures (`dist/report.json` design)
- [x] **VERIFY:** unit/golden tests pass locally + CI

**Phase 1 prep complete:** [x]

---

## Phase 1a — am-portfolio (Java)

- [x] `am-portfolio/observability.yaml` created (apiVersion, tier A, signals.uses)
- [x] Registry entry `am-portfolio` with `enabled: true`
- [ ] Live `k8s_app_label` confirmed on cluster (calibrate if needed)
- [x] Prom label names calibrated (`application` vs `service`) in catalog maps
- [x] `make generate --only am-portfolio` produces `dist/grafana/tech-am-portfolio.yaml`
- [x] am-infra: dashboard provider/sidecar confirmed
- [x] Artifact pinned to `am-infra/k8s/grafana/dashboards/` + `OBSERVABILITY_VERSION`
- [ ] Deploy applied to `monitoring` namespace
- [ ] **VERIFY:** [Phase 1a verification](phases/phase-1a-portfolio.md#verification)

**Phase 1a complete:** [ ]

---

## Phase 1b — am-logging (Python)

- [ ] `am-logging/observability.yaml` created (tier B, no RED/JVM signals)
- [ ] Registry entry `am-logging` with `enabled: true`
- [ ] `make generate --only am-logging` produces `dist/grafana/tech-am-logging.yaml`
- [ ] Pinned + deployed via same am-infra path
- [ ] **VERIFY:** [Phase 1b verification](phases/phase-1b-logging.md#verification)

**Phase 1b complete:** [ ]

**Phase 1 (both pilots) complete:** [ ]

---

## Phase 2 — Alerts / SLOs / monitors

- [ ] Alert IR schema from same catalog signals
- [ ] Alert renderer/publisher (PrometheusRule and/or Grafana unified alerting)
- [ ] Alertmanager (or chosen path) deployed/wired in am-infra if required
- [ ] SLO / burn-rate design for 1–2 pilot signals
- [ ] **VERIFY:** [Phase 2 verification](phases/phase-2-alerts.md#verification)

**Phase 2 complete:** [ ]

---

## Phase 3 — Prove switch (feed or UI)

- [ ] Second **input adapter stub** OR second **output publisher stub**
- [ ] Document am-infra datasource checklist for foreign feeds
- [ ] Binding example showing mixed input/output
- [ ] **VERIFY:** [Phase 3 verification](phases/phase-3-switch-proof.md#verification)

**Phase 3 complete:** [ ]

---

## Ongoing / waves (after Phase 1)

- [ ] Wave 2: other Tier A Java services registered
- [ ] Wave 3: Python gateways/agents
- [ ] Wave 4: remaining services
- [ ] Python `/metrics` parity where needed
- [ ] Align Java metric names with `am-observability-lib`
- [ ] Optional: generate registry from amctl catalog (single SoT)

---

## Sign-off

| Milestone | Owner | Date | Notes |
|-----------|-------|------|-------|
| Phase 0 | | | |
| Phase 1a | | | |
| Phase 1b | | | |
| Phase 2 | | | |
| Phase 3 | | | |
