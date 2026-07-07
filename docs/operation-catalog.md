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
`docs/runbooks/ubuntu-host-readonly-runbook.md`.

Zabbix count-only summaries are documented in
`docs/runbooks/zabbix-readonly-summaries-runbook.md`. The explicit T5 boundary decision for
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
in `docs/runbooks/network-device-readonly-runbook.md`.

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

`docs/runbooks/proxmox-backup-server-readiness-runbook.md` documents the current PBS
readiness gate for the Proxmox deployment. It is an operator-owned runbook, not
an active backup connector or backup-health claim.

`docs/runbooks/proxmox-backup-server-deployment-runbook.md` documents the operator-owned
PBS VM deployment gate. It separates deployment, first backup, restore proof and
external-copy coverage as distinct claims.

`docs/runbooks/proxmox-backup-server-post-deploy-hardening-runbook.md`,
`docs/runbooks/proxmox-backup-server-first-backup-job-runbook.md`,
`docs/runbooks/proxmox-backup-server-restore-proof-runbook.md` and
`docs/runbooks/proxmox-backup-server-external-copy-checkpoint-runbook.md` document the
remaining operator-owned PBS gates. They are not active backup-health operations.

`docs/runbooks/proxmox-backup-server-full-os-upgrade-runbook.md` documents the
operator-owned PBS full OS upgrade retry, including package-integrity retry,
kernel reboot validation and the PBS VM EFI bootloader caveat.

`docs/runbooks/proxmox-external-cifs-backup-runbook.md` documents the operator-owned
external CIFS backup gate for selected Proxmox VM/CT workloads. It complements
local PBS backup and keeps endpoint, share and credential details outside
Tecrax.

`docs/runbooks/proxmox-external-cifs-restore-proof-runbook.md` documents the first
operator-owned restore proof from external CIFS storage. It restores a low-risk
workload to a temporary ID, validates it offline, and removes the temporary
restore target without claiming full disaster recovery.

## Proxmox host readiness

`docs/runbooks/proxmox-host-readiness-runbook.md` documents the manual readiness pass for
the fresh Proxmox host. It is not an active operation and does not add generic
Proxmox mutation to Tecrax.

## Admin-tools substrate

`docs/runbooks/admin-tools-substrate-runbook.md` documents the operator-owned private
layout for live environments, wrappers, runtime evidence and sign-offs. It is
not an active operation and does not turn Tecrax into an Ansible, CMDB, vault or
generic shell-runner layer. It now also records the runtime-node model:
admin-tools is the target place for operator wrappers, policy files, private
state and controlled Tecrax/RExecOp runtime, while the operator workstation
remains the development machine.

`docs/runbooks/admin-tools-ct-deployment-runbook.md` documents the first lightweight
admin-tools CT deployment gate and its role as the initial low-risk PBS backup
and restore-proof workload.

## DNS authority

`docs/runbooks/dns-authority-checkpoint-runbook.md` documents the operator-owned DNS
authority model for Samba AD DNS and AdGuard filtering DNS. It is not an active
DNS connector and does not deploy either service.

`docs/runbooks/samba-ad-dc-deployment-runbook.md` documents the operator-owned Samba AD
DC deployment gate. It keeps domain identity, AD DNS authority, backup handling
and validation separate from any active Tecrax connector or generic identity
management surface.

`docs/runbooks/samba-ad-baseline-runbook.md` documents the first operator-owned AD
baseline for OUs, groups, password policy and low-impact GPO placeholders. It
does not join clients, migrate users or add active identity-management
operations to Tecrax.

`docs/runbooks/samba-ad-user-provisioning-runbook.md` documents bounded
operator-owned creation of ordinary Samba AD user accounts from a private CSV.
It keeps real user lists, temporary passwords and privileged account assignment
outside Tecrax.

`docs/runbooks/samba-ad-user-logon-gpo-pilot-runbook.md` documents the first
operator-owned domain-user logon and low-impact GPO validation gate on a pilot
Windows workstation. It stays at runbook level and does not claim broad endpoint
rollout or a mutating identity-management intent.

`docs/runbooks/samba-ad-workstation-gpo-rdp-pilot-runbook.md` documents the
operator-owned workstation GPO/RDP pilot after the first endpoint is domain
joined. It records separate pilot GPOs, internal-only RDP validation and the
endpoint update-management gate without adding a generic GPO editor, endpoint
manager or Windows Update orchestrator to Tecrax.

`docs/runbooks/windows-endpoint-update-management-pilot-runbook.md` documents
the operator-owned Windows endpoint update-management pilot. It records a
GPO/WUfB ring baseline, active hours, restart boundaries and Wake-on-LAN future
gate without adding WSUS, RMM, WoL automation or endpoint update orchestration
to Tecrax.

`docs/runbooks/windows-endpoint-agent-rollout-runbook.md` documents the
operator-owned Windows endpoint Zabbix/Wazuh agent rollout pilot. It keeps
Zabbix and Wazuh delivery separate, uses small AD/GPO rollout rings, and keeps
installer secrets, enrollment material and endpoint inventories outside Tecrax.

