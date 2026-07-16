# Debugging signal checklist — Technical / Services

Use this when deepening observability for AM microservices. The shared dashboard
**Technical / Services** is the primary surface (Namespace + Service dropdowns).

## Shipped in the SRE redesign

| Area | What you get |
|------|----------------|
| Quick decision | Health score 0–100, GOOD/WATCH/ACT, action checklist |
| Service health | Pods, scrape up, restarts, uptime, CPU, memory, heap gauge, **image + Helm chart + app version**, section blurbs |
| Golden Signals | Traffic, latency p50/p75/p95, 5xx ratio/rate, process CPU; Method + API path filters |
| API SLO table | Per endpoint: Total, 2xx, 4xx, **5xx**, Fail, avg, p50, **p75**, p90, p95 |
| HTTP trends | Status / outcome / outbound client (collapsed by default) |
| Dependencies | Mongo / Redis / Kafka / Hikari — **section-scoped** filters (cmd / listener / topic / pool); multi-color per-entity rate + p95; pool/lag |
| Look & feel | Soft KPI value colors (not brick stats); gradient timeseries; shared crosshair; tags `am`/`sre` |
| Latency | **Avg by API** primary; p95 **or avg fallback** (fixes empty p95); thresholds 1s/5s/20s |
| Functional | **AM / Functional → Functional / Services** — usage, slow APIs hero, success, Tempo act, domain gauges |
| JVM detail | Heap, GC, threads, Tomcat, FDs (collapsed) |
| K8s pressure | CPU + memory timeseries (collapsed) |
| Evidence | Tempo link → **Error logs** → Logs |

## Platform blockers (panels stay empty until fixed)

1. **App scrape** — publish universal-chart that merges `podAnnotations`; redeploy services with Prometheus scrape annotations.
2. **Micrometer** — `micrometer-registry-prometheus` on classpath + rebuild/redeploy (e.g. am-portfolio).
3. **kube-state-metrics** — required for accurate `k8s_restarts` (and later ready/desired replicas).
4. **Promtail / Tempo labels** — pods come from Prometheus join (`$pod` for the selected `$application`); Tempo `service.name` should match the Micrometer `application` label.

## Next tier (add for Amazon-depth debugging)

### Pods / Kubernetes
- Ready vs desired replicas, unavailable pods
- OOMKilled / last termination reason
- CPU throttle vs requests/limits
- Network RX/TX, ephemeral storage
- Deployment rollout generation / pod age

### JVM / app
- Heap used % alerting thresholds as recording rules
- GC pause p95, metaspace pressure
- Thread states dump signal
- Connection pool pending + timeouts (Hikari / mongo)

### HTTP / APIs
- Per-status pivot (200/401/404/500) when needed
- Outbound client latency p95 + errors **by dependency**
- SLO burn-rate panels (error budget)

### Dependencies
- ~~Kafka lag by topic~~ (shipped: topic filter + per-topic lag; listener filter for rate/p95)
- ~~Redis by command~~ (shipped)
- ~~Hikari pool active/pending/idle/timeouts~~ (shipped; empty until JDBC enabled)
- Mongo **collection** / SQL **table** filters (need app `@Timed` — Micrometer has no table label)
- Kafka rebalances, partition lag UI
- Cache hit ratio, Redis timeouts
### Correlation
- `trace_id` extracted in Loki → Tempo links
- Exemplars from Prometheus histograms to Tempo

## How to add a new signal

1. Add entry to `catalog/signals.yaml` (`adapter_map` only — no PromQL in templates).
2. Reference it from `templates/technical/service-overview.yaml`.
3. List it under `signals.uses` in the service `observability.yaml`.
4. `npm run generate` → pin ConfigMap into am-infra → `kubectl apply` (no Grafana restart needed for updates).
