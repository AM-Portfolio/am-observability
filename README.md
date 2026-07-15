# am-observability

Tool-agnostic observability definitions for AM microservices: **signal catalog**, **technical/functional templates**, **input adapters**, **output renderers**, and a **thin service registry**.

Requires **Python 3.11+**.

Grafana + LGTM runtime stays in [`am-infra`](../am-infra). Each service owns its own `observability.yaml`; this repo does **not** duplicate 50+ service manifests.

## Quick start

```bash
python -m pip install -r requirements.txt
python gen.py validate
python -m pytest -q
python gen.py generate --only am-portfolio   # uses fixture until sibling observability.yaml exists
```

Schemas live under [`schema/`](schema/). Generator CLI: `python gen.py validate | generate [--only ID] [--continue] [--fixture PATH]`.

Update goldens after intentional catalog/template changes:

```bash
python -m pytest -q --update-goldens
```

## Quick links

| Doc | Purpose |
|-----|---------|
| [docs/TRACKING.md](docs/TRACKING.md) | **Master task list** — mark `[x]` when done |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Locked design decisions |
| [docs/VERIFICATION.md](docs/VERIFICATION.md) | All verification / acceptance steps |
| [docs/ONBOARDING.md](docs/ONBOARDING.md) | Checklist to add service #N (scale to 50+) |
| [docs/phases/](docs/phases/) | Phase-wise detailed steps |
| [docs/phases/phase-0-bootstrap.md](docs/phases/phase-0-bootstrap.md) | Phase 0 bootstrap |
| [docs/phases/phase-1-prep.md](docs/phases/phase-1-prep.md) | Phase 1 prep (catalog + generator) |

## Phase order (do not skip)

1. **Phase 0** — Bootstrap this repo  
2. **Phase 1 prep** — Catalog + generator core  
3. **Phase 1a** — `am-portfolio` (Java) E2E  
4. **Phase 1b** — `am-logging` (Python) E2E  
5. **Phase 2** — Alerts / SLOs / monitors  
6. **Phase 3** — Prove feed or UI switch (stub adapter/publisher)

Track progress only in [docs/TRACKING.md](docs/TRACKING.md).

## Layout

```text
am-observability/
  catalog/              # signal + label contracts
  bindings/             # per-env input/output bindings
  templates/            # technical / functional / platform
  adapters/             # prometheus, loki, tempo, …
  renderers/grafana/
  publishers/
  services/registry.yaml
  schema/
  testdata/
  am_obs/               # generator package
  docs/                 # THIS documentation + checklists
  gen.py / Makefile
  dist/                 # generated (gitignored); pin into am-infra
```

## Status

**Phase 0 + Phase 1 prep done.** Phase 1a locally wired (manifest + generate + am-infra pin). Remaining: bring cluster up → calibrate `k8s_app_label` → `deploy-monitoring.sh` → Grafana verify.
