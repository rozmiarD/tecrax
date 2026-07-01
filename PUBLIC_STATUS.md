# Tecrax Public Status

- **Source package version:** `0.3.9a0` (`0.3.9-alpha`) alpha
- **Latest published PyPI package:** `tecrax==0.3.8a0`; it contains the current B2 profile vector
- **Dependencies:** `govengine==0.16.5`, `sclite-core==1.0.8`, `rexecop==0.2.11a0`
- **RExecOp profile:** bundled at `src/tecrax/profile/` via `rexecop.profiles:tecrax`
- **Local fixture:** `tecrax fixture-review` — dry-run GovEngine/SCLite proof only
- **R1 profile slice:** `collect_basic_host_inventory` defines fixed read-only Ubuntu
  command shapes, bounded normalization, validation and a sanitized environment template;
  the template includes a tested GovEngine policy enforcement-plan and admission vector
  for receipt, output digest, timeout, maximum steps and bounded output
- **R2 verified slices:** `check_ntp_health`, `check_docker_services_health`,
  application-level `check_zabbix_container_health`, bounded `check_adguard_health`, and
  unauthenticated `check_portainer_health` over verified TLS; Docker inventory and
  authenticated AdGuard/Portainer management APIs remain explicit blockers
- **R2 aggregate:** `diagnose_monitoring_host` preserves bounded partial failures and
  separates diagnostic completion from observed component health
- **R5-lite network inventory:** `collect_network_device_inventory_readonly` defines
  bounded legacy CLI inventory via `local_shell_readonly`; operator wrapper, target
  address and credentials remain outside the repository
- **Deterministic reactions:** profile-owned host/NTP/Zabbix/Docker/AdGuard/Portainer
  findings select only existing read-only intents; healthy state is no-op and unknown
  state escalates
- **Operator catalog metadata:** every bundled intent declares target kinds,
  capabilities, side-effect class, validation and runbook references; RExecOp projects
  applicability from a private target catalog without claiming authorization
- **Controlled apply slice:** `configure_chrony_ntp_server` is the only active
  mutating intent; it is limited to a managed chrony config file and service restart,
  requires GovEngine admission, and uses operator-owned live wrapper configuration
  outside the repository
- **Public docs baseline:** the repo now documents the Proxmox/PBS readiness,
  backup/restore-proof, admin-tools CT, Samba AD DC, AdGuard, chrony/NTP,
  Zabbix, Grafana, Wazuh, basic alerting, BookStack and GLPI isolated
  restore-proof runbooks while keeping private addresses, credentials and
  target mappings out of Git
- **GLPI baseline:** GLPI is documented as the future ticket channel for Zabbix
  and Wazuh alerts, with final ticket-routing automation still outside the
  active profile until an operator-owned credential and suppression policy exist
- **Execution boundary:** RExecOp owns operator-configured SSH execution; Tecrax does not
  manage credentials or embed target infrastructure data
- **Not claimed:** arbitrary host changes, credential management, automatic discovery,
  CMDB synchronization, catalog-based authorization, carrier adapters, scheduler/storage,
  or production readiness
