# Phase 0 — Bootstrap `am-observability`

**Goal:** Empty-but-valid repo structure, schemas, Makefile/CI stubs, docs. No production dashboards yet.

**Depends on:** Nothing  
**Unlocks:** Phase 1 prep + pilots

---

## Detailed steps

### 0.1 Repository

- [x] Create git repo at `am-repos/am-observability` (this folder)
- [ ] Set remote on GitHub/org when ready (`git remote add origin …`)
- [ ] Protect `main` later (after first real generate CI)

### 0.2 Directory skeleton

- [x] `mkdir` / create:

```text
catalog/
bindings/
templates/technical/
templates/functional/
templates/platform/
adapters/prometheus/
adapters/loki/
adapters/tempo/
renderers/grafana/
publishers/
schema/
services/
testdata/fixtures/
testdata/goldens/
docs/          # already present
```

- [x] Add `.gitkeep` where needed so empty dirs are tracked

### 0.3 Python project

- [x] Add `requirements.txt`:

```text
PyYAML>=6.0
jsonschema>=4.0
pytest>=7.0
```

- [x] Optional: `pyproject.toml` with same deps
- [x] Document Python 3.11+ in README

### 0.4 Schemas (stubs OK)

- [x] `schema/service-observability.schema.json`
- [x] `schema/signal-catalog.schema.json`
- [x] `schema/bindings.schema.json`
- [x] `schema/dashboard-ir.schema.json`
- [x] `schema/registry.schema.json`

Minimum: `$schema`, `type: object`, required top-level keys matching ARCHITECTURE.

### 0.5 Makefile

- [x] `make validate` — schema-check YAML under catalog/bindings/services (stub allowed)
- [x] `make test` — `pytest`
- [x] `make generate` — call `gen.py` (stub)
- [x] `make release` — package `dist/` (stub)

### 0.6 Generator stub

- [x] `gen.py` with CLI sketch: `validate | generate [--only ID] [--continue]`
- [x] Exit 0 on validate of empty/minimal fixtures OR print “Phase 0 stub”

### 0.7 Registry stub

- [x] `services/registry.yaml` with portfolio + logging entries, **`enabled: false`**
- [x] Validate against registry schema

### 0.8 CI

- [x] `.github/workflows/ci.yml`: install deps, `make validate`, `make test`
- [x] Runs on pull_request + push to main

### 0.9 Docs sanity

- [x] README links work
- [x] TRACKING Phase 0 items mirrored here

---

## Verification {#verification}

Complete all before checking **Phase 0 complete** in [TRACKING.md](../TRACKING.md).

1. [x] Fresh clone (or clean tree): docs and skeleton present
2. [x] `python -m pip install -r requirements.txt` succeeds
3. [x] `make validate` exits 0
4. [x] `make test` exits 0
5. [x] `services/registry.yaml` loads (`python -c "import yaml; yaml.safe_load(open('services/registry.yaml'))"`)
6. [x] CI workflow file exists and is syntactically valid YAML
7. [x] No secrets committed

### Exit criteria

| Criterion | Pass? |
|-----------|-------|
| Repo usable as empty platform | [x] |
| Schemas/Makefile/CI exist | [x] |
| Ready to land real catalog in Phase 1 prep | [x] |

**Signed off by:** _______________ **Date:** _______________
