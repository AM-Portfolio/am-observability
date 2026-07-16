# Ops: release train (Plane B)

## Publish from am-observability

```bash
git tag v1.0.0
git push origin v1.0.0
# Actions → release.yml uploads zip + catalog-index + schema
```

Or locally:

```bash
make package-release VERSION=v1.0.0
# artifacts under dist/release/
```

## Pin + apply in am-infra

See [am-infra/k8s/grafana/dashboards/README.md](../../am-infra/k8s/grafana/dashboards/README.md).

Workflow: **obs-upgrade** (`pr-only` then `apply`). Sidecar reload only — no Grafana restart.

## Doctor a service manifest

```bash
python gen.py doctor ../am-portfolio/observability.yaml
python gen.py doctor ../am-core-services/services/am-gateway/observability.yaml
```
