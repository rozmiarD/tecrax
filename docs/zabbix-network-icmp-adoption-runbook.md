# Zabbix network ICMP adoption runbook

This runbook covers the first network-device availability adoption gate for the
Zabbix baseline.

It adds selected network devices as ICMP-only targets before SNMP, SSH-based
inventory, alert routing, Grafana dashboards or security hardening.

## Scope

The adoption pass covers:

- creating or reusing a dedicated network host group;
- adding the security gateway and selected managed switches;
- linking only the `ICMP Ping` template;
- validating first ICMP values;
- recording public-safe sign-off evidence.

It does not configure SNMP, SSH access, switch inventory collection, gateway
policy, DHCP, alert routing or dashboard panels.

## Public and Private Boundary

Safe in public docs and sign-offs:

- device aliases and roles;
- monitoring class: ICMP availability;
- host group name if non-sensitive;
- validation summary;
- explicit non-claims.

Must remain outside Git and public sign-offs:

- management addresses and complete VLAN addressing;
- SSH credentials, keys, host fingerprints and legacy cipher details;
- SNMP communities, users and authentication material;
- raw device configuration;
- full network topology.

## Prerequisites

- Zabbix VM deployment gate is complete.
- Zabbix API token is available from an operator-owned secret path outside Git.
- The selected devices respond to ICMP from the monitoring path.
- Device aliases are known and stable enough for first-pass monitoring.

## Procedure

### 1. Confirm target list

Select a narrow first-pass list:

- security gateway primary availability;
- security gateway service/VLAN availability where useful;
- core or managed switches with known operator ownership.

Do not bulk-import every endpoint or user device during this gate.

### 2. Verify ICMP Reachability

Verify each selected target responds to ICMP before creating Zabbix hosts. This
avoids introducing false-positive problems during adoption.

### 3. Create Network Group

Create or reuse a dedicated network group. Keep the name generic and
non-secret.

### 4. Add Hosts

Create one Zabbix host per monitored availability endpoint unless a richer
device model is already prepared.

Link only `ICMP Ping`.

### 5. Validate

Validate:

- each host exists in the network group;
- `ICMP Ping` is linked;
- first `icmpping` value is `1`;
- packet loss value is `0`;
- item state is normal;
- no new active problems were introduced.

## Stop Conditions

Stop before sign-off if any of these are true:

- device ownership or alias is unclear;
- ICMP is blocked or unstable;
- adding a host would require exposing credentials;
- SNMP credentials would enter Git, chat or shell output;
- the adoption would create broad topology disclosure in public artifacts.

## Sign-Off Shape

Use `docs/operator-signoff-template.md` and include:

- date;
- run class: `zabbix-network-icmp-adoption`;
- host group;
- monitored device roles and aliases;
- monitoring class;
- validation summary;
- explicit non-claims.

Non-claims:

- no SNMP coverage;
- no SSH inventory collection;
- no gateway policy validation;
- no DHCP validation;
- no alert routing;
- no Grafana dashboard;
- no full network topology coverage.

## Next Gate

After network ICMP availability is stable, add SNMP read-only coverage for the
security gateway and managed switches, then use those metrics in Grafana.
