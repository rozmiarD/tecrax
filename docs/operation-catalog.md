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

`docs/proxmox-external-cifs-backup-runbook.md` documents the operator-owned
external CIFS backup gate for selected Proxmox VM/CT workloads. It complements
local PBS backup and keeps endpoint, share and credential details outside
Tecrax.

`docs/proxmox-external-cifs-restore-proof-runbook.md` documents the first
operator-owned restore proof from external CIFS storage. It restores a low-risk
workload to a temporary ID, validates it offline, and removes the temporary
restore target without claiming full disaster recovery.

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

`docs/samba-ad-dc-deployment-runbook.md` documents the operator-owned Samba AD
DC deployment gate. It keeps domain identity, AD DNS authority, backup handling
and validation separate from any active Tecrax connector or generic identity
management surface.

`docs/samba-ad-baseline-runbook.md` documents the first operator-owned AD
baseline for OUs, groups, password policy and low-impact GPO placeholders. It
does not join clients, migrate users or add active identity-management
operations to Tecrax.

`docs/adguard-home-deployment-runbook.md` documents the operator-owned AdGuard
Home deployment gate. It keeps filtering DNS, AD DNS authority and Hillstone
DHCP ownership separate, and does not add an active AdGuard connector to Tecrax.

## Zabbix deployment

`docs/zabbix-vm-docker-deployment-runbook.md` documents the operator-owned
Zabbix VM deployment gate. It records the VM, Docker Compose, PostgreSQL and
backup boundaries without turning Tecrax into a Zabbix administration tool or
storing Zabbix credentials in Git.

`docs/zabbix-postgresql-app-backup-runbook.md` documents the operator-owned
Zabbix PostgreSQL logical dump gate. It complements PBS VM-level backup and
keeps database credentials, dump files and restore targets outside Tecrax.

`docs/zabbix-first-targets-adoption-runbook.md` documents the first
operator-owned Zabbix monitored-target adoption gate. It starts with ICMP
availability only and does not claim agent, SNMP, alerting or dashboard
coverage.

## Restart Zabbix agent

`restart_zabbix_agent` is a legacy fixture-only mutating workflow. Current
read-only target descriptors do not declare its target kind, capability or
connector requirements. It must remain unavailable and still requires GovEngine
admission and explicit operator approval in any future environment.
