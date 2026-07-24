# Zabbix network SNMP adoption runbook

This runbook covers the first SNMP monitoring adoption gate for selected network
devices in the Proxmox deployment.

It extends the earlier ICMP-only network baseline with read-only SNMP metrics.
It also covers basic network-device time synchronization where the device and
network policy allow it.

## Scope

The adoption pass covers:

- enabling read-only SNMP for selected network devices;
- restricting SNMP access to the monitoring host where the device supports it;
- storing SNMP credentials outside Git;
- linking suitable Zabbix SNMP templates;
- validating SNMP availability and first system OID values;
- configuring network devices to use the local NTP server where reachable;
- recording public-safe sign-off evidence.

It does not change forwarding policy, reset devices, expose credentials, perform
full topology discovery, create alert routes or tune every vendor-specific
metric.

## Public and Private Boundary

Safe in public docs and sign-offs:

- device aliases and roles;
- SNMP version class;
- template names;
- NTP status class;
- validation summary;
- explicit non-claims.

Must remain outside Git and public sign-offs:

- SNMP communities, SNMPv3 passwords and secret paths;
- SSH passwords, private keys and host fingerprints;
- raw device configuration;
- full VLAN addressing and firewall policy;
- serial numbers and license identifiers.

## Prerequisites

- Zabbix VM deployment gate is complete.
- Network ICMP baseline is complete.
- Zabbix API token is available from an operator-owned secret path outside Git.
- Device management access is available through operator-owned credentials.
- The operator has approved bounded configuration changes for SNMP/NTP only.

## Procedure

### 1. Read current state

Before changing a device, record current state with read-only commands:

- software/device summary;
- current clock or NTP status;
- current SNMP status;
- current management access constraints.

Do not dump full running configuration into public artifacts.

### 2. Configure time synchronization

Point the device at the local infrastructure NTP server where supported.

If the device is in another subnet, confirm that policy allows the device to
initiate NTP to the server. A configured NTP server without reachability is a
pending state, not a successful sync.

### 3. Configure read-only SNMP

Prefer SNMPv3 AuthPriv when the device syntax and credential custody are clear.

If a legacy device is adopted through SNMPv2c:

- generate a unique community per device;
- keep the community outside Git;
- restrict access to the monitoring host where supported;
- rotate any community that was exposed during troubleshooting.

### 4. Validate from Zabbix host

Validate with bounded SNMP reads before linking templates:

- `sysDescr`;
- `sysUpTime`;
- `sysObjectID`.

Do not print communities or SNMPv3 secrets in command output.

### 5. Link Zabbix templates

Add a dedicated SNMP interface and host-level secret macro. Link a vendor or
generic SNMP template.

If the SNMP template already includes ICMP checks, replace the standalone
`ICMP Ping` template on that same host to avoid duplicate item keys.

### 6. Validate in Zabbix

Validate:

- SNMP interface availability is healthy;
- expected system OID items have values;
- `icmpping` remains healthy;
- packet loss is zero;
- no active Zabbix problems were introduced.

### 7. Add bounded license-lifecycle visibility

When the vendor SNMP surface does not expose module-expiration dates, use a
separate read-only collector instead of embedding management credentials or
license payloads in Zabbix.

The collector must:

- verify the exact device identity before every read;
- use only documented read-only license-summary commands;
- keep raw license identifiers, customer fields and encoded license payloads
  in process memory only;
- persist only normalized module names and absolute expiration dates;
- select the latest absolute expiration for each required module when the
  appliance retains historical renewal records;
- reject missing required modules or non-absolute trial values instead of
  guessing;
- expose collector health and data age separately from license expiration.

Run the collector on a bounded schedule appropriate to the lifecycle signal.
Daily collection is sufficient for thresholds measured in days. In Zabbix,
create one expiration item per module and use non-overlapping thresholds:

- warning when fewer than 60 but at least 30 days remain;
- high severity when fewer than 30 days remain;
- a separate collection-health trigger when the last successful read is stale.

Grafana may visualize these Zabbix items, but must not become the alert source
of record. Firmware entitlement and the supported upgrade or downgrade path
still require confirmation from the vendor or authorized partner; license
telemetry is not approval to upgrade.

## Stop Conditions

Stop before sign-off if any of these are true:

- secrets would be exposed in Git or public docs;
- device requires a reset or broad policy change;
- SNMP read-only cannot be enforced or scoped;
- Zabbix template conflicts would delete useful existing monitoring;
- NTP requires firewall policy changes that have not been reviewed;
- vendor CLI syntax is ambiguous for a mutating command.
- the collector would persist license identifiers, encoded payloads or customer
  data;
- historical license records cannot be deterministically reduced to the
  current absolute expiration;

## Sign-Off Shape

Use `../operator-signoff-template.md` and include:

- date;
- run class: `zabbix-network-snmp-adoption`;
- adopted device roles and aliases;
- SNMP version class and template class;
- NTP status summary;
- validation summary;
- explicit non-claims.

Non-claims:

- no alert routing;
- no Grafana dashboard;
- no full network topology discovery;
- no firewall policy audit;
- no SNMP trap handling;
- no complete vendor-specific health coverage.

## Next Gate

Use SNMP network metrics in Grafana. Resolve any remaining NTP reachability
gaps during the firewall/security policy pass before treating all network
devices as time-synchronized.
