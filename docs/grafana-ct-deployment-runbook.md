# Grafana CT deployment runbook

This runbook covers the operator-owned Grafana deployment gate for the Proxmox
stack.

Grafana is the visualization layer. It reads directly from selected sources
instead of treating Zabbix as a universal broker for every future signal.

## Scope

The deployment pass covers:

- creating a lightweight Linux CT for Grafana;
- installing Grafana from the vendor package repository;
- installing and enabling the Grafana Zabbix app plugin;
- creating a Zabbix datasource with a token stored outside Git;
- importing initial Zabbix dashboards;
- adding the Grafana CT to the Linux host monitoring baseline;
- adding local PBS and external backup coverage;
- recording public-safe sign-off evidence.

It does not deploy Wazuh, configure final alert routing, expose credentials,
claim HTTPS/TLS hardening, or make Grafana the source of truth for monitoring
configuration.

## Public and Private Boundary

Safe in public docs and sign-offs:

- service role and target alias;
- CT class and high-level resource shape;
- Grafana and plugin versions;
- datasource class and health summary;
- dashboard class;
- backup coverage class;
- monitoring health summary;
- explicit non-claims.

Must remain outside Git and public sign-offs:

- Grafana admin password;
- Zabbix API token;
- SSH keys, known-hosts, fingerprints and local secret paths;
- full private address plan;
- raw dashboard exports if they contain private topology;
- full API responses containing secrets or private endpoint details.

## Prerequisites

- Proxmox host readiness gate is complete.
- Local NTP service is available.
- Zabbix deployment and API-token custody are complete.
- Zabbix agent onboarding package exists for new Linux hosts.
- PBS local backup and external backup storage are available.
- The operator has approved creation of the Grafana service CT.

## Datasource Model

Grafana should read from the most appropriate source directly:

- Zabbix for infrastructure metrics, Linux hosts, VM/CT checks, ICMP, SNMP and
  network-device metrics;
- Wazuh for security events, security agents, alerts and security logs once
  Wazuh exists;
- AdGuard, Proxmox or PBS directly only if their API or exporter is a cleaner
  source than routing the data through Zabbix.

This keeps Zabbix focused on monitoring and avoids turning it into a generic
metrics relay.

## Procedure

### 1. Create CT

Create a dedicated Grafana CT on the data-service storage class with modest
initial resources. Use the standard operatorship convention for local access
and keep credentials outside Git.

Configure:

- stable service address from the private IPAM plan;
- DNS resolver consistent with the DNS authority model;
- local NTP synchronization through the infrastructure NTP server;
- `rexecop` operator access if an account is needed.

### 2. Install Grafana

Install Grafana from the vendor package repository. Enable and start the
`grafana-server` service.

Install the Zabbix app plugin and restart Grafana if required.

### 3. Secure bootstrap credentials

Generate or set the Grafana admin credential through an operator-owned secret
path outside Git. Reset the admin password against the active Grafana data path,
not against a default CLI-only path.

The operator should rotate or replace the bootstrap credential after first
interactive login.

### 4. Configure Zabbix datasource

Enable the Zabbix app plugin and create a `Zabbix Main` datasource using a
Zabbix API token stored outside Git.

Validate datasource health through the Grafana API. A successful health check
should confirm the Zabbix API version without printing the token.

### 5. Import initial dashboards

Import only starter dashboards that do not embed secrets. If a dashboard export
contains private topology, keep the export outside Git and summarize it in the
sign-off instead.

### 6. Add monitoring for Grafana CT

Apply the Linux host onboarding package:

- local time synchronization;
- `zabbix-agent2` active checks;
- host entry in the infrastructure group;
- `Linux by Zabbix agent active`;
- `ICMP Ping`;
- validation of `agent.ping` and ICMP.

### 7. Add backup coverage

Add a local PBS backup job for the Grafana CT. Include the CT in the external
backup job for base services if it is part of the base monitoring stack.

Run a first manual PBS backup before signing off the deployment.

## Validation

Validate:

- CT is running after service deployment;
- Grafana service is active;
- Grafana login/API works with operator-owned credentials;
- Zabbix plugin is installed and enabled;
- Zabbix datasource health is `OK`;
- initial dashboards are present;
- Grafana web UI returns a login page;
- `zabbix-agent2` is active on the CT;
- Zabbix has fresh `agent.ping=1` and `icmpping=1`;
- local PBS backup job exists;
- external backup job covers the Grafana CT where approved;
- first manual PBS backup completed successfully.

## Stop Conditions

Stop before sign-off if any of these are true:

- Grafana admin credential or Zabbix token would be exposed in Git, chat or raw
  logs;
- datasource health fails;
- Grafana service is not active after install;
- the CT cannot synchronize time;
- the CT cannot be monitored by Zabbix;
- backup coverage cannot be created or the first backup fails;
- dashboard imports require storing private topology in the public repo.

## Sign-Off Shape

Use `docs/operator-signoff-template.md` and include:

- date;
- run class: `grafana-ct-deployment`;
- service alias and deployment class;
- Grafana and plugin versions;
- datasource health summary;
- dashboard summary;
- monitoring validation summary;
- backup coverage summary;
- explicit non-claims.

Non-claims:

- no Wazuh datasource yet;
- no final alert routing;
- no HTTPS/TLS hardening claim;
- no SSO claim;
- no full dashboard design completion;
- no disaster-recovery one-command restore claim.

## Next Gate

Deploy Wazuh and then add Wazuh as a direct Grafana datasource. After Grafana
and Wazuh are both stable, configure basic alerting before the stack security
audit and light hardening pass.
