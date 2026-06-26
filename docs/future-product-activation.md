# Future product activation gates

Tecrax does not add an intent merely because a product is planned, installed
elsewhere, or useful in the future. A product-specific operation becomes active
only when a real endpoint exists and the profile can describe bounded read-only
semantics without taking over RExecOp, GovEngine or SCLite responsibilities.

This document is a gate list, not an active catalog.

## Current decision

The active profile contains no Proxmox, PBS, Wazuh, Samba, Grafana, Frigate,
Hillstone, printer, camera, backup-job or generic deployment intents. Historical
fixture or local-stub behavior is not an operator capability.

Current active work is limited to:

- Ubuntu host observations that are already represented by active Tecrax facts;
- bounded Docker systemd service/socket observation, not Docker socket inventory;
- bounded Zabbix, AdGuard and Portainer health/count summaries already declared
  in the active profile;
- bounded legacy network-device identity and SSH management posture.

## Universal activation gates

Before a new product operation enters `src/tecrax/profile/intents/`, all of these
must be true:

1. The endpoint exists in the operator environment and the operator explicitly
   asks to activate it.
2. The first operation is read-only and bounded.
3. A threat model names what data must never enter facts, evidence, receipts or
   public fixtures.
4. Least-privilege access is proven and secrets remain outside Git.
5. The connector action contract is fixed; no generic passthrough is allowed.
6. A versioned facts contract and JSON schema exist with explicit non-claims.
7. Public fixtures are synthetic or sanitized and include negative vectors.
8. RExecOp can plan/run it through normal lifecycle without domain logic in
   `src/rexecop`.
9. GovEngine admission is required for operation and connector actions.
10. SCLite receipt/bundle output is produced or the blocker is explicit.
11. Public docs and changelog match the code.
12. Operator sign-off contains no private topology, addresses, credentials or
    hostnames.

## Product-specific gates

| Product area | Activation condition | First allowed shape | Explicitly out of scope |
| --- | --- | --- | --- |
| Proxmox | Real Proxmox endpoint and read-only API role exist. | inventory/readiness summaries only. | VM creation, power actions, storage mutation, cluster changes. |
| PBS | Real PBS endpoint and read-only role exist. | backup readiness, job summary and restore-evidence separation. | Calling backup healthy without restore evidence, prune/mutation actions. |
| Wazuh | Real Wazuh endpoint and least-privilege read-only API exist. | count summaries by state/severity. | SIEM replacement, agent management, rule changes. |
| Samba | Real Samba service exists and read-only status can be bounded. | service/share readiness counts without identities. | ACL/user/group dumps, share mutation. |
| Grafana | Real Grafana endpoint and read-only API role exist. | dashboard/datasource reachability counts. | dashboard export with secrets, alert mutation. |
| Frigate | Signals are not covered by generic Ubuntu host checks. | camera availability counts, recording backlog or storage pressure. | stream capture, camera credentials, object/event dumps. |
| Hillstone | Separate threat model for firewall read-only observation is approved. | bounded inventory/posture counts only. | firewall policy dump, NAT/VPN rules, mutation. |
| Printers | Read-only protocol and privacy boundary are approved. | model/status/supply summaries. | job/user history, address books, scan destinations. |
| Switch VLAN/port-security | `docs/vlan-port-security-readonly-checkpoint.md` gates pass. | count/boolean summaries only. | full config, MACs, interface identity, SNMP communities. |

## Backup semantics

Backup work must not collapse different meanings into one `healthy` flag. Future
backup support must separate:

- configuration readiness;
- job execution status;
- restore-test evidence;
- coverage and retention semantics;
- blockers and unknown states.

A successful job status without restore evidence is not a healthy backup claim.

## Frigate semantics

Frigate is not activated simply because it runs on Ubuntu. Generic host health,
load, filesystem, memory, Docker systemd state and update posture belong to the
existing hostlike operations. Frigate-specific activation is justified only for
bounded signals not already covered, such as camera availability counts,
recording backlog or storage pressure.

## Active-profile guard

Until the gates are satisfied, do not add placeholder files for future products:

- no intent YAML;
- no workflow YAML;
- no connector contract;
- no validation rule;
- no target catalog capability;
- no example environment policy rule;
- no public claim in README or operation catalog.

The correct output for a future product before activation is this document plus,
if needed, a separate design checkpoint. It is not an inactive hidden operation.
