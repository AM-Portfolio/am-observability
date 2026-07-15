# Phase 1 prep — Catalog + generator core

**Goal:** Frozen signals, bindings, technical template, and a working validate → compose → adapt → render → publish pipeline with goldens. No cluster deploy yet.

**Depends on:** Phase 0  
**Unlocks:** Phase 1a / 1b pilots

---

## Detailed steps

### Catalog + bindings

- [x] `catalog/signals.yaml` with Phase 1 signal IDs + `adapter_map` expr templates
- [x] `catalog/labels.yaml`
- [x] `adapters/capabilities.yaml`
- [x] `bindings/preprod.yaml` (prometheus / loki / tempo datasource UIDs)
- [x] `templates/technical/service-overview.yaml` (signal refs only — no dialects)
- [x] `templates/functional/domain-kpi.yaml` (skipped when `functional: []`)

### Generator

- [x] Pipeline: validate → compose (template ∩ `signals.uses`) → adapt → render → publish
- [x] `gen.py validate` / `gen.py generate [--only ID] [--continue] [--fixture PATH]`
- [x] `dist/report.json` pass/fail summary
- [x] Fixtures under `testdata/fixtures/` (portfolio + logging)
- [x] Goldens under `testdata/goldens/` (`--update-goldens` to refresh)

---

## Verification {#verification}

1. [x] `python gen.py validate` exits 0
2. [x] `python -m pytest -q` green (includes golden compare)
3. [x] `python gen.py generate --only am-portfolio` writes `dist/grafana/tech-am-portfolio.yaml`
4. [x] `python gen.py generate --only am-logging` writes `dist/grafana/tech-am-logging.yaml` with **no** RED/JVM panels
5. [x] ConfigMap label `grafana_dashboard: "1"` present in generated YAML
6. [x] Templates contain no PromQL/LogQL dialects

### Exit criteria

| Criterion | Pass? |
|-----------|-------|
| Catalog + bindings landed | [x] |
| Generator + goldens green | [x] |
| Ready for Phase 1a service manifests | [x] |

**Signed off by:** _______________ **Date:** _______________
