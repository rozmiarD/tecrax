# Grafana main infrastructure dashboard runbook

This runbook covers the first operator-owned main infrastructure dashboard in
Grafana.

The dashboard is a consolidated operational view backed by the existing Zabbix
datasource. It intentionally marks Wazuh and GLPI as future integration/routing
sections until controlled read-only datasource access and final ticket routing
exist.

## Scope

The dashboard covers:

- top-level infrastructure overview notes;
- active Zabbix problem counters;
- current Zabbix problem table;
- ICMP reachability panels;
- Zabbix agent ping panels;
- CPU and memory trend panels where Zabbix items exist;
- public-safe Wazuh and GLPI status/routing notes.

It does not create Grafana alert rules, Wazuh datasource access, GLPI ticket
automation, private topology exports or compliance dashboards.

## Public and Private Boundary

Safe in public docs and sign-offs:

- dashboard title and UID;
- datasource class;
- panel categories;
- high-level validation summary;
- explicit non-claims.

Must remain outside Git and public sign-offs:

- Grafana credentials, API tokens and session cookies;
- Zabbix API tokens;
- private host addresses and topology exports;
- raw dashboard screenshots if they reveal private data;
- raw query responses containing sensitive host or user data.

## Dashboard Shape

Use the existing `zabbix-main` Grafana datasource.

The first dashboard should remain operational and conservative:

- show Zabbix problem state;
- show reachability and agent signals;
- show basic resource trends only where Zabbix already has matching items;
- label Wazuh/GLPI as future read-only/ticket-routing integrations, not live
  data sources.

Provisioning through files is preferred for this first baseline because it does
not require pasting Grafana credentials or API tokens into shell history.

Provision the main dashboard into the root dashboard folder for discoverability
in the standard Grafana dashboard list. A separate folder can be introduced
later after the naming/IPAM cleanup if the dashboard estate grows.

## Validation

Validate:

- Grafana service is active;
- dashboard resource exists in Grafana storage;
- dashboard title and UID match the expected values;
- dashboard is in the root folder unless the operator explicitly chooses a
  foldered layout;
- panel count is nonzero and includes text, stat, table and time-series panels;
- Zabbix datasource is still present;
- Zabbix has enabled hosts and returns problem state through the existing API
  path.

## Problems Panel Memory Failure

Recent Grafana-Zabbix plugin versions may enrich current problems with item
history from the timestamp of the oldest returned problem to the newest one.
Long-lived active problems can therefore make a visually small problems panel
issue a very large `history.get` request. A Zabbix frontend PHP memory-limit
failure then appears in Grafana as a downstream HTTP 500 even though Grafana,
Zabbix Server and the Zabbix web container remain available.

Diagnose this condition before changing memory limits:

- correlate the Grafana datasource 500 with the Zabbix web/PHP log;
- count active problems and measure the oldest-to-newest event span;
- estimate the history rows for only the item IDs referenced by those active
  problems;
- confirm that bounded `problem.get` and `trigger.get` calls still succeed;
- do not resolve real problems merely to make the dashboard query smaller.

Do not replace the operational problem list with a source-system link as a
permanent fix. That removes the dashboard function instead of correcting it.
For the regression present in Grafana-Zabbix `6.3.1` through `6.4.0`, upgrade
to an official signed release containing the bounded historical-value fix
(`6.4.1` or a later independently validated release).

Before the upgrade:

- take an exact backup of the provisioned dashboard, plugin directory and
  Grafana configuration;
- record the plugin version, dashboard hash, UID, version and exact problem
  panel ID/type;
- define a rollback to the previous plugin plus dashboard;
- inspect Grafana's preinstall and background-plugin policy so a Grafana
  restart cannot silently widen the upgrade scope.

After the upgrade, keep `Item value at problem time`
(`fetchHistoricalItemValue`) explicitly disabled unless historical macro
accuracy is a documented requirement. Restore the functional Problems panel,
then prove that the dashboard differs only by the intended panel safety option
and version metadata. Validate signed-plugin registration, Grafana health,
successful Zabbix datasource queries, the rendered problem list and absence of
new Zabbix frontend memory failures.

Raising the PHP memory limit alone is not closure: it may hide the error while
leaving a large history transfer on every dashboard refresh. A text link to
Zabbix may be used only as a short emergency degradation with a named owner,
expiry and open corrective gate.

This failure is also an observability gap when monitoring checks only process
and container availability. Add a low-noise synthetic dashboard or datasource
check in a separate approved gate before routing it to a ticketing system.

## Read-only API identity

Use a dedicated Grafana service account when an operator tool needs to inspect
dashboard inventory or datasource health. Do not reuse an interactive
administrator session, browser cookie or anonymous access.

The bounded bootstrap must:

- create one uniquely named service account with the organization role
  `Viewer`;
- create one expiring token for one declared runtime consumer;
- keep the administrator credential and generated token outside argv, logs,
  Git and public evidence;
- place the token only in the approved runtime secret store with mode `0600`;
- verify the server certificate through the approved trust path or an exact
  pre-recorded fingerprint while certificate rollout is incomplete;
- compare dashboard identity before and after the change;
- prove read access to dashboard search and the exact datasource health
  endpoint;
- prove that an administrator-only endpoint remains denied;
- record token ownership and expiry without recording its value.

Fail closed if the account name or destination secret already exists. If token
creation or validation fails, delete only the token and service account created
by the current run, using their exact IDs. Do not change dashboards,
datasources, plugins or alert rules as part of this operation.

Token rotation is a separate bounded change. Create and validate the replacement
before revoking the previous token, then update the runtime consumer atomically.

## Stop Conditions

Stop before sign-off if any of these are true:

- provisioning errors appear in Grafana logs;
- the dashboard requires storing Grafana or Zabbix credentials in Git;
- dashboard JSON embeds private topology that should remain outside the repo;
- existing dashboards or datasources would be overwritten unexpectedly;
- Grafana does not come back active after restart.

## Sign-Off Shape

Use `docs/operator-signoff-template.md` and include:

- date;
- service alias;
- run class: `grafana-main-infrastructure-dashboard`;
- datasource class;
- dashboard title and UID;
- panel-category summary;
- validation result summary;
- explicit non-claims.

Non-claims:

- no Grafana alert rules;
- no final GLPI ticket routing;
- no Wazuh datasource yet;
- no compliance dashboard;
- no private topology export.

## Next Gate

After the main dashboard is stable, continue with final GLPI ticket routing for
Zabbix/Wazuh alerts or the Wazuh endpoint rollout plan.
