# Service API boundaries

The HTTP action ownership and activation rules are recorded in
`docs/http-action-identity-checkpoint.md`. RExecOp owns generic shape validation and digest
binding; Tecrax owns domain action declarations, facts contracts, non-claims and validation.

## Zabbix: bounded summaries

The active `check_zabbix_container_health` id is compatibility-bound but proves only the
unauthenticated `apiinfo.version` path.

Authenticated T4 operations are separate and use `zabbix_api_authenticated`. They collect
bounded counts only:

- `collect_zabbix_problem_summary_readonly`;
- `collect_zabbix_host_availability_summary_readonly`.

Host names, raw problems, trigger names, event payloads, history, macros, interface
addresses and configuration must not enter evidence by default. The operator-owned token
must remain outside git and should be constrained to read-only API access.

## AdGuard: current boundary

The current operation proves only DNS resolution and login-page reachability. Management API,
configuration, clients and filter lists remain deliberately not observed. No read-only
management slice is active because a technical read-only boundary has not been verified.
The T5 decision record keeps AdGuard management expansion blocked.

## Portainer: current boundary

The current operation uses only unauthenticated `/api/status` through verified TLS and drops
instance identity. Environments, stacks, containers, users, tokens and configuration remain
not observed. Portainer is not treated as a safe substitute for Docker socket access.
Authenticated Portainer expansion remains blocked until a non-mutating role or constrained
projection adapter is proven.

## Docker: current boundary

Tecrax observes only `docker.service` and `docker.socket` systemd state. It does not use the
Docker socket, `docker exec`, inspect, logs, compose, restart or configuration mutation.
Container-level Docker summaries remain blocked because Docker socket access is not a
read-only boundary for the operator account.

See `docs/service-boundary-decision-t5.md` for the explicit T5 decision.
