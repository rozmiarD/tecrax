# Tecrax operation catalog metadata

Tecrax owns operation vocabulary, target kinds, required capabilities, connector
semantics, validation and runbook references. RExecOp only projects this metadata
against an operator-owned target catalog. A technically applicable operation still
requires GovEngine admission before execution.

The sanitized catalog example is
`examples/catalogs/targets.readonly.example.yaml`. Real target mappings,
environment paths, addresses and connector state remain outside Git. Credentials
remain exclusively in `REXECOP_SECRETS_FILE` or another approved secret resolver.

## Current read-only host operations

The detailed operator procedure for `collect_basic_host_inventory`, host load,
NTP, Docker service/socket state, Zabbix reachability, AdGuard reachability,
Portainer status and `diagnose_monitoring_host` is in
`docs/ubuntu-host-readonly-runbook.md`.

Zabbix count-only summaries are documented in
`docs/zabbix-readonly-summaries-runbook.md`. The explicit T5 boundary decision for
Docker, AdGuard and Portainer expansion is in
`docs/service-boundary-decision-t5.md`.

`diagnose_monitoring_host` produces the versioned
`tecrax.monitoring_host_diagnosis@1.0` aggregate with bounded findings. Reactions may use
those findings to select an already declared read-only intent, no-op or escalation proposal;
they do not create free-form actions.
Bounded escalation proposal vectors are documented in
`docs/escalation-proposal-vectors.md`. They are untrusted advisory artifacts with
`may_execute=false`; RExecOp validation and GovEngine admission remain separate gates.

## Current network-device operation

The bounded adapter contract for `collect_network_device_inventory_readonly` is
in `docs/network-device-readonly-runbook.md`.

## Future backup status

`check_backup_status` is not part of the active profile. Future backup support
must pass `docs/future-product-activation.md` and keep backup readiness, job
execution, restore evidence and coverage as separate claims.

## Restart Zabbix agent

`restart_zabbix_agent` is a legacy fixture-only mutating workflow. Current
read-only target descriptors do not declare its target kind, capability or
connector requirements. It must remain unavailable and still requires GovEngine
admission and explicit operator approval in any future environment.
