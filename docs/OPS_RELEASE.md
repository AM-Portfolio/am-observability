# Ops: release train (Plane B)

## Publish from am-observability

```bash
git tag v1.0.0
git push origin v1.0.0
```

CI (`release.yml`): generate zip → GitHub Release → **dispatches am-infra** (needs secret `INFRA_DISPATCH_TOKEN`).

Push to `main` alone does **not** update Grafana.

## am-infra apply (ConfigMaps only — no Grafana restart)

Auto (preferred): am-obs tag → `repository_dispatch` → `obs-upgrade` `apply` on **self-hosted** (same as am-pipelines `central-deploy`, **no** Docker container).

Manual: Actions → **obs-upgrade** → `mode=apply`, `version=v0.1.0`.

```text
kubectl apply -f k8s/grafana/dashboards/
→ sidecar WATCH → Grafana file provider ~30s
→ never rollout restart grafana
```

`mode=pr-only` only opens a Git PR (no cluster).

## Secret (one-time)

| Secret | Repo | Purpose |
|--------|------|---------|
| `INFRA_DISPATCH_TOKEN` | am-observability | PAT/App token with `repo` on private am-infra for `repository_dispatch` |

Without it, release still publishes assets; run am-infra `obs-upgrade` apply manually.
