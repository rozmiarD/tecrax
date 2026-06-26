# Tecrax domain contracts

Tecrax facts use static `FactsContractSpec` definitions in `tecrax.contracts`. They are
small profile-owned payload contracts inside SCLite canonical observation envelopes; they
are not a schema service, registry daemon, storage layer, DSL, or replacement for SCLite.

Every active intent declares profile-owned `facts_contract`. A result separates:

- `contract`: stable id and version;
- `scope`: requested, observed and deliberately not observed fields;
- `coverage`: complete, partial or blocked plus bounded blockers;
- `assessment`: healthy, degraded, unhealthy or unknown;
- `non_claims`: facts the operation explicitly does not establish.

Malformed facts, raw connector output and payloads above 16 KiB are rejected before Tecrax
builds a SCLite observation. A negative health assessment remains a valid observation.

## Reference contract: basic host inventory v1

`collect_basic_host_inventory` is the first T1 reference slice:

- intent declaration: `facts_contract: tecrax.basic_host_inventory@1.0`;
- domain capability: `tecrax.host.basic_inventory.v1`;
- static schema artifact: `src/tecrax/schemas/basic_host_inventory.v1.schema.json`;
- typed model/builder: `BasicHostInventoryV1` and `build_basic_host_inventory_v1`;
- pure validator: `validate_basic_host_inventory_v1`.

The contract covers only bounded read-only facts: target label, OS release fields, kernel,
hostname, uptime string, load averages, root filesystem summary from `df -P /`, and memory
summary from `free -m`. It explicitly does not claim package inventory, users, processes or
network listeners.

Compatibility policy: additive optional fields may stay within `1.x`; removing fields,
changing meaning or changing required keys requires a new major contract version and golden
N-1 vectors. RExecOp executes the workflow, GovEngine governs it, and SCLite owns the
canonical envelope and evidence lifecycle.

## Local SSH/systemd facts v1

The next T1 slice extends the same pattern to local read-only host observations that do not
depend on authenticated HTTP APIs:

- `tecrax.ntp_local_health@1.0`:
  `schemas/ntp_local_health.v1.schema.json`,
  `NtpLocalHealthV1`, `build_ntp_local_health_v1`,
  `validate_ntp_local_health_v1`;
- `tecrax.docker_service_health@1.0`:
  `schemas/docker_service_health.v1.schema.json`,
  `DockerServiceHealthV1`, `build_docker_service_health_v1`,
  `validate_docker_service_health_v1`;
- `tecrax.host_security_posture@1.0`:
  `schemas/host_security_posture.v1.schema.json`,
  `HostSecurityPostureV1`, `build_host_security_posture_v1`,
  `validate_host_security_posture_v1`;
- `tecrax.ntp_server_observation@1.0`:
  `schemas/ntp_server_observation.v1.schema.json`,
  `NtpServerObservationV1`, `build_ntp_server_observation_v1`,
  `validate_ntp_server_observation_v1`.

These contracts intentionally stay small. Docker remains a systemd service/socket
observation and does not claim container runtime health, Docker socket access, `inspect`,
logs or `exec`. NTP server observation keeps bounded daemon/system variables and does not
persist peer identities, peer addresses or raw command output. Host security posture remains
a minimal signal set, not a CIS scanner or package/user/process inventory. Its available
updates observation is a bounded count summary only: regular updates, security updates,
unknown parse state and an explicit `held_back_or_blocked` non-measurement. Package names,
repositories, changelogs and local package paths are not part of the facts contract.

## Network device facts v1

The network slice versions the existing bounded legacy CLI observations without expanding
device access:

- `tecrax.network_device_inventory@1.0`:
  `schemas/network_device_inventory.v1.schema.json`,
  `NetworkDeviceInventoryV1`, `build_network_device_inventory_v1`,
  `validate_network_device_inventory_v1`;
- `tecrax.network_management_posture@1.0`:
  `schemas/network_management_posture.v1.schema.json`,
  `NetworkManagementPostureV1`, `build_network_management_posture_v1`,
  `validate_network_management_posture_v1`.

The inventory contract covers only sanitized target label, bounded device identity,
management SSH access posture and hardening observations derived from fixed wrapper actions.
It does not claim running configuration, VLANs, port state, port security, SNMP telemetry or
firmware compliance. The posture contract consumes the inventory fact and emits bounded
findings such as legacy SSH v1, observed legacy SSH crypto, disabled SSH server, disabled
SSH v2, unknown idle timeout and unknown max-client bound.

HTTP reachability facts for Zabbix, AdGuard and Portainer keep their current narrow shape.
The HTTP action identity checkpoint in `docs/http-action-identity-checkpoint.md` defines
the activation gate for any future HTTP expansion without moving domain semantics into
RExecOp.

Authenticated Zabbix T4 summaries are separate facts contracts:

- `tecrax.zabbix_problem_summary@1.0` contains only open problem counts by severity.
- `tecrax.zabbix_host_availability_summary@1.0` contains only enabled/disabled host
  counts and Zabbix agent availability counts.

They do not contain host names, problem names, trigger names, event payloads, interface
addresses, templates, inventory fields or Zabbix configuration.

`tecrax.monitoring_host_diagnosis@1.0` aggregates implemented bounded observations into a
single diagnosis fact with `aggregation_completed`, `coverage_status`, `observed_health`,
component states and bounded `findings`. Findings carry stable `kind`, `component`,
`reason_code` and `severity` fields from the Tecrax finding taxonomy. They are deterministic
diagnostic summaries, not remediation instructions, policy decisions or SCLite canonical
truth.

`build_monitoring_host_escalation_proposal()` can project those diagnosis facts into a
bounded SCLite `escalation_proposal.v0.1` advisory artifact. The proposal is untrusted,
contains no connector payload or command, rejects unsafe evidence refs and secret-like
explanations, and cannot grant execution. RExecOp validates the generic proposal shape;
GovEngine owns any later admission decision.
