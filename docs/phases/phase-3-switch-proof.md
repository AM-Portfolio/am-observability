# Phase 3 — Prove input/output switch

**Goal:** Show templates stay unchanged when feed or dashboard product binding changes (stub is enough).

**Depends on:** Phase 1 (Phase 2 helpful but not required)  
**Unlocks:** Confidence for future provider migrations

---

## Detailed steps

### 3.1 Choose proof type (pick one first)

- [ ] **Option A — Input stub:** fake `adapters/example_logs/` that emits a marker query string
- [ ] **Option B — Output stub:** `publishers/file_json/` writing plain dashboard IR dump (not Grafana CM)

### 3.2 Binding example

- [ ] Add `bindings/preprod-switch-demo.yaml` (not default) selecting stub
- [ ] Document: Grafana UI + foreign logs still needs am-infra datasource

### 3.3 am-infra checklist doc

- [ ] Write `docs/ops/foreign-datasource-checklist.md`:
  - [ ] Install Grafana plugin if needed
  - [ ] Datasource ConfigMap + secret
  - [ ] Matching `datasource_uid` in bindings
  - [ ] Generate + pin + verify Explore

### 3.4 Implement stub + test

- [ ] Generator accepts alternate `--binding bindings/preprod-switch-demo.yaml`
- [ ] Golden or unit test: template files unchanged; only adapt/publish output differs

---

## Verification {#verification}

1. [ ] `make generate --binding bindings/preprod-switch-demo.yaml --only am-portfolio` succeeds
2. [ ] Diff shows **no** template file changes required
3. [ ] Default `bindings/preprod.yaml` generate still matches Phase 1 goldens
4. [ ] Ops checklist reviewed by someone who can edit am-infra
5. [ ] README mentions how to switch feeds vs UI

### Exit criteria

| Criterion | Pass? |
|-----------|-------|
| Mix-and-match story proven with stub | [ ] |
| No redesign needed for a real second provider later | [ ] |

**Signed off by:** _______________ **Date:** _______________
