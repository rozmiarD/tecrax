# Proxmox Backup Server readiness runbook

This runbook covers readiness for deploying Proxmox Backup Server as the local
operational backup layer for the fresh Proxmox host.

It is not an active Tecrax profile intent. It is an operator-owned readiness
procedure used before any PBS VM/CT deployment or backup-health claim.

## Scope

The readiness pass covers:

- host and storage preflight;
- PBS placement decision;
- datastore and retention decision boundaries;
- first backup and restore-test gates;
- external-copy checkpoint;
- public-safe sign-off.

It does not install PBS, create VM/CT workloads, configure backup jobs, claim
restore readiness, configure off-host replication, or add a Tecrax backup
connector.

## Public and Private Boundary

Safe in public docs and sign-offs:

- generic target aliases and roles;
- storage role names, such as data pool and backup datastore;
- aggregate preflight status;
- operation class: readiness, deployment, backup test or restore test;
- artifact digests and bounded status summaries.

Must remain outside Git and public sign-offs:

- real host addresses and private DNS names;
- PBS admin credentials, API tokens and recovery codes;
- datastore encryption keys;
- exact repository URLs if they reveal topology;
- target catalogs, live environment files and wrapper paths;
- raw logs, full backup job output, file lists and VM disk details;
- full serial inventory or physical bay mapping.

## Placement Decision

PBS on the same physical T150 is allowed only as local operational backup. It is
not disaster recovery and does not satisfy the second-copy requirement.

Recommended readiness decision:

- run PBS as an isolated VM or CT on the data pool, not as an unmanaged set of
  scripts on the Proxmox host;
- keep PBS datastore storage logically separate from Proxmox `vzdump` directory
  storage;
- keep retention explicit and conservative until restore proof exists;
- do not put Vaultwarden or domain-critical services into production before the
  backup and restore path is proven.

The exact VM/CT id, address, hostname, datastore path, credentials and
encryption choices are private operator material.

## Stop Conditions

Stop before deployment if any of these are true:

- host update/reboot status is unresolved;
- data pool is not online or reports data errors;
- PBS placement has not been selected;
- there is no plan for a first restore test;
- the operator cannot distinguish local operational backup from an external
  disaster-recovery copy;
- credentials or encryption keys would need to be exposed to an LLM or public
  repository.

## Preflight Procedure

### 1. Host and storage state

Confirm:

- Proxmox host version and running kernel are known;
- data pool is online with no known data errors;
- backup-capable storage role exists or a new PBS datastore role is planned;
- no existing workloads are assumed to be protected before jobs exist;
- root/operator console access exists for deployment work.

### 2. Workload inventory

Before backup jobs are created, record whether VM/CT workloads exist.

If no VM/CT workloads exist, the first restore proof must wait until a disposable
test VM/CT exists. Do not fabricate restore evidence.

### 3. Datastore and retention

Define, outside Git:

- PBS deployment form: VM or CT;
- datastore role and capacity target;
- retention policy for daily, weekly and monthly backups;
- prune schedule;
- garbage-collection schedule;
- notification path for job failures.

Retention is a policy decision, not proof that backups are restorable.

### 4. First backup gate

The first backup gate is complete only when:

- PBS is reachable through the operator-approved path;
- a datastore exists;
- at least one backup job completed successfully;
- job output is summarized without raw logs or secrets;
- public-safe sign-off records only bounded facts.

### 5. Restore proof gate

Restore proof is separate from backup-job success.

The restore gate is complete only when:

- a disposable VM/CT restore or file-level restore test is executed;
- the restored object boots or the restored file is verified;
- the result is signed off without private topology or raw backup contents.

### 6. External-copy checkpoint

Before any critical service is treated as protected, choose and document a
second copy outside the T150. Valid target classes include:

- NAS or another server;
- offline USB disk rotation;
- remote PBS datastore;
- another operator-approved storage repository.

Until this exists and is tested, PBS remains local operational backup only.

## Validation

PBS readiness is complete when:

- host/storage preflight is documented;
- deployment form is selected or a blocker is explicit;
- datastore and retention decisions are documented privately;
- first-backup and restore-test gates are defined;
- external-copy requirement is documented as pending or satisfied;
- public-safe sign-off is written.

## Sign-Off Shape

Use `docs/operator-signoff-template.md` and include:

- date;
- generic target alias;
- run class: `pbs-readiness`;
- host/storage preflight summary;
- workload inventory status;
- PBS placement decision or blocker;
- datastore/retention decision status;
- external-copy checkpoint status;
- explicit non-claims.

Non-claims:

- no PBS deployment unless actually installed;
- no backup job success unless a job actually completed;
- no restore readiness unless a restore test actually passed;
- no external disaster-recovery copy until a second target exists;
- no secret, credential, key or raw-backup-content exposure.

## Next Gate

After readiness, either deploy PBS with a private operator plan or stop and
resolve placement/external-copy blockers before critical services depend on it.
