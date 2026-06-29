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

## Current trigger rules

The first active trigger rules are documented in `docs/trigger-rules.md`. They map
a bounded `network.host_observed` event either to a planned dry-run
`collect_basic_host_inventory` operation for a known catalog target, or to
escalation for an unknown host. RExecOp owns trigger mechanics; Tecrax owns only
this domain mapping.

## Future backup status

`check_backup_status` is not part of the active profile. Future backup support
must pass `docs/future-product-activation.md` and keep backup readiness, job
execution, restore evidence and coverage as separate claims.

`docs/proxmox-backup-server-readiness-runbook.md` documents the current PBS
readiness gate for the Proxmox deployment. It is an operator-owned runbook, not
an active backup connector or backup-health claim.

`docs/proxmox-backup-server-deployment-runbook.md` documents the operator-owned
PBS VM deployment gate. It separates deployment, first backup, restore proof and
external-copy coverage as distinct claims.

`docs/proxmox-backup-server-post-deploy-hardening-runbook.md`,
`docs/proxmox-backup-server-first-backup-job-runbook.md`,
`docs/proxmox-backup-server-restore-proof-runbook.md` and
`docs/proxmox-backup-server-external-copy-checkpoint-runbook.md` document the
remaining operator-owned PBS gates. They are not active backup-health operations.

## Proxmox host readiness

`docs/proxmox-host-readiness-runbook.md` documents the manual readiness pass for
the fresh Proxmox host. It is not an active operation and does not add generic
Proxmox mutation to Tecrax.

## Admin-tools substrate

`docs/admin-tools-substrate-runbook.md` documents the operator-owned private
layout for live environments, wrappers, runtime evidence and sign-offs. It is
not an active operation and does not turn Tecrax into an Ansible, CMDB, vault or
generic shell-runner layer.

`docs/admin-tools-ct-deployment-runbook.md` documents the first lightweight
admin-tools CT deployment gate and its role as the initial low-risk PBS backup
and restore-proof workload.

## DNS authority

`docs/dns-authority-checkpoint-runbook.md` documents the operator-owned DNS
authority model for Samba AD DNS and AdGuard filtering DNS. It is not an active
DNS connector and does not deploy either service.

## Restart Zabbix agent

`restart_zabbix_agent` is a legacy fixture-only mutating workflow. Current
read-only target descriptors do not declare its target kind, capability or
connector requirements. It must remain unavailable and still requires GovEngine
admission and explicit operator approval in any future environment.
