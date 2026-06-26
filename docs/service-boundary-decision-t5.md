# T5 Service Boundary Decision

This record closes the T5 AdGuard, Portainer and Docker boundary checkpoint.

## Decision

Keep the current active profile narrow:

- Docker stays `systemd` service/socket state only.
- AdGuard stays DNS resolution plus web-login reachability only.
- Portainer stays unauthenticated `/api/status` only.

Do not add container inventory, Docker socket access, Portainer object discovery
or AdGuard management API reads in this checkpoint.

## Rationale

Docker socket access is not read-only for the operator account. Docker group
membership would effectively grant mutation capability and must not be used as a
shortcut for observation.

Portainer can expose Docker-managed objects, stacks, endpoints, users, tokens and
configuration. The current `/api/status` check is useful because it is
unauthenticated, bounded, and drops instance identity. Authenticated Portainer
expansion needs a proven non-mutating role or a constrained projection adapter.

AdGuard management API reads can expose configuration, clients, filters and
runtime DNS details. The current check proves DNS resolution and login-page
reachability without management credentials.

## Active Operations

- `check_docker_services_health`
- `check_adguard_health`
- `check_portainer_health`

These operations are health/reachability checks, not inventory or management
APIs.

## Blocked Expansion

The following remain blocked until a separate design checkpoint proves a bounded
technical boundary:

- `collect_docker_runtime_summary_readonly`
- `collect_portainer_runtime_summary_readonly`
- `collect_adguard_runtime_summary_readonly`

Any future activation must provide:

- immutable profile-owned HTTP or command action shapes;
- a least-privilege role or constrained projection adapter;
- count-only or otherwise bounded facts;
- negative permission tests;
- secret canaries and artifact scans;
- operator sign-off without private topology or token values.

## Non-claims

Tecrax does not claim container health, image inventory, stack state, compose
configuration, Docker network state, AdGuard filter effectiveness, AdGuard client
inventory, Portainer endpoint inventory or Portainer user/token state.

RExecOp core remains domain-neutral and must not gain Docker, AdGuard or
Portainer semantics.
