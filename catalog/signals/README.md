# Signal modules

Each file is a SignalModule (`signals:` map) grouped by domain.

- `http.yaml`: HTTP / API technical signals
- `functional.yaml`: product/domain KPI signals
- `jvm.yaml`: JVM + process signals
- `client-deps.yaml`: Mongo/Redis/Kafka client/Hikari signals
- `kubernetes.yaml`: k8s + service health signals
- `logs-traces.yaml`: service logs + trace link/latency
- `platform-overview.yaml`: namespace-level platform overview
- `platform-exporters.yaml`: infra Redis/Mongo/Postgres exporter signals
- `kafka.yaml`: infra Kafka exporter signals
