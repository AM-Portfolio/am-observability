# Architecture (locked)

## Goal

Switch **feeds** (logs/metrics/traces) and **dashboard UI** independently — same provider or mixed — without rewriting templates. Scale to ~100 repos with **zero service inventory in am-observability**.

## Repos

| Concern | Owns it |
|---------|---------|
| Catalog, templates, adapters, renderers, bindings, release artifacts | **am-observability** |
| Prometheus, Grafana, Loki, Tempo, OTEL, **pinned** dashboard ConfigMaps, `obs-upgrade` | **am-infra** |
| Per-service KPIs / tier / labels / optional panel prefs | **Each service** → `observability.yaml` |

## Three planes

```text
Plane A — Service deploy
  observability.yaml + scrape annotations
  → Prometheus discovers application=
  → shared tech-am-services Service dropdown via label_values (no am-obs/am-infra PR)

Plane B — Shared dashboard upgrade
  am-obs tag → package-release zip
  → am-infra obs-upgrade (PR then kubectl apply ConfigMaps)
  → k8s-sidecar + Grafana file provider (~30s)
  → NO Grafana pod/DB restart

Plane C — Optional service view
  dashboard.panels / rows in service yaml
  → gen.py compose-view → tech-view-{service} ConfigMap
```

## Pipeline (compiler)

```text
catalog + templates → compose IR → adapt → render Grafana JSON → ConfigMap YAML
                     → package-release → GitHub Release asset
```

Service manifests are **not** required to build shared `tech-am-services` / platform dashboards.

## Bindings

Shared LGTM: single [`bindings/platform.yaml`](../bindings/platform.yaml). App env via `$namespace` / manifest `namespace:`.

## am-infra role

- Runtime for Grafana/Prometheus on VPS.
- Git pin: `k8s/grafana/dashboards/` + `OBSERVABILITY_VERSION`.
- CI: `.github/workflows/obs-upgrade.yml` (`pr-only` | `apply` on self-hosted runner).
- Does **not** register services; does **not** store panel prefs.

## Non-goals

Alertmanager cluster, inventing per-service Grafana JSON in app repos, registration DB, hand Copy-Item of `dist/` into am-infra.
