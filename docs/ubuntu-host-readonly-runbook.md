# Ubuntu host read-only inventory

This runbook covers `collect_basic_host_inventory`, discovered-host `check_ntp_health`,
bounded `check_docker_services_health`, bounded `check_zabbix_container_health`, bounded
`check_adguard_health`, and `diagnose_monitoring_host`. Host inventory includes bounded
uptime, load average, root filesystem usage and memory summary. NTP and Docker service
checks use `ssh_readonly`; Zabbix uses its unauthenticated `apiinfo.version` endpoint
through `http_api`; AdGuard uses fixed `dig` and `curl` probes through
`local_shell_readonly`.
`check_portainer_health` uses only the unauthenticated status endpoint through a verified
TLS tunnel; it does not list Portainer-managed objects.

## Operator prerequisites

- dedicated target account without sudo or Docker/admin groups;
- SSH private key outside the repository;
- target fingerprint verified through an independent channel;
- operator-managed `known_hosts` outside the repository with strict checking;
- `REXECOP_SECRETS_FILE` outside the repository and mode `0600`;
- environment copy outside the repository with the real host address;
- explicit operator approval before the real SSH run.
- a local SSH tunnel to the Portainer HTTPS listener, with `ExitOnForwardFailure=yes`;
- the Portainer self-signed certificate stored outside git and referenced through
  `portainer_ca_file` in `REXECOP_SECRETS_FILE`.

Do not use `accept-new`. Do not add sudo, Docker CLI commands,
configuration changes, arbitrary `cat`, arbitrary command arguments, process listings,
logs, service restart/reload/start/stop, or log collection.

`check_zabbix_container_health` proves application endpoint reachability. It does not
claim Docker container state because the read-only SSH account must not receive Docker
socket access. `check_docker_services_health` proves only Docker systemd service/socket
state and returns `container_runtime_state: not_observed`. `check_adguard_health` proves
DNS resolution and web-login reachability only; it does not use or claim management API
state.

The Portainer certificate is valid for `localhost`, not the target host address. Establish
the operator-owned tunnel before running the Portainer intent. Keep the real target, local
port, key path and CA path outside git:

```bash
ssh -N -o BatchMode=yes -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile=/path/outside/repo/known_hosts \
  -o ExitOnForwardFailure=yes -i /path/outside/repo/identity \
  -L 127.0.0.1:LOCAL_PORT:127.0.0.1:9443 \
  readonly-user@monitoring-host.example.invalid
```

Configure `portainer_base_url` as `https://localhost:LOCAL_PORT`. Do not use `-k`,
`verify=false`, direct HTTP, a Portainer token, or an authenticated management endpoint.

## Run

Copy `examples/environments/ubuntu-host.readonly.example.yaml` outside the repository,
replace only the target host and operator-owned paths, then run from an isolated runtime
directory:

```bash
export REXECOP_SECRETS_FILE=/path/outside/repo/secrets.yaml
rexecop plan --profile tecrax --env environment.yaml \
  --intent collect_basic_host_inventory --target monitoring-host-01 --mode dry_run
rexecop start --operation OPERATION_ID
rexecop validate --operation OPERATION_ID
rexecop status --operation OPERATION_ID
rexecop history --operation OPERATION_ID
```

The `produce_receipt` workflow step emits the SCLite bundle during `start`.

The environment allowlist must exactly match the profile command shapes. Any changed
command, argument, backend, unknown action, mutating action, or unmatched policy rule
must fail closed before connector execution.

`collect_host_security_posture_readonly` observes only a small hostlike security posture:
unattended-upgrades service state, a bounded available-update count summary from
`/usr/lib/update-notifier/apt-check`, ASLR mode, `dmesg_restrict` and the pending reboot
marker. The update summary must not persist package names, repository names, changelogs,
held package identities or local paths. If the update summary cannot be parsed, Tecrax marks
that part as unknown instead of inventing package state.

For `collect_basic_host_inventory`, the sanitized example also requires a receipt,
per-step output digests, at most nine workflow steps, a ten-second per-connector-call
timeout, and an 8192-byte persisted output bound. GovEngine owns projection and digest
binding of these controls. RExecOp validates that binding at start and enforces it;
SCLite owns the resulting canonical execution contract and receipt artifacts.
