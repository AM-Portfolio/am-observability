# am-observability

Tool-agnostic observability definitions for AM microservices: **signal catalog**, **technical/functional templates**, **input adapters**, **output renderers**, and a **thin service registry**.

Requires **Python 3.11+**. Optional: **Node 18+** only if you prefer `npm run …` script shortcuts (they call Python under the hood — this is not a Node app).

Grafana + LGTM runtime stays in [`am-infra`](../am-infra). Each service owns its own `observability.yaml`; this repo does **not** duplicate 50+ service manifests.

## Run locally (recommended)

### 1. One-time setup

```bash
cd am-observability
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
# source .venv/bin/activate

npm run setup
# same as: python -m pip install -r requirements.txt
```

### 2. Validate + test (do this before CI)

```bash
npm run validate   # schema-check catalog / bindings / registry
npm run test       # unit + golden tests
```

Or the CI-equivalent combo:

```bash
npm run ci         # validate && test
```

### 3. Generate dashboards locally

```bash
npm run generate:portfolio   # → dist/grafana/tech-am-portfolio.yaml
npm run generate:logging     # fixture until am-logging/observability.yaml exists
npm run generate             # all registry entries with enabled: true
```

Inspect output:

- `dist/grafana/*.yaml` — ConfigMaps to pin into am-infra
- `dist/report.json` — pass/fail + warnings

### 4. Full local preflight

```bash
npm run preflight   # setup + validate + test + generate portfolio
```

### 5. Update goldens (only when catalog/template change is intentional)

```bash
npm run goldens:update
npm run test
```

### npm scripts

| Script | What it runs |
|--------|----------------|
| `npm run setup` | `pip install -r requirements.txt` |
| `npm run validate` | `python gen.py validate` |
| `npm run test` | `pytest -q` |
| `npm run ci` | validate + test (same checks as GitHub Actions) |
| `npm run generate` | generate all enabled registry services |
| `npm run generate:portfolio` | `--only am-portfolio` |
| `npm run generate:logging` | `--only am-logging` |
| `npm run generate:continue` | continue on per-service failures |
| `npm run goldens:update` | rewrite `testdata/goldens/` |
| `npm run preflight` | setup + ci + generate portfolio |

Plain Python equivalents (no npm):

```bash
python -m pip install -r requirements.txt
python gen.py validate
python -m pytest -q
python gen.py generate --only am-portfolio
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
  catalog/                 # signal + label contracts
  bindings/                # platform input/output bindings (shared LGTM)
  templates/               # technical / functional / platform
  adapters/                # prometheus, loki, tempo (+ capabilities.yaml)
  renderers/grafana/       # Grafana JSON renderer
  publishers/              # grafana_configmap publisher
  services/registry.yaml
  schema/
  testdata/
  am_obs/                  # pipeline orchestration (validate/compose/CLI helpers)
  docs/
  gen.py / Makefile / package.json
  dist/                    # generated (gitignored); pin into am-infra
```

## Local / CI notes

- Default binding: `bindings/platform.yaml` (shared monitoring).
- CI runs `validate` + `test` only; do **not** matrix-generate per app env when LGTM is shared.
- Generate pins into `am-infra`; am-observability is not deployed as a K8s pod.
