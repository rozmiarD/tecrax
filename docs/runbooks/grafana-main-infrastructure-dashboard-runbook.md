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

## Validation

Validate:

- Grafana service is active;
- dashboard resource exists in Grafana storage;
- dashboard title and UID match the expected values;
- panel count is nonzero and includes text, stat, table and time-series panels;
- Zabbix datasource is still present;
- Zabbix has enabled hosts and returns problem state through the existing API
  path.

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
