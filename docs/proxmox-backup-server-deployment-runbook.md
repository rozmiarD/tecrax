# Proxmox Backup Server deployment runbook

This runbook covers deployment of Proxmox Backup Server as a local operational
backup VM for the fresh Proxmox host.

It is not an active Tecrax profile intent and does not add a backup connector.
It is an operator-owned deployment procedure that must produce public-safe
sign-off evidence before any backup-health or restore-readiness claim exists.

## Scope

The deployment pass covers:

- VM deployment for PBS;
- datastore creation through PBS tooling;
- operator account bootstrap;
- SSH and guest-agent access validation;
- reboot validation;
- public-safe deployment sign-off.

It does not create production backup jobs, prove restore, configure external
replication, rotate credentials, define long-term retention, or activate a
Tecrax backup-status intent.

## Public and Private Boundary

Safe in public docs and sign-offs:

- generic target aliases and roles;
- deployment form: VM or CT;
- bounded service status;
- datastore name if it is non-sensitive;
- reboot proof summary;
- explicit non-claims and next gates.

Must remain outside Git and public sign-offs:

- real addresses, hostnames that reveal topology, fingerprints and key paths;
- root passwords, operator passwords, API tokens and datastore encryption keys;
- exact VM ids if they identify private infrastructure;
- raw installer logs, screenshots with private details and full command output;
- backup contents, backup namespaces and repository URLs that reveal topology.

## Prerequisites

- Proxmox host readiness is complete.
- PBS readiness sign-off exists.
- Operator has break-glass console access.
- Operator account naming follows the environment hard rule: use `rexecop`.
- Bootstrap credentials are temporary and must be rotated outside LLM/tooling.
- PBS datastore target is logically separate from Proxmox `vzdump` storage.

## Deployment Procedure

### 1. Prepare the install media

Use the official PBS ISO and verify its checksum before use. If unattended
install is used, keep the answer file and first-boot customization outside Git.

The answer file may contain secrets and target topology. It is private operator
material.

### 2. Create the VM

Use a small system disk and a separate datastore disk. Keep the datastore disk
on the data pool selected during readiness. Enable QEMU guest agent in the VM
configuration.

Do not claim the VM protects any workload until a backup job and restore proof
exist.

### 3. Install PBS

Install PBS from the verified media. Remove install media or set boot order to
the installed disk before the first normal boot.

If unattended install does not complete first-boot customization, use break-glass
console access and repair only the missing bounded items:

- bootloader/initramfs;
- SSH host keys and SSH service;
- `rexecop` account and key-based login;
- passwordless sudo for `rexecop`;
- no-subscription repository;
- QEMU guest agent;
- datastore creation through PBS tooling.

### 4. Create the datastore

Create the local datastore through PBS tooling rather than hand-editing PBS
configuration. Keep datastore path, disk identity and capacity details private
unless the operator has explicitly classified them as safe.

### 5. Validate access

Validate:

- SSH as `rexecop`;
- passwordless sudo for `rexecop`;
- QEMU guest agent reachable from Proxmox;
- PBS services active;
- PBS web/API listener active;
- datastore listed by PBS tooling.

### 6. Reboot proof

Reboot the PBS VM once before sign-off. After reboot, validate again:

- boot completes without install media;
- network returns;
- SSH as `rexecop` works;
- guest agent is reachable;
- PBS services are active;
- datastore is mounted and listed.

## Stop Conditions

Stop before sign-off if any of these are true:

- boot requires manual intervention after install;
- bootstrap credential cannot be rotated by the operator;
- SSH or guest agent access is unavailable;
- datastore was created by ad-hoc manual config instead of PBS tooling;
- PBS service status is unknown;
- the VM was not reboot-tested;
- evidence would require exposing secrets, fingerprints, raw logs or topology.

## Sign-Off Shape

Use `docs/operator-signoff-template.md` and include:

- date;
- generic target alias;
- run class: `pbs-deployment`;
- deployment form;
- service status summary;
- datastore status summary;
- reboot proof summary;
- manual remediation summary, if any;
- explicit non-claims.

Non-claims:

- no production backup coverage until jobs run;
- no restore readiness until restore proof passes;
- no external disaster recovery until a second copy exists;
- no credential-rotation completion unless the operator confirms it outside
  LLM/tooling.

## Next Gate

After deployment, rotate temporary bootstrap credentials outside LLM/tooling,
choose retention, create a first backup job and perform restore proof before
critical services depend on PBS.
