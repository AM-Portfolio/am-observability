# Onboard a service (50+ scale)

Use this checklist for every new workload after Phase 1 pilots work.

## Prerequisites

- [ ] Phase 1a + 1b complete ([TRACKING.md](TRACKING.md))
- [ ] You know `k8s_app_label` / pod naming in `am-apps-preprod`
- [ ] Tier chosen: **A** (Java Prom+OTEL) or **B** (logs+k8s first)

## Steps

### 1. Manifest in the service repo

- [ ] Add `{repo}/observability.yaml` (or nested path for multi-app repos)

```yaml
apiVersion: am.obs/v1
kind: ServiceObservability
service: am-example
tier: B   # or A
runtime: python  # or java
k8s_app_label: am-example
# Optional: when Micrometer/Spring application label differs from service id
# metrics_application: my-spring-app-name
namespace: am-apps-preprod
owners: [your-team]
signals:
  bundle: tier-b-python   # Tier A example: tier-a-java-core
  domain: []              # Optional domain KPIs (e.g. portfolio_*)
```

- [ ] CODEOWNERS covers this file for the service team

### 2. Registry entry

- [ ] Add to `am-observability/services/registry.yaml`:

```yaml
  - id: am-example
    repo: am-example
    path: observability.yaml
    ref: main
    enabled: true
```

- [ ] For multi-workload repos, use distinct `id` + `path` per workload

### 3. Generate and verify

- [ ] `make generate --only am-example`
- [ ] Open `dist/grafana/tech-am-example.yaml` — review panels
- [ ] Pin into am-infra dashboards path (or wait for next release train)
- [ ] Apply to cluster / deploy-monitoring
- [ ] Grafana: folder `AM / Technical`, UID `tech-am-example`
- [ ] Logs panel shows data for preprod
- [ ] Tier B: confirm no empty RED panels

### 4. Optional follow-ups

- [ ] Add `prometheus.io/scrape` annotations if Tier A metrics missing
- [ ] Add real `signals.domain` KPIs only when metrics exist
- [ ] Set `enabled: false` in registry to pause without deleting manifest

## Wave guidance

| Wave | Who |
|------|-----|
| 1 | am-portfolio, am-logging |
| 2 | Other Tier A Java |
| 3 | Python gateways / agents |
| 4 | Remainder |

Do not enable whole wave until one service in that wave verifies clean.
