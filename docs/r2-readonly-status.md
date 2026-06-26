# R2 read-only status

R2 extends manual, evidence-producing diagnostics. It does not add polling, alerts,
scheduling, or a second monitoring system.

## Implemented and verified

- `check_ntp_health`: fixed `timedatectl show` properties plus `systemctl is-active ntp`
  over `ssh_readonly`; validates synchronization and the discovered daemon state.
- `check_docker_services_health`: fixed `systemctl show` properties for `docker` and
  `docker.socket` over `ssh_readonly`; validates Docker systemd service health without
  Docker socket access or container inspection.
- `check_zabbix_container_health`: bounded JSON-RPC `apiinfo.version` through `http_api`;
  validates application reachability and reports `container_runtime_state: not_observed`.
- `check_adguard_health`: bounded DNS resolution and web-login reachability through
  `local_shell_readonly`; validates observable service health without management API
  credentials and reports `management_api_state: not_observed`.
- `check_portainer_health`: bounded, unauthenticated `GET /api/status` through `http_api`;
  stores only the version field, deliberately excludes `InstanceID`, and uses verified TLS
  through an operator-managed SSH tunnel and CA file.

These workflows use plain PolicyEngine `allow`, bounded evidence, deterministic validation,
receipt generation and an SCLite bundle.

`diagnose_monitoring_host` aggregates host inventory, NTP, Docker service state, Zabbix,
AdGuard and Portainer. Connector failures are retained as bounded step IDs plus error
classes while later diagnostics continue. Its validation means the diagnostic completed;
component health remains a separate field. The aggregate now uses the versioned
`tecrax.monitoring_host_diagnosis@1.0` contract with bounded finding reason codes.

## Explicit blockers

- Container-level Docker inventory remains blocked. The dedicated SSH account must not
  access the Docker socket. Membership in the `docker` group would grant mutation capability
  and must not be used as a read-only solution.
- Authenticated Portainer API discovery remains blocked. No token is accepted as a read-only
  boundary until the installation can provide a genuinely non-mutating role or a separately
  constrained API. Container, endpoint, stack and user inventory are not collected.
- AdGuard management API remains blocked without a read-only credential/role. The current
  health check intentionally uses only DNS resolution and web-login reachability.
- T5 keeps these blockers active. See `docs/service-boundary-decision-t5.md`.
- Future HTTP expansion must satisfy the action identity checkpoint in
  `docs/http-action-identity-checkpoint.md`; runtime environments must not redefine
  Tecrax-owned method/path/body/query/projection semantics.

No Docker inspect, `ps`, logs, exec, lifecycle command, configuration change, service restart,
or NTP modification is part of R2.