`docs/runbooks/samba-ad-app-backup-runbook.md` documents the operator-owned
application-aware Samba AD backup gate that complements VM-level PBS backup
without exposing domain backup contents or secrets.

`docs/runbooks/samba-ad-isolated-restore-proof-runbook.md` documents the
operator-owned isolated restore proof for the Samba AD DC VM. It restores a DC
backup to a temporary network-isolated VM, validates local Samba AD and AD DNS
health through the guest agent and removes the temporary target.

`docs/runbooks/windows-ad-pilot-endpoint-runbook.md` documents the operator-owned
Windows endpoint pilot baseline before AD join. It covers public-safe naming,
SSH/PowerShell access, endpoint DNS/NTP baseline and validation gates without
adding a domain-join intent or storing private endpoint inventory in Tecrax.

`docs/runbooks/adguard-home-deployment-runbook.md` documents the operator-owned AdGuard
Home deployment gate. It keeps filtering DNS, AD DNS authority and Hillstone
DHCP ownership separate, and does not add an active AdGuard connector to Tecrax.

## Zabbix deployment

`docs/runbooks/zabbix-vm-docker-deployment-runbook.md` documents the operator-owned
Zabbix VM deployment gate. It records the VM, Docker Compose, PostgreSQL and
backup boundaries without turning Tecrax into a Zabbix administration tool or
storing Zabbix credentials in Git.

`docs/runbooks/zabbix-postgresql-app-backup-runbook.md` documents the operator-owned
Zabbix PostgreSQL logical dump gate. It complements PBS VM-level backup and
keeps database credentials, dump files and restore targets outside Tecrax.

`docs/runbooks/zabbix-postgresql-restore-proof-runbook.md` documents the
operator-owned isolated restore proof for the Zabbix PostgreSQL logical dump.
It restores the custom-format dump into a disposable PostgreSQL target, validates
bounded schema/data counters and removes the temporary restore target without
mutating production.

`docs/runbooks/zabbix-first-targets-adoption-runbook.md` documents the first
operator-owned Zabbix monitored-target adoption gate. It starts with ICMP
availability only and does not claim agent, SNMP, alerting or dashboard
coverage.

`docs/runbooks/zabbix-agent-baseline-runbook.md` documents the operator-owned Linux
agent baseline and mandatory new-host onboarding package. It adds active
`zabbix-agent2` checks without claiming alerting, Grafana, Wazuh or full
application monitoring.

`docs/runbooks/zabbix-network-icmp-adoption-runbook.md` documents the first
operator-owned network-device ICMP adoption gate. It adds the security gateway
and selected managed switches as availability-only targets without claiming
SNMP, SSH inventory, alerting or full topology coverage.

`docs/runbooks/zabbix-network-snmp-adoption-runbook.md` documents the first
operator-owned network-device SNMP adoption gate. It adds read-only SNMP metrics
and basic NTP configuration for selected devices while keeping SNMP credentials,
device secrets and full topology outside Tecrax.

`docs/runbooks/zabbix-naming-normalization-runbook.md` documents the controlled
Zabbix host-name, visible-name, group and tag normalization gate before GLPI
ticket automation. It keeps canonical aliases stable, preserves upstream
templates and leaves Wazuh agent names unchanged.

`docs/runbooks/grafana-ct-deployment-runbook.md` documents the operator-owned Grafana CT
deployment gate. Grafana is introduced as the visualization layer with a direct
Zabbix datasource, initial dashboards, Zabbix monitoring of the Grafana CT and
backup coverage, while keeping Grafana credentials, Zabbix tokens and private
dashboard exports outside Tecrax.

`docs/runbooks/grafana-main-infrastructure-dashboard-runbook.md` documents the
first consolidated infrastructure dashboard. It uses the existing Zabbix
datasource for problem, reachability, agent and resource panels while keeping
Wazuh read-only datasource access and GLPI ticket automation as explicit future
gates.

`docs/runbooks/serverroom-environment-sensor-runbook.md` documents the
operator-owned server room temperature and humidity sensor integration. It adds
bounded Zabbix Agent 2 user parameters on `pve01`, Zabbix items and range-based
temperature triggers, plus Grafana panels backed by the existing Zabbix
datasource.

`docs/runbooks/wazuh-vm-deployment-runbook.md` documents the operator-owned Wazuh VM
deployment gate. Wazuh is introduced as the security monitoring layer with
single-node central components, host-level monitoring and VM-level backup
coverage while keeping generated passwords, enrollment secrets and certificates
outside Tecrax.

`docs/runbooks/wazuh-agent-baseline-runbook.md` documents the operator-owned Wazuh agent
baseline for Linux infrastructure hosts. It enrolls the current server stack
into Wazuh while keeping enrollment secrets, generated keys and user endpoint
inventory outside Tecrax.

`docs/runbooks/basic-alerting-baseline-runbook.md` documents the first operator-owned
basic alerting baseline. It adds local Zabbix and Wazuh alert spools through
systemd timers without claiming final external notification routing, GLPI ticket
creation or incident escalation policy.

