# Tecrax

[![CI](https://github.com/rozmiarD/tecrax/actions/workflows/ci.yml/badge.svg)](https://github.com/rozmiarD/tecrax/actions/workflows/ci.yml)
[![Package: tecrax 0.3.21a0](https://img.shields.io/badge/package-tecrax%200.3.21a0-blueviolet.svg)](https://pypi.org/project/tecrax/0.3.21a0/)
[![Python: 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![Dependency: GovEngine ==0.16.11](https://img.shields.io/badge/dependency-GovEngine%20%3D%3D0.16.11-informational.svg)](https://github.com/rozmiarD/GovEngine)
[![Dependency: RExecOp ==0.2.24a0](https://img.shields.io/badge/dependency-RExecOp%20%3D%3D0.2.24a0-informational.svg)](https://github.com/rozmiarD/RExecOP)
[![Dependency: SCLite ==1.0.9](https://img.shields.io/badge/dependency-SCLite%20%3D%3D1.0.9-informational.svg)](https://github.com/rozmiarD/SCLite)
[![Status: alpha](https://img.shields.io/badge/status-alpha-green.svg)](#status)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

**Governed infrastructure-operations profile** for RExecOp, using GovEngine governance
and SCLite artifact truth.

Tecrax owns infrastructure intent vocabulary, connector semantics, bounded normalization,
validation rules, runbooks, reactions, triggers and operator catalog metadata. RExecOp
plans and executes; GovEngine admits; SCLite records evidence. Tecrax does not manage
credentials, embed target topology, or accept arbitrary infrastructure commands.

## Status

| Item | Value |
| --- | --- |
| Current source line | `0.3.21a0` (`0.3.21-alpha`) |
| Maturity | **alpha** — operator evaluation with documented limits |
| Latest PyPI | [`tecrax==0.3.21a0`](https://pypi.org/project/tecrax/0.3.21a0/) |
| Source dependencies | `govengine==0.16.11`, `sclite-core==1.0.9`, `rexecop==0.2.24a0` |
| Profile entry point | `rexecop.profiles:tecrax` |
| Active mutating intent | `configure_chrony_ntp_server` only |
| Public status | [`PUBLIC_STATUS.md`](PUBLIC_STATUS.md) |

Latest published PyPI baseline: `tecrax==0.3.21a0`; it contains the coordinated
B2 dependency floor and read-only policy vector.

## What Tecrax provides

- **RExecOp domain profile** — bundled YAML profile with intents, workflows, connectors,
  validation rules, finding taxonomy and escalation rules (entry point
  `rexecop.profiles:tecrax`).
- **Local fixture review** — dry-run proof slice without live infrastructure.
- **B2 policy vector** — profile-owned receipt, output-digest, timeout, step-count and
  output-size controls compiled and admitted by GovEngine, enforced by RExecOp.
- **Operator catalog metadata** — target kinds, required capabilities, side-effect
  classes, validation and runbook references projected by RExecOp from intent files;
  sanitized target-catalog example included.
- **Deterministic reactions** — monitoring-host findings map only to existing read-only
  intents; healthy state is `no_op`, unknown state escalates.
- **Bounded escalation proposals** — `diagnose_monitoring_host` facts project into
  untrusted SCLite proposal artifacts with `may_execute=false`.
- **Source-line trigger rules** — bounded `network.host_observed` events map known catalog
  targets to dry-run `collect_basic_host_inventory` planning; unknown hosts escalate.
- **Governed mutation slice** — `configure_chrony_ntp_server` is the only active apply
  operation, limited to a managed chrony config file and service restart with GovEngine
  admission.

### Active intents (14)

| Group | Intent | Effect |
| --- | --- | --- |
| Host inventory | `collect_basic_host_inventory` | read-only SSH inventory |
| Host security | `collect_host_security_posture_readonly` | read-only posture summary |
| NTP health | `check_ntp_health`, `check_ntp_server_health` | read-only chrony/systemd checks |
| Container services | `check_docker_services_health` | read-only systemd service state |
| Application health | `check_zabbix_container_health`, `check_adguard_health`, `check_portainer_health` | read-only API/reachability |
| Zabbix summaries | `collect_zabbix_problem_summary_readonly`, `collect_zabbix_host_availability_summary_readonly` | read-only bounded counts |
| Network devices | `collect_network_device_inventory_readonly`, `assess_network_device_management_posture_readonly` | read-only legacy CLI inventory/posture |
| Diagnosis | `diagnose_monitoring_host` | bounded aggregate over component checks |
| Mutation | `configure_chrony_ntp_server` | governed chrony/NTP server apply |

Connectors in the active profile: SSH local readonly, Zabbix API, AdGuard, Portainer,
network-device CLI wrapper, and `tecrax_chrony_ntp` for the mutation slice.

### Operator runbooks

Public-safe operator procedures live under `docs/runbooks/`. They document deployment,
readiness and validation gates; private addresses, credentials and target mappings stay
outside Git. See also [`docs/operation-catalog.md`](docs/operation-catalog.md).

| Area | Runbooks |
| --- | --- |
| Proxmox host | [`proxmox-host-readiness-runbook.md`](docs/runbooks/proxmox-host-readiness-runbook.md) |
| Proxmox backup (PBS) | [`proxmox-backup-server-readiness-runbook.md`](docs/runbooks/proxmox-backup-server-readiness-runbook.md), [`proxmox-backup-server-deployment-runbook.md`](docs/runbooks/proxmox-backup-server-deployment-runbook.md), [`proxmox-backup-server-post-deploy-hardening-runbook.md`](docs/runbooks/proxmox-backup-server-post-deploy-hardening-runbook.md), [`proxmox-backup-server-first-backup-job-runbook.md`](docs/runbooks/proxmox-backup-server-first-backup-job-runbook.md), [`proxmox-backup-server-restore-proof-runbook.md`](docs/runbooks/proxmox-backup-server-restore-proof-runbook.md), [`proxmox-backup-server-external-copy-checkpoint-runbook.md`](docs/runbooks/proxmox-backup-server-external-copy-checkpoint-runbook.md), [`proxmox-external-cifs-backup-runbook.md`](docs/runbooks/proxmox-external-cifs-backup-runbook.md), [`proxmox-external-cifs-restore-proof-runbook.md`](docs/runbooks/proxmox-external-cifs-restore-proof-runbook.md) |
| Admin tools CT | [`admin-tools-substrate-runbook.md`](docs/runbooks/admin-tools-substrate-runbook.md), [`admin-tools-ct-deployment-runbook.md`](docs/runbooks/admin-tools-ct-deployment-runbook.md) |
| DNS & identity | [`dns-authority-checkpoint-runbook.md`](docs/runbooks/dns-authority-checkpoint-runbook.md), [`samba-ad-dc-deployment-runbook.md`](docs/runbooks/samba-ad-dc-deployment-runbook.md), [`samba-ad-baseline-runbook.md`](docs/runbooks/samba-ad-baseline-runbook.md), [`samba-ad-user-provisioning-runbook.md`](docs/runbooks/samba-ad-user-provisioning-runbook.md), [`samba-ad-user-logon-gpo-pilot-runbook.md`](docs/runbooks/samba-ad-user-logon-gpo-pilot-runbook.md), [`samba-ad-workstation-gpo-rdp-pilot-runbook.md`](docs/runbooks/samba-ad-workstation-gpo-rdp-pilot-runbook.md) |
| Windows endpoints | [`windows-ad-pilot-endpoint-runbook.md`](docs/runbooks/windows-ad-pilot-endpoint-runbook.md), [`windows-endpoint-update-management-pilot-runbook.md`](docs/runbooks/windows-endpoint-update-management-pilot-runbook.md), [`windows-endpoint-agent-rollout-runbook.md`](docs/runbooks/windows-endpoint-agent-rollout-runbook.md) |
| DNS filtering | [`adguard-home-deployment-runbook.md`](docs/runbooks/adguard-home-deployment-runbook.md) |
| Monitoring | [`zabbix-vm-docker-deployment-runbook.md`](docs/runbooks/zabbix-vm-docker-deployment-runbook.md), [`zabbix-postgresql-app-backup-runbook.md`](docs/runbooks/zabbix-postgresql-app-backup-runbook.md), [`zabbix-first-targets-adoption-runbook.md`](docs/runbooks/zabbix-first-targets-adoption-runbook.md), [`zabbix-readonly-summaries-runbook.md`](docs/runbooks/zabbix-readonly-summaries-runbook.md), [`zabbix-naming-normalization-runbook.md`](docs/runbooks/zabbix-naming-normalization-runbook.md), [`grafana-ct-deployment-runbook.md`](docs/runbooks/grafana-ct-deployment-runbook.md), [`grafana-main-infrastructure-dashboard-runbook.md`](docs/runbooks/grafana-main-infrastructure-dashboard-runbook.md), [`wazuh-vm-deployment-runbook.md`](docs/runbooks/wazuh-vm-deployment-runbook.md), [`basic-alerting-baseline-runbook.md`](docs/runbooks/basic-alerting-baseline-runbook.md), [`alert-presentation-language-baseline-runbook.md`](docs/runbooks/alert-presentation-language-baseline-runbook.md), [`expected-off-monitoring-policy-runbook.md`](docs/runbooks/expected-off-monitoring-policy-runbook.md), [`frigate-host-monitoring-runbook.md`](docs/runbooks/frigate-host-monitoring-runbook.md) |
| Knowledge & tickets | [`bookstack-ct-deployment-runbook.md`](docs/runbooks/bookstack-ct-deployment-runbook.md), [`glpi-vm-deployment-runbook.md`](docs/runbooks/glpi-vm-deployment-runbook.md), [`glpi-minimal-operational-baseline-runbook.md`](docs/runbooks/glpi-minimal-operational-baseline-runbook.md), [`glpi-inventory-scope-runbook.md`](docs/runbooks/glpi-inventory-scope-runbook.md), [`basic-incident-handling-runbook.md`](docs/runbooks/basic-incident-handling-runbook.md) |
| Secrets custody | [`vaultwarden-bootstrap-runbook.md`](docs/runbooks/vaultwarden-bootstrap-runbook.md), [`vaultwarden-backup-restore-proof-runbook.md`](docs/runbooks/vaultwarden-backup-restore-proof-runbook.md), [`vaultwarden-app-backup-break-glass-runbook.md`](docs/runbooks/vaultwarden-app-backup-break-glass-runbook.md) |
| PKI | [`pki-center-bootstrap-runbook.md`](docs/runbooks/pki-center-bootstrap-runbook.md), [`pki-certificate-lifecycle-planning-runbook.md`](docs/runbooks/pki-certificate-lifecycle-planning-runbook.md) |
| Network devices | [`network-device-readonly-runbook.md`](docs/runbooks/network-device-readonly-runbook.md) |
| Time sync | [`chrony-ntp-server-mutation-runbook.md`](docs/runbooks/chrony-ntp-server-mutation-runbook.md) |
| Ubuntu host ops | [`ubuntu-host-readonly-runbook.md`](docs/runbooks/ubuntu-host-readonly-runbook.md) |

## Stack ownership

```text
Tecrax profile -> RExecOp plan -> GovEngine admission -> RExecOp execution -> SCLite evidence
```

| Layer | Owns |
| --- | --- |
| SCLite | Canonical evidence, receipts and review artifacts |
| GovEngine | Governance, PolicyEngine and admission decisions |
| RExecOp | Domain-neutral lifecycle, execution and deterministic reaction mechanics |
| Tecrax | Infrastructure intent, connector, normalization, validation and runbook semantics |

Live SSH execution is performed by RExecOp only from explicit operator configuration
outside this package.

## Install

Install the coordinated published line to register the current domain profile:

```bash
pip install "tecrax==0.3.21a0"
tecrax status
```

For an explicit cross-stack pin:

```bash
pip install "rexecop[tecrax]==0.2.24a0"
```

The profile root is exposed via `tecrax:profile_root` (directory `src/tecrax/profile/`).

## Target and operation catalog

Tecrax intent files contain profile-owned operator catalog metadata. RExecOp derives
the operation list from those same intent and workflow files; there is no second
manually maintained operation registry.

Use the sanitized template in `examples/catalogs/targets.readonly.example.yaml` as
the shape for an operator-owned catalog outside Git:

```bash
rexecop targets list --catalog /path/outside/repo/targets.yaml
rexecop operations list --catalog /path/outside/repo/targets.yaml \
  --target monitoring-host-01
```

An `admission_required` result means only that target kind, capabilities and
connectors match. GovEngine still decides whether a concrete plan may execute.
See [`docs/operation-catalog.md`](docs/operation-catalog.md).

## Deterministic reactions

Tecrax owns the monitoring vocabulary and rules in
`src/tecrax/profile/reactions/reaction_pack.yaml`. Build a canonical observation
from a bounded `diagnose_monitoring_host` result, then pass it to RExecOp:

```bash
tecrax reaction-observation \
  --input diagnosis.json \
  --operation op-source \
  --target monitoring-host-01 > observation.json

rexecop reaction-plan \
  --profile tecrax \
  --env /path/outside/repo/environment.yaml \
  --observation observation.json \
  --target monitoring-host-01
```

The first reaction release is deliberately read-only. It can re-run bounded host inventory,
NTP, Docker service, Zabbix, AdGuard, Portainer, or network device inventory checks; a
healthy observation is `no_op`, and an unclassified state is `escalate`. RExecOp owns
deterministic mechanics and lifecycle, GovEngine owns admission, and SCLite owns the
evidence chain.

For operator review, Tecrax can also build a bounded untrusted escalation proposal from
the diagnosis facts. Validate it with `rexecop reaction-proposal-validate`; a valid proposal
still has `may_execute=false` and requires GovEngine admission before any future follow-up.
See [`docs/escalation-proposal-vectors.md`](docs/escalation-proposal-vectors.md).

## Trigger rules

Tecrax declares domain trigger mappings in
`src/tecrax/profile/triggers/trigger_rules.yaml`. The initial source-line rule family
handles bounded `network.host_observed` events: a known host subject maps to a dry-run
`collect_basic_host_inventory` plan through an operator-owned target catalog; an unknown
host escalates and does not execute anything. RExecOp owns event intake, dedupe,
cooldown and planning mechanics. See [`docs/trigger-rules.md`](docs/trigger-rules.md).

## Local fixture proof

```bash
tecrax fixture-review --service demo-web
```

The command emits a public-safe fixture review payload. It uses GovEngine
profile/planning/supervision/runtime-review contracts and binds its fixture
receipt through an SCLite artifact descriptor. It has no live runner, host
inventory, credential path, or infrastructure adapter.

The source `0.3.21-alpha` line combines the profile-owned read-only reaction pack,
B2 policy vector, and the first governed chrony/NTP apply slice over RExecOp
`0.2.24a0`, GovEngine `0.16.11`, and SCLite `1.0.9`. It does not add a second
policy engine, lifecycle runner, or truth layer.

The Ubuntu environment example uses profile-owned policy semantics, but GovEngine
compiles and admits the controls and RExecOp enforces them. Tecrax does not claim
that writing obligations in YAML alone satisfies them.

`configure_chrony_ntp_server` is the only active mutating intent. It is deterministic,
requires GovEngine admission, uses the `tecrax_chrony_ntp` connector backend, and is
documented in [`docs/runbooks/chrony-ntp-server-mutation-runbook.md`](docs/runbooks/chrony-ntp-server-mutation-runbook.md).

## Validation

```bash
python scripts/validate_public_truth.py
python scripts/validate_active_profile.py
python scripts/validate_secret_topology.py
python -m pytest -q
```

The validator keeps domain semantics in Tecrax and lifecycle/execution in
RExecOp. Any future mutation, credential, scheduler, discovery, or
carrier-adapter claim must be backed by code and tests before it becomes public
truth.
