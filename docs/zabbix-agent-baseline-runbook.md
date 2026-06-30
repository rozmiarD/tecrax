# Zabbix agent baseline runbook

This runbook covers the first Zabbix agent baseline for Linux hosts in the
Proxmox deployment.

It extends the earlier ICMP-only monitoring baseline with host-level metrics
using `zabbix-agent2` and the active-agent template. It does not configure
alert routing, Grafana dashboards, Wazuh agents or full service monitoring.

## Scope

The baseline covers:

- installing `zabbix-agent2` on selected Linux hosts;
- configuring active checks toward the Zabbix server;
- matching agent hostnames to existing Zabbix host aliases;
- linking `Linux by Zabbix agent active` while preserving existing templates;
- validating `agent.ping` for each adopted host;
- adding Zabbix agent setup to the mandatory new-host onboarding package.

It does not open broad inbound firewall access, install Windows agents, configure
SNMP, add alert channels or store Zabbix API tokens in Tecrax.

## Public and Private Boundary

Safe in public docs and sign-offs:

- host aliases and service roles;
- package name and major/minor product line;
- active-agent model;
- template names;
- validation summary;
- explicit non-claims.

Must remain outside Git and public sign-offs:

- Zabbix API tokens;
- exact secret paths;
- private endpoint addresses unless separately approved;
- raw API payloads containing topology or credentials;
- shell history containing tokens or passwords.

## Baseline Model

Use `zabbix-agent2` with active checks for the first host metrics pass.

Reasons:

- agents initiate telemetry toward Zabbix;
- the first pass does not require opening inbound agent ports on every host;
- host identity is controlled by explicit `Hostname` values matching Zabbix;
- the model works consistently for Proxmox host, VMs and CTs.

Recommended first template:

- `Linux by Zabbix agent active`

Preserve existing templates such as `ICMP Ping` and service-specific health
templates.

## Mandatory New-Host Onboarding Package

Every new Linux host should get this baseline package before being treated as a
normal managed workload:

- time synchronization configured and verified;
- DNS resolver/search baseline configured and verified;
- backup eligibility decision recorded;
- monitoring agent installed and registered;
- host alias added to the monitoring inventory;
- public-safe sign-off or private operator note created, depending on sensitivity.

This package is an operator workflow. It is not yet an active Tecrax mutation
intent.

## Procedure

### 1. Confirm inventory

Confirm the target hosts already exist in Zabbix and have stable aliases. Avoid
creating duplicate hosts when an ICMP-only baseline already exists.

### 2. Install agent

Install `zabbix-agent2` from the operating-system package repository or another
operator-approved source.

Enable and start the service.

### 3. Configure active checks

Set:

- `ServerActive` to the Zabbix server endpoint;
- `Hostname` to the exact Zabbix host alias;
- `Server` conservatively, even if passive checks are not the first model.

Restart the agent after changes.

### 4. Link templates

Using the Zabbix API or UI, add `Linux by Zabbix agent active` to each selected
host while preserving existing templates.

Do not remove `ICMP Ping` during this gate.

### 5. Validate

Validate:

- package is installed;
- service is enabled and active;
- template is linked;
- `agent.ping` last value is `1`;
- item state is normal;
- no new active problems were introduced by the agent baseline.

Unsupported optional items from unrelated service-health templates should be
tracked separately and not confused with agent baseline failure.

## Stop Conditions

Stop before sign-off if any of these are true:

- agent hostname does not match the Zabbix host alias;
- Zabbix API token would be exposed to Git, shell output or chat;
- template linking would remove existing templates unintentionally;
- the host cannot reach the Zabbix active-check endpoint;
- `agent.ping` does not become healthy after a reasonable wait;
- agent installation requires changing unrelated security policy.

## Sign-Off Shape

Use `docs/operator-signoff-template.md` and include:

- date;
- run class: `zabbix-agent-baseline`;
- selected host aliases;
- package and template class;
- validation summary;
- onboarding package update;
- explicit non-claims.

Non-claims:

- no alert routing;
- no Grafana dashboard;
- no Wazuh agent coverage;
- no Windows agent coverage;
- no SNMP coverage;
- no full application monitoring.

## Next Gate

After agent metrics are stable, continue with richer data sources and
visualization: Grafana, Wazuh and then basic alert routing before the security
audit / hardening stage.
