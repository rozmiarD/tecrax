# Frigate host monitoring runbook

This runbook covers the first monitoring baseline for an existing Ubuntu host
running Frigate.

It adds host-level telemetry, security telemetry and bounded Frigate service
availability checks. It does not collect camera credentials, camera streams,
recording payloads, event clips, object detections or private video metadata.

## Scope

Allowed:

- establish key-based operator access through the standard `rexecop` account;
- verify Ubuntu host identity, time synchronization and storage pressure;
- install and configure Zabbix Agent 2 for active checks;
- enroll the host into Wazuh as a Linux infrastructure endpoint;
- add Zabbix ICMP, Linux active-agent and bounded Frigate TCP service checks;
- monitor Frigate web/API listener availability without authentication;
- monitor Frigate RTSP listener availability without fetching stream payloads;
- monitor recording storage usage through host filesystem metrics;
- record a public-safe sign-off.

Not allowed:

- read, copy or delete recordings;
- enumerate camera credentials;
- fetch RTSP/video streams;
- export Frigate event clips, snapshots or object metadata;
- change Frigate retention policy;
- clean up storage automatically;
- add the monitoring account to the Docker group as a shortcut;
- expose private host addresses, camera names or credentials in Tecrax.

## Public and Private Boundary

Safe in public docs and sign-offs:

- host alias;
- operating-system family and product major line;
- agent package classes;
- Frigate service check classes;
- storage usage summary without path-sensitive data;
- validation status;
- explicit non-claims.

Must remain outside Git and public sign-offs:

- private host address and SSH fingerprints;
- SSH private keys and known_hosts files;
- camera credentials and stream URLs;
- Frigate configuration containing camera definitions;
- recordings, snapshots, clips and event payloads;
- Zabbix API tokens and Wazuh enrollment material;
- raw command transcripts if they expose topology or secrets.

## Baseline Model

Use the existing Ubuntu host as a monitored infrastructure endpoint.

Recommended public alias:

```text
<frigate-host>
```

Recommended first checks:

- ICMP availability from Zabbix;
- `zabbix-agent2` active checks;
- Wazuh agent active status;
- Frigate HTTP/UI listener TCP check;
- Frigate RTSP listener TCP check;
- filesystem usage for the recordings mount.

Do not use Docker socket access for the first Tecrax-owned monitoring gate. If
container health is needed, prefer a later bounded check with an explicit
contract and least-privilege execution path.

## Procedure

### 1. Establish Operator Access

Create or validate the standard operator account:

```text
rexecop
```

Use key-based SSH with strict host-key checking. Keep the key and known_hosts
file outside the repository.

If temporary root access is used for bootstrap, close the bootstrap path after
key-based `rexecop` access and sudo behavior are verified.

### 2. Read-Only Host Baseline

Collect only bounded host facts:

- hostname and OS family;
- time synchronization state;
- root filesystem usage;
- Frigate recordings/storage mount usage;
- Docker presence;
- Frigate container high-level state.

Do not inspect Frigate camera configuration or recordings.

### 3. Zabbix Baseline

In Zabbix, create or update one host for the Frigate system:

- host alias matches the approved inventory alias;
- group includes the infrastructure/monitoring group;
- templates include ICMP and Linux active-agent baseline;
- no duplicate temporary host is created.

On the Ubuntu host:

- install `zabbix-agent2` from an operator-approved package source;
- configure `ServerActive` for the Zabbix server;
- set `Hostname` to the Zabbix host alias;
- enable and start the agent.

Validate:

- `zabbix-agent2` service is enabled and active;
- `agent.ping` becomes healthy;
- storage mount metrics are discovered;
- Frigate listener checks report healthy values.

### 4. Frigate Service Checks

Add only unauthenticated availability checks in the first gate:

```text
Frigate web/API listener TCP
Frigate RTSP listener TCP
```

These checks prove port-level availability only. They do not prove camera health,
recording correctness, stream quality or event detection behavior.

### 5. Wazuh Baseline

Install and enroll `wazuh-agent` using the approved manager endpoint and host
alias.

After installation:

- enable and start the agent;
- verify the agent is active on the Wazuh manager;
- disable the Wazuh package repository on the endpoint, keeping upgrades in a
  planned maintenance window.

### 6. Storage Pressure Handling

If the recordings mount is near full:

- alert through Zabbix;
- record the risk;
- do not delete or prune recordings automatically;
- require an operator decision for retention, cleanup, archive or storage
  expansion.

Treat a rotation-managed recordings filesystem as a workload, not as a generic
office-server volume. A high percentage-used value can be the intended steady
state when Frigate continuously expires old recordings. Do not suppress the
whole host and do not keep permanently firing percentage or ordinary HDD
latency triggers merely to show that steady state.

Prefer narrow workload signals:

- a minimum free-byte safety reserve sustained for a bounded window;
- filesystem read-only state and inode exhaustion;
- sustained disk utilization, rather than a generic seek-latency threshold;
- Frigate HTTP and RTSP availability;
- host and monitoring-agent availability;
- actual memory pressure, rather than swap occupancy alone.

Retain exact rollback IDs for every disabled generic trigger and every
workload-specific replacement. A monitoring change must not alter retention,
delete recordings, restart the container or hide camera-service outages.

## Stop Conditions

Stop if:

- the host identity is ambiguous;
- the operator would need to expose camera credentials;
- monitoring requires reading recordings or streams;
- package installation would restart Frigate or Docker unexpectedly;
- Zabbix host creation would duplicate an existing host;
- Wazuh enrollment creates duplicate stale agents;
- storage cleanup is suggested without explicit operator approval.

## Sign-Off Shape

Use `../operator-signoff-template.md` and include:

- date;
- run class: `frigate-host-monitoring-baseline`;
- host alias;
- Zabbix baseline status;
- Wazuh baseline status;
- Frigate listener checks;
- storage pressure summary;
- generic-trigger overrides and their workload-specific replacements;
- explicit non-claims.

Non-claims:

- no camera stream monitoring;
- no recording cleanup;
- no Frigate retention change;
- no camera credential handling;
- no compliance hardening.

## Tecrax Artifact Decision

Current activation level: `L1 - public-safe runbook`.

Frigate-specific Tecrax facts or intents should be added only if the live
baseline proves that generic Ubuntu/Zabbix checks are not enough. Candidate
future facts may include bounded camera availability counts, recording backlog
pressure or storage retention risk, but never stream payloads or credentials.
