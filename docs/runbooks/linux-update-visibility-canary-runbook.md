# Linux Update Visibility Canary Runbook

This runbook covers a bounded, read-only Linux update and reboot visibility
canary through Zabbix. It does not refresh APT metadata, install packages,
restart a service other than the monitoring agent during deployment, reboot a
host or create a GLPI ticket.

## Scope

The collector exposes only:

- pending package count from a simulated upgrade;
- pending security package count derived from the simulated APT origin;
- age of the newest local APT list file;
- presence of `/var/run/reboot-required`;
- collector completeness and a fixed schema/source identifier.

Package names, repositories, changelogs, command output and local paths are not
sent to Zabbix. The values describe the existing local APT cache. They do not
claim that package metadata was refreshed recently.

## Preconditions

- exact host identity and monitoring ownership are confirmed;
- Zabbix Agent 2 is active and its include directory is known;
- the target is assigned to the `pilot` update ring in private inventory;
- the Zabbix host resolves to exactly one enabled monitored object;
- no existing item uses the `tecrax.update.*` key namespace;
- rollback paths for the collector, UserParameter and created item IDs are
  recorded before widening the canary.

## Collector

Install `scripts/collect-linux-update-status.py` as a root-owned executable,
for example `/usr/local/libexec/tecrax-update-status`, and expose one master
UserParameter:

```text
UserParameter=tecrax.update.status,/usr/local/libexec/tecrax-update-status
```

The master value is compact JSON. Zabbix dependent items should extract:

```text
$.pending_total
$.pending_security
$.cache_age_seconds
$.pending_reboot
$.collector_complete
```

The first canary creates no triggers. Trigger thresholds and GLPI routing are a
separate gate after the values, cadence, cache freshness and noise are proven.

## Validation

1. Execute the collector as the `zabbix` user and validate JSON syntax.
2. Run the Agent 2 item test for `tecrax.update.status`.
3. Validate Agent 2 configuration and restart only that agent.
4. Confirm the agent is active and the master item receives a supported value.
5. Confirm all dependent items receive numeric values and no trigger exists for
   the canary namespace.
6. Confirm no GLPI ticket was created by this gate.

## Stop Conditions

Stop and roll back if:

- the live hostname differs from the approved target;
- the collector would refresh APT metadata or acquire a package-management
  write lock;
- the simulation proposes removals or emits package details to Zabbix;
- Agent 2 validation fails or the service does not return active;
- the Zabbix host lookup has zero or multiple matches;
- an existing item or trigger already owns the canary key namespace;
- the live GLPI route would be widened during this gate.

## Rollback

- remove only the canary UserParameter file and collector;
- restore the immediate Agent 2 configuration backup if one was changed;
- restart Agent 2 and confirm its previous active state;
- delete only the exact Zabbix item IDs created by this canary;
- do not modify APT state, packages, update timers or unrelated monitoring.

## Promotion Gate

Promotion beyond one host requires representative values, explicit cache-age
thresholds, approved `pilot` and `staff` membership, conservative trigger
severity, GLPI dry-run and deduplication proof. Installation and reboot remain
manual and outside this visibility gate.

The first trigger canary may use only data-quality conditions:

- collector completeness remains zero for two samples within two hours;
- local APT metadata cache age exceeds seven days while the collector reports
  a complete result.

Keep both warning-class and shadow-only for GLPI until a natural event is
observed. Do not create security-update or reboot triggers while cache
freshness, persistence windows and operator action semantics remain unresolved.
Do not force an active-agent sample by changing item type, injecting a value or
temporarily changing cadence merely to make a new trigger evaluate.

## Metadata Refresh Policy

The collector remains read-only and must never refresh APT itself. If the cache
age trigger proves that the host has no effective refresh policy, configure
metadata refresh as a separate, explicitly approved host operation:

- enable periodic package-list refresh;
- keep automatic package download, installation and reboot disabled;
- capture the existing APT policy before the change;
- run one bounded metadata refresh;
- prove that the installed package database did not change;
- validate the collector directly and wait for the next natural active-agent
  sample at the existing cadence.

Do not inject history, convert the item to a passive check or shorten its
cadence merely to clear the warning immediately.
