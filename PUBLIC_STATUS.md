# Tecrax Public Status

- **Package version:** `0.3.4a0` (`0.3.3-alpha`)
- **Dependencies:** `govengine>=0.15.0,<0.16`, `sclite-core>=1.0.4,<1.1`, `rexecop>=0.2.5a0,<0.3`
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
- **Execution boundary:** RExecOp owns operator-configured SSH execution; Tecrax does not
  manage credentials or embed target infrastructure data
- **Not claimed:** infrastructure mutation, credential management, automatic discovery,
  CMDB synchronization, catalog-based authorization, carrier adapters, scheduler/storage,
  or production readiness