`docs/runbooks/alert-presentation-language-baseline-runbook.md` documents the
operator-facing language baseline before GLPI ticket automation. It defines
Polish severity labels, alert categories, GLPI ticket templates and Grafana
language rules while keeping upstream Zabbix/Wazuh technical identifiers intact.

`docs/runbooks/alert-source-hygiene-checkpoint-runbook.md` documents the
alert-source hygiene checkpoint before live GLPI routing. The supporting
`scripts/summarize-wazuh-alerts.py` helper aggregates Wazuh alert volume, top
rules and routing classes without reading credentials or emitting raw payloads.

`docs/runbooks/glpi-alert-ticket-routing-runbook.md` documents the
operator-owned GLPI alert-ticket routing gate. The supporting
`scripts/route-glpi-alerts.py` helper accepts normalized Zabbix/Wazuh events,
renders Polish ticket drafts, applies duplicate suppression and can create GLPI
tickets only when credentials are supplied from outside Git.
`scripts/collect-zabbix-problems-for-glpi.py` is the bounded read-only Zabbix
shadow collector for this gate: it exports active Zabbix problems as normalized
alert events for dry-run routing before any broad live ticket creation.

`docs/runbooks/frigate-host-monitoring-runbook.md` documents the first
operator-owned monitoring baseline for an existing Ubuntu Frigate host. It adds
Zabbix, Wazuh, bounded Frigate listener checks and storage-pressure monitoring
without reading camera streams, credentials, recordings or event payloads.

`docs/runbooks/bookstack-ct-deployment-runbook.md` documents the operator-owned
BookStack CT deployment gate. It introduces BookStack as the documentation and
handoff layer while keeping application secrets, database credentials and future
documentation migration outside Tecrax.

`docs/runbooks/bookstack-isolated-restore-proof-runbook.md` documents the
operator-owned BookStack isolated restore proof. It restores an existing CT
backup to a temporary isolated CT, validates local web/database/application
state and removes the temporary target without exposing documentation contents
or secrets.

`docs/runbooks/glpi-vm-deployment-runbook.md` documents the operator-owned GLPI VM
deployment gate. It introduces GLPI as the helpdesk, inventory and incident
register layer while keeping credentials, mail/LDAP integration and compliance
claims outside Tecrax.

## GLPI Isolated Restore Proof

`docs/runbooks/glpi-isolated-restore-proof-runbook.md` documents the operator-owned GLPI
restore-proof gate. It restores the GLPI VM backup to an isolated temporary VM,
validates bounded application and database health, then removes the temporary
target without exposing restored data or secrets.

## GLPI Minimal Operational Baseline

`docs/runbooks/glpi-minimal-operational-baseline-runbook.md` documents the first
operator-owned GLPI operational baseline. It records default-account hygiene,
minimal helpdesk/inventory/incident categories, request-source values and the
decision that GLPI is the future ticket channel for Zabbix and Wazuh alerts
without enabling final alert automation or claiming compliance readiness.

## GLPI Inventory Scope

`docs/runbooks/glpi-inventory-scope-runbook.md` documents the first
operator-owned GLPI inventory scope. It defines which infrastructure records may
be entered first, which endpoint/device classes remain deferred, and how GLPI
relates to Zabbix, Wazuh, AD, Proxmox and private operator context without
becoming an uncontrolled discovery engine or second source of truth.

## Vaultwarden Bootstrap And Restore Proof

`docs/runbooks/vaultwarden-bootstrap-runbook.md` documents the operator-owned
Vaultwarden bootstrap gate. It introduces Vaultwarden as a critical VM-based
custody service in `bootstrap` status only, keeps the initial web endpoint
restricted before PKI/HTTPS, and blocks final trusted custody until restore
proof, offline break-glass, PKI restore proof and Proxmox root-of-trust
hardening gates are complete.

`docs/runbooks/vaultwarden-backup-restore-proof-runbook.md` documents the
operator-owned Vaultwarden backup and isolated restore-proof gate. It validates
VM-level restore mechanics and bounded service health without inspecting,
exporting or publishing vault contents.

## PKI Center Bootstrap

`docs/runbooks/pki-center-bootstrap-runbook.md` documents the operator-owned
PKI Center bootstrap gate. It creates the on-demand VM substrate and public-safe
custody boundaries before any production CA material, trust-root distribution or
service HTTPS migration exists.

## Basic Incident Handling Baseline

`docs/runbooks/basic-incident-handling-runbook.md` documents the first
operator-owned incident-handling baseline. It defines intake, triage,
classification, containment, evidence custody, closure and follow-up rules for
GLPI incident records without claiming NIS2/KSC2 readiness, legal notification
workflow, forensics or automatic containment.

## Restart Zabbix agent

`restart_zabbix_agent` is a legacy fixture-only mutating workflow. Current
read-only target descriptors do not declare its target kind, capability or
connector requirements. It must remain unavailable and still requires GovEngine
admission and explicit operator approval in any future environment.
