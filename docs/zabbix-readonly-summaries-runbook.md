# Zabbix Read-only Summaries Runbook

Tecrax can use Zabbix as an existing monitoring source for bounded evidence. It
does not replace Zabbix polling, alerting, escalation, host discovery or
configuration.

## Prerequisites

- A Zabbix API endpoint is reachable from the operator host.
- A constrained read-only Zabbix API token is stored outside git.
- The operator environment uses `zabbix_api_authenticated` with:
  - `auth.secret_ref: zabbix_api_token`
  - an `Authorization` bearer header resolved from the external secret reference
- `REXECOP_SECRETS_FILE` points at the operator-owned secrets file with mode
  `0600`.

## Operations

`collect_zabbix_problem_summary_readonly` collects only open problem counts by
severity:

- not classified;
- information;
- warning;
- average;
- high;
- disaster.

It does not collect problem names, event payloads, trigger names, host names or
root-cause analysis.

`collect_zabbix_host_availability_summary_readonly` collects only counts:

- enabled and disabled host counts;
- Zabbix agent availability counts: unknown, available, unavailable.

It does not collect host names, interface addresses, templates, inventory fields
or configuration.

## Operator Commands

Run from an operator runtime directory, not from a repository:

```bash
export REXECOP_SECRETS_FILE=/path/outside/repo/secrets.yaml

OPERATION_ID=$(rexecop plan \
  --profile tecrax \
  --env /path/outside/repo/environment.yaml \
  --intent collect_zabbix_problem_summary_readonly \
  --target monitoring-host-01 \
  --mode dry_run)

rexecop start --operation "$OPERATION_ID"
rexecop validate --operation "$OPERATION_ID"
```

Use the same flow for `collect_zabbix_host_availability_summary_readonly`.

## Acceptance

- Each operation completes with a receipt and SCLite bundle or fails closed.
- Evidence contains bounded count summaries only.
- Evidence does not contain Zabbix API token values.
- Evidence does not contain host names, interface addresses, problem names,
  trigger names or configuration payloads.
