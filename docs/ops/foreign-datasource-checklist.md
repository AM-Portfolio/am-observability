# Foreign datasource checklist (am-infra)

Use when `bindings` point logs/metrics/traces at a provider Grafana does not already have.

- [ ] Confirm output still `grafana` (if not, use a different publisher — skip this list)
- [ ] Install/enable required Grafana datasource plugin on the Grafana deployment
- [ ] Add datasource to Grafana datasources ConfigMap (UID must match bindings)
- [ ] Add credentials via existing secret/Vault pattern — never commit secrets to am-observability
- [ ] Reload/restart Grafana if required
- [ ] Explore → test a manual query against the new datasource
- [ ] Update `am-observability/bindings/{env}.yaml` `datasource_uid`
- [ ] `make generate` + pin + deploy
- [ ] Verify dashboard panels using that input
- [ ] Document rollback (revert binding + ConfigMaps + remove datasource if unused)

Related: [ARCHITECTURE.md](../ARCHITECTURE.md), [phase-3-switch-proof.md](../phases/phase-3-switch-proof.md)
