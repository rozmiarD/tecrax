# Ubuntu host read-only inventory

This runbook covers `collect_basic_host_inventory`, discovered-host `check_ntp_health`,
bounded `check_zabbix_container_health`, and `diagnose_monitoring_host`. Host inventory
includes bounded uptime, load average, root filesystem usage and memory summary. NTP uses
`ssh_readonly`; Zabbix uses its unauthenticated `apiinfo.version` endpoint through `http_api`.

## Operator prerequisites

- dedicated target account without sudo or Docker/admin groups;
- SSH private key outside the repository;
- target fingerprint verified through an independent channel;
- operator-managed `known_hosts` outside the repository with strict checking;
- `REXECOP_SECRETS_FILE` outside the repository and mode `0600`;
- environment copy outside the repository with the real host address;
- explicit operator approval before the real SSH run.

Do not use `accept-new`. Do not add sudo, service management, Docker commands,
configuration changes, arbitrary `cat`, arbitrary command arguments, process listings,
or log collection.

`check_zabbix_container_health` proves application endpoint reachability. It does not
claim Docker container state because the read-only SSH account must not receive Docker
socket access. `check_docker_services_health`, AdGuard health and the aggregate diagnosis
remain blocked until a bounded read-only adapter or verified endpoint exists.

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
